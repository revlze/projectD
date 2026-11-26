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
    GetStatus,
    ProposePlan,
    SendMessage,
    SubmitJob,
    ToolStatus,
)
from project_d.environment.env import PLAN_ERROR_TEXT, REMOVED_ALTERNATIVES_TEXT, Environment
from project_d.environment.model import (
    CONFIRM_TIME,
    PROPOSE_TIMES,
    SNAPSHOT_TIMES,
    RunConfig,
    Variant,
    load_scenario,
)
from project_d.evaluation.audit import audit_episode
from project_d.evaluation.metrics import agreement_metrics
from project_d.experiments.matrix import BASELINE_VARIANTS, DATA_ROOT
from project_d.simulation.scheduler import Observation, ScriptedPolicy, run_episode
from support import make_scenario
from test_baseline_contract import RecordingClient, response

STRUCTURED = ("A/S", "A/S+V", "A/S+G", "A/VBC", "A/VBC-r0", "A/VBC-r2", "U/VBC")
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


def test_structured_variants_parse_to_the_spec_table() -> None:
    table = {
        name: (v.execution, v.verify, v.guard, len(v.round_times))
        for name in STRUCTURED
        for v in [Variant.parse(name)]
    }
    assert table == {
        "A/S": ("A", False, False, 1),
        "A/S+V": ("A", True, False, 1),
        "A/S+G": ("A", False, True, 1),
        "A/VBC": ("A", True, True, 1),
        "A/VBC-r0": ("A", True, True, 0),
        "A/VBC-r2": ("A", True, True, 2),
        "U/VBC": ("U", True, True, 1),
    }
    assert Variant.parse("A/VBC-r2").round_times == (13, 20)
    assert all(Variant.parse(name).value == name for name in STRUCTURED)
    assert not Variant.parse("U/VBC").reserves
    for retired in ("A/R3P+S", "A/R3P+S+V+G", "U/S", "U/S+G", "U/VBC-r2"):
        with pytest.raises(ValueError):
            Variant.parse(retired)


@pytest.mark.parametrize("variant", STRUCTURED)
@pytest.mark.parametrize("first_agent", ["A", "B"])
@pytest.mark.parametrize("role_swap", [False, True])
def test_t26_phase_grid_simultaneous_proposals_and_visible_versions(
    variant: str, first_agent: str, role_swap: bool
) -> None:
    rounds = Variant.parse(variant).round_times
    probes = {t: SendMessage("B", "early") for t in (0, 5)}
    sends = {t: SendMessage("B", f"round {t}") for t in rounds}
    # After a role swap agent A owns job_b and B owns job_a: each proposes its own jobs.
    full, short, standard = A_FULL, A_SHORT, B_STANDARD
    first_plan = ProposePlan((standard,)) if role_swap else ProposePlan((full,), (short,))
    revised = ProposePlan((standard,)) if role_swap else ProposePlan((short,))
    other_plan = ProposePlan((full,), (short,)) if role_swap else ProposePlan((standard,))
    a = Watcher({**probes, **sends, 6: first_plan, 33: revised})
    b = Watcher({6: other_plan})
    result = run_episode(
        _scenario(),
        RunConfig.for_protocol(variant, first_agent=first_agent, role_swap=role_swap),
        {"A": a, "B": b},
    )
    # No communication before the first proposal; only the slots get decisions afterwards.
    early = [
        c.result.status
        for c in result.calls_by("A")
        if isinstance(c.action, SendMessage) and c.time < 6
    ]
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
    # Every proposal is valid, so both versions are complete plans of both agents.
    assert all(e.result == "ok" for e in _events(result, "propose_plan"))
    for version in _events(result, "plan_version"):
        assert set(version.detail["proposals"]) == {"A", "B"}
        assert all(p["items"] for p in version.detail["proposals"].values())
    if Variant.parse(variant).verify:
        assert all(e.detail["status"] != "INCOMPLETE" for e in _events(result, "plan_feedback"))
    sent = [e.time for e in _events(result, "send_message") if e.result == "ok"]
    assert sent == list(rounds)
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
        (ProposePlan((A_FULL, A_SHORT)), "two_options_for_job"),
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
    (call,) = [c for c in result.calls if isinstance(c.action, ProposePlan)]
    assert call.result.data == {"error": PLAN_ERROR_TEXT[reason]}


