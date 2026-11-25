"""Root-conflict table recomputed from saved journals, without calling a model.

Usage: python -m project_d.evaluation.root_report <run dir> [<run dir> ...]
Each run dir holds ``<model>/*.log.jsonl``; a later dir replaces episodes of the same
model and name from an earlier one (for example a rerun of some variants).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import load_scenario
from project_d.evaluation.metrics import root_conflict

DATA = Path(__file__).resolve().parents[3] / "data" / "scenarios"


def _scenario(scenario_id: str):
    split = "dev" if scenario_id.startswith("dev_") else "test"
    return load_scenario(DATA / split / f"{scenario_id}.json")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    journals: dict[tuple[str, str], Path] = {}
    for root in map(Path, argv):
        for path in sorted(root.glob("*/*.log.jsonl")):
            journals[path.parent.name, path.name] = path
    table: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for (model, _), path in sorted(journals.items()):
        raw = [json.loads(line) for line in path.read_bytes().splitlines()]
        metadata = EpisodeMetadata(**raw[0]["metadata"])
        log = [LogEntry(**entry) for entry in raw[1:]]
        result = root_conflict(_scenario(metadata.scenario_id), metadata, log)
        if not result.conflict:
            continue
        cell = table[model, metadata.variant]
        cell["episodes"] += 1
        cell[result.outcome or "unknown"] += 1
        if result.right_root_won is not None:
            cell["decided"] += 1
            cell["right_root_won"] += result.right_root_won
    print("model,variant,episodes,yielded,lost_race,other,right_root_won,decided")
    for (model, variant), c in sorted(table.items()):
        print(
            f"{model},{variant},{c['episodes']},{c['yielded']},{c['lost_race']},"
            f"{c['other'] + c['both_lost'] + c['none_lost']},{c['right_root_won']},{c['decided']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
