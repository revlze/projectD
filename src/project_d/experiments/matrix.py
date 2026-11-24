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
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from project_d.agents.llm_client import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ChatClient,
    LLMConfig,
    OpenAICompatibleClient,
)
from project_d.agents.runner import LLMEpisode, run_llm_episode, write_episode
from project_d.environment.actions import SubmitJob
from project_d.environment.model import (
    AgentSpec,
    Job,
    Mode,
    Option,
    RunConfig,
    Scenario,
    load_scenario,
)
from project_d.evaluation.audit import audit_episode
from project_d.evaluation.metrics import agreement_metrics, episode_metrics
from project_d.simulation.scheduler import ScriptedPolicy, run_episode

DATA_ROOT = Path("data/protocol_v2")

# Ollama defaults to 4096 below 24 GiB of VRAM and then silently drops the start of the history.
REQUIRED_CONTEXT = 16384
CONTEXT_SAFETY = 0.9

# Every profile runs both processing orders crossed with both role assignments.
REPEATS = (("A", False), ("B", False), ("A", True), ("B", True))

E1_VARIANTS = (
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
    "A/R3P+S",
    "A/R3P+S+V",
    "A/R3P+S+G",
    "A/VBC",
)
E2_VARIANTS = ("U/N", "U/F", "A/N", "A/F", "U/R3", "A/R3", "U/R3P", "A/R3P", "A/VBC")
# E3 reuses the E2 episodes of A/R3, U/R3, A/R3P and A/VBC on the same profiles.
E3_VARIANTS = ("U/R1", "A/R1", "A/R3P+S", "A/R3P+S+V", "A/R3P+S+G")
E4_H1_VARIANTS = ("U/N", "U/R3P")
E4_H1_PROFILES = ("test/test_s1_01.json", "test/test_s1_02.json")
E4_DELAY_VARIANTS = ("A/R3P", "A/VBC")
E4_DELAYS = (1, 4, 8)
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
    return json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))


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
    """Detect silent truncation: histories only grow, so a falling prompt size means lost turns."""
    by_agent: dict[str, list[int]] = {}
    for turn in episode.turns:
        by_agent.setdefault(turn.agent_id, []).append(turn.usage.get("prompt_tokens", 0))
    drops = sum(
        after < before
        for tokens in by_agent.values()
        for before, after in itertools.pairwise(tokens)
    )
    if drops:
        return f"context_truncated: prompt size fell {drops} times"
    largest = max((max(tokens) for tokens in by_agent.values()), default=0)
    if context_length is not None and largest >= CONTEXT_SAFETY * context_length:
        return f"context_limit: prompt reached {largest} of {context_length} tokens"
    return None


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
        "failure": episode.failure or context_problem(episode, context_length),
        "max_prompt_tokens": max(
            (turn.usage.get("prompt_tokens", 0) for turn in episode.turns), default=0
        ),
        "llm_turns": len(episode.turns),
        "parse_errors": sum(turn.parse_error is not None for turn in episode.turns),
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
        "agreement": audit.agreement,
        "plan_mismatches": audit.plan_mismatches,
        "audit_issues": len(audit.issues),
    }
    shown = [(turn.agent_id, turn.logical_time, turn.shown_plan) for turn in episode.turns]
    row |= asdict(agreement_metrics(result.log, result.metadata.budget, shown))
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