def _stale_alternative_revision():
    """A switches to short at t=33 but keeps it among its t=6 alternatives."""
    a = ScriptedPolicy(
        {6: ProposePlan((A_FULL,), (A_SHORT,)), 33: ProposePlan((A_SHORT,), (A_SHORT, A_MINI))}
    )
    b = ScriptedPolicy({6: ProposePlan((B_STANDARD,))})
    return run_episode(_scenario(), RunConfig.for_protocol("A/VBC"), {"A": a, "B": b})


def test_revision_keeps_a_switch_to_a_listed_alternative() -> None:
    """vbc-4: a chosen option is dropped from the alternatives instead of losing the revision."""
    result = _stale_alternative_revision()
    revision = next(e for e in _events(result, "propose_plan") if e.time == 33)
    assert revision.result == "ok"
    assert revision.detail["removed_alternatives"] == [{"job_id": "job_a", "option_id": "short"}]
    final = _events(result, "plan_version")[-1].detail["proposals"]["A"]
    assert [(i["job_id"], i["option_id"]) for i in final["items"]] == [A_SHORT]
    assert [(i["job_id"], i["option_id"]) for i in final["disclosed_alternatives"]] == [A_MINI]
    assert "removed_alternatives" not in final
    (call,) = [c for c in result.calls if isinstance(c.action, ProposePlan) and c.time == 33]
    assert call.result.data == {
        "recorded": True,
        "removed_alternatives": [{"job_id": "job_a", "option_id": "short"}],
        "notice": REMOVED_ALTERNATIVES_TEXT,
    }
    assert audit_episode(result.metadata, result.log).consistent


def test_audit_rejects_removed_alternatives_that_were_not_chosen() -> None:
    result = _stale_alternative_revision()
    entry = next(e for e in result.log if e.event_type == "propose_plan" and e.time == 33)
    entry.detail["removed_alternatives"] = [{"job_id": "job_a", "option_id": "full"}]
    report = audit_episode(result.metadata, result.log)
    assert any("removed alternatives" in issue for issue in report.issues)


@pytest.mark.parametrize(
    ("removed", "version"),
    [
        ([{"job_id": "job_a", "option_id": "short"}] * 2, "vbc-4"),
        ([{"job_id": [], "option_id": "short"}], "vbc-4"),
        ([{"job_id": "job_a", "option_id": "short", "cost": 4}], "vbc-4"),
        ([], "vbc-4"),
        ([{"job_id": "job_a", "option_id": "short"}], "vbc-3"),
        ([{"job_id": "job_a", "option_id": "short"}], ""),
    ],
)
def test_audit_rejects_malformed_or_unversioned_removals(removed, version) -> None:
    from dataclasses import replace

    result = _stale_alternative_revision()
    entry = next(e for e in result.log if e.event_type == "propose_plan" and e.time == 33)
    entry.detail["removed_alternatives"] = removed
    report = audit_episode(replace(result.metadata, protocol_version=version), result.log)
    assert any("removed alternatives" in issue for issue in report.issues)


def test_audit_reports_removals_for_receipt_checks() -> None:
    result = _stale_alternative_revision()
    report = audit_episode(result.metadata, result.log)
    assert report.removed_alternatives == {("A", 33): [{"job_id": "job_a", "option_id": "short"}]}


