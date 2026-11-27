"""E5 (A/VBC-F) against E2 on the same test keys, recomputed from saved summaries.

Usage: python -m project_d.evaluation.e5_analysis <E5 summary.csv> <E2 summary.csv> --out <dir>

E5 is a post-hoc exploratory series: A/VBC-F alone on the 28 test profiles x 4 repeats.
Reference variants come from E2 on the same (profile, repeat) keys; the join checks that the
episode setup matches. Same statistics as E2: repeats averaged per profile, paired
differences, 10 000 stratified profile bootstrap draws with seed 20261124 (descriptive).
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path

from project_d.evaluation.bootstrap import paired_stratified_bootstrap
from project_d.evaluation.test_analysis import (
    _derive,
    _usage,
    family_table,
    join_from_e2,
    paired_summary,
    structured_table,
    write_csv,
)

CANDIDATE = "A/VBC-F"
REFERENCES = ("A/VBC", "A/F", "A/R3P", "A/R3", "A/N")
METRICS = ("safe_fraction", "utility_fraction")


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [_derive(row) for row in csv.DictReader(handle)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("e5", type=Path)
    parser.add_argument("e2", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    e5, e2 = _load(args.e5), _load(args.e2)
    if len(e5) != 112 or any(r["failure"] or r["audit_issues"] not in ("", "0") for r in e5):
        raise ValueError("E5 must have 112 completed, audited episodes")
    joined = [{**r, "series": "E5"} for r in e5] + join_from_e2(e5, e2, REFERENCES, "E5")

    paired = []
    for reference in REFERENCES:
        for metric in METRICS:
            interval = asdict(paired_stratified_bootstrap(joined, CANDIDATE, reference, metric))
            paired.append(
                {
                    **paired_summary(joined, CANDIDATE, reference, metric),
                    "lower": interval["lower"],
                    "upper": interval["upper"],
                    "draws": interval["draws"],
                    "seed": interval["seed"],
                }
            )
    write_csv(args.out / "e5_paired.csv", paired)
    write_csv(args.out / "e5_families_safe_fraction.csv", family_table(joined, "safe_fraction"))
    write_csv(args.out / "e5_structured.csv", structured_table(joined))
    write_csv(
        args.out / "e5_usage.csv",
        _usage([r for r in joined if r["variant"] in (CANDIDATE, "A/VBC", "A/F")]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
