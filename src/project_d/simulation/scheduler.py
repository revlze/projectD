"""Synchronous logical-time loop: agents decide together, then actions run in a fixed order."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from project_d.environment.actions import Action, Finish, ToolResult, WaitUntil
from project_d.environment.env import Environment
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import JobStatus, RunConfig, Scenario, ScenarioError


@dataclass(frozen=True)
class Observation:
    """Everything a policy learns at its turn. Hidden values never appear here."""

    agent_id: str
    logical_time: int
    submission_open_at: int
    turns_remaining: int
    unread_messages: int
    last_result: ToolResult | None


class Policy(Protocol):
    def decide(self, observation: Observation) -> Action: ...


class ScriptedPolicy:
    """Plays fixed actions at fixed times, waiting in between and finishing afterwards."""

    def __init__(self, steps: Mapping[int, Action] | None = None) -> None:
        self.steps = dict(steps or {})
        self.decisions = 0

    def decide(self, observation: Observation) -> Action:
        self.decisions += 1
        now = observation.logical_time
        if now in self.steps:
            return self.steps[now]
        upcoming = [time for time in self.steps if time > now]
        return WaitUntil(min(upcoming)) if upcoming else Finish()


@dataclass(frozen=True)
class ToolCall:
    time: int
    agent_id: str
    action: Action
    result: ToolResult


@dataclass(frozen=True)
class EpisodeResult:
    metadata: EpisodeMetadata
    log: list[LogEntry]
    calls: list[ToolCall]
    turns_used: dict[str, int]
    job_statuses: dict[str, JobStatus]
    spent: int
    held: int

    def calls_by(self, agent_id: str) -> list[ToolCall]:
        return [call for call in self.calls if call.agent_id == agent_id]


def run_episode(
    scenario: Scenario, config: RunConfig, policies: Mapping[str, Policy]
) -> EpisodeResult:
    env = Environment(scenario, config)
    missing = set(env.processing_order) - set(policies)
    if missing:
        raise ScenarioError(f"no policy for agents: {sorted(missing)}")

    limit = env.scenario.agent_turn_limit
    turns = dict.fromkeys(env.processing_order, 0)
    last_results: dict[str, ToolResult | None] = dict.fromkeys(env.processing_order)
    calls: list[ToolCall] = []

    # Actions stop before the horizon; the final pass only drains events due at the horizon.
    for time in range(env.scenario.horizon + 1):
        env.advance_to(time)
        if time == env.scenario.horizon:
            break

        ready = [a for a in env.processing_order if env.is_ready(a) and turns[a] < limit]
        decisions = {
            agent_id: policies[agent_id].decide(
                Observation(
                    agent_id=agent_id,
                    logical_time=time,
                    submission_open_at=env.submission_open_at[agent_id],
                    turns_remaining=limit - turns[agent_id],
                    unread_messages=env.unread_count(agent_id),
                    last_result=last_results[agent_id],
                )
            )
            for agent_id in ready
        }
        for agent_id in ready:
            result = env.execute(agent_id, decisions[agent_id])
            turns[agent_id] += 1
            last_results[agent_id] = result
            calls.append(ToolCall(time, agent_id, decisions[agent_id], result))

    return EpisodeResult(
        metadata=env.metadata,
        log=env.log,
        calls=calls,
        turns_used=turns,
        job_statuses={
            job.job_id: env.job_status(job.job_id)
            for agent in env.scenario.agents
            for job in agent.jobs
        },
        spent=env.spent,
        held=env.held,
    )
