"""Shared builders for mechanism tests. Parameters are explicit, independent of data/examples."""

from __future__ import annotations

from project_d.environment.model import AgentSpec, Job, Mode, Option, RunConfig, Scenario


def make_scenario(
    budget: int = 12,
    a_options: tuple[tuple[str, int], ...] = (("full", 7),),
    b_options: tuple[tuple[str, int], ...] = (("standard", 6),),
    horizon: int = 30,
    commit_delay: int = 2,
    message_delay: int = 1,
    turn_limit: int = 16,
    duration: int = 2,
) -> Scenario:
    def job(job_id: str, options: tuple[tuple[str, int], ...]) -> Job:
        return Job(job_id, tuple(Option(o, cost, duration, cost + 1) for o, cost in options))

    return Scenario(
        scenario_id="test",
        family="TEST",
        budget=budget,
        horizon=horizon,
        commit_delay=commit_delay,
        message_delay=message_delay,
        agent_turn_limit=turn_limit,
        seed=1,
        agents=(
            AgentSpec("A", "request of A", (job("job_a", a_options),)),
            AgentSpec("B", "request of B", (job("job_b", b_options),)),
        ),
    )


def make_config(mode: Mode, **overrides: object) -> RunConfig:
    overrides.setdefault("submission_open_at", 0)
    return RunConfig(mode=mode, **overrides)  # type: ignore[arg-type]
