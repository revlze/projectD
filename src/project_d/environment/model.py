"""Scenario data model, JSON loading and per-run configuration."""

from __future__ import annotations

import graphlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

# Legacy pilot timing, kept so that the historical runs stay reproducible.
DEFAULT_SUBMISSION_OPEN_AT = 13

# Shared timing grid of the new protocol (system_spec.md, section 5).
PROTOCOL_SUBMISSION_OPEN_AT = 40
PROTOCOL_HORIZON = 80
PROTOCOL_TURN_LIMIT = 24
ROUND_TIMES = (6, 13, 20)
PROPOSE_TIMES = (29, 33)
SNAPSHOT_TIMES = (30, 34)
FEEDBACK_TIMES = (30, 35)
CONFIRM_TIME = 37


class ScenarioError(ValueError):
    """A scenario or run configuration violates the data contract."""


class Comm(StrEnum):
    N = "N"
    F = "F"
    R1 = "R1"
    R3 = "R3"
    R3P = "R3P"


_VARIANT_RE = re.compile(r"^(U|A)/(N|F|R1|R3P|R3)((?:\+[SVG])*)$")


@dataclass(frozen=True)
class Variant:
    """Execution mechanism, communication protocol and VBC components (decisions D18, D19)."""

    execution: str
    comm: Comm
    structured: bool = False
    verify: bool = False
    guard: bool = False

    def __post_init__(self) -> None:
        if self.execution not in ("U", "A"):
            raise ScenarioError(f"unknown execution {self.execution!r}")
        if (self.verify or self.guard) and not self.structured:
            raise ScenarioError("V and G require S")
        if self.structured and (self.execution != "A" or self.comm is not Comm.R3P):
            raise ScenarioError("S, V and G are defined only on top of A/R3P")

    @classmethod
    def parse(cls, name: str) -> Variant:
        if name in _LEGACY_VARIANTS:
            return cls.parse(_LEGACY_VARIANTS[name])
        if name == "A/VBC":
            return cls("A", Comm.R3P, True, True, True)
        match = _VARIANT_RE.match(name)
        if match is None:
            raise ScenarioError(f"unknown variant {name!r}")
        flags = match.group(3).split("+")[1:]
        if flags != sorted(set(flags), key="SVG".index):
            raise ScenarioError(f"components must be unique and ordered S, V, G: {name!r}")
        return cls(match.group(1), Comm(match.group(2)), "S" in flags, "V" in flags, "G" in flags)

    @property
    def value(self) -> str:
        if self.structured and self.verify and self.guard:
            return "A/VBC"
        flags = "".join(
            f"+{flag}"
            for flag, on in (("S", self.structured), ("V", self.verify), ("G", self.guard))
            if on
        )
        return f"{self.execution}/{self.comm.value}{flags}"

    @property
    def reserves(self) -> bool:
        return self.execution == "A"

    @property
    def messaging(self) -> bool:
        return self.comm is not Comm.N

    @property
    def round_times(self) -> tuple[int, ...]:
        if self.comm is Comm.R1:
            return ROUND_TIMES[:1]
        if self.comm in (Comm.R3, Comm.R3P):
            return ROUND_TIMES
        return ()

    @property
    def wake_times(self) -> tuple[int, ...]:
        """Scheduled phases that interrupt a wait. Free-form F has none."""
        plan_times = (*PROPOSE_TIMES, CONFIRM_TIME) if self.structured else ()
        if not self.round_times:
            return ()
        # The wake at opening gives every round arm a turn after late deliveries.
        return (*self.round_times, *plan_times, PROTOCOL_SUBMISSION_OPEN_AT)


_LEGACY_VARIANTS = {"B0": "U/N", "B1": "U/F", "B2": "A/N", "B3": "A/F"}


class Mode(StrEnum):
    """Original B0-B3 labels. They select the historical prompts and map to U/A x N/F."""

    B0 = "B0"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"

    @property
    def variant(self) -> Variant:
        return Variant.parse(self.value)

    @property
    def reserves(self) -> bool:
        return self.variant.reserves

    @property
    def messaging(self) -> bool:
        return self.variant.messaging


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
    requires: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.options:
            raise ScenarioError(f"job {self.job_id} has no options")
        _require_unique(f"option_id in {self.job_id}", [o.option_id for o in self.options])
        _require_unique(f"requires in {self.job_id}", list(self.requires))

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
        own = {job.job_id for job in self.jobs}
        graph = {job.job_id: set(job.requires) for job in self.jobs}
        for job_id, required in graph.items():
            if not required <= own:
                raise ScenarioError(f"{job_id} requires jobs of another user: {required - own}")
        try:
            graphlib.TopologicalSorter(graph).prepare()
        except graphlib.CycleError as exc:
            raise ScenarioError(f"cyclic requires for agent {self.agent_id}") from exc


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
                            requires=tuple(j.get("requires", ())),
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

    mode: Mode | Variant
    first_agent: str = "A"
    role_swap: bool = False
    submission_open_at: int | None = None
    start_gap: int = 0
    horizon: int | None = None
    commit_delay: int | None = None
    message_delay: int | None = None
    agent_turn_limit: int | None = None
    environment_seed: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, Mode | Variant):
            raise ScenarioError(f"mode must be a Mode or Variant, got {self.mode!r}")
        # B0-B3 labels keep the legacy grid; named variants default to the new protocol.
        if isinstance(self.mode, Mode):
            if self.submission_open_at is None:
                object.__setattr__(self, "submission_open_at", DEFAULT_SUBMISSION_OPEN_AT)
        else:
            if self.submission_open_at is None:
                object.__setattr__(self, "submission_open_at", PROTOCOL_SUBMISSION_OPEN_AT)
            if self.submission_open_at == PROTOCOL_SUBMISSION_OPEN_AT:
                if self.horizon is None:
                    object.__setattr__(self, "horizon", PROTOCOL_HORIZON)
                if self.agent_turn_limit is None:
                    object.__setattr__(self, "agent_turn_limit", PROTOCOL_TURN_LIMIT)
        _require_int("submission_open_at", self.submission_open_at, 0)
        _require_int("start_gap", self.start_gap, 0)
        if self.variant.wake_times and self.submission_open_at != PROTOCOL_SUBMISSION_OPEN_AT:
            raise ScenarioError(
                f"{self.variant.value} requires submission_open_at={PROTOCOL_SUBMISSION_OPEN_AT}"
            )

    @classmethod
    def for_protocol(cls, variant: Variant | str, **overrides: Any) -> RunConfig:
        """A run on the new shared grid: open at 40, horizon 80, 24 decisions per agent."""
        resolved = Variant.parse(variant) if isinstance(variant, str) else variant
        settings: dict[str, Any] = {
            "submission_open_at": PROTOCOL_SUBMISSION_OPEN_AT,
            "horizon": PROTOCOL_HORIZON,
            "agent_turn_limit": PROTOCOL_TURN_LIMIT,
        }
        return cls(mode=resolved, **(settings | overrides))

    @property
    def variant(self) -> Variant:
        return self.mode.variant if isinstance(self.mode, Mode) else self.mode

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
