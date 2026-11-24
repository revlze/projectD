"""Experiment matrix E0-E4 (docs/experiments.md, section 3) and its resumable runner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from project_d.agents.llm_client import (
    DEFAULT_MODEL,
    ChatClient,
    LLMConfig,
    OpenAICompatibleClient,
)
from project_d.agents.prompts import PROMPT_VERSION, build_protocol_prompt, prompt_sha256
from project_d.agents.providers import PROVIDERS, is_local, provider_config
from project_d.agents.runner import LLMEpisode, run_llm_episode, write_episode
from project_d.agents.tools import tool_schemas
from project_d.environment.actions import SubmitJob
from project_d.environment.env import Environment
from project_d.environment.model import (
    AgentSpec,
    Job,
    Option,
    RunConfig,
    Scenario,
    load_scenario,
)
from project_d.evaluation.audit import audit_episode
from project_d.evaluation.metrics import agreement_metrics, episode_metrics
from project_d.experiments.generator import validate_dataset
from project_d.experiments.storage import RunStore, file_sha256, fingerprint
from project_d.simulation.scheduler import ScriptedPolicy, run_episode

DATA_ROOT = Path("data/scenarios")

# Ollama defaults to 4096 below 24 GiB of VRAM and then silently drops the start of the history.
REQUIRED_CONTEXT = 16384
CONTEXT_SAFETY = 0.9

# Every profile runs both processing orders crossed with both role assignments.
REPEATS = (("A", False), ("B", False), ("A", True), ("B", True))

BASELINE_VARIANTS = (
    "U/N",
    "U/F",
    "A/N",
    "A/F",
    "U/R1",
    "A/R1",
    "U/R3",
    "A/R3",
    "U/R3P",
    "A/R3P",
)
E3_VARIANTS = ("A/S", "A/S+V", "A/S+G", "A/VBC-r0", "A/VBC-r2")
E1_VARIANTS = (*BASELINE_VARIANTS, *E3_VARIANTS[:3], "A/VBC", *E3_VARIANTS[3:])
E2_VARIANTS = (*BASELINE_VARIANTS, "A/VBC")
E4_H1_VARIANTS = ("U/N", "U/R3P")
E4_H1_PROFILES = ("test/test_s1_01.json", "test/test_s1_02.json")
E4_DELAY_VARIANTS = ("A/R3P", "A/VBC")
E4_DELAYS = (4, 8)
E4_COMMIT_DELAYS = (0, 1, 3)
E4_START_GAPS = (0, 2, 4)
SERIES = ("E1", "E2", "E3", "E4-H1", "E4-delay")


@dataclass(frozen=True)
class EpisodeSpec:
    series: str
    profile: str
    variant: str
    repeat: int
    commit_delay: int | None = None
    start_gap: int = 0
    message_delay: int | None = None

    @property
    def split(self) -> str:
        return self.profile.split("/", 1)[0]

    @property
    def name(self) -> str:
        profile = Path(self.profile).stem
        variant = self.variant.replace("/", "-").replace("+", "_")
        parts = [self.series, profile, variant, f"r{self.repeat}"]
        if self.commit_delay is not None:
            parts.append(f"cd{self.commit_delay}")
        if self.start_gap:
            parts.append(f"gap{self.start_gap}")
        if self.message_delay is not None:
            parts.append(f"md{self.message_delay}")
        return "__".join(parts)

    def run_config(self, scenario: Scenario) -> RunConfig:
        first_agent, role_swap = REPEATS[self.repeat]
        overrides: dict[str, Any] = {}
        if self.commit_delay is not None:
            overrides["commit_delay"] = self.commit_delay
        if self.message_delay is not None:
            overrides["message_delay"] = self.message_delay
        return RunConfig.for_protocol(
            self.variant,
            first_agent=first_agent,
            role_swap=role_swap,
            start_gap=self.start_gap,
            environment_seed=scenario.seed,
            **overrides,
        )


def load_manifest(data_root: Path) -> dict[str, Any]:
    return validate_dataset(data_root)


def verify_profiles(data_root: Path, manifest: dict[str, Any], profiles: Iterable[str]) -> None:
    """Refuse to run on inputs that differ from the frozen manifest."""
    for profile in sorted(set(profiles)):
        digest = hashlib.sha256((data_root / profile).read_bytes()).hexdigest()
        if digest != manifest["files"][profile]["sha256"]:
            raise ValueError(f"{profile} differs from the frozen manifest")


def build_matrix(series: str, manifest: dict[str, Any]) -> list[EpisodeSpec]:
    files = manifest["files"]
    split = {
        name: [p for p in sorted(files) if p.startswith(f"{name}/")] for name in ("dev", "test")
    }
    repeats = range(len(REPEATS))

    def grid(profiles: Iterable[str], variants: Iterable[str]) -> list[EpisodeSpec]:
        return [
            EpisodeSpec(series, profile, variant, repeat)
            for profile, variant, repeat in itertools.product(profiles, variants, repeats)
        ]

    match series:
        case "E1":
            return grid(split["dev"], E1_VARIANTS)
        case "E2":
            return grid(split["test"], E2_VARIANTS)
        case "E3":
            return grid(manifest["e3_subset"], E3_VARIANTS)
        case "E4-H1":
            return [
                EpisodeSpec(series, profile, variant, repeat, commit_delay=delay, start_gap=gap)
                for profile, variant, delay, gap, repeat in itertools.product(
                    E4_H1_PROFILES, E4_H1_VARIANTS, E4_COMMIT_DELAYS, E4_START_GAPS, repeats
                )
            ]
        case "E4-delay":
            s4 = [p for p in split["test"] if files[p]["family"] == "S4"]
            return [
                EpisodeSpec(series, profile, variant, repeat, message_delay=delay)
                for profile, variant, delay, repeat in itertools.product(
                    s4, E4_DELAY_VARIANTS, E4_DELAYS, repeats
                )
            ]
    raise ValueError(f"unknown series {series!r}")


def context_problem(episode: LLMEpisode, context_length: int | None) -> str | None:
    """Return usage warnings, not proof of truncation or a reason to discard an episode."""
    by_agent: dict[str, list[int]] = {}
    for turn in episode.turns:
        by_agent.setdefault(turn.agent_id, []).append(turn.usage.get("prompt_tokens", 0))
    drops = sum(
        after < before
        for tokens in by_agent.values()
        for before, after in itertools.pairwise(tokens)
    )
    warnings = []
    if drops:
        warnings.append(
            f"context_usage_drop: prompt size fell {drops} times; phase tool sets can shrink"
        )
    largest = max((max(tokens) for tokens in by_agent.values()), default=0)
    if context_length is not None and largest >= CONTEXT_SAFETY * context_length:
        warnings.append(f"context_limit: prompt reached {largest} of {context_length} tokens")
    return "; ".join(warnings) or None


def summarize_episode(
    spec: EpisodeSpec,
    scenario: Scenario,
    episode: LLMEpisode,
    context_length: int | None = None,
) -> dict[str, Any]:
    first_agent, role_swap = REPEATS[spec.repeat]
    row: dict[str, Any] = {
        "episode": spec.name,
        "series": spec.series,
        "profile": Path(spec.profile).stem,
        "family": scenario.family,
        "variant": spec.variant,
        "repeat": spec.repeat,
        "first_agent": first_agent,
        "role_swap": role_swap,
        "start_gap": spec.start_gap,
        "failure": episode.failure,
        "context_warning": context_problem(episode, context_length),
        "max_prompt_tokens": max(
            (turn.usage.get("prompt_tokens", 0) for turn in episode.turns), default=0
        ),
        "llm_turns": len(episode.turns),
        "parse_errors": sum(turn.parse_error is not None for turn in episode.turns),
        "length_finishes": sum(turn.finish_reason == "length" for turn in episode.turns),
        "prompt_tokens": sum(turn.usage.get("prompt_tokens", 0) for turn in episode.turns),
        "completion_tokens": sum(turn.usage.get("completion_tokens", 0) for turn in episode.turns),
        "llm_seconds": round(sum(turn.latency_s for turn in episode.turns), 3),
        "prompt_version": episode.prompts.get("version"),
    }
    if episode.result is None:
        return row
    result = episode.result
    metrics = episode_metrics(scenario, result.metadata, result.log)
    audit = metrics.audit
    if audit.issues and row["failure"] is None:
        row["failure"] = "environment_audit_failed"
    row |= {
        "commit_delay": result.metadata.commit_delay,
        "message_delay": result.metadata.message_delay,
        "violated": audit.violated,
        "max_overrun": audit.max_overrun,
        "U": metrics.raw_utility,
        "U_safe": metrics.safe_utility,
        "U_star": metrics.optimal_utility,
        "safe_fraction": metrics.safe_fraction,
        "completed_jobs": metrics.completed_jobs,
        "budget_refusals": metrics.budget_refusals,
        "unused_budget": metrics.unused_budget,
        "completion_time": metrics.completion_time,
        "messages": metrics.message_count,
        "tool_calls": len(result.calls),
        "rounds_missed": sum(e.event_type == "round_missed" for e in result.log),
        "rounds_skipped": sum(e.event_type == "round_skipped" for e in result.log),
        "early_finish_attempts": sum(
            e.event_type == "finish" and e.result == "finish_not_open" for e in result.log
        ),
        "agreement": audit.agreement,
        "plan_mismatches": audit.plan_mismatches,
        "audit_issues": len(audit.issues),
    }
    shown = [(turn.agent_id, turn.logical_time, turn.shown_plan) for turn in episode.turns]
    row |= asdict(agreement_metrics(result.log, result.metadata.budget, shown))
    resolved = spec.run_config(scenario).apply(scenario)
    row["primary_completed"] = {
        agent.agent_id: {
            "job_id": agent.jobs[0].job_id,
            "completed": agent.jobs[0].job_id in audit.completed_jobs,
        }
        for agent in resolved.agents
    }
    return row


def _write_table(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _command_output(*command: str) -> str | None:
    try:
        done = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip()


def _server_version(base_url: str) -> str | None:
    url = base_url.rstrip("/").removesuffix("/v1") + "/api/version"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8")).get("version")
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def _model_card(llm: LLMConfig) -> dict[str, Any] | None:
    """Weights file and parameters, so an alias such as a thread-limited copy is traceable."""
    url = llm.base_url.rstrip("/").removesuffix("/v1") + "/api/show"
    request = urllib.request.Request(url, data=json.dumps({"model": llm.model}).encode("utf-8"))
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            card = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None
    weights = next(
        (
            line.split()[1]
            for line in card.get("modelfile", "").splitlines()
            if line.startswith("FROM ")
        ),
        None,
    )
    return {
        "weights": weights and Path(weights).name,
        "parameters": card.get("parameters"),
        "template": card.get("template"),
        "details": card.get("details"),
    }


def loaded_context_length(llm: LLMConfig) -> int | None:
    """Load the model with a minimal request and read the context the server actually gave it."""
    OpenAICompatibleClient(replace(llm, max_tokens=1)).chat([{"role": "user", "content": "ok"}], [])
    url = llm.base_url.rstrip("/").removesuffix("/v1") + "/api/ps"
    with urllib.request.urlopen(url, timeout=5) as response:
        models = json.loads(response.read().decode("utf-8")).get("models", [])
    return next((m.get("context_length") for m in models if m.get("name") == llm.model), None)


SERVER_ENV = (
    "OLLAMA_CONTEXT_LENGTH",
    "OLLAMA_FLASH_ATTENTION",
    "OLLAMA_KV_CACHE_TYPE",
    "OLLAMA_NUM_PARALLEL",
)


def hardware() -> dict[str, Any]:
    """Name the machine, since CUDA and Metal sample different tokens from the same seed."""
    gpu = _command_output(
        "nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"
    )
    chip = None if gpu else _command_output("sysctl", "-n", "machdep.cpu.brand_string")
    return {"platform": platform.platform(), "gpu": gpu, "chip": chip}


def run_manifest(
    llm: LLMConfig, base_seed: int, context_length: int | None, provider: str = "ollama"
) -> dict[str, Any]:
    settings = asdict(llm)
    settings.pop("seed")
    if not is_local(provider):
        # Hosted weights cannot be pinned; record the provider and the date instead.
        return {
            "provider": provider,
            "llm": settings,
            "context_length": context_length,
            "llm_base_seed": base_seed,
            "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "git_commit": _command_output("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_command_output("git", "status", "--porcelain")),
            "prompt_version": PROMPT_VERSION,
        }
    return {
        "llm": settings,
        "context_length": context_length,
        "llm_base_seed": base_seed,
        "server_version": _server_version(llm.base_url),
        "model_card": _model_card(llm),
        "hardware": hardware(),
        # Only meaningful when the server shares this environment, as on a vast.ai pod.
        "ollama_env": {name: os.environ.get(name) for name in SERVER_ENV},
        "git_commit": _command_output("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_command_output("git", "status", "--porcelain")),
        "prompt_version": PROMPT_VERSION,
    }


def run_specs(
    specs: list[EpisodeSpec],
    data_root: Path,
    output_dir: Path,
    client_for_seed: Callable[[int], ChatClient],
    base_seed: int = 0,
    context_length: int | None = None,
    *,
    run_identity: dict[str, Any],
    workers: int = 1,
) -> list[dict[str, Any]]:
    """Resume only identical, complete episodes; preserve failed attempts before retrying."""
    if not specs or len({spec.name for spec in specs}) != len(specs):
        raise ValueError("Episode selection must be nonempty and have unique keys")
    if any(spec.variant not in BASELINE_VARIANTS for spec in specs):
        raise ValueError("Structured protocols require the separate VBC implementation stage")
    manifest = load_manifest(data_root)
    verify_profiles(data_root, manifest, (spec.profile for spec in specs))
    source_root = Path(__file__).resolve().parents[1]
    source_hashes = {
        path.relative_to(source_root).as_posix(): hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for path in sorted(source_root.rglob("*.py"))
    }
    identities = {}
    for spec in specs:
        scenario = load_scenario(data_root / spec.profile)
        config = spec.run_config(scenario)
        resolved = config.apply(scenario)
        ids = [agent.agent_id for agent in resolved.agents]
        opens = config.open_times(ids)
        identities[spec.name] = {
            "spec": asdict(spec),
            "llm_seed": base_seed + spec.repeat,
            "scenario_sha256": file_sha256(data_root / spec.profile),
            "config": asdict(config),
            "metadata": asdict(Environment(scenario, config).metadata),
            "system_sha256": {
                agent.agent_id: prompt_sha256(
                    build_protocol_prompt(
                        agent,
                        next(peer for peer in ids if peer != agent.agent_id),
                        config.variant,
                        opens[agent.agent_id],
                    )
                )
                for agent in resolved.agents
            },
            "tools_sha256": {
                phase: fingerprint(tool_schemas(config.variant, phase))
                for phase in ("preparation", "message_round", "execution_wait", "execution")
            },
        }
    identity = {
        "schema_version": 1,
        "runtime": run_identity,
        "source_sha256": source_hashes,
        "prompt_version": PROMPT_VERSION,
        "context_length": context_length,
        "episodes": identities,
        "scenario_manifest_sha256": file_sha256(data_root / "manifest.json"),
    }
    with RunStore(output_dir, identity) as store:
        saved = {spec.name: store.load(spec.name) for spec in specs}
        pending = [spec for spec in specs if saved[spec.name] is None]

        def run_one(spec: EpisodeSpec) -> dict[str, Any]:
            # Each episode writes only its own files, so episodes can run side by side.
            scenario = load_scenario(data_root / spec.profile)
            client = client_for_seed(base_seed + spec.repeat)
            episode = run_llm_episode(scenario, spec.run_config(scenario), client)
            write_episode(output_dir, spec.name, episode)
            row = summarize_episode(spec, scenario, episode, context_length)
            store.complete(spec.name, row)
            print(f"[{spec.name}] {row.get('U_safe', 'failed')}", flush=True)
            return row

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            done = dict(zip((s.name for s in pending), pool.map(run_one, pending), strict=True))
        rows = [saved[spec.name] or done[spec.name] for spec in specs]
        _write_table(output_dir / "summary.csv", rows)
    return rows


def run_e0(output_dir: Path) -> list[dict[str, Any]]:
    """The 108 scripted mechanism runs. No LLM is involved."""
    rows = []
    for (budget, cost_a, cost_b), delay, offset, mode, first in itertools.product(
        ((12, 5, 6), (12, 7, 6), (12, 7, 5)), (0, 1, 3), (0, 1, 3), ("U/N", "A/N"), ("A", "B")
    ):
        scenario = Scenario(
            scenario_id="e0",
            family="E0",
            budget=budget,
            horizon=80,
            commit_delay=delay,
            message_delay=1,
            agent_turn_limit=24,
            seed=0,
            agents=(
                AgentSpec("A", "e0", (Job("job_a", (Option("full", cost_a, 2, 1),)),)),
                AgentSpec("B", "e0", (Job("job_b", (Option("full", cost_b, 2, 1),)),)),
            ),
        )
        policies = {
            "A": ScriptedPolicy({40: SubmitJob("job_a", "full")}),
            "B": ScriptedPolicy({40 + offset: SubmitJob("job_b", "full")}),
        }
        config = RunConfig.for_protocol(mode, first_agent=first)
        result = run_episode(scenario, config, policies)
        report = audit_episode(result.metadata, result.log)
        rows.append(
            {
                "budget": budget,
                "cost_a": cost_a,
                "cost_b": cost_b,
                "commit_delay": delay,
                "offset": offset,
                "mode": mode,
                "first_agent": first,
                "violated": report.violated,
                "max_overrun": report.max_overrun,
                "completed": "+".join(report.completed_jobs),
                "audit_issues": len(report.issues),
            }
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_table(output_dir / "e0.csv", rows)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("series", choices=("E0", *SERIES))
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--provider", choices=tuple(PROVIDERS), default="ollama")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", help="Overrides the provider's endpoint")
    parser.add_argument(
        "--reasoning-effort",
        default="none",
        help='Sent as reasoning_effort; "omit" leaves the field out of the request',
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Episodes run in parallel within this process"
    )
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--llm-seed", type=int, default=0)
    parser.add_argument(
        "--context-length",
        type=int,
        default=REQUIRED_CONTEXT,
        help="Context the server must provide (set OLLAMA_CONTEXT_LENGTH before ollama serve)",
    )
    parser.add_argument("--profiles", help="Comma-separated profile stems (for debugging on dev)")
    parser.add_argument("--variants", help="Comma-separated variants (for debugging on dev)")
    parser.add_argument(
        "--baseline-only", action="store_true", help="Select the ten baseline methods on dev"
    )
    parser.add_argument("--repeats", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--dry-run", action="store_true", help="Print the planned episode count")
    parser.add_argument(
        "--allow-test",
        action="store_true",
        help="Required for the frozen test split, after prompts and configuration are fixed",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir or Path("outputs") / args.series.lower()

    if args.series == "E0":
        rows = run_e0(output_dir)
        print(json.dumps({"runs": len(rows), "violations": sum(r["violated"] for r in rows)}))
        return 1 if any(r["audit_issues"] for r in rows) else 0

    manifest = load_manifest(args.data_root)
    specs = build_matrix(args.series, manifest)
    if args.profiles:
        wanted = set(args.profiles.split(","))
        if not wanted <= {Path(spec.profile).stem for spec in specs}:
            print("Unknown profile selection for this series.", file=sys.stderr)
            return 2
        specs = [s for s in specs if Path(s.profile).stem in wanted]
    if args.variants:
        wanted = set(args.variants.split(","))
        if not wanted <= set(E1_VARIANTS):
            print("Unknown variant selection.", file=sys.stderr)
            return 2
        specs = [s for s in specs if s.variant in wanted]
    if args.baseline_only:
        specs = [spec for spec in specs if spec.variant in BASELINE_VARIANTS]
    specs = [s for s in specs if s.repeat < args.repeats]
    if args.dry_run:
        print(json.dumps({"series": args.series, "episodes": len(specs)}))
        return 0
    uses_test = any(spec.split == "test" for spec in specs)
    if uses_test and (
        not args.allow_test
        or args.profiles
        or args.variants
        or args.baseline_only
        or args.repeats != 4
    ):
        print("The test split runs only as a full series with --allow-test.", file=sys.stderr)
        return 2
    if not specs or any(spec.variant not in BASELINE_VARIANTS for spec in specs):
        print(
            "No runnable baseline selection; VBC requires its separate implementation stage.",
            file=sys.stderr,
        )
        return 2
    verify_profiles(args.data_root, manifest, (spec.profile for spec in specs))

    effort = None if args.reasoning_effort == "omit" else args.reasoning_effort
    base = LLMConfig(model=args.model, temperature=args.temperature, reasoning_effort=effort)
    llm = provider_config(args.provider, base, base_url=args.base_url)
    if is_local(args.provider):
        actual_context = loaded_context_length(llm)
        if actual_context != args.context_length:
            print(
                f"Server context is {actual_context}, expected {args.context_length}. Restart "
                f"with OLLAMA_CONTEXT_LENGTH={args.context_length} ollama serve.",
                file=sys.stderr,
            )
            return 2
        runtime = run_manifest(llm, args.llm_seed, actual_context)
        card = runtime["model_card"]
        if (
            not card
            or not str(card.get("weights", "")).startswith("sha256-")
            or not card.get("template")
        ):
            print(
                "Cannot freeze the model weights and chat template from the server.",
                file=sys.stderr,
            )
            return 2
    else:
        # Hosted context windows exceed the episode budget; there is no server to query.
        actual_context = None
        runtime = run_manifest(llm, args.llm_seed, actual_context, args.provider)
    rows = run_specs(
        specs,
        args.data_root,
        output_dir,
        lambda seed: OpenAICompatibleClient(replace(llm, seed=seed)),
        args.llm_seed,
        actual_context,
        run_identity=runtime,
        workers=args.workers,
    )
    failed = sum(row["failure"] is not None for row in rows)
    issues = sum(row.get("audit_issues", 0) for row in rows)
    print(json.dumps({"episodes": len(rows), "failed": failed, "audit_issues": issues}))
    return 0 if not failed and not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
