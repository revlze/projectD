"""Scenario data model, JSON loading and per-run configuration."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

DEFAULT_SUBMISSION_OPEN_AT = 13


class ScenarioError(ValueError):
    """A scenario or run configuration violates the data contract."""


class Mode(StrEnum):
    B0 = "B0"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"

    @property
    def reserves(self) -> bool:
        return self in (Mode.B2, Mode.B3)

    @property
    def messaging(self) -> bool:
        return self in (Mode.B1, Mode.B3)


class JobStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


def _require_int(name: str, value: Any, minimum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ScenarioError(f"{name} must be an int >= {minimum}, got {value!r}")


def _require_unique(name: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ScenarioError(f"duplicate {name}: {values}")


@dataclass(frozen=True)
class Option:
    option_id: str
    cost: int
    duration: int
    value: int

    def __post_init__(self) -> None:
        _require_int(f"{self.option_id}.cost", self.cost, 1)
        _require_int(f"{self.option_id}.duration", self.duration, 1)
        _require_int(f"{self.option_id}.value", self.value, 0)


@dataclass(frozen=True)
class Job:
    job_id: str
    options: tuple[Option, ...]

    def __post_init__(self) -> None:
        if not self.options:
            raise ScenarioError(f"job {self.job_id} has no options")
        _require_unique(f"option_id in {self.job_id}", [o.option_id for o in self.options])

    def option(self, option_id: str) -> Option | None:
        return next((o for o in self.options if o.option_id == option_id), None)


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    user_request: str
    jobs: tuple[Job, ...]

    def __post_init__(self) -> None:
        if not 1 <= len(self.jobs) <= 3:
            raise ScenarioError(f"agent {self.agent_id} must have 1-3 jobs, got {len(self.jobs)}")


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    family: str
    budget: int
    horizon: int
    commit_delay: int
    message_delay: int
    agent_turn_limit: int
    seed: int
    agents: tuple[AgentSpec, ...]

    def __post_init__(self) -> None:
        _require_int("budget", self.budget, 1)
        _require_int("horizon", self.horizon, 1)
        _require_int("commit_delay", self.commit_delay, 0)
        _require_int("message_delay", self.message_delay, 0)
        _require_int("agent_turn_limit", self.agent_turn_limit, 1)
        if not self.agents:
            raise ScenarioError("scenario has no agents")
        _require_unique("agent_id", [a.agent_id for a in self.agents])
        _require_unique("job_id", [j.job_id for a in self.agents for j in a.jobs])

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Scenario:
        try:
            agents = tuple(
                AgentSpec(
                    agent_id=a["agent_id"],
                    user_request=a["user_request"],
                    jobs=tuple(
                        Job(
                            job_id=j["job_id"],
                            options=tuple(
                                Option(o["option_id"], o["cost"], o["duration"], o["value"])
                                for o in j["options"]
                            ),
                        )
                        for j in a["jobs"]
                    ),
                )
                for a in raw["agents"]
            )
            return cls(
                scenario_id=raw["scenario_id"],
                family=raw["family"],
                budget=raw["budget"],
                horizon=raw["horizon"],
                commit_delay=raw["commit_delay"],
                message_delay=raw["message_delay"],
                agent_turn_limit=raw["agent_turn_limit"],
                seed=raw["seed"],
                agents=agents,
            )
        except (KeyError, TypeError) as exc:
            raise ScenarioError(f"malformed scenario: {exc!r}") from exc

    def with_role_swap(self) -> Scenario:
        """Exchange the two agent identifiers together with their requests and jobs."""
        if len(self.agents) != 2:
            raise ScenarioError("role swap requires exactly two agents")
        first, second = self.agents
        swapped = (
            replace(second, agent_id=first.agent_id),
            replace(first, agent_id=second.agent_id),
        )
        return replace(self, agents=swapped)


def load_scenario(path: str | Path) -> Scenario:
    with Path(path).open(encoding="utf-8") as handle:
        return Scenario.from_dict(json.load(handle))


@dataclass(frozen=True)
class RunConfig:
    """Parameters of one run. ``None`` overrides keep the scenario's value."""

    mode: Mode
    first_agent: str = "A"
    role_swap: bool = False
    submission_open_at: int = DEFAULT_SUBMISSION_OPEN_AT
    start_gap: int = 0
    horizon: int | None = None
    commit_delay: int | None = None
    message_delay: int | None = None
    agent_turn_limit: int | None = None
    environment_seed: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, Mode):
            raise ScenarioError(f"mode must be a Mode, got {self.mode!r}")
        _require_int("submission_open_at", self.submission_open_at, 0)
        _require_int("start_gap", self.start_gap, 0)

    def open_times(self, agent_ids: Iterable[str]) -> dict[str, int]:
        """Earliest submission time per agent: the second agent opens ``start_gap`` later."""
        return {
            agent_id: self.submission_open_at
            + (0 if agent_id == self.first_agent else self.start_gap)
            for agent_id in agent_ids
        }

    def apply(self, scenario: Scenario) -> Scenario:
        resolved = scenario.with_role_swap() if self.role_swap else scenario
        overrides = {
            name: value
            for name in ("horizon", "commit_delay", "message_delay", "agent_turn_limit")
            if (value := getattr(self, name)) is not None
        }
        return replace(resolved, **overrides)
