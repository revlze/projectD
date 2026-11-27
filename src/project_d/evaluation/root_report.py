"""Root-conflict table recomputed from saved journals, without calling a model.

Usage: python -m project_d.evaluation.root_report <run dir> [<run dir> ...]
Pass a run directory or a parent containing one level of run directories.
Every run manifest and protocol version is reported separately.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import load_scenario
from project_d.evaluation.audit import audit_episode
from project_d.evaluation.metrics import root_conflict

DATA = Path(__file__).resolve().parents[3] / "data" / "scenarios"
OUTCOMES = ("not_submitted", "budget_refused", "other_refusal", "accepted_incomplete", "completed")


def _scenario(scenario_id: str):
    split = "dev" if scenario_id.startswith("dev_") else "test"
    return load_scenario(DATA / split / f"{scenario_id}.json")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, help="Write the aggregate CSV instead of stdout")
    parser.add_argument("--timings-out", type=Path, help="Write the per-episode submission times")
    args = parser.parse_args(argv)
    journals: set[Path] = set()
    for root in args.runs:
        found = {*root.glob("*.log.jsonl"), *root.glob("*/*.log.jsonl")}
        if not found:
            raise ValueError(f"{root}: no episode journals")
        journals.update(path.resolve() for path in found)
    sources: dict[Path, tuple[str, ...]] = {}
    table: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    timings = []
    for path in sorted(journals):
        if path.parent not in sources:
            manifest = (path.parent / "run_manifest.json").read_bytes()
            saved = json.loads(manifest)
            runtime = saved.get("runtime", saved)
            run_path = path.parent
            if run_path.is_relative_to(Path.cwd()):
                run_path = run_path.relative_to(Path.cwd())
            sources[path.parent] = (
                run_path.as_posix(),
                runtime["llm"]["model"],
                runtime.get("git_commit") or "",
                runtime.get("prompt_version") or "",
                hashlib.sha256(manifest).hexdigest(),
            )
        summary_path = path.with_name(path.name.removesuffix(".log.jsonl") + ".summary.json")
        if (
            summary_path.exists()
            and json.loads(summary_path.read_bytes()).get("failure") is not None
        ):
            continue
        raw = [json.loads(line) for line in path.read_bytes().splitlines()]
        metadata = EpisodeMetadata(**raw[0]["metadata"])
        log = [LogEntry(**entry) for entry in raw[1:]]
        report = audit_episode(metadata, log, require_complete=bool(metadata.protocol_version))
        if report.issues:
            raise ValueError(f"{path}: journal audit failed: {report.issues}")
        result = root_conflict(_scenario(metadata.scenario_id), metadata, log)
        if result.outcomes is None:
            continue
        cell = table[
            (*sources[path.parent], metadata.protocol_version, metadata.variant or metadata.mode)
        ]
        cell["episodes"] += 1
        cell.update(result.outcomes.values())
        first = result.first_submissions or {}
        time_gap = max(first.values()) - min(first.values()) if len(first) == 2 else None
        cell["both_submitted"] += time_gap is not None
        cell["staggered_submissions"] += time_gap is not None and time_gap > 0
        if args.timings_out:
            timings.append(
                (
                    sources[path.parent][2],
                    path.name.removesuffix(".log.jsonl"),
                    metadata.scenario_id,
                    metadata.variant or metadata.mode,
                    metadata.first_agent,
                    metadata.role_swap,
                    first.get("A"),
                    first.get("B"),
                    time_gap,
                )
            )
        cell[f"{sum(v == 'completed' for v in result.outcomes.values())}_completed"] += 1
        if result.higher_value_root_completed is not None:
            cell["decided"] += 1
            cell["higher_value_root_completed"] += result.higher_value_root_completed
    fields = (
        "episodes",
        *OUTCOMES,
        "0_completed",
        "1_completed",
        "2_completed",
        "higher_value_root_completed",
        "decided",
        "both_submitted",
        "staggered_submissions",
    )
    aggregate = [
        (
            "run",
            "model",
            "commit",
            "prompt_version",
            "manifest_sha256",
            "protocol_version",
            "variant",
            *fields,
        ),
    ]
    for source, counts in sorted(table.items()):
        aggregate.append((*source, *(counts[field] for field in fields)))
    _write_csv(args.out, aggregate)
    if args.timings_out:
        _write_csv(
            args.timings_out,
            [
                (
                    "commit",
                    "episode",
                    "profile",
                    "variant",
                    "first_agent",
                    "role_swap",
                    "first_root_submit_A",
                    "first_root_submit_B",
                    "absolute_gap",
                ),
                *timings,
            ],
        )
    return 0


def _write_csv(path, rows) -> None:
    if path is None:
        csv.writer(sys.stdout, lineterminator="\n").writerows(rows)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
