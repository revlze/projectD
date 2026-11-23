from __future__ import annotations

import json
import re

import pytest

from project_d.agents.llm_client import ChatResponse
from project_d.agents.runner import run_llm_episode
from project_d.environment.actions import ConfirmPlan, ProposePlan, SubmitJob
from project_d.environment.model import RunConfig
from project_d.evaluation.metrics import agreement_metrics
from project_d.simulation.scheduler import ScriptedPolicy, run_episode
from support import make_scenario


def scripted_run(variant: str, cost_a: int = 7, b_version: int = 2):
    a = ScriptedPolicy(
        {
            29: ProposePlan((("job_a", "full"),)),
            37: ConfirmPlan(2),
            40: SubmitJob("job_a", "full"),
        }
    )
    b = ScriptedPolicy(
        {
            29: ProposePlan((("job_b", "standard"),)),
            37: ConfirmPlan(b_version),
            40: SubmitJob("job_b", "standard"),
        }
    )
    scenario = make_scenario(a_options=(("full", cost_a),))
    return run_episode(scenario, RunConfig.for_protocol(variant), {"A": a, "B": b})


def shown(version: int, overage: int, agents: tuple[str, ...] = ("A", "B")) -> list[tuple]:
    plan = {
        "plan_version": version,
        "feedback_shown": True,
        "budget": 12,
        "requested_total": 12 + overage,
        "overage": overage,
    }
    return [(agent, 37, plan) for agent in agents]


def test_variants_without_plans_have_no_agreement_metrics() -> None:
    result = run_episode(
        make_scenario(),
        RunConfig.for_protocol("A/R3P"),
        {"A": ScriptedPolicy(), "B": ScriptedPolicy()},
    )
    assert agreement_metrics(result.log, 12).agreed is None


def test_valid_agreement_and_completion() -> None:
    result = scripted_run("A/VBC", cost_a=5)
    metrics = agreement_metrics(result.log, 12, shown(2, 0))
    assert metrics.agreed and metrics.valid_agreement
    assert not metrics.agreed_over_budget
    assert (metrics.agreed_total, metrics.agreed_overage) == (11, 0)
    assert (metrics.agreed_jobs, metrics.agreed_jobs_completed) == (2, 2)
    assert metrics.agreed_plan_completed is True
    assert metrics.v_warning_status is None


def test_over_budget_after_warning_is_a_coordination_error() -> None:
    result = scripted_run("A/VBC")
    metrics = agreement_metrics(result.log, 12, shown(2, 1))
    assert metrics.agreed and metrics.agreed_over_budget
    assert metrics.valid_agreement is False
    assert (metrics.agreed_total, metrics.agreed_overage) == (13, 1)
    assert metrics.agreed_jobs_completed == 1
    assert metrics.agreed_plan_completed is False
    assert (metrics.v_warned_agents, metrics.v_warning_status) == (2, "warned_and_confirmed")


@pytest.mark.parametrize(
    "seen",
    [
        [],
        shown(2, 1, ("A",)),
        shown(1, 1),
        [("A", 38, shown(2, 1)[0][2]), ("B", 38, shown(2, 1)[0][2])],
    ],
)
def test_missing_warning_is_not_called_ignored(seen: list[tuple]) -> None:
    metrics = agreement_metrics(scripted_run("A/VBC").log, 12, seen)
    assert metrics.agreed_over_budget is True
    assert metrics.v_warning_status == "warning_not_delivered"


def test_over_budget_without_v_is_labelled() -> None:
    metrics = agreement_metrics(scripted_run("A/R3P+S+G").log, 12)
    assert metrics.agreed_over_budget is True
    assert metrics.v_warned_agents is None
    assert metrics.v_warning_status == "no_v"


def test_mismatched_confirmations_are_not_an_agreement() -> None:
    metrics = agreement_metrics(scripted_run("A/VBC", b_version=1).log, 12, shown(2, 1))
    assert metrics.agreed is False
    assert metrics.agreed_over_budget is False
    assert metrics.valid_agreement is False
    assert metrics.agreed_total is None


class PlanClient:
    """Proposes, confirms and submits, and records every prompt it receives."""

    def __init__(self) -> None:
        self.prompts: dict[tuple[str, int], str] = {}

    def chat(self, messages, tools) -> ChatResponse:
        agent = "A" if "агент A и" in messages[0]["content"] else "B"
        note = messages[-1]["content"]
        now = int(re.search(r"logical_time=(\d+)", note).group(1))
        self.prompts[agent, now] = note
        job, option = ("job_a", "full") if agent == "A" else ("job_b", "standard")
        if now == 29:
            name, args = "propose_plan", {"items": [{"job_id": job, "option_id": option}]}
        elif now == 37:
            name, args = "confirm_plan", {"plan_version": 2}
        elif now == 40:
            name, args = "submit_job", {"job_id": job, "option_id": option}
        elif now < 40:
            name, args = "wait_until", {"target_time": 40}
        else:
            name, args = "finish", {}
        call = {"id": "c", "function": {"name": name, "arguments": json.dumps(args)}}
        return ChatResponse({"role": "assistant", "content": "", "tool_calls": [call]})


def test_llm_turn_records_feedback_that_is_really_in_the_prompt() -> None:
    client = PlanClient()
    episode = run_llm_episode(make_scenario(), RunConfig.for_protocol("A/VBC"), client)
    at_confirm = [turn for turn in episode.turns if turn.logical_time == 37]
    assert len(at_confirm) == 2
    for turn in at_confirm:
        assert turn.shown_plan["plan_version"] == 2
        assert turn.shown_plan["feedback_shown"] is True
        assert turn.shown_plan["overage"] == 1
        assert '"overage": 1' in client.prompts[turn.agent_id, 37]
    assert all(t.shown_plan is None for t in episode.turns if t.logical_time < 30)
    triples = [(t.agent_id, t.logical_time, t.shown_plan) for t in episode.turns]
    metrics = agreement_metrics(episode.result.log, 12, triples)
    assert metrics.v_warning_status == "warned_and_confirmed"


def test_without_v_the_prompt_has_no_feedback() -> None:
    episode = run_llm_episode(make_scenario(), RunConfig.for_protocol("A/R3P+S+G"), PlanClient())
    at_confirm = [turn for turn in episode.turns if turn.logical_time == 37]
    assert all(turn.shown_plan["feedback_shown"] is False for turn in at_confirm)
