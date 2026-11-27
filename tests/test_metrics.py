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


def _conflict_log(env_actions):
    from project_d.environment.env import Environment
    from project_d.environment.model import Variant
    from support import make_config, make_scenario

    scenario = make_scenario(budget=12, a_options=(("full", 7),), b_options=(("standard", 6),))
    env = Environment(scenario, make_config(Variant.parse("A/N")))
    for agent, action in env_actions:
        env.execute(agent, action)
    env.advance_to(scenario.horizon)
    return scenario, env


def test_root_conflict_separates_budget_refusal_from_no_submission() -> None:
    from project_d.environment.actions import SubmitJob
    from project_d.evaluation.metrics import root_conflict

    race, env = _conflict_log(
        [("A", SubmitJob("job_a", "full")), ("B", SubmitJob("job_b", "standard"))]
    )
    lost = root_conflict(race, env.metadata, env.log)
    assert lost.conflict and lost.higher_value_root_completed
    assert lost.outcomes == {"A": "completed", "B": "budget_refused"}
    assert lost.first_submissions == {"A": 0, "B": 0}

    calm, env = _conflict_log([("B", SubmitJob("job_b", "standard"))])
    result = root_conflict(calm, env.metadata, env.log)
    assert result.outcomes == {"A": "not_submitted", "B": "completed"}
    assert result.first_submissions == {"B": 0}
    assert result.higher_value_root_completed is False


def test_root_conflict_respects_owner_horizon_and_tied_values() -> None:
    from dataclasses import replace

    from project_d.environment.actions import SubmitJob
    from project_d.evaluation.metrics import root_conflict

    scenario, env = _conflict_log(
        [("A", SubmitJob("job_a", "full")), ("B", SubmitJob("job_b", "missing"))]
    )
    result = root_conflict(scenario, env.metadata, env.log)
    assert result.outcomes == {"A": "completed", "B": "other_refusal"}
    for changes in ({"time": env.metadata.horizon + 1}, {"agent_id": "B"}):
        rows = [replace(e, **changes) if e.event_type == "complete" else e for e in env.log]
        result = root_conflict(scenario, env.metadata, rows)
        assert result.outcomes == {"A": "accepted_incomplete", "B": "other_refusal"}
        assert result.higher_value_root_completed is None
    a, b = scenario.agents
    tied = replace(
        scenario,
        agents=(
            a,
            replace(
                b,
                jobs=(
                    replace(
                        b.jobs[0],
                        options=(replace(b.jobs[0].options[0], value=a.jobs[0].options[0].value),),
                    ),
                    *b.jobs[1:],
                ),
            ),
        ),
    )
    assert root_conflict(tied, env.metadata, env.log).higher_value_root_completed is None


def test_roots_that_fit_together_are_not_a_conflict() -> None:
    from project_d.environment.actions import SubmitJob
    from project_d.environment.env import Environment
    from project_d.environment.model import Variant
    from project_d.evaluation.metrics import root_conflict
    from support import make_config, make_scenario

    scenario = make_scenario(budget=13)
    env = Environment(scenario, make_config(Variant.parse("A/N")))
    env.execute("A", SubmitJob("job_a", "full"))
    assert not root_conflict(scenario, env.metadata, env.log).conflict


def test_root_report_does_not_merge_same_episode_across_manifests(tmp_path, capsys, monkeypatch):
    import csv
    import io
    import json

    from project_d.environment.actions import SubmitJob
    from project_d.environment.journal import write_jsonl
    from project_d.environment.model import RunConfig
    from project_d.evaluation import root_report
    from project_d.simulation.scheduler import ScriptedPolicy, run_episode

    scenario, _ = _conflict_log([])
    monkeypatch.setattr(root_report, "_scenario", lambda _: scenario)
    for index, first in enumerate(("A", "B")):
        directory = tmp_path / f"run{index}"
        directory.mkdir()
        (directory / "run_manifest.json").write_text(
            json.dumps({"runtime": {"llm": {"model": "same"}, "git_commit": f"commit-{index}"}}),
            encoding="utf-8",
        )
        episode = run_episode(
            scenario,
            RunConfig.for_protocol("A/N", first_agent=first),
            {
                "A": ScriptedPolicy({40: SubmitJob("job_a", "full")}),
                "B": ScriptedPolicy({40 + index: SubmitJob("job_b", "standard")}),
            },
        )
        write_jsonl(directory / "same_episode.log.jsonl", episode.metadata, episode.log)
    timings = tmp_path / "timings.csv"
    assert (
        root_report.main([str(tmp_path), str(tmp_path / "run0"), "--timings-out", str(timings)])
        == 0
    )
    results = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert [row["commit"] for row in results] == ["commit-0", "commit-1"]
    assert [row["higher_value_root_completed"] for row in results] == ["1", "1"]
    assert all(row["episodes"] == "1" for row in results)
    assert [row["staggered_submissions"] for row in results] == ["0", "1"]
    times = list(csv.DictReader(io.StringIO(timings.read_text(encoding="utf-8"))))
    assert [
        (r["first_root_submit_A"], r["first_root_submit_B"], r["absolute_gap"]) for r in times
    ] == [("40", "40", "0"), ("40", "41", "1")]