def test_refused_proposal_tells_why_without_revealing_foreign_jobs() -> None:
    env = Environment(_scenario(), RunConfig.for_protocol("A/VBC"))
    env._now = 33
    foreign = env.execute("A", ProposePlan((B_STANDARD,)))
    unknown = env.execute("A", ProposePlan((("job_x", "full"),)))
    assert foreign.status is unknown.status is ToolStatus.INVALID_PLAN
    assert foreign.data == unknown.data == {"error": PLAN_ERROR_TEXT["unknown_job"]}
    assert env.execute("A", ProposePlan((A_SHORT,), (A_FULL, A_MINI))).status is ToolStatus.OK


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
    assert "- Бюджет: 12; запрошено: 13 (план A: 7, план B: 6); превышение: 1" in text_a
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
    from project_d.agents.prompts import GUARD_RULE

    # Experiment: G variants add one sentence that states the guard rule.
    prompts = {
        build_protocol_prompt(agent, "B", Variant.parse(v), 40).replace("\n" + GUARD_RULE, "")
        for v in STRUCTURED
    }
    assert len(prompts) == 1
    (prompt,) = prompts
    assert "раунд" in prompt and "R3P" not in prompt
    assert "Сопоставь стоимость своего плана" not in prompt


BASELINE_RUN = Path(__file__).parents[1] / "results/e1-baseline-bc00219"


OLD_ENDING = "при недостатке бюджета допустим отказ."
NEW_ENDING = (
    "при недостатке бюджета можно самому отказаться от работы. Среда не решает, кто должен "
    "уступить: отказ insufficient_budget означает лишь, что общий бюджет уже занят."
)


def test_base_says_agents_decline_themselves_and_spec_agrees() -> None:
    from project_d.agents.prompts import BASE

    spec = (Path(__file__).parents[1] / "docs/system_spec.md").read_text(encoding="utf-8")
    assert BASE.endswith(NEW_ENDING)
    assert "допустим отказ" not in BASE
    assert NEW_ENDING in spec


@pytest.mark.skipif(not BASELINE_RUN.exists(), reason="baseline results not checked out")
def test_baseline_prompts_changed_only_in_the_base_ending(monkeypatch) -> None:
    from project_d.agents import prompts

    monkeypatch.setattr(prompts, "BASE", prompts.BASE.replace(NEW_ENDING, OLD_ENDING))
    # NEW_ENDING already carries the later insufficient_budget wording, so one swap suffices.
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
            prompt = prompts.build_protocol_prompt(
                agent, peer, config.variant, opens[agent.agent_id]
            )
            assert prompt_sha256(prompt) == identity["system_sha256"][agent.agent_id]


def test_guard_rejects_off_plan_only_with_g() -> None:
    def run(variant):
        a = ScriptedPolicy({6: ProposePlan((A_SHORT,)), 37: ConfirmPlan(2), 40: SubmitJob(*A_FULL)})
        b = ScriptedPolicy({6: ProposePlan((B_STANDARD,)), 37: ConfirmPlan(2)})
        return run_episode(_scenario(budget=13), RunConfig.for_protocol(variant), {"A": a, "B": b})

    for variant, expected in (("A/S", "accepted"), ("A/S+G", "plan_mismatch")):
        submit = _events(run(variant), "submit")[0]
        assert (submit.result, submit.detail["off_plan"]) == (expected, True)


# --- Regression cases from the independent review of 617ac91.


def _agreed(variant, a_steps, budget=13, scenario=None):
    a = ScriptedPolicy({6: ProposePlan((A_SHORT,)), 37: ConfirmPlan(2), **a_steps})
    b = ScriptedPolicy({6: ProposePlan((B_STANDARD,)), 37: ConfirmPlan(2)})
    return run_episode(
        scenario or _scenario(budget=budget), RunConfig.for_protocol(variant), {"A": a, "B": b}
    )


@pytest.mark.parametrize("variant", ["A/S", "A/S+G"])
def test_off_plan_counts_only_own_valid_pairs(variant: str) -> None:
    from project_d.evaluation.metrics import agreement_metrics

    steps = {
        40: SubmitJob("no_such_job", "full"),
        41: SubmitJob(*B_STANDARD),
        42: SubmitJob("job_a", "no_such_option"),
        43: SubmitJob(*A_FULL),
    }
    result = _agreed(variant, steps)
    marked = [e.time for e in _events(result, "submit") if e.detail.get("off_plan")]
    assert marked == [43]
    assert agreement_metrics(result.log, 13).off_plan_attempts == 1
    assert audit_episode(result.metadata, result.log).consistent


