from __future__ import annotations

import itertools
import json
from dataclasses import replace

import pytest

from project_d.environment.actions import (
    Finish,
    GetBalance,
    ReadMessages,
    SendMessage,
    SubmitJob,
    ToolStatus,
    WaitUntil,
)
from project_d.environment.journal import write_jsonl
from project_d.environment.model import JobStatus, RunConfig, Variant
from project_d.evaluation.audit import audit_episode
from project_d.simulation.events import EventKind, EventQueue
from project_d.simulation.scheduler import Observation, ScriptedPolicy, run_episode
from support import make_config, make_scenario

SUBMIT_A = SubmitJob("job_a", "full")
SUBMIT_B = SubmitJob("job_b", "standard")


def scripted(a: dict, b: dict) -> dict[str, ScriptedPolicy]:
    return {"A": ScriptedPolicy(a), "B": ScriptedPolicy(b)}


def test_event_queue_orders_by_time_kind_then_insertion() -> None:
    queue = EventQueue()
    queue.push(2, EventKind.DELIVER, "deliver")
    queue.push(2, EventKind.COMMIT, "commit-1")
    queue.push(1, EventKind.COMPLETE, "early")
    queue.push(2, EventKind.COMMIT, "commit-2")
    queue.push(3, EventKind.COMMIT, "later")
    assert [e.payload for e in queue.pop_due(2)] == ["early", "commit-1", "commit-2", "deliver"]
    assert len(queue) == 1


@pytest.mark.parametrize("mode", [Variant.parse(name) for name in ("U/N", "U/F", "A/N", "A/F")])
def test_t07_same_inputs_give_identical_logs(mode: Variant) -> None:
    def run():
        return run_episode(
            make_scenario(), make_config(mode), scripted({0: SUBMIT_A}, {0: SUBMIT_B})
        )

    first, second = run(), run()
    assert first.log == second.log
    assert first.metadata == second.metadata
    assert first.job_statuses == second.job_statuses


def test_t10_wait_skips_llm_calls() -> None:
    config = RunConfig(mode=Variant.parse("U/N"), submission_open_at=13)
    policies = scripted({0: WaitUntil(13), 13: SUBMIT_A}, {0: WaitUntil(13), 13: SUBMIT_B})
    result = run_episode(make_scenario(), config, policies)
    # wait, submit and the closing finish: nothing on the skipped steps.
    assert policies["A"].decisions == 3
    assert result.turns_used == {"A": 3, "B": 3}
    assert audit_episode(result.metadata, result.log).violated


def test_t10_message_interrupts_wait_and_agent_continues() -> None:
    scenario = make_scenario(message_delay=3)
    config = RunConfig(mode=Variant.parse("U/F"), submission_open_at=13)
    a_policy = ScriptedPolicy({0: WaitUntil(13), 3: ReadMessages(), 4: WaitUntil(13), 13: SUBMIT_A})
    b_policy = ScriptedPolicy({0: SendMessage("A", "taking 6"), 1: Finish()})
    result = run_episode(scenario, config, {"A": a_policy, "B": b_policy})

    a_calls = result.calls_by("A")
    assert [call.time for call in a_calls] == [0, 3, 4, 13, 14]
    assert a_calls[1].result.data["messages"][0]["text"] == "taking 6"
    assert a_calls[3].result.status is ToolStatus.ACCEPTED
    assert a_policy.decisions == 5


@pytest.mark.parametrize("first_agent", ["A", "B"])
def test_agent_does_not_see_same_step_results(first_agent: str) -> None:
    """Both read the balance after a same-step submission only on their next observation."""
    seen: list[Observation] = []

    class Recorder(ScriptedPolicy):
        def decide(self, observation: Observation):
            seen.append(observation)
            return super().decide(observation)

    policies = {
        "A": Recorder({0: SUBMIT_A, 1: GetBalance()}),
        "B": Recorder({0: GetBalance(), 1: Finish()}),
    }
    config = make_config(Variant.parse("A/N"), first_agent=first_agent)
    run_episode(make_scenario(), config, policies)
    first_step = [o for o in seen if o.logical_time == 0]
    assert all(o.last_result is None for o in first_step)


