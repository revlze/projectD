"""Paired, profile-level bootstrap for the test comparison in experiments.md."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path
from random import Random
from statistics import fmean

DRAW_COUNT = 10_000
BOOTSTRAP_SEED = 20261124
REPEATS = frozenset(range(4))


@dataclass(frozen=True)
class PairedBootstrap:
    mean_difference: float
    lower: float
    upper: float
    profiles_per_family: dict[str, int]
    draws: int
    seed: int


def paired_stratified_bootstrap(
    rows: Iterable[Mapping[str, object]],
    variant: str,
    reference: str,
    metric: str = "safe_fraction",
) -> PairedBootstrap:
    """Average paired repeats within profiles, then resample whole profiles within families."""
    if variant == reference:
        raise ValueError("The compared variants must differ")
    profiles: dict[str, dict[str, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    families: dict[str, str] = {}
    partitions: set[str] = set()
    for row in rows:
        method = str(row["variant"])
        if method not in (variant, reference):
            continue
        profile, family, repeat = str(row["profile"]), str(row["family"]), int(str(row["repeat"]))
        if row.get("failure") or row.get(metric) in ("", None):
            raise ValueError(f"{profile}/{method}/{repeat}: missing completed outcome")
        if families.setdefault(profile, family) != family:
            raise ValueError(f"{profile}: inconsistent family")
        partitions.add(str(row["series"]))
        score = float(str(row[metric]))
        scores = profiles[profile][method]
        if repeat in scores or not isfinite(score):
            raise ValueError(f"{profile}/{method}/{repeat}: duplicate or invalid observation")
        scores[repeat] = score

    strata: dict[str, list[float]] = defaultdict(list)
    if len(partitions) != 1:
        raise ValueError("Provide one nonempty experimental series")
    for profile, methods in sorted(profiles.items()):
        candidate, baseline = methods.get(variant, {}), methods.get(reference, {})
        if candidate.keys() != REPEATS or baseline.keys() != REPEATS:
            raise ValueError(f"{profile}: both methods must have the same four repeats")
        strata[families[profile]].append(fmean(candidate[r] - baseline[r] for r in sorted(REPEATS)))

    groups = [group for _, group in sorted(strata.items())]
    random = Random(BOOTSTRAP_SEED)
    distribution = sorted(
        fmean(sample for group in groups for sample in random.choices(group, k=len(group)))
        for _ in range(DRAW_COUNT)
    )
    return PairedBootstrap(
        mean_difference=fmean(diff for group in groups for diff in group),
        lower=_percentile(distribution, 0.025),
        upper=_percentile(distribution, 0.975),
        profiles_per_family={family: len(group) for family, group in sorted(strata.items())},
        draws=DRAW_COUNT,
        seed=BOOTSTRAP_SEED,
    )


def _percentile(sorted_values: Sequence[float], fraction: float) -> float:
    position = fraction * (len(sorted_values) - 1)
    index = int(position)
    lower, upper = sorted_values[index], sorted_values[min(index + 1, len(sorted_values) - 1)]
    return lower + (upper - lower) * (position - index)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="summary.csv from one run")
    parser.add_argument("variant", help="candidate variant, e.g. A/VBC")
    parser.add_argument("reference", help="reference variant, e.g. A/R3P")
    parser.add_argument("--metric", default="safe_fraction")
    args = parser.parse_args()
    with args.summary.open(encoding="utf-8", newline="") as handle:
        result = paired_stratified_bootstrap(
            csv.DictReader(handle), args.variant, args.reference, args.metric
        )
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
