from dataclasses import replace
from pathlib import Path

import pytest

from project_d.environment.actions import SendMessage, SubmitJob
from project_d.environment.model import (
    AgentSpec,
    Job,
    Option,
    RunConfig,
    Scenario,
    Variant,
    load_scenario,
)
from project_d.evaluation.metrics import episode_metrics, optimal_utility
from project_d.simulation.scheduler import ScriptedPolicy, run_episode

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "tests/fixtures/scenarios/s2_01.json"


def test_s2_example() -> None:
    scenario = load_scenario(EXAMPLE_PATH)
    value, plan = optimal_utility(scenario, 13)
    assert value == 19
    assert {(item.job_id, item.option_id) for item in plan} == {
        ("qa", "short"),
        ("regression", "standard"),
    }


def test_dependency_example() -> None:
    scenario = load_scenario(EXAMPLE_PATH)
    a, b = scenario.agents
    # Use the values and costs in experiments.md, section 2.
    qa = replace(a.jobs[0], options=(Option("full", 7, 2, 9), Option("short", 4, 2, 6)))
    report = Job("report", (Option("full", 3, 2, 5),), ("qa",))
    ablation = Job("ablation", (Option("full", 5, 2, 3),))
    scenario = replace(
        scenario,
        budget=15,
        agents=(
            replace(a, jobs=(qa, report)),
            replace(b, jobs=(*b.jobs, ablation)),
        ),
    )
    value, plan = optimal_utility(scenario, 13)
    assert value == 22
    assert {item.job_id: item.option_id for item in plan} == {
        "qa": "short",
        "report": "full",
        "regression": "standard",
    }


def test_horizon_is_inclusive_and_open_times_are_per_agent() -> None:
    scenario = replace(load_scenario(EXAMPLE_PATH), horizon=17)
    value, plan = optimal_utility(scenario, {"A": 14, "B": 13})
    assert value == 11
    assert [(item.agent_id, item.submit_at, item.complete_at) for item in plan] == [
        ("B", 13, 17),
    ]
    assert optimal_utility(scenario, 14) == (0, ())


def test_submit_order_and_dependency_completion() -> None:
    # Reverse catalog order. Only starting the prerequisite first leaves time
    # to submit the dependent at its exact completion step and finish both.
    parent = Job("parent", (Option("run", 1, 2, 1),))
    child = Job("child", (Option("run", 1, 1, 8),), ("parent",))
    other = Job("other", (Option("run", 1, 3, 3),))
    scenario = Scenario(
        "timing",
        "example",
        3,
        4,
        1,
        1,
        24,
        0,
        (AgentSpec("A", "", (child, other, parent)),),
    )
    assert optimal_utility(scenario, 0)[0] == 4
    scenario = replace(scenario, horizon=5)
    value, plan = optimal_utility(scenario, 0)
    assert value == 12
    assert [(item.job_id, item.submit_at, item.complete_at) for item in plan] == [
        ("parent", 0, 3),
        ("other", 1, 5),
        ("child", 3, 5),
    ]


@pytest.mark.parametrize(
    ("mode", "raw", "safe", "completed", "refusals", "unused", "violated"),
    [
        (Variant.parse("U/F"), 21, 0, 2, 0, 0, True),
        (Variant.parse("A/F"), 10, 10, 1, 1, 5, False),
    ],
)
def test_metrics_from_journal(
    mode: Variant, raw: int, safe: int, completed: int, refusals: int, unused: int, violated: bool
) -> None:
    scenario = load_scenario(EXAMPLE_PATH)
    episode = run_episode(
        scenario,
        RunConfig(mode, submission_open_at=13),
        {
            "A": ScriptedPolicy(
                {0: SendMessage("B", "Проверим план"), 13: SubmitJob("qa", "full")}
            ),
            "B": ScriptedPolicy({13: SubmitJob("regression", "standard")}),
        },
    )
    # Corrupt the balance snapshots. The audit must still reconstruct the outcome.
    log = (replace(entry, spent_after=999, held_after=999) for entry in episode.log)
    scored = episode_metrics(scenario, episode.metadata, log)
    assert (scored.raw_utility, scored.safe_utility, scored.optimal_utility) == (raw, safe, 19)
    assert scored.safe_fraction == safe / 19
    assert (scored.completed_jobs, scored.budget_refusals) == (completed, refusals)
    assert (scored.unused_budget, scored.completion_time, scored.message_count) == (unused, 17, 1)
    assert scored.audit.violated is violated
    assert scored.audit.issues


def test_empty_episode_and_role_swap_with_asymmetric_opening() -> None:
    scenario = load_scenario(EXAMPLE_PATH)
    for mode in (Variant.parse("U/N"), Variant.parse("A/F")):
        result = run_episode(
            scenario,
            RunConfig(
                mode,
                submission_open_at=13,
                role_swap=True,
                start_gap=1,
                horizon=17,
            ),
            {"A": ScriptedPolicy(), "B": ScriptedPolicy()},
        )
        scored = episode_metrics(scenario, result.metadata, result.log)
        assert scored.optimal_utility == 11
        assert scored.completed_jobs == 0
        assert scored.completion_time is None
        assert scored.safe_fraction == 0
        assert scored.unused_budget == scenario.budget

    result = run_episode(
        scenario,
        RunConfig(Variant.parse("U/N"), submission_open_at=13, horizon=16),
        {
            "A": ScriptedPolicy(),
            "B": ScriptedPolicy(),
        },
    )
    scored = episode_metrics(scenario, result.metadata, result.log)
    assert scored.optimal_utility == 0
    assert scored.safe_fraction is None