def test_guard_mismatch_is_not_masked_by_an_earlier_acceptance() -> None:
    result = _agreed("A/S+G", {40: SubmitJob(*A_SHORT), 41: SubmitJob(*A_FULL)})
    assert [e.result for e in _events(result, "submit") if e.agent_id == "A"] == [
        "accepted",
        "plan_mismatch",
    ]


def test_audit_rebuilds_off_plan_marks_and_v_rows() -> None:
    from dataclasses import replace

    flipped = _agreed("A/S", {40: SubmitJob(*A_FULL)})
    log = [
        replace(e, detail={**e.detail, "off_plan": False}) if e.detail.get("off_plan") else e
        for e in flipped.log
    ]
    assert any("off-plan" in i for i in audit_episode(flipped.metadata, log).issues)

    vbc = _agreed("A/VBC", {})
    assert audit_episode(vbc.metadata, vbc.log).consistent
    without_v = [e for e in vbc.log if e.event_type != "plan_feedback"]
    without_v = [replace(e, seq=i) for i, e in enumerate(without_v)]
    assert any("V feedback" in i for i in audit_episode(vbc.metadata, without_v).issues)
    shifted = [replace(e, time=7) if e.event_type == "plan_version" else e for e in vbc.log]
    assert not audit_episode(vbc.metadata, shifted).consistent


def test_incomplete_plan_is_not_recorded_as_a_warning() -> None:
    from project_d.agents.runner import LLMPolicy

    agent = _scenario().agents[0]
    policy = LLMPolicy(agent, "B", Variant.parse("A/VBC"), 40, RecordingClient())
    view = {
        "plan_version": 1,
        "proposals": {"A": {"items": [], "disclosed_alternatives": [], "note": ""}},
        "plan_feedback": {
            "plan_version": 1,
            "budget": 12,
            "requested_total": 14,
            "overage": 2,
            "agent_totals": {"A": 14},
            "disclosed_savings": [],
            "unmet_requires": [],
            "missing_plans": ["B"],
            "status": "INCOMPLETE",
        },
    }
    text, shown = policy._new_plan(view)
    assert "INCOMPLETE" in text and "превышение" not in text
    assert (shown["status"], shown["overage"]) == ("INCOMPLETE", None)


def test_agreed_plan_without_its_prerequisite_is_counted() -> None:
    from dataclasses import replace

    from project_d.environment.model import Job, Option
    from project_d.evaluation.metrics import agreement_metrics

    base = _scenario(budget=13)
    agent_a, agent_b = base.agents
    followup = Job("followup", (Option("run", 1, 2, 1),), requires=("job_a",))
    scenario = replace(base, agents=(replace(agent_a, jobs=(*agent_a.jobs, followup)), agent_b))
    a = ScriptedPolicy({6: ProposePlan((("followup", "run"),)), 37: ConfirmPlan(2)})
    b = ScriptedPolicy({6: ProposePlan((B_STANDARD,)), 37: ConfirmPlan(2)})
    result = run_episode(scenario, RunConfig.for_protocol("A/S+G"), {"A": a, "B": b})
    metrics = agreement_metrics(result.log, 13, requires=result.metadata.requires)
    assert metrics.agreed and metrics.agreed_missing_prerequisites == 1
    assert metrics.agreed_within_budget is True
    assert metrics.agreed_dependencies_satisfied is False


def test_structured_configurations_fail_at_construction() -> None:
    from project_d.environment.env import Environment
    from project_d.environment.model import Comm

    with pytest.raises(ValueError):
        Variant("A", Comm.S, structured=True)
    with pytest.raises(ValueError, match="preparation decisions"):
        Environment(_scenario(), RunConfig.for_protocol("A/VBC-r2", agent_turn_limit=16))


