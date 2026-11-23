"""Scripted protocol checks derived from system_spec.md and decisions D15-D20."""

from dataclasses import asdict, replace

import pytest

from project_d.environment.actions import (
    Action,
    ConfirmPlan,
    Finish,
    GetBalance,
    GetStatus,
    ListJobs,
    ProposePlan,
    ReadMessages,
    SendMessage,
    SubmitJob,
    ToolStatus,
    WaitUntil,
)
from project_d.environment.env import Environment
from project_d.environment.model import Job, JobStatus, Option, RunConfig, Variant
from project_d.evaluation.audit import audit_episode
from project_d.simulation.scheduler import EpisodeResult, Observation, ScriptedPolicy, run_episode
from support import make_scenario

A_FULL = ("job_a", "full")
A_SHORT = ("job_a", "short")
B_STANDARD = ("job_b", "standard")
PLAN_A = ProposePlan((A_FULL,), (A_SHORT,))
PLAN_B = ProposePlan((B_STANDARD,))
REVISED_A = ProposePlan((A_SHORT,), (A_FULL,))


class ObservedScript(ScriptedPolicy):
    def __init__(self, steps: dict[int, Action], *, confirm_from: int | None = None) -> None:
        super().__init__(steps)
        self.observations: dict[int, Observation] = {}
        self.confirm_from = confirm_from

    def decide(self, observation: Observation) -> Action:
        assert observation.logical_time not in self.observations
        self.observations[observation.logical_time] = observation
        if observation.logical_time == 37 and self.confirm_from is not None:
            view = self.observations[self.confirm_from].plan_view
            assert view is not None
            self.steps[37] = ConfirmPlan(view["plan_version"])
        return super().decide(observation)


def _scenario(**settings):
    return make_scenario(a_options=(("full", 7), ("short", 4)), **settings)


def _events(result: EpisodeResult, event_type: str):
    return [entry for entry in result.log if entry.event_type == event_type]


def _statuses(result: EpisodeResult, agent: str, action_type: type):
    return [
        (call.time, call.result.status)
        for call in result.calls_by(agent)
        if isinstance(call.action, action_type)
    ]


def _assert_no_value(payload: object) -> None:
    if isinstance(payload, dict):
        assert "value" not in payload
        for child in payload.values():
            _assert_no_value(child)
    elif isinstance(payload, (list, tuple)):
        for child in payload:
            _assert_no_value(child)


def _assert_fallback(result: EpisodeResult) -> None:
    assert [(entry.time, entry.result) for entry in _events(result, "agreement")] == [
        (40, "agreement_failed")
    ]
    assert _events(result, "agreement")[0].detail["fallback"] is True
    report = audit_episode(result.metadata, result.log)
    assert report.agreement == "agreement_failed"
    assert report.consistent, report.issues


@pytest.mark.parametrize("delay", [1, 4, 8])
def test_t11_messages_visible_only_after_delivery(delay: int) -> None:
    sender = ScriptedPolicy({6: SendMessage("B", "first round"), 40: Finish()})
    receiver = ObservedScript({40: Finish()})
    result = run_episode(
        _scenario(message_delay=delay),
        RunConfig.for_protocol("A/R3"),
        {"A": sender, "B": receiver},
    )

    assert [entry.time for entry in _events(result, "message_delivered")] == [6 + delay]
    assert receiver.observations[6].inbox == ()
    visible_at = 13 if delay in (1, 4) else 20
    if delay == 8:
        assert receiver.observations[13].inbox == ()
    assert [message["text"] for message in receiver.observations[visible_at].inbox] == [
        "first round"
    ]


