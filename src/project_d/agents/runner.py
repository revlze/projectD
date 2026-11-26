"""Agent dialogue, exact request records and episode artifacts."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from project_d.agents.llm_client import ChatClient, LLMTransportError
from project_d.agents.plan_text import render_plan
from project_d.agents.prompts import (
    PROMPT_VERSION,
    build_protocol_prompt,
    prompt_sha256,
    protocol_note,
)
from project_d.agents.tools import parse_tool_call, render_result, tool_schemas
from project_d.environment.actions import Action, InvalidCall
from project_d.environment.journal import write_jsonl
from project_d.environment.model import AgentSpec, Comm, RunConfig, Scenario, Variant
from project_d.simulation.scheduler import (
    EpisodeInterrupted,
    EpisodeResult,
    Observation,
    run_episode,
)


@dataclass(frozen=True)
class TurnRecord:
    agent_id: str
    logical_time: int
    message: dict[str, Any]
    finish_reason: str | None
    usage: dict[str, Any]
    latency_s: float
    parsed_action: str
    parse_error: str | None
    dropped_tool_calls: int
    shown_plan: dict[str, Any] | None = None
    request: dict[str, Any] = field(default_factory=dict)
    request_sha256: str = ""
    tool_result: dict[str, Any] | None = None
    transport_error: str | None = None
    http: dict[str, Any] | None = None


class LLMPolicy:
    """Keep one private dialogue and execute at most one valid call per response."""

    def __init__(
        self,
        agent: AgentSpec,
        other_agent: str,
        mode: Variant,
        submission_open_at: int,
        client: ChatClient,
    ) -> None:
        self.agent = agent
        self.client = client
        self.mode = mode
        self.other_agent = other_agent
        self.system_prompt = build_protocol_prompt(agent, other_agent, mode, submission_open_at)
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": agent.user_request},
        ]
        self.turns: list[TurnRecord] = []
        self._pending_ids: list[str] = []
        self._pending_error: str | None = None
        self._missing_call = False
        self._shown_version: int | None = None

    def _new_plan(self, view: dict[str, Any] | None) -> tuple[str | None, dict[str, Any] | None]:
        """Render a plan version once, on the first decision after it is published."""
        if view is None or view["plan_version"] == self._shown_version:
            return None, None
        self._shown_version = view["plan_version"]
        text = render_plan(view, self.agent.agent_id, self.other_agent)
        feedback = view.get("plan_feedback")
        shown = {
            "plan_version": view["plan_version"],
            "feedback_shown": feedback is not None,
            # An incomplete plan is rendered without an overage, so it is not a warning.
            "overage": feedback["overage"]
            if feedback and feedback["status"] != "INCOMPLETE"
            else None,
            "status": feedback["status"] if feedback else None,
            "text_sha256": prompt_sha256(text),
        }
        return text, shown

    def decide(self, observation: Observation) -> Action:
        self._append_previous_outcome(observation)
        phase = observation.phase or (
            "execution"
            if observation.logical_time >= observation.submission_open_at
            else "preparation"
        )
        plan_text, shown_plan = self._new_plan(observation.plan_view)
        note = protocol_note(
            phase, observation.inbox, observation.plan_view, self.other_agent, plan_text
        )
        if phase in ("execution", "execution_wait") and observation.phase_started:
            if observation.logical_time >= observation.submission_open_at:
                note += (
                    "Началось окно исполнения. Показаны фактические статусы собственных работ.\n"
                )
            else:
                # Only with start_gap > 0 (E4-H1): the other agent may already submit.
                note += (
                    "Подготовка закончилась, но твоя подача откроется только в "
                    f"t={observation.submission_open_at}. Показаны фактические статусы "
                    "собственных работ.\n"
                )
        for notice in observation.protocol_notices:
            note += f"{notice}\n"
        window = (
            "открыта" if observation.logical_time >= observation.submission_open_at else "закрыта"
        )
        states = json.dumps(observation.own_jobs, ensure_ascii=False)
        self.messages.append(
            {
                "role": "user",
                "content": (
                    f"logical_time={observation.logical_time}; "
                    f"submission_open_at={observation.submission_open_at}; "
                    f"phase={phase}; horizon={observation.horizon}; "
                    f"turns_remaining={observation.turns_remaining}; "
                    f"preparation_remaining={observation.preparation_turns_remaining}; "
                    f"execution_remaining={observation.execution_turns_remaining}; "
                    f"unread_messages={observation.unread_messages}.\n"
                    f"Твоя подача: {window}. Фактические состояния своих работ: {states}.\n"
                    f"{note}Выбери один доступный вызов инструмента."
                ),
            }
        )
        tools = tool_schemas(self.mode, phase)
        request = deepcopy({"messages": self.messages, "tools": tools})
        digest = prompt_sha256(json.dumps(request, ensure_ascii=False, sort_keys=True))
        try:
            response = self.client.chat(deepcopy(self.messages), deepcopy(tools))
        except LLMTransportError as exc:
            self.turns.append(
                TurnRecord(
                    self.agent.agent_id,
                    observation.logical_time,
                    {},
                    None,
                    {},
                    0.0,
                    "",
                    None,
                    0,
                    shown_plan=shown_plan,
                    request=request,
                    request_sha256=digest,
                    transport_error=str(exc),
                    http=asdict(exc.trace) if exc.trace is not None else None,
                )
            )
            raise
        message = deepcopy(response.message)
        raw_calls = message.get("tool_calls") or []
        calls = raw_calls if isinstance(raw_calls, list) else []
        if len(calls) == 1 and isinstance(calls[0], dict):
            function = calls[0].get("function")
            function = function if isinstance(function, dict) else {}
            action = parse_tool_call(function.get("name"), function.get("arguments"))
        elif len(calls) > 1:
            action = InvalidCall(None, "multiple_tool_calls")
        else:
            action = InvalidCall(None, "no_tool_call")
        self._pending_error = action.reason if isinstance(action, InvalidCall) else None
        normalized = []
        for index, call in enumerate(calls):
            call = call if isinstance(call, dict) else {}
            function = call.get("function")
            function = function if isinstance(function, dict) else {}
            call_id = f"call_{len(self.turns)}_{index}"
            arguments = function.get("arguments")
            normalized.append(
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": str(function.get("name", "invalid")),
                        "arguments": arguments
                        if isinstance(arguments, str)
                        else json.dumps(arguments or {}),
                    },
                }
            )
            self._pending_ids.append(call_id)
        history_message = {"role": "assistant", "content": message.get("content") or ""}
        if normalized:
            history_message["tool_calls"] = normalized
        else:
            self._missing_call = True
        self.messages.append(history_message)
        self.turns.append(
            TurnRecord(
                self.agent.agent_id,
                observation.logical_time,
                message,
                response.finish_reason,
                deepcopy(response.usage),
                response.latency_s,
                repr(action),
                self._pending_error,
                0,
                shown_plan=shown_plan,
                request=request,
                request_sha256=digest,
                http=asdict(response.http) if response.http is not None else None,
            )
        )
        return action

    def _append_previous_outcome(self, observation: Observation) -> None:
        if observation.last_result is not None:
            content = render_result(observation.last_result, self._pending_error)
            for call_id in self._pending_ids:
                self.messages.append({"role": "tool", "tool_call_id": call_id, "content": content})
            if self._missing_call:
                self.messages.append({"role": "user", "content": content})
        self._pending_ids = []
        self._pending_error = None
        self._missing_call = False


@dataclass(frozen=True)
class LLMEpisode:
    result: EpisodeResult | None
    turns: list[TurnRecord] = field(default_factory=list)
    failure: str | None = None
    prompts: dict[str, Any] = field(default_factory=dict)
    failure_kind: str | None = None


def run_llm_episode(scenario: Scenario, config: RunConfig, client: ChatClient) -> LLMEpisode:
    resolved = config.apply(scenario)
    ids = [agent.agent_id for agent in resolved.agents]
    opens = config.open_times(ids)
    policies = {
        agent.agent_id: LLMPolicy(
            agent,
            next(other for other in ids if other != agent.agent_id),
            config.variant,
            opens[agent.agent_id],
            client,
        )
        for agent in resolved.agents
    }
    failure, failure_kind, result = None, None, None
    try:
        result = run_episode(scenario, config, policies)
    except EpisodeInterrupted as exc:
        failure, result = str(exc.cause), exc.result
        failure_kind = "transport" if isinstance(exc.cause, LLMTransportError) else "environment"
    turns = sorted(
        (turn for policy in policies.values() for turn in policy.turns),
        key=lambda turn: (turn.logical_time, turn.agent_id),
    )
    if result is not None:
        outcomes = {(call.agent_id, call.time): asdict(call.result) for call in result.calls}
        turns = [
            replace(turn, tool_result=outcomes.get((turn.agent_id, turn.logical_time)))
            for turn in turns
        ]
    prompts = {
        "version": PROMPT_VERSION,
        "system_sha256": {
            agent: prompt_sha256(policy.system_prompt) for agent, policy in policies.items()
        },
    }
    return LLMEpisode(result, turns, failure, prompts, failure_kind)


def write_episode(directory: Path, name: str, episode: LLMEpisode) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if episode.result is not None:
        write_jsonl(directory / f"{name}.log.jsonl", episode.result.metadata, episode.result.log)
    payloads = {
        "llm.jsonl": "".join(
            json.dumps(asdict(turn), ensure_ascii=False) + "\n" for turn in episode.turns
        ),
        "prompts.json": json.dumps(episode.prompts, ensure_ascii=False, indent=2) + "\n",
    }
    for suffix, content in payloads.items():
        target = directory / f"{name}.{suffix}"
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        temporary.replace(target)


def smoke_check(client: ChatClient) -> dict[str, Any]:
    response = client.chat(
        [{"role": "user", "content": "Покажи мои работы. Вызови list_jobs."}],
        tool_schemas(Variant("U", Comm.N), "preparation"),
    )
    calls = response.message.get("tool_calls") or []
    name = calls[0].get("function", {}).get("name") if len(calls) == 1 else None
    return {"ok": name == "list_jobs", "tool": name, "latency_s": round(response.latency_s, 3)}