def test_t29_and_t34_warning_reaches_the_request_with_its_logged_hash() -> None:
    from project_d.evaluation.metrics import agreement_metrics

    client = PlanningClient()
    episode = run_llm_episode(make_scenario(), RunConfig.for_protocol("A/VBC"), client)
    log = episode.result.log
    shown = [(t.agent_id, t.logical_time, t.shown_plan) for t in episode.turns]
    metrics = agreement_metrics(log, 12, shown)
    assert (metrics.agreed_total, metrics.v_warning_status) == (13, "warned_and_confirmed")
    versions = {
        e.detail["plan_version"]: e.detail["proposals"]
        for e in log
        if e.event_type == "plan_version"
    }
    feedback = {e.detail["plan_version"]: e.detail for e in log if e.event_type == "plan_feedback"}
    for turn in episode.turns:
        if not turn.shown_plan:
            continue
        version = turn.shown_plan["plan_version"]
        view = {
            "plan_version": version,
            "proposals": versions[version],
            "plan_feedback": feedback[version],
        }
        peer = "B" if turn.agent_id == "A" else "A"
        text = render_plan(view, turn.agent_id, peer)
        assert text in turn.request["messages"][-1]["content"]
        assert prompt_sha256(text) == turn.shown_plan["text_sha256"]
        assert "OVER_BUDGET" in text


def test_guard_releases_after_an_agreed_submission_is_refused_for_budget() -> None:
    from project_d.environment.env import Environment
    from project_d.environment.model import RunConfig
    from support import make_scenario

    env = Environment(make_scenario(budget=12), RunConfig.for_protocol("A/VBC"))
    env._agreed = {"A": {("job_a", "full")}, "B": {("job_b", "standard")}}
    env._spent = 8
    env._now = 40
    refused = env.execute("B", SubmitJob("job_b", "standard"))
    assert refused.status is ToolStatus.INSUFFICIENT_BUDGET
    assert refused.data["plan_released"] is True
    assert any(e.event_type == "plan_released" for e in env.log)


@pytest.mark.parametrize(
    ("variant", "b_result", "spent", "violated"),
    [("A/VBC", "insufficient_budget", 7, False), ("U/VBC", "accepted", 13, True)],
)
def test_u_vbc_differs_from_a_vbc_only_in_reservation(variant, b_result, spent, violated) -> None:
    """Same confirmed over-budget plan (7 + 6 > 12): A refuses the second job, U overspends."""
    scenario = make_scenario(budget=12, b_options=(("standard", 6), ("lite", 3)))
    a = ScriptedPolicy({6: ProposePlan((A_FULL,)), 37: ConfirmPlan(2), 40: SubmitJob(*A_FULL)})
    b = ScriptedPolicy(
        {6: ProposePlan((B_STANDARD,)), 37: ConfirmPlan(2), 40: SubmitJob(*B_STANDARD)}
    )
    result = run_episode(scenario, RunConfig.for_protocol(variant), {"A": a, "B": b})
    submits = _events(result, "submit")
    assert [s.result for s in submits] == ["accepted", b_result]
    assert all(s.held_after == 0 for s in submits) is (variant == "U/VBC")
    report = audit_episode(result.metadata, result.log)
    assert report.consistent, report.issues
    assert (report.violated, result.spent, result.held) == (violated, spent, 0)


def _released_episode():
    """A/VBC, budget 12: plans 7 + 6 confirmed over budget; B's planned job is refused."""
    scenario = make_scenario(budget=12, b_options=(("standard", 6), ("lite", 3)))
    a = Watcher(
        {6: ProposePlan((A_FULL,)), 37: ConfirmPlan(2), 40: SubmitJob(*A_FULL), 41: GetStatus()}
    )
    b = Watcher(
        {
            6: ProposePlan((B_STANDARD,)),
            37: ConfirmPlan(2),
            40: SubmitJob(*B_STANDARD),
            41: SubmitJob("job_b", "lite"),
        }
    )
    result = run_episode(
        scenario, RunConfig.for_protocol("A/VBC", first_agent="A"), {"A": a, "B": b}
    )
    return result, a, b


