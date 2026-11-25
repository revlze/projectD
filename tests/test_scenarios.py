"""Independent portfolio and executable schedule checks of the tracked scenarios."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import pytest

from project_d.environment.actions import SubmitJob, WaitUntil
from project_d.environment.model import Job, Option, RunConfig, Scenario, load_scenario
from project_d.evaluation.metrics import episode_metrics, optimal_utility
from project_d.experiments.matrix import DATA_ROOT
from project_d.simulation.scheduler import ScriptedPolicy, run_episode

ROOT = Path(__file__).resolve().parents[1] / DATA_ROOT
MANIFEST = json.loads((ROOT / "manifest.json").read_bytes())
PROFILES = sorted(MANIFEST["files"])
REPEATS = tuple(product(("A", "B"), (False, True)))


def _portfolio_oracle(scenario: Scenario) -> tuple[int, dict[str, Option]]:
    """Enumerate budget/dependency-feasible portfolios without the production optimizer.

    Tests below first establish that even serial execution of every job fits the
    horizon and decision budget. Time therefore cannot exclude a feasible portfolio.
    """
    jobs = [job for agent in scenario.agents for job in agent.jobs]
    best_value, best = 0, {}
    for choices in product(*((None, *job.options) for job in jobs)):
        selected = {
            job.job_id: option
            for job, option in zip(jobs, choices, strict=True)
            if option is not None
        }
        if sum(option.cost for option in selected.values()) > scenario.budget:
            continue
        if any(not set(job.requires) <= selected.keys() for job in jobs if job.job_id in selected):
            continue
        value = sum(option.value for option in selected.values())
        if value > best_value:
            best_value, best = value, selected
    return best_value, best


def _serial_submissions(
    scenario: Scenario, selected: dict[str, Option], opens: dict[str, int]
) -> dict[str, dict[int, SubmitJob]]:
    schedules = {}
    for agent in scenario.agents:
        remaining: list[Job] = [job for job in agent.jobs if job.job_id in selected]
        completed: set[str] = set()
        time = opens[agent.agent_id]
        steps = {}
        while remaining:
            job = next(job for job in remaining if set(job.requires) <= completed)
            option = selected[job.job_id]
            steps[time] = SubmitJob(job.job_id, option.option_id)
            time += scenario.commit_delay + option.duration
            completed.add(job.job_id)
            remaining.remove(job)
        schedules[agent.agent_id] = steps
    return schedules


def _check_optimum(scenario: Scenario, config: RunConfig) -> int:
    resolved = config.apply(scenario)
    opens = config.open_times(agent.agent_id for agent in resolved.agents)
    for agent in resolved.agents:
        # A conservative all-jobs schedule fits even without exploiting concurrency.
        serial_duration = sum(
            resolved.commit_delay + max(option.duration for option in job.options)
            for job in agent.jobs
        )
        assert opens[agent.agent_id] + serial_duration <= resolved.horizon
        assert 2 * len(agent.jobs) + 2 <= 12

    expected, selected = _portfolio_oracle(resolved)
    computed, plan = optimal_utility(resolved, opens)
    assert computed == expected > 0
    production_schedule: dict[str, dict[int, SubmitJob]] = {
        agent.agent_id: {} for agent in resolved.agents
    }
    for item in plan:
        steps = production_schedule[item.agent_id]
        assert item.submit_at not in steps
        steps[item.submit_at] = SubmitJob(item.job_id, item.option_id)
    for schedules in (_serial_submissions(resolved, selected, opens), production_schedule):
        policies = {
            agent.agent_id: ScriptedPolicy(
                {0: WaitUntil(opens[agent.agent_id]), **schedules[agent.agent_id]}
            )
            for agent in resolved.agents
        }
        result = run_episode(scenario, config, policies)
        metrics = episode_metrics(scenario, result.metadata, result.log)
        assert metrics.raw_utility == metrics.safe_utility == expected
        assert metrics.audit.consistent, metrics.audit.issues
        assert not metrics.audit.violated
        for agent in resolved.agents:
            assert sum(call.time >= 40 for call in result.calls_by(agent.agent_id)) <= 12
    return expected


@pytest.mark.parametrize("relative", PROFILES)
def test_tracked_u_star_and_schedules(relative: str) -> None:
    scenario = load_scenario(ROOT / relative)
    for first, swap in REPEATS:
        expected = _check_optimum(
            scenario, RunConfig.for_protocol("A/N", first_agent=first, role_swap=swap)
        )
        assert expected == MANIFEST["files"][relative]["u_star"]


@pytest.mark.parametrize("profile", ("test_s1_01", "test_s1_02"))
@pytest.mark.parametrize("delay,gap", tuple(product((0, 1, 3), (0, 2, 4))))
@pytest.mark.parametrize("first,swap", REPEATS)
def test_e4_h1_optimum_with_actual_opening_times(
    profile: str, delay: int, gap: int, first: str, swap: bool
) -> None:
    scenario = load_scenario(ROOT / "test" / f"{profile}.json")
    config = RunConfig.for_protocol(
        "A/N", first_agent=first, role_swap=swap, commit_delay=delay, start_gap=gap
    )
    _check_optimum(scenario, config)
