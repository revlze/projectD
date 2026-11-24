"""Regressions for defects found in the review of the new protocol."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from project_d.environment.actions import (
    ConfirmPlan,
    ProposePlan,
    ReadMessages,
    SendMessage,
    SubmitJob,
    WaitUntil,
)
from project_d.environment.env import Environment
from project_d.environment.model import (
    AgentSpec,
    Job,
    Option,
    RunConfig,
    Scenario,
    Variant,
)
from project_d.evaluation.audit import audit_episode
from project_d.simulation.scheduler import ScriptedPolicy, run_episode
from support import make_scenario


def dependent_scenario() -> Scenario:
    option = Option("o", 2, 2, 5)
    return Scenario(
        scenario_id="review",
        family="TEST",
        budget=12,
        horizon=80,
        commit_delay=2,
        message_delay=1,
        agent_turn_limit=24,
        seed=1,
        agents=(
            AgentSpec(
                "A",
                "request of A",
                (Job("a0", (option,)), Job("a1", (option,), requires=("a0",))),
            ),
            AgentSpec("B", "request of B", (Job("b0", (option,)),)),
        ),
    )


def agreed_run():
    a = ScriptedPolicy(
        {29: ProposePlan((("a0", "o"),)), 37: ConfirmPlan(2), 40: SubmitJob("a0", "o")}
    )
    b = ScriptedPolicy(
        {29: ProposePlan((("b0", "o"),)), 37: ConfirmPlan(2), 40: SubmitJob("b0", "o")}
    )
    return run_episode(dependent_scenario(), RunConfig.for_protocol("A/VBC"), {"A": a, "B": b})


def test_feedback_does_not_reveal_undisclosed_prerequisite() -> None:
    env = Environment(dependent_scenario(), RunConfig.for_protocol("A/VBC"))
    env.advance_to(29)
    env.execute("A", ProposePlan((("a1", "o"),)))
    env.execute("B", ProposePlan((("b0", "o"),)))
    env.advance_to(30)
    view = env.plan_view()
    assert view["plan_feedback"]["unmet_requires"] == [{"agent_id": "A", "job_id": "a1"}]
    assert "a0" not in json.dumps(view)


def test_observed_plan_cannot_change_snapshot_or_journal() -> None:
    env = Environment(dependent_scenario(), RunConfig.for_protocol("A/VBC"))
    env.advance_to(29)
    env.execute("A", ProposePlan((("a0", "o"),)))
    env.advance_to(30)
    view = env.plan_view()
    view["proposals"]["A"]["items"].append({"job_id": "a1", "option_id": "o", "cost": 2})
    assert len(env.plan_view()["proposals"]["A"]["items"]) == 1
    logged = next(e for e in env.log if e.event_type == "plan_version")
    assert len(logged.detail["proposals"]["A"]["items"]) == 1


def test_clean_agreed_run_passes_audit() -> None:
    result = agreed_run()
    report = audit_episode(result.metadata, result.log)
    assert report.consistent, report.issues
    assert report.agreement == "agreed"


@pytest.mark.parametrize("event", ["agreement", "propose_plan", "plan_version", "complete"])
def test_audit_flags_deleted_rows(event: str) -> None:
    result = agreed_run()
    tampered = [e for e in result.log if e.event_type != event]
    assert not audit_episode(result.metadata, tampered).consistent


def test_audit_flags_moved_confirmation() -> None:
    result = agreed_run()
    tampered = [replace(e, time=38) if e.event_type == "confirm_plan" else e for e in result.log]
    assert not audit_episode(result.metadata, tampered).consistent


def test_audit_flags_relabelled_completion() -> None:
    result = agreed_run()
    tampered = [
        replace(e, job_id="b0") if e.event_type == "complete" and e.job_id == "a0" else e
        for e in result.log
    ]
    assert not audit_episode(result.metadata, tampered).consistent


def test_audit_flags_falsified_cost() -> None:
    result = agreed_run()
    tampered = [
        replace(e, cost=0) if e.event_type in ("submit", "commit", "complete") else e
        for e in result.log
    ]
    assert not audit_episode(result.metadata, tampered).consistent


def test_audit_flags_falsified_agreement_fields() -> None:
    result = agreed_run()
    tampered = [
        replace(e, detail={**e.detail, "enforced": False}) if e.event_type == "agreement" else e
        for e in result.log
    ]
    assert not audit_episode(result.metadata, tampered).consistent


def test_send_id_does_not_reveal_other_agents_activity() -> None:
    def first_id(other_sends: bool) -> int:
        config = RunConfig.for_protocol("A/R3", first_agent="B", message_delay=8)
        env = Environment(make_scenario(), config)
        env.advance_to(6)
        if other_sends:
            env.execute("B", SendMessage("A", "plan"))
        return env.execute("A", SendMessage("B", "plan")).data["message_id"]

    assert first_id(True) == first_id(False)


def test_shown_message_is_still_returned_by_read() -> None:
    env = Environment(make_scenario(), RunConfig.for_protocol("A/R3"))
    env.advance_to(6)
    env.execute("A", SendMessage("B", "plan"))
    env.advance_to(13)
    assert env.take_inbox("B")[0]["text"] == "plan"
    assert env.unread_count("B") == 0
    assert env.take_inbox("B") == ()
    env.advance_to(40)
    assert env.execute("B", ReadMessages()).status.value == "wrong_phase"


def test_r1_sleeper_gets_turn_at_opening_after_late_delivery() -> None:
    config = RunConfig.for_protocol("A/R1", message_delay=8)
    env = Environment(make_scenario(), config)
    env.advance_to(6)
    env.execute("A", SendMessage("B", "plan"))
    env.suspend_until("B", 80, "between_rounds")
    env.advance_to(39)
    assert not env.is_ready("B")
    env.advance_to(40)
    assert env.is_ready("B")
    assert env.take_inbox("B")[0]["text"] == "plan"


def test_jump_resolves_wake_at_earliest_phase() -> None:
    env = Environment(make_scenario(), RunConfig.for_protocol("A/R3"))
    env.execute("A", WaitUntil(8))
    env.advance_to(20)
    wake = next(e for e in env.log if e.event_type == "wake")
    assert (wake.time, wake.result) == (6, "phase")


@pytest.mark.parametrize("name", ["A/N", "A/F", "U/N", "U/F"])
def test_named_variants_default_to_new_grid(name: str) -> None:
    config = RunConfig(mode=Variant.parse(name))
    resolved = config.apply(make_scenario())
    assert (config.submission_open_at, resolved.horizon, resolved.agent_turn_limit) == (40, 80, 24)


def test_malformed_plan_is_refused_without_crashing() -> None:
    env = Environment(dependent_scenario(), RunConfig.for_protocol("A/VBC"))
    env.advance_to(29)
    result = env.execute("A", ProposePlan(None))  # type: ignore[arg-type]
    assert result.status.value == "invalid_action"
