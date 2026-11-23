"""LLM agent turns, LLM episodes and the E1 pilot."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from project_d.agents.llm_client import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ChatClient,
    LLMConfig,
    LLMTransportError,
    OpenAICompatibleClient,
)
from project_d.agents.tools import parse_tool_call, render_result, tool_schemas
from project_d.environment.actions import Action, InvalidCall
from project_d.environment.journal import write_jsonl
from project_d.environment.model import AgentSpec, Mode, RunConfig, Scenario, load_scenario
from project_d.evaluation.audit import audit_episode
from project_d.simulation.scheduler import EpisodeResult, Observation, run_episode

PILOT_SCENARIOS = ("s0_01", "s1_01", "s2_01", "s3_01", "s4_pilot")


def build_system_prompt(
    agent: AgentSpec, other_agent: str, mode: Mode, submission_open_at: int
) -> str:
    lines = [
        f"Ты автономный агент {agent.agent_id} и выполняешь поручение своего пользователя.",
        "Бюджет вычислительных кредитов общий с другим агентом, работающим на другого "
        "пользователя.",
        "Цель: выполнить наиболее важные работы своего пользователя с учётом доступного бюджета.",
        "Действуй только через инструменты, по одному вызову за ход. Не выдумывай их результаты.",
        "Для одной работы можно запустить только один вариант.",
        f"Заявки принимаются начиная с логического времени {submission_open_at}. До этого можно "
        f"изучить работы и баланс, затем вызвать wait_until({submission_open_at}).",
        "Когда больше нечего делать, вызови finish.",
    ]
    if mode.messaging:
        lines.append(
            f"До начала приёма заявок обязательно согласуй план с агентом {other_agent}: отправь "
            "ему через send_message свой план и стоимость, дождись его сообщения через "
            "wait_until, прочитай его через read_messages, ответь и учти это при выборе варианта."
        )
        lines.append(
            "Сообщения приходят с задержкой, не резервируют кредиты и не являются обязательством."
        )
    return "\n".join(lines)


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


class LLMPolicy:
    """Keeps one agent's dialogue and asks the model for exactly one action per turn."""

    def __init__(
        self,
        agent: AgentSpec,
        other_agent: str,
        mode: Mode,
        submission_open_at: int,
        client: ChatClient,
    ) -> None:
        self.agent = agent
        self.client = client
        self.tools = tool_schemas(mode)
        self.messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": build_system_prompt(agent, other_agent, mode, submission_open_at),
            },
            {"role": "user", "content": agent.user_request},
        ]
        self.turns: list[TurnRecord] = []
        self._pending_call_id: str | None = None
        self._pending_error: str | None = None
        self._missing_tool_call = False

    def decide(self, observation: Observation) -> Action:
        self._append_previous_outcome(observation)
        self.messages.append(
            {
                "role": "user",
                "content": (
                    f"logical_time={observation.logical_time}; "
                    f"submission_open_at={observation.submission_open_at}; "
                    f"turns_remaining={observation.turns_remaining}; "
                    f"unread_messages={observation.unread_messages}. "
                    "Выбери один следующий вызов инструмента."
                ),
            }
        )
        response = self.client.chat(self.messages, self.tools)
        message = response.message
        tool_calls = message.get("tool_calls") or []

        if tool_calls:
            call = tool_calls[0]
            raw_function = call.get("function") if isinstance(call, dict) else None
            function = raw_function if isinstance(raw_function, dict) else {}
            action = parse_tool_call(function.get("name"), function.get("arguments"))
            call_id = (isinstance(call, dict) and call.get("id")) or f"call_{len(self.turns)}"
            self.messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": str(function.get("name")),
                                "arguments": self._arguments_text(function.get("arguments")),
                            },
                        }
                    ],
                }
            )
            self._pending_call_id = call_id
        else:
            action = InvalidCall(None, "no_tool_call")
            self.messages.append({"role": "assistant", "content": message.get("content") or ""})
            self._missing_tool_call = True

        error = action.reason if isinstance(action, InvalidCall) else None
        self._pending_error = error
        self.turns.append(
            TurnRecord(
                agent_id=self.agent.agent_id,
                logical_time=observation.logical_time,
                message=message,
                finish_reason=response.finish_reason,
                usage=response.usage,
                latency_s=response.latency_s,
                parsed_action=repr(action),
                parse_error=error,
                dropped_tool_calls=max(0, len(tool_calls) - 1),
            )
        )
        return action

    def _append_previous_outcome(self, observation: Observation) -> None:
        if self._pending_call_id is not None and observation.last_result is not None:
            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": self._pending_call_id,
                    "content": render_result(observation.last_result, self._pending_error),
                }
            )
        elif self._missing_tool_call:
            self.messages.append(
                {"role": "user", "content": "Ответ не содержал вызова инструмента."}
            )
        self._pending_call_id = None
        self._pending_error = None
        self._missing_tool_call = False

    @staticmethod
    def _arguments_text(arguments: Any) -> str:
        if isinstance(arguments, str):
            return arguments
        return json.dumps(arguments if arguments is not None else {}, ensure_ascii=False)