@pytest.mark.parametrize("first_agent", ["A", "B"])
def test_t12_r1_and_r3_share_submission_schedule(first_agent: str) -> None:
    for variant, slots in [("A/R1", (6,)), ("A/R3", (6, 13, 20))]:
        policies = {
            agent: ScriptedPolicy(
                {time: SendMessage(peer, "planning") for time in slots}
                | {39: SubmitJob(*item), 40: SubmitJob(*item)}
            )
            for agent, peer, item in [("A", "B", A_SHORT), ("B", "A", B_STANDARD)]
        }
        result = run_episode(
            _scenario(commit_delay=3),
            RunConfig.for_protocol(variant, first_agent=first_agent),
            policies,
        )
        assert result.metadata.submission_open_at == {"A": 40, "B": 40}
        assert result.metadata.horizon == 80
        for agent in policies:
            assert _statuses(result, agent, SendMessage) == [(t, ToolStatus.OK) for t in slots]
            assert _statuses(result, agent, SubmitJob) == [
                (39, ToolStatus.SUBMISSION_NOT_OPEN),
                (40, ToolStatus.ACCEPTED),
            ]
        assert [entry.time for entry in _events(result, "commit")] == [43, 43]


@pytest.mark.parametrize("field", ["items", "disclosed_alternatives"])
def test_t13_foreign_job_rejected_without_disclosure(field: str) -> None:
    with_foreign_job = _scenario()
    agent_a, agent_b = with_foreign_job.agents
    renamed_job = replace(agent_b.jobs[0], job_id="other_job")
    without_foreign_job = replace(
        with_foreign_job, agents=(agent_a, replace(agent_b, jobs=(renamed_job,)))
    )
    proposal = replace(ProposePlan(()), **{field: (B_STANDARD,)})

    def run(scenario):
        proposer = ObservedScript({29: proposal, 35: Finish()})
        result = run_episode(
            scenario,
            RunConfig.for_protocol("A/R3P+S"),
            {
                "A": proposer,
                "B": ScriptedPolicy({40: Finish()}),
            },
        )
        call = next(call for call in result.calls_by("A") if isinstance(call.action, ProposePlan))
        assert call.result.status != ToolStatus.OK
        assert all(entry.spent_after == entry.held_after == 0 for entry in result.log)
        assert all(not entry.detail["proposals"] for entry in _events(result, "plan_version"))
        return call.result, proposer.observations

    assert run(with_foreign_job) == run(without_foreign_job)


def test_t14_only_disclosed_catalog_costs_are_shared() -> None:
    scenario = _scenario()
    agent_a, agent_b = scenario.agents
    hidden_job = Job("private_job", (Option("private_option", 2, 1, 901),))
    scenario = replace(
        scenario, agents=(replace(agent_a, jobs=(*agent_a.jobs, hidden_job)), agent_b)
    )
    receiver = ObservedScript({30: ListJobs(), 31: GetStatus(), 35: Finish()})
    result = run_episode(
        scenario,
        RunConfig.for_protocol("A/R3P+S"),
        {"A": ScriptedPolicy({29: PLAN_A, 35: Finish()}), "B": receiver},
    )
    assert _statuses(result, "A", ProposePlan) == [(29, ToolStatus.OK)]
    observation = receiver.observations[30]
    assert {job["job_id"] for job in observation.own_jobs} == {"job_b"}
    assert observation.plan_view is not None
    assert "plan_feedback" not in observation.plan_view
    assert observation.plan_view["proposals"] == {
        "A": {
            "items": [{"job_id": "job_a", "option_id": "full", "cost": 7}],
            "disclosed_alternatives": [{"job_id": "job_a", "option_id": "short", "cost": 4}],
            "note": "",
        }
    }
    for seen in receiver.observations.values():
        _assert_no_value(asdict(seen))


def test_t15_feedback_reports_savings_without_choosing_who_yields() -> None:
    receiver = ObservedScript({29: PLAN_B, 30: GetBalance(), 35: Finish()})
    result = run_episode(
        _scenario(b_options=(("standard", 6), ("undisclosed", 2))),
        RunConfig.for_protocol("A/VBC"),
        {"A": ScriptedPolicy({29: PLAN_A, 35: Finish()}), "B": receiver},
    )

    plan = receiver.observations[30].plan_view
    assert plan is not None
    feedback = plan["plan_feedback"]
    assert feedback == {
        "plan_version": plan["plan_version"],
        "budget": 12,
        "requested_total": 13,
        "overage": 1,
        "agent_totals": {"A": 7, "B": 6},
        "disclosed_savings": [
            {"agent_id": "A", "job_id": "job_a", "option_id": "short", "saving": 3}
        ],
        "unmet_requires": [],
    }
    for time in (30, 35):
        view = receiver.observations[time].plan_view
        assert view is not None
        assert view["proposals"]["A"]["items"][0]["option_id"] == "full"
        _assert_no_value(view["plan_feedback"])
    assert all(entry.spent_after == entry.held_after == 0 for entry in result.log)