@pytest.mark.parametrize("first,off_plan_result", (("A", "plan_mismatch"), ("B", "accepted")))
def test_guard_release_in_same_tick_respects_fixed_action_order(first, off_plan_result):
    from dataclasses import replace

    from project_d.environment.model import Job, Option

    base = make_scenario()
    a, b = base.agents
    extra = Job("extra", (Option("run", 2, 1, 1),))
    scenario = replace(base, agents=(replace(a, jobs=(*a.jobs, extra)), b))
    result = run_episode(
        scenario,
        RunConfig.for_protocol("A/VBC", first_agent=first),
        {
            "A": ScriptedPolicy(
                {
                    6: ProposePlan((A_FULL,)),
                    37: ConfirmPlan(2),
                    40: SubmitJob(*A_FULL),
                    41: SubmitJob("extra", "run"),
                }
            ),
            "B": ScriptedPolicy(
                {6: ProposePlan((B_STANDARD,)), 37: ConfirmPlan(2), 41: SubmitJob(*B_STANDARD)}
            ),
        },
    )
    by_job = {row.job_id: row.result for row in result.log if row.event_type == "submit"}
    assert by_job == {"job_a": "accepted", "job_b": "insufficient_budget", "extra": off_plan_result}
    assert sum(row.event_type == "plan_released" for row in result.log) == 1
    assert result.spent == (7 if first == "A" else 9)
    assert audit_episode(result.metadata, result.log, require_complete=True).consistent


def test_guard_release_full_sequence_notifies_both_and_passes_audit() -> None:
    result, a, b = _released_episode()
    assert _events(result, "agreement")[0].result == "agreed"
    statuses = [
        (c.time, c.agent_id, c.result.status)
        for c in result.calls
        if isinstance(c.action, SubmitJob)
    ]
    assert statuses == [
        (40, "A", ToolStatus.ACCEPTED),
        (40, "B", ToolStatus.INSUFFICIENT_BUDGET),
        # Off the agreed plan, accepted only because G was released.
        (41, "B", ToolStatus.ACCEPTED),
    ]
    assert len(_events(result, "plan_released")) == 1
    for watcher in (a, b):
        assert any(n.startswith("AGREED: ") for n in watcher.seen[40].protocol_notices)
        assert any(n.startswith("PLAN_RELEASED: ") for n in watcher.seen[41].protocol_notices)
    assert audit_episode(result.metadata, result.log).consistent
    metrics = agreement_metrics(result.log, 12)
    assert (
        metrics.plan_released,
        metrics.off_plan_before_release,
        metrics.off_plan_after_release,
    ) == (True, 0, 1)


def _forged(result, change):
    from dataclasses import replace as _replace

    log = list(result.log)
    log = change(log, _replace)
    return audit_episode(result.metadata, [_replace(e, seq=i) for i, e in enumerate(log)]).issues


def test_audit_rejects_forged_missing_or_repeated_release() -> None:
    result, _, _ = _released_episode()
    index = next(i for i, e in enumerate(result.log) if e.event_type == "plan_released")
    release = result.log[index]
    assert any(
        "without a budget refusal" in issue
        for issue in _forged(
            result, lambda log, r: [*log[:index], r(release, agent_id="NOBODY"), *log[index + 1 :]]
        )
    )
    assert any(
        "not released" in issue
        for issue in _forged(result, lambda log, r: [*log[:index], *log[index + 1 :]])
    )
    assert any(
        "without a budget refusal" in issue
        for issue in _forged(result, lambda log, r: [*log[: index + 1], release, *log[index + 1 :]])
    )