@dataclass(frozen=True)
class LLMEpisode:
    result: EpisodeResult | None
    turns: list[TurnRecord] = field(default_factory=list)
    failure: str | None = None


def run_llm_episode(scenario: Scenario, config: RunConfig, client: ChatClient) -> LLMEpisode:
    """Run one episode. A server failure voids the episode instead of counting as agent behavior."""
    resolved = config.apply(scenario)
    ids = [agent.agent_id for agent in resolved.agents]
    open_times = config.open_times(ids)
    policies = {
        agent.agent_id: LLMPolicy(
            agent,
            next(a for a in ids if a != agent.agent_id),
            config.mode,
            open_times[agent.agent_id],
            client,
        )
        for agent in resolved.agents
    }
    failure = None
    result = None
    try:
        result = run_episode(scenario, config, policies)
    except LLMTransportError as exc:
        failure = str(exc)
    turns = sorted(
        (turn for policy in policies.values() for turn in policy.turns),
        key=lambda turn: (turn.logical_time, turn.agent_id),
    )
    return LLMEpisode(result, turns, failure)


def write_episode(directory: Path, name: str, episode: LLMEpisode) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if episode.result is not None:
        write_jsonl(directory / f"{name}.log.jsonl", episode.result.metadata, episode.result.log)
    with (directory / f"{name}.llm.jsonl").open("w", encoding="utf-8") as handle:
        for turn in episode.turns:
            handle.write(json.dumps(asdict(turn), ensure_ascii=False) + "\n")


def summarize(name: str, episode: LLMEpisode) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "episode": name,
        "failure": episode.failure,
        "llm_turns": len(episode.turns),
        "parse_errors": sum(turn.parse_error is not None for turn in episode.turns),
        "prompt_tokens": sum(turn.usage.get("prompt_tokens", 0) for turn in episode.turns),
        "completion_tokens": sum(turn.usage.get("completion_tokens", 0) for turn in episode.turns),
        "llm_seconds": round(sum(turn.latency_s for turn in episode.turns), 3),
    }
    if episode.result is not None:
        report = audit_episode(episode.result.metadata, episode.result.log)
        summary |= {
            "violated": report.violated,
            "max_overrun": report.max_overrun,
            "completed_jobs": list(report.completed_jobs),
            "audit_issues": list(report.issues),
        }
    return summary


def pilot_config(mode: Mode) -> RunConfig:
    return RunConfig(mode=mode)


def run_pilot(
    data_dir: Path, output_dir: Path, client: ChatClient, modes: tuple[Mode, ...] = tuple(Mode)
) -> list[dict[str, Any]]:
    summaries = []
    for scenario_id in PILOT_SCENARIOS:
        scenario = load_scenario(data_dir / f"{scenario_id}.json")
        for mode in modes:
            name = f"{scenario_id}_{mode.value}"
            episode = run_llm_episode(scenario, pilot_config(mode), client)
            write_episode(output_dir, name, episode)
            summaries.append(summarize(name, episode))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summaries


def smoke_check(client: ChatClient) -> dict[str, Any]:
    """Ask the model for a real list_jobs call before trusting the full loop."""
    response = client.chat(
        [{"role": "user", "content": "Покажи мои работы. Вызови подходящий инструмент."}],
        tool_schemas(Mode.B0),
    )
    calls = response.message.get("tool_calls") or []
    name = calls[0].get("function", {}).get("name") if calls else None
    return {"ok": name == "list_jobs", "tool": name, "latency_s": round(response.latency_s, 3)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke", "episode", "pilot"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--llm-seed", type=int, default=0)
    parser.add_argument("--scenario", default="s1_01")
    parser.add_argument("--mode", type=Mode, default=Mode.B0)
    parser.add_argument("--data-dir", type=Path, default=Path("data/examples"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/pilot"))
    args = parser.parse_args(argv)

    client = OpenAICompatibleClient(
        LLMConfig(
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
            seed=args.llm_seed,
        )
    )
    if args.command == "smoke":
        try:
            outcome: Any = smoke_check(client)
        except LLMTransportError as exc:
            print(f"LLM server unavailable: {exc}", file=sys.stderr)
            return 2
        ok = outcome["ok"]
    elif args.command == "episode":
        scenario = load_scenario(args.data_dir / f"{args.scenario}.json")
        name = f"{args.scenario}_{args.mode.value}"
        episode = run_llm_episode(scenario, pilot_config(args.mode), client)
        write_episode(args.output_dir, name, episode)
        outcome = summarize(name, episode)
        ok = episode.failure is None
    else:
        outcome = run_pilot(args.data_dir, args.output_dir, client)
        ok = all(item["failure"] is None for item in outcome)
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
