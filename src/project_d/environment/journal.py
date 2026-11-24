"""Append-only record of the operations an episode actually performed."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EpisodeMetadata:
    scenario_id: str
    mode: str
    budget: int
    horizon: int
    commit_delay: int
    message_delay: int
    agent_turn_limit: int
    environment_seed: int
    first_agent: str
    role_swap: bool
    start_gap: int
    submission_open_at: dict[str, int]
    variant: str = ""
    requires: dict[str, list[str]] = field(default_factory=dict)
    # Owner, cost and duration per option for the audit. Hidden values are never stored here.
    catalog: dict[str, dict[str, Any]] = field(default_factory=dict)
    preparation_turn_limit: int = 12
    execution_turn_limit: int = 12
    protocol_version: str = ""


@dataclass(frozen=True)
class LogEntry:
    seq: int
    scenario_id: str
    mode: str
    time: int
    agent_id: str | None
    request_id: str | None
    event_type: str
    job_id: str | None
    option_id: str | None
    cost: int | None
    spent_before: int
    spent_after: int
    held_before: int
    held_after: int
    result: str
    detail: dict[str, Any] = field(default_factory=dict)


def write_jsonl(path: str | Path, metadata: EpisodeMetadata, entries: list[LogEntry]) -> None:
    """Write the metadata as the first line, then one log entry per line."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        header = asdict(metadata)
        handle.write(json.dumps({"metadata": header}, ensure_ascii=False) + "\n")
        for entry in entries:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    temporary.replace(target)
