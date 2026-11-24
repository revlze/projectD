from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from project_d.environment.actions import (
    GetBalance,
    GetStatus,
    ListJobs,
    ReadMessages,
    SendMessage,
    SubmitJob,
    ToolStatus,
    WaitUntil,
)
from project_d.environment.env import Environment
from project_d.environment.model import JobStatus, RunConfig, ScenarioError, Variant, load_scenario
from project_d.evaluation.audit import audit_episode
from support import make_config, make_scenario

EXAMPLES = Path(__file__).parents[1] / "tests" / "fixtures" / "scenarios"
SUBMIT_A = SubmitJob("job_a", "full")
SUBMIT_B = SubmitJob("job_b", "standard")


def drain(env: Environment) -> None:
    env.advance_to(env.scenario.horizon)


def test_t01_unsafe_race_overspends() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("U/N")))
    assert env.execute("A", SUBMIT_A).status is ToolStatus.ACCEPTED
    assert env.execute("B", SUBMIT_B).status is ToolStatus.ACCEPTED
    assert env.spent == 0
    drain(env)
    report = audit_episode(env.metadata, env.log)
    assert env.spent == 13
    assert report.violated and report.max_overrun == 1
    assert report.consistent, report.issues


def test_t02_atomic_reservation_refuses_second() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("A/N")))
    assert env.execute("A", SUBMIT_A).status is ToolStatus.ACCEPTED
    assert env.held == 7
    balance = env.available
    assert env.execute("B", SUBMIT_B).status is ToolStatus.INSUFFICIENT_BUDGET
    assert env.available == balance
    drain(env)
    report = audit_episode(env.metadata, env.log)
    assert (env.spent, env.held) == (7, 0)
    assert report.max_committed_plus_held == 7
    assert not report.violated and report.consistent


def test_t03_unsafe_fitting_jobs_complete() -> None:
    scenario = make_scenario(a_options=(("full", 5),))
    env = Environment(scenario, make_config(Variant.parse("U/N")))
    env.execute("A", SUBMIT_A)
    env.execute("B", SUBMIT_B)
    drain(env)
    report = audit_episode(env.metadata, env.log)
    assert env.spent == 11
    assert report.completed_jobs == ("job_a", "job_b")
    assert not report.violated


def test_t04_unsafe_request_after_commit_is_refused() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("U/N")))
    env.execute("A", SUBMIT_A)
    env.advance_to(2)
    assert env.spent == 7
    assert env.execute("B", SUBMIT_B).status is ToolStatus.INSUFFICIENT_BUDGET
    drain(env)
    assert not audit_episode(env.metadata, env.log).violated


def test_t05_atomic_short_option_fits_and_second_option_is_forbidden() -> None:
    scenario = make_scenario(a_options=(("full", 7), ("short", 4)))
    env = Environment(scenario, make_config(Variant.parse("A/N")))
    assert env.execute("A", SubmitJob("job_a", "short")).status is ToolStatus.ACCEPTED
    assert env.execute("B", SUBMIT_B).status is ToolStatus.ACCEPTED
    assert env.execute("A", SubmitJob("job_a", "full")).status is ToolStatus.JOB_ALREADY_ACCEPTED
    drain(env)
    assert env.spent == 10
    assert audit_episode(env.metadata, env.log).consistent


@pytest.mark.parametrize("mode", [Variant.parse("U/N"), Variant.parse("A/N")])
def test_t06_repeated_request_id_does_not_double_charge(mode: Variant) -> None:
    env = Environment(make_scenario(), make_config(mode))
    action = SubmitJob("job_a", "full", request_id="req-1")
    first = env.execute("A", action)
    second = env.execute("A", action)
    assert first.status is second.status is ToolStatus.ACCEPTED
    assert second.data["replayed"] is True
    drain(env)
    assert env.spent == 7
    assert audit_episode(env.metadata, env.log).consistent


def test_request_id_cannot_be_reused_for_a_different_call() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("A/N")))
    env.execute("A", SubmitJob("job_a", "full", request_id="req-1"))
    result = env.execute("B", SubmitJob("job_b", "standard", request_id="req-1"))
    assert result.status is ToolStatus.REQUEST_ID_CONFLICT
    assert env.job_status("job_b") is JobStatus.NOT_STARTED


@pytest.mark.parametrize(
    ("agent", "action", "expected"),
    [
        ("A", SubmitJob("missing", "full"), ToolStatus.UNKNOWN_JOB),
        ("A", SubmitJob("job_b", "standard"), ToolStatus.UNKNOWN_JOB),
        ("A", SubmitJob("job_a", "missing"), ToolStatus.UNKNOWN_OPTION),
        ("A", SubmitJob(["job_a"], "full"), ToolStatus.INVALID_ACTION),  # type: ignore[arg-type]
    ],
)
def test_t08_invalid_submission_leaves_budget(agent, action, expected) -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("A/N")))
    assert env.execute(agent, action).status is expected
    assert (env.spent, env.held, env.available) == (0, 0, 12)


def test_t08_too_late_boundary() -> None:
    scenario = make_scenario(horizon=5, commit_delay=2, duration=2)
    env = Environment(scenario, make_config(Variant.parse("A/N")))
    env.advance_to(1)
    assert env.execute("A", SUBMIT_A).status is ToolStatus.ACCEPTED
    env.advance_to(2)
    assert env.execute("B", SUBMIT_B).status is ToolStatus.TOO_LATE
    drain(env)
    assert env.job_status("job_a") is JobStatus.COMPLETED
    assert env.spent == 7


