from __future__ import annotations

import pytest

from project_d.evaluation.test_analysis import join_from_e2, paired_summary


def _row(variant, profile, repeat, score, family="S1", first_agent="A", series="E3"):
    return {
        "episode": f"{series}__{profile}__{variant}__r{repeat}",
        "series": series,
        "variant": variant,
        "profile": profile,
        "family": family,
        "repeat": str(repeat),
        "first_agent": first_agent,
        "role_swap": "False",
        "commit_delay": "2",
        "start_gap": "0",
        "safe_fraction": str(score),
    }


def test_paired_summary_averages_repeats_then_pairs_profiles() -> None:
    rows = [
        *(_row("A/S", "p1", r, 0.5) for r in range(4)),
        *(_row("A/S+V", "p1", r, 0.5 + 0.1 * r) for r in range(4)),
        *(_row("A/S", "p2", r, 1.0, family="S2") for r in range(4)),
        *(_row("A/S+V", "p2", r, 1.0, family="S2") for r in range(4)),
    ]
    result = paired_summary(rows, "A/S+V", "A/S", "safe_fraction")
    assert result["mean_difference"] == pytest.approx(0.075)
    assert (result["profiles_better"], result["profiles_tied"]) == (1, 1)
    assert result["family_mean_difference"] == pytest.approx({"S1": 0.15, "S2": 0.0})


def test_join_requires_same_episode_setup_and_all_keys() -> None:
    e3 = [_row("A/S", "p1", r, 1.0) for r in range(4)]
    e2 = [_row("A/VBC", "p1", r, 1.0, series="E2") for r in range(4)]
    joined = join_from_e2(e3, e2, ("A/VBC",), "E3")
    assert {row["series"] for row in joined} == {"E3"} and len(joined) == 4
    with pytest.raises(ValueError, match="first_agent"):
        join_from_e2(e3, [{**e2[0], "first_agent": "B"}, *e2[1:]], ("A/VBC",), "E3")
    with pytest.raises(ValueError, match="lacks"):
        join_from_e2(e3, e2[:3], ("A/VBC",), "E3")