def test_t16_different_confirmed_versions_trigger_fallback() -> None:
    result = run_episode(
        _scenario(),
        RunConfig.for_protocol("A/VBC"),
        {
            "A": ObservedScript(
                {29: PLAN_A, 30: GetBalance(), 33: REVISED_A, 40: SubmitJob(*A_FULL)},
                confirm_from=30,
            ),
            "B": ObservedScript({29: PLAN_B, 40: SubmitJob(*B_STANDARD)}, confirm_from=37),
        },
    )
    confirmations = [call.action for call in result.calls if isinstance(call.action, ConfirmPlan)]
    initial, final = (entry.detail["plan_version"] for entry in _events(result, "plan_version"))
    assert initial != final
    assert confirmations == [ConfirmPlan(initial), ConfirmPlan(final)]
    assert _statuses(result, "B", ConfirmPlan) == [(37, ToolStatus.OK)]
    assert _statuses(result, "A", SubmitJob) == [(40, ToolStatus.ACCEPTED)]
    assert _statuses(result, "B", SubmitJob) == [(40, ToolStatus.INSUFFICIENT_BUDGET)]
    _assert_fallback(result)


def test_t17_agreement_rejects_other_option_without_spending() -> None:
    result = run_episode(
        _scenario(),
        RunConfig.for_protocol("A/VBC"),
        {
            "A": ObservedScript(
                {29: REVISED_A, 40: SubmitJob(*A_FULL), 41: SubmitJob(*A_SHORT)},
                confirm_from=37,
            ),
            "B": ObservedScript({29: PLAN_B, 40: SubmitJob(*B_STANDARD)}, confirm_from=37),
        },
    )
    assert _statuses(result, "A", SubmitJob) == [
        (40, ToolStatus.PLAN_MISMATCH),
        (41, ToolStatus.ACCEPTED),
    ]
    assert _statuses(result, "B", SubmitJob) == [(40, ToolStatus.ACCEPTED)]
    refusal = next(entry for entry in _events(result, "submit") if entry.result == "plan_mismatch")
    assert (refusal.spent_before, refusal.held_before) == (refusal.spent_after, refusal.held_after)
    assert (result.spent, result.held) == (10, 0)
    report = audit_episode(result.metadata, result.log)
    assert report.agreement == "agreed"
    assert report.plan_mismatches == 1
    assert report.consistent, report.issues


@pytest.mark.parametrize("variant", ["A/R3P+S", "A/R3P+S+V", "A/R3P+S+G", "A/VBC"])
@pytest.mark.parametrize(("first_agent", "cost"), [("A", 7), ("B", 6)])
def test_t18_v_g_keep_atomic_budget_rules(variant: str, first_agent: str, cost: int) -> None:
    result = run_episode(
        _scenario(commit_delay=3),
        RunConfig.for_protocol(Variant.parse(variant), first_agent=first_agent),
        {
            "A": ObservedScript({29: PLAN_A, 40: SubmitJob(*A_FULL)}, confirm_from=37),
            "B": ObservedScript({29: PLAN_B, 40: SubmitJob(*B_STANDARD)}, confirm_from=37),
        },
    )
    assert result.metadata.variant == variant
    assert _events(result, "agreement")[0].result == "agreed"
    assert [
        (e.agent_id, e.time, e.result, e.spent_after, e.held_after)
        for e in _events(result, "submit")
    ] == [
        (first_agent, 40, "accepted", 0, cost),
        ("B" if first_agent == "A" else "A", 40, "insufficient_budget", 0, cost),
    ]
    assert [(e.time, e.spent_after, e.held_after) for e in _events(result, "commit")] == [
        (43, cost, 0)
    ]
    report = audit_episode(result.metadata, result.log)
    assert report.max_committed_plus_held == cost
    assert not report.violated
    assert report.consistent, report.issues


