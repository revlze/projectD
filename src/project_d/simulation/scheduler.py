"""Synchronous logical-time loop: agents decide together, then actions run in a fixed order."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from project_d.environment.actions import Action, Finish, SkipRound, ToolResult, WaitUntil
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
    own_jobs: tuple[dict[str, Any], ...] = ()
    phase: str | None = None
    inbox: tuple[dict[str, Any], ...] = ()
    plan_view: dict[str, Any] | None = None
    preparation_turns_remaining: int = 0
    execution_turns_remaining: int = 0
    phase_started: bool = False
    horizon: int = 80
    protocol_notices: tuple[str, ...] = ()


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
        if observation.phase == "message_round":
            return SkipRound()
        upcoming = [time for time in self.steps if time > now]
        if upcoming:
            return WaitUntil(min(upcoming))
        if now < observation.submission_open_at:
            return WaitUntil(observation.submission_open_at)
        return Finish()


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


class EpisodeInterrupted(RuntimeError):
    """A policy failed; retain operations and decisions already performed."""

    def __init__(self, result: EpisodeResult, cause: Exception) -> None:
        super().__init__(str(cause))
        self.result = result
        self.cause = cause


def run_episode(
    scenario: Scenario, config: RunConfig, policies: Mapping[str, Policy]
) -> EpisodeResult:
    env = Environment(scenario, config)
    missing = set(env.processing_order) - set(policies)
    if missing:
        raise ScenarioError(f"no policy for agents: {sorted(missing)}")

    total_limit = env.scenario.agent_turn_limit
    execution_limit = min(12, total_limit)
    preparation_limit = min(12, total_limit - execution_limit)
    turns = {agent: {"preparation": 0, "execution": 0} for agent in env.processing_order}
    last_results: dict[str, ToolResult | None] = dict.fromkeys(env.processing_order)
    calls: list[ToolCall] = []
    previous_phases: dict[str, str | None] = dict.fromkeys(env.processing_order)
    scheduled = sorted(set(env.variant.wake_times) - {config.submission_open_at})

    def snapshot() -> EpisodeResult:
        return EpisodeResult(
            env.metadata,
            env.log,
            calls,
            {agent: sum(counts.values()) for agent, counts in turns.items()},
            {
                job.job_id: env.job_status(job.job_id)
                for agent in env.scenario.agents
                for job in agent.jobs
            },
            env.spent,
            env.held,
        )

    # Actions stop before the horizon; the final pass only drains events due at the horizon.
    for time in range(env.scenario.horizon + 1):
        env.advance_to(time)
        if time == env.scenario.horizon:
            break

        budget_phase = "preparation" if time < config.submission_open_at else "execution"
        phase_limit = preparation_limit if budget_phase == "preparation" else execution_limit
        ready = []
        for agent in env.processing_order:
            if not env.is_ready(agent):
                continue
            future_slots = [slot for slot in scheduled if time < slot < config.submission_open_at]
            reserved = len(future_slots) if budget_phase == "preparation" else 0
            remaining = phase_limit - turns[agent][budget_phase]
            if remaining <= reserved and time not in scheduled:
                target = (
                    future_slots[0]
                    if future_slots
                    else (
                        config.submission_open_at
                        if budget_phase == "preparation"
                        else env.scenario.horizon
                    )
                )
                env.suspend_until(agent, target, "reserved_slots" if reserved else "turn_limit")
                continue
            if remaining <= 0:
                env.suspend_until(agent, env.scenario.horizon, "turn_limit")
                continue
            if env.phase() == "negotiation_wait":
                target = next((slot for slot in future_slots), config.submission_open_at)
                env.suspend_until(agent, target, "between_rounds")
                continue
            ready.append(agent)
        inboxes = {agent_id: env.take_inbox(agent_id, mark_read=False) for agent_id in ready}
        observations = {}
        for agent_id in ready:
            phase = env.phase() or budget_phase
            if phase == "execution" and time < env.submission_open_at[agent_id]:
                phase = "execution_wait"
            observations[agent_id] = Observation(
                agent_id=agent_id,
                logical_time=time,
                submission_open_at=env.submission_open_at[agent_id],
                turns_remaining=phase_limit - turns[agent_id][budget_phase],
                unread_messages=env.unread_count(agent_id) - len(inboxes[agent_id]),
                last_result=last_results[agent_id],
                own_jobs=tuple(env.own_jobs(agent_id)),
                phase=phase,
                inbox=inboxes[agent_id],
                plan_view=env.plan_view(),
                preparation_turns_remaining=preparation_limit - turns[agent_id]["preparation"],
                execution_turns_remaining=execution_limit - turns[agent_id]["execution"],
                phase_started=previous_phases[agent_id] != phase,
                horizon=env.scenario.horizon,
                protocol_notices=env.take_notices(agent_id),
            )
        decisions = {}
        for agent_id in ready:
            env.take_inbox(agent_id)
            env.record_decision(agent_id, budget_phase, turns[agent_id][budget_phase], phase_limit)
            try:
                decisions[agent_id] = policies[agent_id].decide(observations[agent_id])
            except Exception as exc:
                raise EpisodeInterrupted(snapshot(), exc) from exc
            previous_phases[agent_id] = observations[agent_id].phase
        for agent_id in ready:
            result = env.execute(agent_id, decisions[agent_id])
            turns[agent_id][budget_phase] += 1
            last_results[agent_id] = result
            calls.append(ToolCall(time, agent_id, decisions[agent_id], result))
            if time in env.variant.slot_times:
                target = next(
                    (slot for slot in env.variant.slot_times if slot > time),
                    config.submission_open_at,
                )
                env.suspend_until(agent_id, target, "between_rounds")

    env.finish_episode(turns)
    return snapshot()