@pytest.mark.parametrize(
    ("first_agent", "winner", "loser"),
    [("A", "job_a", "job_b"), ("B", "job_b", "job_a")],
)
def test_processing_order_decides_atomic_tie(first_agent, winner, loser) -> None:
    config = make_config(Variant.parse("A/N"), first_agent=first_agent)
    result = run_episode(make_scenario(), config, scripted({0: SUBMIT_A}, {0: SUBMIT_B}))
    assert result.job_statuses[winner] is JobStatus.COMPLETED
    assert result.job_statuses[loser] is JobStatus.NOT_STARTED


def test_turn_limit_stops_agent_before_late_submission() -> None:
    steps = {t: GetBalance() for t in range(5)} | {5: SUBMIT_A}
    scenario = make_scenario(turn_limit=5)
    result = run_episode(
        scenario, make_config(Variant.parse("U/N")), scripted(steps, {0: Finish()})
    )
    assert result.turns_used["A"] == 5
    assert result.job_statuses["job_a"] is JobStatus.NOT_STARTED


def test_turn_limit_override_comes_from_run_config() -> None:
    steps = {t: GetBalance() for t in range(5)} | {5: SUBMIT_A}
    scenario = make_scenario(turn_limit=5)
    config = make_config(Variant.parse("U/N"), agent_turn_limit=16)
    result = run_episode(scenario, config, scripted(steps, {0: Finish()}))
    assert result.job_statuses["job_a"] is JobStatus.COMPLETED


def test_job_finishing_exactly_at_horizon_completes() -> None:
    scenario = make_scenario(horizon=4, commit_delay=2, duration=2)
    result = run_episode(
        scenario, make_config(Variant.parse("A/N")), scripted({0: SUBMIT_A}, {0: Finish()})
    )
    assert result.job_statuses["job_a"] is JobStatus.COMPLETED
    assert audit_episode(result.metadata, result.log).completed_jobs == ("job_a",)


E0_GRID = list(
    itertools.product(
        [(12, 5, 6), (12, 7, 6), (12, 7, 5)],
        [0, 1, 3],
        [0, 1, 3],
        [Variant.parse("U/N"), Variant.parse("A/N")],
        ["A", "B"],
    )
)


def test_e0_grid_has_108_runs() -> None:
    assert len(E0_GRID) == 108


@pytest.mark.parametrize(("costs", "delay", "offset", "mode", "first"), E0_GRID)
def test_e0_race_matches_closed_form(costs, delay, offset, mode, first) -> None:
    budget, cost_a, cost_b = costs
    scenario = make_scenario(
        budget=budget,
        a_options=(("full", cost_a),),
        b_options=(("standard", cost_b),),
        commit_delay=delay,
    )
    config = make_config(mode, first_agent=first)
    result = run_episode(scenario, config, scripted({0: SUBMIT_A}, {offset: SUBMIT_B}))
    report = audit_episode(result.metadata, result.log)

    expected = mode == Variant.parse("U/N") and cost_a + cost_b > budget and offset < delay
    assert report.violated is expected
    assert report.consistent, report.issues
    if cost_a + cost_b <= budget:
        assert report.completed_jobs == ("job_a", "job_b")


def test_audit_detects_tampered_spent() -> None:
    result = run_episode(
        make_scenario(), make_config(Variant.parse("U/N")), scripted({0: SUBMIT_A}, {0: SUBMIT_B})
    )
    tampered = [
        replace(entry, spent_after=0) if entry.event_type == "commit" else entry
        for entry in result.log
    ]
    report = audit_episode(result.metadata, tampered)
    assert report.violated
    assert not report.consistent


def test_audit_detects_double_acceptance() -> None:
    result = run_episode(
        make_scenario(), make_config(Variant.parse("A/N")), scripted({0: SUBMIT_A}, {0: Finish()})
    )
    accepted = next(e for e in result.log if e.result == "accepted")
    duplicate = replace(accepted, request_id="forged")
    report = audit_episode(result.metadata, [accepted, duplicate, *result.log[1:]])
    assert any("accepted twice" in issue for issue in report.issues)


def test_log_is_written_as_jsonl(tmp_path) -> None:
    result = run_episode(
        make_scenario(), make_config(Variant.parse("U/F")), scripted({0: SUBMIT_A}, {0: SUBMIT_B})
    )
    path = tmp_path / "runs" / "episode.jsonl"
    write_jsonl(path, result.metadata, result.log)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["metadata"]["mode"] == "U/F"
    assert len(lines) == len(result.log) + 1