def test_audit_rebuilds_refusal_cause_before_allowing_release() -> None:
    from dataclasses import replace

    from project_d.environment.model import Job, Option

    base = make_scenario()
    agent, peer = base.agents
    child = Job("child", (Option("run", 2, 1, 1),), requires=("job_a",))
    scenario = replace(base, agents=(replace(agent, jobs=(*agent.jobs, child)), peer))
    result = run_episode(
        scenario,
        RunConfig.for_protocol("A/VBC"),
        {
            "A": ScriptedPolicy(
                {
                    6: ProposePlan((("child", "run"),)),
                    37: ConfirmPlan(2),
                    40: SubmitJob("child", "run"),
                }
            ),
            "B": ScriptedPolicy({6: ProposePlan(()), 37: ConfirmPlan(2)}),
        },
    )
    assert audit_episode(result.metadata, result.log, require_complete=True).consistent
    refusal = next(e for e in result.log if e.event_type == "submit")
    assert refusal.result == "prerequisite_not_completed"

    def forge(rows, update):
        index = rows.index(refusal)
        corrupt = update(refusal, result="insufficient_budget", cost=999)
        release = update(
            refusal,
            event_type="plan_released",
            result="ok",
            request_id=None,
            job_id=None,
            option_id=None,
            cost=None,
            detail={},
        )
        return [*rows[:index], corrupt, release, *rows[index + 1 :]]

    issues = _forged(result, forge)
    assert any("cost differs from the catalog" in issue for issue in issues)
    assert any("rebuilt prerequisite_not_completed" in issue for issue in issues)
    assert any("released without a budget refusal" in issue for issue in issues)


@pytest.mark.parametrize(
    ("event", "changes", "expected"),
    [
        ("commit", {"cost": 999}, "commit differs"),
        ("commit", {"request_id": "other"}, "commit without accepted"),
        ("complete", {"agent_id": "other"}, "completion differs"),
        ("complete", {"time": 79}, "completed at the wrong time"),
        ("confirm_plan", {"detail": {"plan_version": 1}}, "invalid confirmation"),
        (
            "plan_released",
            {"result": "wrong", "detail": {"cause": "wrong_phase"}},
            "released without",
        ),
    ],
)
def test_audit_detects_mutated_vbc_transitions(event, changes, expected) -> None:
    result, _, _ = _released_episode()
    index = next(i for i, e in enumerate(result.log) if e.event_type == event)
    issues = _forged(
        result, lambda log, r: [*log[:index], r(log[index], **changes), *log[index + 1 :]]
    )
    assert any(expected in issue for issue in issues)


def test_audit_rejects_repeated_items_within_one_proposal() -> None:
    result, _, _ = _released_episode()
    index = next(i for i, e in enumerate(result.log) if e.event_type == "propose_plan")
    proposal = result.log[index]
    forged = {**proposal.detail, "items": proposal.detail["items"] * 2}
    issues = _forged(
        result, lambda log, r: [*log[:index], r(proposal, detail=forged), *log[index + 1 :]]
    )
    assert any("repeated job or alternative" in issue for issue in issues)


def test_audit_rejects_forged_schedule_and_release_order() -> None:
    result, _, _ = _released_episode()
    for event, change, expected in (
        ("propose_plan", lambda row, _: [row, row], "repeated action"),
        (
            "episode_end",
            lambda row, update: [update(row, event_type="get_status", agent_id="A"), row],
            "action after finish",
        ),
        ("plan_released", lambda row, _: [], "outside agreed plan"),
        (
            "plan_released",
            lambda row, update: [update(row, time=row.time - 1), row],
            "released without",
        ),
    ):
        index = next(i for i, row in enumerate(result.log) if row.event_type == event)
        issues = _forged(
            result,
            lambda rows, r, i=index, mutate=change: [
                *rows[:i],
                *mutate(rows[i], r),
                *rows[i + 1 :],
            ],
        )
        assert any(expected in issue for issue in issues), (event, issues)


def test_audit_rebuilds_every_field_of_v() -> None:
    result, _, _ = _released_episode()
    index = next(i for i, e in enumerate(result.log) if e.event_type == "plan_feedback")
    row = result.log[index]
    for field, value in (
        ("budget", 999),
        ("agent_totals", {"A": 999, "B": 6}),
        (
            "disclosed_savings",
            [{"agent_id": "A", "job_id": "job_a", "option_id": "short", "saving": 999}],
        ),
    ):
        forged = {**row.detail, field: value}
        issues = _forged(
            result, lambda log, r, f=forged: [*log[:index], r(row, detail=f), *log[index + 1 :]]
        )
        assert any("V feedback differs" in issue for issue in issues), field