def _chain_scenario():
    scenario = _scenario(commit_delay=3, duration=6)
    agent_a, agent_b = scenario.agents
    followup = Job("followup", (Option("run", 2, 6, 5),), requires=("job_a",))
    final = Job("final", (Option("run", 2, 6, 5),), requires=("followup",))
    return replace(
        scenario, agents=(replace(agent_a, jobs=(*agent_a.jobs, followup, final)), agent_b)
    )


def test_t19_three_sequential_jobs_require_completion_and_fit_horizon() -> None:
    chained = (A_SHORT, ("followup", "run"), ("final", "run"))
    result = run_episode(
        _chain_scenario(),
        RunConfig.for_protocol("A/VBC", first_agent="B", start_gap=4),
        {
            "A": ObservedScript(
                {
                    29: ProposePlan(chained),
                    43: SubmitJob(*A_SHORT),
                    44: SubmitJob(*A_SHORT),
                    52: SubmitJob("followup", "run"),
                    53: SubmitJob("followup", "run"),
                    61: SubmitJob("final", "run"),
                    62: SubmitJob("final", "run"),
                },
                confirm_from=37,
            ),
            "B": ObservedScript({29: ProposePlan(()), 40: Finish()}, confirm_from=37),
        },
    )
    assert result.metadata.submission_open_at == {"A": 44, "B": 40}
    assert _statuses(result, "A", SubmitJob) == [
        (43, ToolStatus.SUBMISSION_NOT_OPEN),
        (44, ToolStatus.ACCEPTED),
        (52, ToolStatus.PREREQUISITE_NOT_COMPLETED),
        (53, ToolStatus.ACCEPTED),
        (61, ToolStatus.PREREQUISITE_NOT_COMPLETED),
        (62, ToolStatus.ACCEPTED),
    ]
    assert [(e.job_id, e.time) for e in _events(result, "complete")] == [
        ("job_a", 53),
        ("followup", 62),
        ("final", 71),
    ]
    assert result.metadata.horizon == 80
    assert all(result.job_statuses[job] is JobStatus.COMPLETED for job, _ in chained)
    report = audit_episode(result.metadata, result.log)
    assert report.agreement == "agreed"
    assert report.consistent, report.issues


@pytest.mark.parametrize("one_confirmed", [False, True])
def test_t20_missing_confirmation_keeps_atomic_fallback(one_confirmed: bool) -> None:
    result = run_episode(
        _scenario(commit_delay=3),
        RunConfig.for_protocol("A/VBC"),
        {
            "A": ObservedScript(
                {29: REVISED_A, 40: SubmitJob(*A_FULL)}, confirm_from=37 if one_confirmed else None
            ),
            "B": ScriptedPolicy({29: PLAN_B, 40: SubmitJob(*B_STANDARD)}),
        },
    )

    _assert_fallback(result)
    assert _statuses(result, "A", ConfirmPlan) == ([(37, ToolStatus.OK)] if one_confirmed else [])
    assert not _statuses(result, "B", ConfirmPlan)
    assert _statuses(result, "A", SubmitJob) == [(40, ToolStatus.ACCEPTED)]
    assert _statuses(result, "B", SubmitJob) == [(40, ToolStatus.INSUFFICIENT_BUDGET)]
    assert max(e.spent_after + e.held_after for e in result.log) == 7
    assert (result.spent, result.held) == (7, 0)


