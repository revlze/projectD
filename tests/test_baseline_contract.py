"""End-to-end baseline checks using the exact requests sent to a recording client."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import replace
from itertools import product

import pytest

from project_d.agents.llm_client import ChatResponse
from project_d.agents.prompts import BASE, BUDGET_CHECK_INSTRUCTION, build_protocol_prompt
from project_d.agents.runner import run_llm_episode
from project_d.agents.tools import tool_schemas
from project_d.environment.actions import (
    Finish,
    GetBalance,
    SkipRound,
    ToolStatus,
    WaitUntil,
)
from project_d.environment.env import Environment
from project_d.environment.model import RunConfig, Variant
from project_d.evaluation.audit import audit_episode
from project_d.experiments.matrix import BASELINE_VARIANTS, E1_VARIANTS
from project_d.simulation.scheduler import Observation, run_episode
from support import make_scenario


def response(name: str, arguments: dict | None = None) -> ChatResponse:
    return ChatResponse(
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call",
                    "function": {"name": name, "arguments": json.dumps(arguments or {})},
                }
            ],
        }
    )


class RecordingClient:
    def __init__(self, *, skip: bool = False, multiple: bool = False) -> None:
        self.requests: list[dict] = []
        self.skip = skip
        self.multiple = multiple

    def chat(self, messages, tools) -> ChatResponse:
        self.requests.append(deepcopy({"messages": messages, "tools": tools}))
        note = messages[-1]["content"]
        now = int(re.search(r"logical_time=(\d+)", note).group(1))
        opens = int(re.search(r"submission_open_at=(\d+)", note).group(1))
        phase = re.search(r"phase=([a-z_]+)", note).group(1)
        agent = "A" if "агент A и" in messages[0]["content"] else "B"
        peer = "B" if agent == "A" else "A"
        results = [json.loads(item["content"]) for item in messages if item["role"] == "tool"]
        jobs = next((item["jobs"] for item in results if "jobs" in item), None)
        if phase == "message_round":
            if self.skip:
                return response("skip_round")
            return response("send_message", {"agent_id": peer, "text": f"intent-{agent}-{now}"})
        if jobs is None:
            return response("list_jobs")
        if not any("shared_budget" in item for item in results):
            return response("get_balance")
        option = min(jobs[0]["options"], key=lambda item: item["cost"])
        pair = {"job_id": jobs[0]["job_id"], "option_id": option["option_id"]}
        if phase == "propose":
            return response("propose_plan", {"items": [pair]})
        if phase == "confirm":
            if "подтверждение недоступно" in note:
                return response("wait_until", {"target_time": 40})
            return response("confirm_plan", {"plan_version": 2})
        if now < opens:
            if any(tool["function"]["name"] == "send_message" for tool in tools) and now == 2:
                return response("send_message", {"agent_id": peer, "text": f"intent-{agent}-free"})
            if (
                "read_messages" in {tool["function"]["name"] for tool in tools}
                and "unread_messages=1" in note
            ):
                return response("read_messages")
            return response("wait_until", {"target_time": 80})
        if self.multiple and now == opens:
            first = response("submit_job", {"job_id": jobs[0]["job_id"], "option_id": "full"})
            first.message["tool_calls"].append(response("finish").message["tool_calls"][0])
            return first
        if any(item["status"] == "accepted" for item in results):
            return response("finish")
        return response("submit_job", pair)


@pytest.mark.parametrize("variant", E1_VARIANTS)
@pytest.mark.parametrize("delay", (1, 4, 8))
@pytest.mark.parametrize("first,swap", tuple(product(("A", "B"), (False, True))))
def test_phases_requests_privacy_and_execution(variant, delay, first, swap) -> None:
    scenario = make_scenario(
        a_options=(("full", 7), ("short", 4)), horizon=80, turn_limit=24, message_delay=delay
    )
    scenario = replace(
        scenario,
        agents=tuple(
            replace(
                agent,
                jobs=tuple(
                    replace(
                        job,
                        options=tuple(replace(option, value=90001234) for option in job.options),
                    )
                    for job in agent.jobs
                ),
            )
            for agent in scenario.agents
        ),
    )
    config = RunConfig.for_protocol(variant, first_agent=first, role_swap=swap, start_gap=4)
    client = RecordingClient()
    episode = run_llm_episode(scenario, config, client)
    result = episode.result
    assert episode.failure is None
    assert result.spent == 10 and result.held == 0
    assert audit_episode(result.metadata, result.log, require_complete=True).consistent
    requests = {
        (request["messages"][0]["content"], request["messages"][-1]["content"]): request
        for request in client.requests
    }
    for turn in episode.turns:
        assert (
            turn.request
            == requests[
                turn.request["messages"][0]["content"], turn.request["messages"][-1]["content"]
            ]
        )
        payload = json.dumps(turn.request, ensure_ascii=False)
        assert "90001234" not in payload
        other = next(
            agent for agent in config.apply(scenario).agents if agent.agent_id != turn.agent_id
        )
        assert other.user_request not in payload
        assert turn.tool_result is not None
        latest = turn.request["messages"][-1]["content"]
        names = {tool["function"]["name"] for tool in turn.request["tools"]}
        if turn.logical_time in config.variant.round_times:
            assert names == {"send_message", "skip_round"}
        if turn.logical_time == 0:
            assert (
                '"options"' not in latest and '"cost"' not in latest and '"requires"' not in latest
            )
            assert other.jobs[0].job_id not in latest
            assert "submit_job" not in names and "finish" not in names
        if turn.logical_time >= config.submission_open_at:
            assert "Фактические состояния" in latest
        if turn.logical_time == config.submission_open_at:
            own_open = config.open_times(("A", "B"))[turn.agent_id]
            if own_open == config.submission_open_at:
                assert "Началось окно исполнения" in latest
            else:
                # A lagging agent is not told that its own window has begun (start_gap > 0).
                assert "Началось окно исполнения" not in latest
                assert f"твоя подача откроется только в t={own_open}" in latest
    for agent in ("A", "B"):
        times = [turn.logical_time for turn in episode.turns if turn.agent_id == agent]
        assert 40 in times
        assert config.open_times(("A", "B"))[agent] in times
        assert sum(time < 40 for time in times) <= 12
        assert sum(time >= 40 for time in times) <= 12
        if config.variant.slot_times:
            assert [time for time in times if 6 <= time < 40] == list(config.variant.slot_times)
    if config.variant.round_times:
        for sent in config.variant.round_times:
            for turn in episode.turns:
                if turn.logical_time < sent:
                    continue
                peer = "B" if turn.agent_id == "A" else "A"
                text = f"intent-{peer}-{sent}"
                payload = json.dumps(turn.request, ensure_ascii=False)
                if turn.logical_time < sent + delay:
                    assert text not in payload
                elif turn.logical_time >= sent + delay:
                    assert text in payload
    if config.variant.structured:
        assert next(row for row in result.log if row.event_type == "agreement").result == "agreed"


@pytest.mark.parametrize("variant", ("A/S", "A/VBC"))
def test_incomplete_plan_notice_appears_in_the_actual_request(variant) -> None:
    class MissingProposal(RecordingClient):
        def chat(self, messages, tools):
            reply = super().chat(messages, tools)
            if (
                "агент B и" in messages[0]["content"]
                and "phase=propose;" in messages[-1]["content"]
            ):
                return response("wait_until", {"target_time": 40})
            return reply

    episode = run_llm_episode(make_scenario(), RunConfig.for_protocol(variant), MissingProposal())
    for turn in (turn for turn in episode.turns if turn.logical_time == 37):
        assert (
            "Совместный план неполный; подтверждение недоступно"
            in (turn.request["messages"][-1]["content"])
        )
    result = episode.result
    assert (
        next(row for row in result.log if row.event_type == "agreement").result
        == "agreement_failed"
    )
    assert any(row.event_type == "submit" and row.result == "accepted" for row in result.log)


def test_explicit_skip_and_automatic_wait_still_allow_execution() -> None:
    client = RecordingClient(skip=True)
    episode = run_llm_episode(make_scenario(), RunConfig.for_protocol("A/R3"), client)
    assert sum(row.event_type == "round_skipped" for row in episode.result.log) == 6
    assert not any(row.event_type in ("send_message", "round_missed") for row in episode.result.log)
    assert any(
        row.event_type == "submit" and row.result == "accepted" for row in episode.result.log
    )


def test_multiple_calls_execute_nothing_and_all_receive_real_error_responses() -> None:
    episode = run_llm_episode(
        make_scenario(), RunConfig.for_protocol("A/N"), RecordingClient(multiple=True)
    )
    assert episode.failure is None
    at_open = [turn for turn in episode.turns if turn.logical_time == 40]
    assert all(turn.parse_error == "multiple_tool_calls" for turn in at_open)
    assert all(turn.tool_result["status"] == "invalid_action" for turn in at_open)
    assert not any(row.event_type == "submit" and row.time == 40 for row in episode.result.log)
    for turn in [item for item in episode.turns if item.logical_time == 41]:
        replies = [json.loads(item["content"]) for item in turn.request["messages"][-3:-1]]
        assert len(replies) == 2
        assert all(
            item["status"] == "invalid_action" and item["error"] == "multiple_tool_calls"
            for item in replies
        )


@pytest.mark.parametrize("variant", BASELINE_VARIANTS)
def test_early_finish_is_rejected_without_ending_participation(variant) -> None:
    env = Environment(
        make_scenario(), RunConfig.for_protocol(variant, first_agent="B", start_gap=4)
    )
    for time in (0, 40, 43):
        env.advance_to(time)
        assert env.execute("A", Finish()).status == ToolStatus.FINISH_NOT_OPEN
        assert env.is_ready("A")
    env.advance_to(44)
    assert env.execute("A", Finish()).status == ToolStatus.OK
    assert not env.is_ready("A")


@pytest.mark.parametrize("variant", BASELINE_VARIANTS)
def test_preparation_limit_preserves_rounds_and_twelve_execution_decisions(variant) -> None:
    class BusyPolicy:
        def decide(self, observation: Observation):
            return SkipRound() if observation.phase == "message_round" else GetBalance()

    result = run_episode(
        make_scenario(), RunConfig.for_protocol(variant), {"A": BusyPolicy(), "B": BusyPolicy()}
    )
    for agent in ("A", "B"):
        calls = result.calls_by(agent)
        assert sum(call.time < 40 for call in calls) <= 12
        assert sum(call.time >= 40 for call in calls) == 12
        assert [call.time for call in calls if isinstance(call.action, SkipRound)] == list(
            Variant.parse(variant).round_times
        )


def test_round_instructions_are_identical_and_budget_instruction_is_only_r3p() -> None:
    agent = make_scenario().agents[0]
    r1 = build_protocol_prompt(agent, "B", Variant.parse("A/R1"), 40)
    assert r1 == build_protocol_prompt(agent, "B", Variant.parse("A/R3"), 40)
    assert (
        build_protocol_prompt(agent, "B", Variant.parse("A/R3P"), 40)
        == r1 + "\n" + BUDGET_CHECK_INSTRUCTION
    )
    assert "только своего" not in BASE


def test_failed_round_call_cannot_execute_a_catalog_read() -> None:
    env = Environment(make_scenario(), RunConfig.for_protocol("A/R3"))
    env.advance_to(6)
    assert env.execute("A", GetBalance()).status == ToolStatus.WRONG_PHASE
    assert env.execute("A", WaitUntil(40)).status == ToolStatus.WRONG_PHASE
    assert (
        tool_schemas(Variant.parse("A/R3"), "message_round")[1]["function"]["name"] == "skip_round"
    )


def test_response_without_a_call_is_an_agent_error_and_execution_can_continue() -> None:
    class ChattyClient(RecordingClient):
        def chat(self, messages, tools):
            reply = super().chat(messages, tools)
            if "logical_time=40;" in messages[-1]["content"]:
                return ChatResponse({"role": "assistant", "content": "I have a plan."})
            return reply

    episode = run_llm_episode(make_scenario(), RunConfig.for_protocol("A/N"), ChattyClient())
    assert episode.failure is None
    for turn in episode.turns:
        if turn.logical_time == 40:
            assert turn.parse_error == "no_tool_call"
            assert turn.tool_result["status"] == "invalid_action"
        elif turn.logical_time == 41:
            assert "no_tool_call" in json.dumps(turn.request)
    assert any(
        entry.event_type == "submit" and entry.result == "accepted" for entry in episode.result.log
    )


def test_delivery_after_opening_does_not_interrupt_free_form_wait() -> None:
    from project_d.environment.actions import SendMessage

    scenario = make_scenario(message_delay=50)
    env = Environment(scenario, RunConfig.for_protocol("A/F"))
    env.execute("A", SendMessage("B", "late"))
    env.execute("B", WaitUntil(80))
    env.advance_to(40)
    assert env.is_ready("B")
    env.execute("B", WaitUntil(80))
    env.advance_to(50)
    assert not env.is_ready("B")
    assert env.unread_count("B") == 1