def run_manifest(llm: LLMConfig, base_seed: int, context_length: int) -> dict[str, Any]:
    settings = asdict(llm)
    settings.pop("seed")
    return {
        "llm": settings,
        "context_length": context_length,
        "llm_base_seed": base_seed,
        "server_version": _server_version(llm.base_url),
        "hardware": hardware(),
        # Only meaningful when the server shares this environment, as on a vast.ai pod.
        "ollama_env": {name: os.environ.get(name) for name in SERVER_ENV},
        "git_commit": _command_output("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_command_output("git", "status", "--porcelain")),
    }


def run_specs(
    specs: list[EpisodeSpec],
    data_root: Path,
    output_dir: Path,
    client_for_seed: Callable[[int], ChatClient],
    base_seed: int = 0,
    context_length: int | None = None,
) -> list[dict[str, Any]]:
    """Run episodes, skipping finished ones. Failed episodes are retried on the next run."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, spec in enumerate(specs, start=1):
        summary_path = output_dir / f"{spec.name}.summary.json"
        if summary_path.exists():
            saved = json.loads(summary_path.read_text(encoding="utf-8"))
            if saved["failure"] is None:
                rows.append(saved)
                continue
        scenario = load_scenario(data_root / spec.profile)
        # The same repeat gets the same seed in every method, which keeps comparisons paired.
        client = client_for_seed(base_seed + spec.repeat)
        episode = run_llm_episode(scenario, spec.run_config(scenario), client)
        write_episode(output_dir, spec.name, episode)
        row = summarize_episode(spec, scenario, episode, context_length)
        summary_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append(row)
        print(f"[{index}/{len(specs)}] {spec.name}: {row.get('U_safe', 'failed')}", flush=True)
    _write_table(output_dir / "summary.csv", rows)
    return rows


def run_e0(output_dir: Path) -> list[dict[str, Any]]:
    """The 108 scripted mechanism runs. No LLM is involved."""
    rows = []
    for (budget, cost_a, cost_b), delay, offset, mode, first in itertools.product(
        ((12, 5, 6), (12, 7, 6), (12, 7, 5)), (0, 1, 3), (0, 1, 3), (Mode.B0, Mode.B2), ("A", "B")
    ):
        scenario = Scenario(
            scenario_id="e0",
            family="E0",
            budget=budget,
            horizon=30,
            commit_delay=delay,
            message_delay=1,
            agent_turn_limit=16,
            seed=0,
            agents=(
                AgentSpec("A", "e0", (Job("job_a", (Option("full", cost_a, 2, 1),)),)),
                AgentSpec("B", "e0", (Job("job_b", (Option("full", cost_b, 2, 1),)),)),
            ),
        )
        policies = {
            "A": ScriptedPolicy({0: SubmitJob("job_a", "full")}),
            "B": ScriptedPolicy({offset: SubmitJob("job_b", "full")}),
        }
        config = RunConfig(mode=mode, first_agent=first, submission_open_at=0)
        result = run_episode(scenario, config, policies)
        report = audit_episode(result.metadata, result.log)
        rows.append(
            {
                "budget": budget,
                "cost_a": cost_a,
                "cost_b": cost_b,
                "commit_delay": delay,
                "offset": offset,
                "mode": mode.value,
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
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
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
        specs = [s for s in specs if Path(s.profile).stem in wanted]
    if args.variants:
        wanted = set(args.variants.split(","))
        specs = [s for s in specs if s.variant in wanted]
    specs = [s for s in specs if s.repeat < args.repeats]
    if args.dry_run:
        print(json.dumps({"series": args.series, "episodes": len(specs)}))
        return 0
    uses_test = any(spec.split == "test" for spec in specs)
    if uses_test and (not args.allow_test or args.profiles or args.variants or args.repeats != 4):
        print("The test split runs only as a full series with --allow-test.", file=sys.stderr)
        return 2
    verify_profiles(args.data_root, manifest, (spec.profile for spec in specs))

    llm = LLMConfig(model=args.model, base_url=args.base_url, temperature=args.temperature)
    actual_context = loaded_context_length(llm)
    if actual_context != args.context_length:
        print(
            f"Server context is {actual_context}, expected {args.context_length}. Restart with "
            f"OLLAMA_CONTEXT_LENGTH={args.context_length} ollama serve.",
            file=sys.stderr,
        )
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest(llm, args.llm_seed, actual_context), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rows = run_specs(
        specs,
        args.data_root,
        output_dir,
        lambda seed: OpenAICompatibleClient(replace(llm, seed=seed)),
        args.llm_seed,
        actual_context,
    )
    failed = sum(row["failure"] is not None for row in rows)
    issues = sum(row.get("audit_issues", 0) for row in rows)
    print(json.dumps({"episodes": len(rows), "failed": failed, "audit_issues": issues}))
    return 0 if not failed and not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