def test_vbc_grid_and_full_script_fit_turn_limit() -> None:
    policies = {}
    for agent, peer, proposal, item in [
        ("A", "B", PLAN_A, A_SHORT),
        ("B", "A", PLAN_B, B_STANDARD),
    ]:
        steps = {
            0: ListJobs(),
            1: GetBalance(),
            **{time: SendMessage(peer, f"{agent}-{time}") for time in (6, 13, 20)},
            29: proposal,
            30: GetBalance(),
            33: REVISED_A if agent == "A" else PLAN_B,
            34: GetStatus(),
            35: GetBalance(),
            40: SubmitJob(*item),
            44: GetStatus(),
            45: Finish(),
        }
        policies[agent] = ObservedScript(steps, confirm_from=37)

    result = run_episode(
        _scenario(message_delay=8, commit_delay=3), RunConfig.for_protocol("A/VBC"), policies
    )

    assert result.metadata.horizon == 80
    assert result.metadata.agent_turn_limit == 24
    assert result.metadata.submission_open_at == {"A": 40, "B": 40}
    assert [e.time for e in _events(result, "message_delivered")] == [14, 14, 21, 21, 28, 28]
    assert [e.time for e in _events(result, "plan_version")] == [30, 34]
    assert [e.time for e in _events(result, "plan_feedback")] == [30, 35]
    assert not _events(result, "round_missed")

    for agent, peer in [("A", "B"), ("B", "A")]:
        assert _statuses(result, agent, SendMessage) == [
            (6, ToolStatus.OK),
            (13, ToolStatus.OK),
            (20, ToolStatus.OK),
        ]
        assert _statuses(result, agent, ProposePlan) == [(29, ToolStatus.OK), (33, ToolStatus.OK)]
        assert _statuses(result, agent, ConfirmPlan) == [(37, ToolStatus.OK)]
        assert _statuses(result, agent, SubmitJob) == [(40, ToolStatus.ACCEPTED)]

        script = policies[agent]
        observed = script.observations
        assert [m["text"] for m in observed[29].inbox] == [f"{peer}-20"]
        assert observed[29].plan_view is None
        initial = observed[30].plan_view
        revised = observed[34].plan_view
        final = observed[35].plan_view
        assert initial is not None and revised is not None and final is not None
        assert initial["plan_version"] != revised["plan_version"]
        assert revised["plan_version"] == final["plan_version"]
        assert initial["plan_feedback"]["overage"] == 1
        assert revised["proposals"]["A"]["items"][0]["option_id"] == "short"
        assert "plan_feedback" not in revised
        assert final["plan_feedback"]["requested_total"] == 10
        assert final["plan_feedback"]["overage"] == 0

        for observation in observed.values():
            _assert_no_value(asdict(observation))
        assert all(call.time in observed for call in result.calls_by(agent))
        assert script.decisions == result.turns_used[agent] == len(observed) <= 24
        assert isinstance(result.calls_by(agent)[-1].action, Finish)

    assert result.job_statuses == {"job_a": JobStatus.COMPLETED, "job_b": JobStatus.COMPLETED}
    assert audit_episode(result.metadata, result.log).agreement == "agreed"


def test_send_slots_close_and_skipped_rounds_are_logged() -> None:
    result = run_episode(
        _scenario(),
        RunConfig.for_protocol("A/R3P", start_gap=4),
        {
            "A": ScriptedPolicy({6: SendMessage("B", "sent"), 45: Finish()}),
            "B": ScriptedPolicy(
                {time: SendMessage("A", "probe") for time in (5, 6, 7, 13, 20, 39, 40, 44)}
            ),
        },
    )
    assert _statuses(result, "B", SendMessage) == [
        (5, ToolStatus.MESSAGING_ROUND_CLOSED),
        (6, ToolStatus.OK),
        (7, ToolStatus.MESSAGING_ROUND_CLOSED),
        (13, ToolStatus.OK),
        (20, ToolStatus.OK),
        (39, ToolStatus.MESSAGING_ROUND_CLOSED),
        (40, ToolStatus.MESSAGING_CLOSED),
        (44, ToolStatus.MESSAGING_CLOSED),
    ]
    assert [(e.agent_id, e.detail["round_time"]) for e in _events(result, "round_missed")] == [
        ("A", 13),
        ("A", 20),
    ]


