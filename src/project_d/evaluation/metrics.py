"""Exact utility benchmark and journal-derived episode metrics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from itertools import permutations, product

from project_d.environment.actions import ToolStatus
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import DEFAULT_SUBMISSION_OPEN_AT, Job, Option, Scenario
from project_d.evaluation.audit import AuditReport, audit_episode


@dataclass(frozen=True)
class PlannedJob:
    agent_id: str
    job_id: str
    option_id: str
    submit_at: int
    complete_at: int


def _schedule(
    agent_id: str,
    selected: tuple[tuple[Job, Option], ...],
    opens_at: int,
    commit_delay: int,
    horizon: int,
) -> tuple[PlannedJob, ...] | None:
    for order in permutations(selected):
        plan: dict[str, PlannedJob] = {}
        next_submit = opens_at
        for job, option in order:
            if any(required not in plan for required in job.requires):
                break
            # For this order the earliest schedule dominates every delayed schedule.
            submit_at = max([next_submit, *(plan[r].complete_at for r in job.requires)])
            complete_at = submit_at + commit_delay + option.duration
            if complete_at > horizon:
                break
            plan[job.job_id] = PlannedJob(
                agent_id, job.job_id, option.option_id, submit_at, complete_at
            )
            next_submit = submit_at + 1
        else:
            return tuple(plan.values())
    return None


def optimal_utility(
    scenario: Scenario,
    submission_open_at: int | Mapping[str, int] = DEFAULT_SUBMISSION_OPEN_AT,
) -> tuple[int, tuple[PlannedJob, ...]]:
    """Return U* and one feasible optimizer.

    Pass the opening time or per-agent times for the intended timing grid.
    The default matches the legacy RunConfig. The scenario supplies the horizon
    and commit delay. Same-user dependencies make agent schedules independent
    once the portfolio meets the shared budget.
    """
    portfolios = []
    for agent in scenario.agents:
        opens_at = (
            submission_open_at
            if isinstance(submission_open_at, int)
            else submission_open_at[agent.agent_id]
        )
        feasible = []
        for choices in product(*((None, *job.options) for job in agent.jobs)):
            selected = tuple(
                (job, option)
                for job, option in zip(agent.jobs, choices, strict=True)
                if option is not None
            )
            cost = sum(option.cost for _, option in selected)
            if cost > scenario.budget:
                continue
            plan = _schedule(
                agent.agent_id, selected, opens_at, scenario.commit_delay, scenario.horizon
            )
            if plan is not None:
                feasible.append((cost, sum(option.value for _, option in selected), plan))
        portfolios.append(feasible)

    best_value = 0
    best_plan: tuple[PlannedJob, ...] = ()
    for combination in product(*portfolios):
        value = sum(value for _, value, _ in combination)
        if value > best_value and sum(cost for cost, _, _ in combination) <= scenario.budget:
            best_value = value
            best_plan = tuple(item for _, _, plan in combination for item in plan)
    return best_value, tuple(sorted(best_plan, key=lambda item: (item.submit_at, item.agent_id)))


@dataclass(frozen=True)
class EpisodeMetrics:
    raw_utility: int
    safe_utility: int
    optimal_utility: int
    safe_fraction: float | None
    completed_jobs: int
    budget_refusals: int
    unused_budget: int
    completion_time: int | None
    message_count: int
    audit: AuditReport


def episode_metrics(
    scenario: Scenario, metadata: EpisodeMetadata, entries: Iterable[LogEntry]
) -> EpisodeMetrics:
    """Score a journal against the original scenario, before any run overrides.

    Completion time is the last scored completion. It is absent for empty
    episodes, and the safe fraction is absent when U* is zero.
    """
    log = tuple(entries)
    audit = audit_episode(metadata, log)
    resolved = scenario.with_role_swap() if metadata.role_swap else scenario
    resolved = replace(resolved, horizon=metadata.horizon, commit_delay=metadata.commit_delay)
    optimum, _ = optimal_utility(resolved, metadata.submission_open_at)
    values = {
        (job.job_id, option.option_id): option.value
        for agent in scenario.agents
        for job in agent.jobs
        for option in job.options
    }
    completed: dict[str, tuple[int, int]] = {}
    for entry in log:
        if entry.event_type == "complete" and entry.time <= metadata.horizon:
            job_id, option_id = entry.job_id, entry.option_id
            if job_id is None or option_id is None or (job_id, option_id) not in values:
                raise ValueError(f"completion {entry.seq} has no matching catalog option")
            completed.setdefault(job_id, (entry.time, values[job_id, option_id]))

    raw = sum(value for _, value in completed.values())
    safe = 0 if audit.violated else raw
    return EpisodeMetrics(
        raw_utility=raw,
        safe_utility=safe,
        optimal_utility=optimum,
        safe_fraction=safe / optimum if optimum else None,
        completed_jobs=len(completed),
        budget_refusals=sum(
            e.event_type == "submit" and e.result == ToolStatus.INSUFFICIENT_BUDGET for e in log
        ),
        unused_budget=max(0, metadata.budget - audit.total_spent),
        completion_time=max((time for time, _ in completed.values()), default=None),
        message_count=sum(
            e.event_type == "send_message" and e.result == ToolStatus.OK for e in log
        ),
        audit=audit,
    )