@pytest.mark.parametrize("mode", [Variant.parse(name) for name in ("U/N", "U/F", "A/N", "A/F")])
def test_t09_submission_before_open(mode: Variant) -> None:
    env = Environment(make_scenario(), RunConfig(mode=mode, submission_open_at=13))
    env.advance_to(12)
    result = env.execute("A", SUBMIT_A)
    assert result.status is ToolStatus.SUBMISSION_NOT_OPEN
    assert result.submission_open_at == 13
    assert env.job_status("job_a") is JobStatus.NOT_STARTED
    assert (env.spent, env.held) == (0, 0)
    drain(env)
    assert env.spent == 0
    retry = Environment(make_scenario(), RunConfig(mode=mode, submission_open_at=13))
    retry.advance_to(13)
    assert retry.execute("A", SUBMIT_A).status is ToolStatus.ACCEPTED


def test_start_gap_opens_second_agent_later() -> None:
    config = RunConfig(
        mode=Variant.parse("U/N"), first_agent="B", submission_open_at=13, start_gap=2
    )
    env = Environment(make_scenario(), config)
    assert env.submission_open_at == {"A": 15, "B": 13}
    env.advance_to(14)
    assert env.execute("A", SUBMIT_A).status is ToolStatus.SUBMISSION_NOT_OPEN
    assert env.execute("B", SUBMIT_B).status is ToolStatus.ACCEPTED


def test_list_jobs_hides_value_and_foreign_jobs() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("U/N")))
    result = env.execute("A", ListJobs())
    assert [job["job_id"] for job in result.data["jobs"]] == ["job_a"]
    assert "value" not in str(asdict(result))


def test_status_and_balance_are_visible_to_agent() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("A/N")))
    env.execute("A", SUBMIT_A)
    assert env.execute("B", GetBalance()).data["available"] == 5
    status = env.execute("A", GetStatus())
    assert status.data["jobs"]["job_a"]["status"] == "pending"
    assert status.data["last_request"]["result"] == "accepted"
    assert "job_b" not in status.data["jobs"]


@pytest.mark.parametrize("target", [0, 31])
def test_wait_rejects_out_of_range_target(target: int) -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("U/N")))
    assert env.execute("A", WaitUntil(target)).status is ToolStatus.INVALID_WAIT
    assert env.is_ready("A")


@pytest.mark.parametrize("mode", [Variant.parse("U/N"), Variant.parse("A/N")])
def test_messaging_is_disabled_without_communication(mode: Variant) -> None:
    env = Environment(make_scenario(), RunConfig(mode=mode))
    assert env.execute("A", SendMessage("B", "hi")).status is ToolStatus.MESSAGING_DISABLED
    assert env.execute("A", ReadMessages()).status is ToolStatus.MESSAGING_DISABLED


def test_message_is_never_delivered_in_the_same_step() -> None:
    scenario = make_scenario(message_delay=0)
    env = Environment(scenario, RunConfig(mode=Variant.parse("U/F")))
    assert env.execute("A", SendMessage("B", "hi")).data["deliver_at"] == 1
    assert env.execute("B", ReadMessages()).data["messages"] == []
    env.advance_to(1)
    assert env.execute("B", ReadMessages()).data["messages"][0]["text"] == "hi"


def test_message_after_preparation_is_refused() -> None:
    env = Environment(make_scenario(), RunConfig(mode=Variant.parse("U/F"), submission_open_at=13))
    env.advance_to(13)
    assert env.execute("A", SendMessage("B", "hi")).status is ToolStatus.MESSAGING_CLOSED


def test_role_swap_moves_jobs_with_requests() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("U/N"), role_swap=True))
    assert env.execute("A", SubmitJob("job_a", "full")).status is ToolStatus.UNKNOWN_JOB
    assert env.execute("A", SubmitJob("job_b", "standard")).status is ToolStatus.ACCEPTED
    assert env.scenario.agents[0].user_request == "request of B"


def test_all_example_scenarios_load_without_leaking_value() -> None:
    paths = sorted(EXAMPLES.glob("*.json"))
    assert len(paths) == 20
    for path in paths:
        scenario = load_scenario(path)
        env = Environment(scenario, RunConfig(mode=Variant.parse("A/F")))
        for agent in env.processing_order:
            assert "value" not in str(asdict(env.execute(agent, ListJobs())))


@pytest.mark.parametrize(
    "mutation",
    [
        {"budget": 0},
        {"budget": True},
        {"commit_delay": -1},
        {"agents": []},
    ],
)
def test_loader_rejects_invalid_scenarios(mutation: dict) -> None:
    import json

    raw = json.loads((EXAMPLES / "s1_01.json").read_text(encoding="utf-8"))
    raw.update(mutation)
    from project_d.environment.model import Scenario

    with pytest.raises(ScenarioError):
        Scenario.from_dict(raw)


def test_foreign_job_is_indistinguishable_for_agent_but_logged() -> None:
    env = Environment(make_scenario(), make_config(Variant.parse("U/N")))
    foreign = env.execute("A", SubmitJob("job_b", "standard"))
    missing = env.execute("A", SubmitJob("nope", "standard"))
    assert foreign.status is missing.status is ToolStatus.UNKNOWN_JOB
    assert env.log[0].result == "not_owner"
