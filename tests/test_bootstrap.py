from __future__ import annotations

import pytest

from project_d.evaluation.bootstrap import paired_stratified_bootstrap


def _rows(profile_differences):
    return [
        {
            "series": "E2",
            "profile": f"{family}-{index}",
            "family": family,
            "variant": variant,
            "repeat": repeat,
            "safe_fraction": score,
            "failure": "",
        }
        for family, differences in profile_differences.items()
        for index, difference in enumerate(differences)
        for repeat in range(4)
        for variant, score in (("A/R3P", repeat / 16), ("A/VBC", repeat / 16 + difference))
    ]


def test_bootstrap_preserves_each_test_stratum() -> None:
    strata = {"S0": [0] * 4, **{f"S{i}": [0.5] * 6 for i in range(1, 5)}}
    result = paired_stratified_bootstrap(_rows(strata), "A/VBC", "A/R3P")
    assert result.mean_difference == result.lower == result.upper == 12 / 28
    assert result.profiles_per_family == {"S0": 4, "S1": 6, "S2": 6, "S3": 6, "S4": 6}
    assert (result.draws, result.seed) == (10_000, 20261124)


def test_bootstrap_reproducibly_resamples_paired_profiles() -> None:
    rows = _rows({"S0": [0.0, 0.5], "S1": [0.25]})
    result = paired_stratified_bootstrap(rows, "A/VBC", "A/R3P")
    assert (result.mean_difference, result.lower, result.upper) == (0.25, 0.25 / 3, 1.25 / 3)
    assert result == paired_stratified_bootstrap(reversed(rows), "A/VBC", "A/R3P")


@pytest.mark.parametrize("change", ("missing", "duplicate", "failed", "mixed_series"))
def test_bootstrap_refuses_incomplete_or_mixed_pairs(change) -> None:
    rows = _rows({"S0": [0.0], "S1": [0.5]})
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows.append(rows[0])
    elif change == "failed":
        rows[0]["failure"] = "transport"
    else:
        rows[0]["series"] = "E1"
    with pytest.raises(ValueError):
        paired_stratified_bootstrap(rows, "A/VBC", "A/R3P")
