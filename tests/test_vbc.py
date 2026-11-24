"""VBC protocol checks T26-T28 and T34 from system_spec.md, section 8, on the section 6 grid."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from project_d.agents.plan_text import credits, render_plan
from project_d.agents.prompts import build_protocol_prompt, prompt_sha256
from project_d.agents.runner import run_llm_episode
from project_d.environment.actions import (
    ConfirmPlan,
    ProposePlan,
    SendMessage,
    SubmitJob,
    ToolStatus,
)
from project_d.environment.model import (
    CONFIRM_TIME,
    PROPOSE_TIMES,
    SNAPSHOT_TIMES,
    RunConfig,
    Variant,
    load_scenario,
)
from project_d.evaluation.audit import audit_episode
from project_d.experiments.matrix import BASELINE_VARIANTS, DATA_ROOT
from project_d.simulation.scheduler import Observation, ScriptedPolicy, run_episode
from support import make_scenario
from test_baseline_contract import RecordingClient, response

STRUCTURED = ("A/S", "A/S+V", "A/S+G", "A/VBC", "A/VBC-r0", "A/VBC-r2")
A_FULL, A_SHORT, A_MINI = ("job_a", "full"), ("job_a", "short"), ("job_a", "mini")
B_STANDARD = ("job_b", "standard")


class Watcher(ScriptedPolicy):
    def __init__(self, steps) -> None:
        super().__init__(steps)
        self.seen: dict[int, Observation] = {}

    def decide(self, observation: Observation):
        self.seen[observation.logical_time] = observation
        return super().decide(observation)


def _scenario(**settings):
    return make_scenario(a_options=(("full", 7), ("short", 4), ("mini", 2)), **settings)


def _events(result, event_type):
    return [entry for entry in result.log if entry.event_type == event_type]


def test_six_structured_variants_parse_to_the_spec_table() -> None:
    table = {
        name: (v.verify, v.guard, len(v.round_times))
        for name in STRUCTURED
        for v in [Variant.parse(name)]
    }
    assert table == {
        "A/S": (False, False, 1),
        "A/S+V": (True, False, 1),
        "A/S+G": (False, True, 1),
        "A/VBC": (True, True, 1),
        "A/VBC-r0": (True, True, 0),
        "A/VBC-r2": (True, True, 2),
    }
    assert Variant.parse("A/VBC-r2").round_times == (13, 20)
    for retired in ("A/R3P+S", "A/R3P+S+V+G", "U/VBC"):
        with pytest.raises(ValueError):
            Variant.parse(retired)


@pytest.mark.parametrize("variant", STRUCTURED)
@pytest.mark.parametrize(("first_agent", "role_swap"), [("A", False), ("B", True)])
def test_t26_phase_grid_simultaneous_proposals_and_visible_versions(
    variant: str, first_agent: str, role_swap: bool
) -> None:
    rounds = Variant.parse(variant).round_times
    probes = {t: SendMessage("B", "early") for t in (0, 5)}
    a = Watcher({**probes, 6: ProposePlan((A_FULL,), (A_SHORT,)), 33: ProposePlan((A_SHORT,))})
    b = Watcher({6: ProposePlan((B_STANDARD,))})
    result = run_episode(
        _scenario(),
        RunConfig.for_protocol(variant, first_agent=first_agent, role_swap=role_swap),
        {"A": a, "B": b},
    )
    # No communication before the first proposal; only the slots get decisions afterwards.
    early = [c.result.status for c in result.calls_by("A") if isinstance(c.action, SendMessage)]
    assert len(early) == 2 and ToolStatus.OK not in early
    slots = {6, *rounds, 33, 37}
    for watcher in (a, b):
        assert {t for t in watcher.seen if 6 <= t < 40} == slots
        assert watcher.seen[6].plan_view is None
        for time in (*rounds, 33):
            assert watcher.seen[time].plan_view["plan_version"] == 1
        assert watcher.seen[37].plan_view["plan_version"] == 2
    assert [e.time for e in _events(result, "plan_version")] == list(SNAPSHOT_TIMES)
    assert {e.time for e in _events(result, "propose_plan")} <= set(PROPOSE_TIMES)
    assert all(e.time in rounds for e in _events(result, "send_message") if e.result == "ok")
    assert audit_episode(result.metadata, result.log).consistent


def test_t27_empty_missing_and_skipped_revision() -> None:
    a = ScriptedPolicy({6: ProposePlan(()), 37: ConfirmPlan(2)})
    b = ScriptedPolicy({37: ConfirmPlan(2)})
    result = run_episode(_scenario(), RunConfig.for_protocol("A/VBC"), {"A": a, "B": b})
    versions = [e.detail["proposals"] for e in _events(result, "plan_version")]
    # An explicit empty plan is present; a missing plan is absent; a skipped revision keeps v1.
    assert versions == [{"A": {"items": [], "disclosed_alternatives": [], "note": ""}}] * 2
    feedback = _events(result, "plan_feedback")[-1].detail
    assert (feedback["status"], feedback["missing_plans"]) == ("INCOMPLETE", ["B"])
    assert [c.result.status for c in result.calls if isinstance(c.action, ConfirmPlan)] == [
        ToolStatus.INVALID_PLAN
    ] * 2
    assert _events(result, "agreement")[0].result == "agreement_failed"
    assert audit_episode(result.metadata, result.log).consistent


@pytest.mark.parametrize(
    ("plan", "reason"),
    [
        (ProposePlan((A_FULL,), (A_SHORT, A_SHORT)), "duplicate_alternative"),
        (ProposePlan((A_FULL,), (A_FULL,)), "chosen_option_as_alternative"),
    ],
)
def test_proposal_format_errors_are_refused(plan, reason) -> None:
    result = run_episode(
        _scenario(),
        RunConfig.for_protocol("A/VBC"),
        {"A": ScriptedPolicy({6: plan})} | {"B": ScriptedPolicy()},
    )
    refusal = _events(result, "propose_plan")[0]
    assert (refusal.result, refusal.detail["reason"]) == ("invalid_plan", reason)
    assert _events(result, "plan_version")[0].detail["proposals"] == {}


@pytest.mark.parametrize("variant", ["A/S", "A/S+V"])
def test_t28_same_disclosure_with_and_without_v(variant: str) -> None:
    b = Watcher({6: ProposePlan((B_STANDARD,))})
    run_episode(
        _scenario(),
        RunConfig.for_protocol(variant),
        {"A": ScriptedPolicy({6: ProposePlan((A_FULL,), (A_SHORT, A_MINI))}), "B": b},
    )
    view = b.seen[13].plan_view
    assert view["proposals"]["A"]["disclosed_alternatives"] == [
        {"job_id": "job_a", "option_id": "short", "cost": 4},
        {"job_id": "job_a", "option_id": "mini", "cost": 2},
    ]
    if variant == "A/S":
        assert "plan_feedback" not in view
        text = render_plan(view, "B", "A")
        assert "экономия" not in text and "ПРОВЕРКА" not in text
        return
    feedback = view["plan_feedback"]
    # Mutually exclusive replacements are listed one by one, never summed or ranked.
    assert [s["saving"] for s in feedback["disclosed_savings"]] == [3, 5]
    assert (feedback["requested_total"], feedback["overage"]) == (13, 1)
    assert set(feedback) == {
        "plan_version",
        "budget",
        "requested_total",
        "overage",
        "agent_totals",
        "disclosed_savings",
        "unmet_requires",
        "missing_plans",
        "status",
    }


def test_t34_same_facts_for_both_agents() -> None:
    a = Watcher({6: ProposePlan((A_FULL,), (A_SHORT,), "главное - полный вариант")})
    b = Watcher({6: ProposePlan((B_STANDARD,))})
    run_episode(_scenario(), RunConfig.for_protocol("A/VBC"), {"A": a, "B": b})
    view = a.seen[13].plan_view
    assert view == b.seen[13].plan_view
    text_a, text_b = render_plan(view, "A", "B"), render_plan(view, "B", "A")
    assert text_a.splitlines()[:4] == [
        "Совместный план #1",
        "ТВОЙ ПЛАН (A)",
        "- job_a/full: 7 кредитов",
        "- Альтернатива job_a/short: 4 кредита (экономия 3)",
    ]
    assert "- Бюджет: 12; запрошено: 13; превышение: 1" in text_a
    assert "- OVER_BUDGET" in text_a
    assert "- A: главное - полный вариант" in text_a

    def facts(text: str) -> Counter:
        return Counter(line for line in text.splitlines() if line.startswith("- "))

    assert facts(text_a) == facts(text_b)
    assert text_a != text_b


def test_credit_word_forms() -> None:
    assert [credits(n) for n in (1, 2, 5, 11, 12, 21, 24, 25)] == [
        "1 кредит",
        "2 кредита",
        "5 кредитов",
        "11 кредитов",
        "12 кредитов",
        "21 кредит",
        "24 кредита",
        "25 кредитов",
    ]


class PlanningClient(RecordingClient):
    """Recording client that also answers the plan slots."""

    def chat(self, messages, tools):
        note = messages[-1]["content"]
        phase = re.search(r"phase=([a-z_]+)", note).group(1)
        agent = "A" if "агент A и" in messages[0]["content"] else "B"
        if phase == "propose":
            self.requests.append({"messages": messages, "tools": tools})
            job = "job_a" if agent == "A" else "job_b"
            option = "full" if agent == "A" else "standard"
            return response("propose_plan", {"items": [{"job_id": job, "option_id": option}]})
        if phase == "confirm":
            self.requests.append({"messages": messages, "tools": tools})
            version = int(re.search(r"plan_version=(\d+)", note).group(1))
            return response("confirm_plan", {"plan_version": version})
        return super().chat(messages, tools)


def test_vbc_runs_through_the_llm_loop_and_records_shown_plans() -> None:
    client = PlanningClient()
    episode = run_llm_episode(make_scenario(budget=13), RunConfig.for_protocol("A/VBC"), client)
    assert episode.failure is None
    assert _events(episode.result, "agreement")[0].result == "agreed"
    shown = [(t.agent_id, t.logical_time, t.shown_plan) for t in episode.turns if t.shown_plan]
    assert [(agent, time, plan["plan_version"]) for agent, time, plan in shown] == [
        ("A", 13, 1),
        ("B", 13, 1),
        ("A", CONFIRM_TIME, 2),
        ("B", CONFIRM_TIME, 2),
    ]
    assert all(plan["feedback_shown"] and plan["status"] == "WITHIN_BUDGET" for *_, plan in shown)
    # The rendered text reaches the request once per version and its hash is logged.
    for turn in episode.turns:
        if turn.shown_plan:
            content = turn.request["messages"][-1]["content"]
            assert f"Совместный план #{turn.shown_plan['plan_version']}" in content
    tools_at = {
        t.logical_time: {tool["function"]["name"] for tool in t.request["tools"]}
        for t in episode.turns
        if t.agent_id == "A"
    }
    assert tools_at[6] == tools_at[33] == {"propose_plan", "wait_until"}
    assert tools_at[13] == {"send_message", "skip_round"}
    assert tools_at[37] == {"confirm_plan", "wait_until"}


def test_structured_prompt_is_shared_by_v_g_and_round_count() -> None:
    agent = make_scenario().agents[0]
    prompts = {build_protocol_prompt(agent, "B", Variant.parse(v), 40) for v in STRUCTURED}
    assert len(prompts) == 1
    (prompt,) = prompts
    assert "раунд" in prompt and "R3P" not in prompt
    assert "Сопоставь стоимость своего плана" not in prompt


BASELINE_RUN = Path(__file__).parents[1] / "results/e1-baseline-bc00219"


@pytest.mark.skipif(not BASELINE_RUN.exists(), reason="baseline results not checked out")
def test_baseline_prompts_are_unchanged_since_the_baseline_run() -> None:
    manifest = json.loads((BASELINE_RUN / "mistral-small-2603/run_manifest.json").read_bytes())
    for identity in manifest["episodes"].values():
        spec = identity["spec"]
        assert spec["variant"] in BASELINE_VARIANTS
        scenario = load_scenario(DATA_ROOT.parent.parent / "data/scenarios" / spec["profile"])
        config = RunConfig.for_protocol(
            spec["variant"],
            first_agent=identity["config"]["first_agent"],
            role_swap=identity["config"]["role_swap"],
        )
        resolved = config.apply(scenario)
        ids = [agent.agent_id for agent in resolved.agents]
        opens = config.open_times(ids)
        for agent in resolved.agents:
            peer = next(other for other in ids if other != agent.agent_id)
            prompt = build_protocol_prompt(agent, peer, config.variant, opens[agent.agent_id])
            assert prompt_sha256(prompt) == identity["system_sha256"][agent.agent_id]


def test_guard_rejects_off_plan_only_with_g() -> None:
    def run(variant):
        a = ScriptedPolicy({6: ProposePlan((A_SHORT,)), 37: ConfirmPlan(2), 40: SubmitJob(*A_FULL)})
        b = ScriptedPolicy({6: ProposePlan((B_STANDARD,)), 37: ConfirmPlan(2)})
        return run_episode(_scenario(budget=13), RunConfig.for_protocol(variant), {"A": a, "B": b})

    for variant, expected in (("A/S", "accepted"), ("A/S+G", "plan_mismatch")):
        submit = _events(run(variant), "submit")[0]
        assert (submit.result, submit.detail["off_plan"]) == (expected, True)