@pytest.mark.parametrize(
    ("variant", "wake_at"), [("A/R1", 40), ("A/R3", 13), ("A/R3P", 13), ("A/F", 10)]
)
def test_wait_wakes_on_delivery_only_in_free_messaging(variant: str, wake_at: int) -> None:
    # The intentional round behavior follows the B1/B3 distinction in the tool table.
    receiver = ObservedScript({6: WaitUntil(40), 40: Finish()})
    if variant == "A/F":
        receiver.steps[10] = ReadMessages()
    result = run_episode(
        _scenario(message_delay=4),
        RunConfig.for_protocol(variant),
        {
            "A": ScriptedPolicy({6: SendMessage("B", "delivery probe"), 40: Finish()}),
            "B": receiver,
        },
    )
    assert [e.time for e in _events(result, "message_delivered")] == [10]
    assert min(time for time in receiver.observations if time > 6) == wake_at
    if variant == "A/F":
        call = next(call for call in result.calls_by("B") if call.time == wake_at)
        assert [m["text"] for m in call.result.data["messages"]] == ["delivery probe"]
    else:
        assert [m["text"] for m in receiver.observations[wake_at].inbox] == ["delivery probe"]


def test_plan_tools_return_wrong_phase_outside_slots() -> None:
    env = Environment(_scenario(), RunConfig.for_protocol("A/VBC"))
    for time, action in [
        (28, PLAN_A),
        (30, PLAN_A),
        (32, PLAN_A),
        (34, PLAN_A),
        (36, ConfirmPlan(2)),
        (38, ConfirmPlan(2)),
    ]:
        env.advance_to(time)
        assert env.execute("A", action).status is ToolStatus.WRONG_PHASE
        assert (env.spent, env.held) == (0, 0)
    view = env.plan_view()
    assert view is not None
    assert not view["proposals"]


@pytest.mark.parametrize("variant", ["A/R3P+S", "A/R3P+S+V"])
def test_g_off_confirmation_does_not_restrict_submit_job(variant: str) -> None:
    result = run_episode(
        _scenario(budget=13),
        RunConfig.for_protocol(variant),
        {
            "A": ObservedScript({29: REVISED_A, 40: SubmitJob(*A_FULL)}, confirm_from=37),
            "B": ObservedScript({29: PLAN_B, 40: SubmitJob(*B_STANDARD)}, confirm_from=37),
        },
    )
    assert _events(result, "agreement")[0].result == "agreed"
    for agent in ("A", "B"):
        assert _statuses(result, agent, ConfirmPlan) == [(37, ToolStatus.OK)]
        assert _statuses(result, agent, SubmitJob) == [(40, ToolStatus.ACCEPTED)]
    assert result.spent == 13


def test_audit_flags_an_accepted_option_outside_the_agreed_plan() -> None:
    # Equal catalog prices keep the forged request and all balance transitions coherent.
    result = run_episode(
        make_scenario(a_options=(("full", 7), ("same_cost", 7)), budget=13),
        RunConfig.for_protocol("A/VBC"),
        {
            "A": ObservedScript(
                {29: ProposePlan((A_FULL,)), 40: SubmitJob(*A_FULL)}, confirm_from=37
            ),
            "B": ObservedScript({29: PLAN_B, 40: SubmitJob(*B_STANDARD)}, confirm_from=37),
        },
    )
    clean = audit_episode(result.metadata, result.log)
    assert clean.consistent and clean.agreement == "agreed"
    tampered = [
        replace(e, option_id="same_cost") if e.job_id == "job_a" and e.request_id else e
        for e in result.log
    ]
    report = audit_episode(result.metadata, tampered)
    assert any("outside agreed plan" in issue for issue in report.issues)


def test_audit_flags_acceptance_before_prerequisite_completion() -> None:
    result = run_episode(
        _chain_scenario(),
        RunConfig.for_protocol("A/R3P"),
        {
            "A": ScriptedPolicy({40: SubmitJob(*A_SHORT), 49: SubmitJob("followup", "run")}),
            "B": ScriptedPolicy({40: Finish()}),
        },
    )
    clean = audit_episode(result.metadata, result.log)
    assert clean.consistent and clean.completed_jobs == ("followup", "job_a")
    early = next(e for e in result.log if e.event_type == "submit" and e.job_id == "followup")
    forged = [e for e in result.log if e.seq != early.seq]
    first_later_event = next(i for i, e in enumerate(forged) if e.time >= 49)
    forged.insert(first_later_event, replace(early, time=48))
    report = audit_episode(
        result.metadata, [replace(e, seq=i) for i, e in enumerate(forged, start=1)]
    )
    assert any("accepted before" in issue and "job_a" in issue for issue in report.issues)
