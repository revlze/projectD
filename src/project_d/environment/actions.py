"""Agent actions and tool results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToolStatus(StrEnum):
    OK = "ok"
    ACCEPTED = "accepted"
    INSUFFICIENT_BUDGET = "insufficient_budget"
    TOO_LATE = "too_late"
    SUBMISSION_NOT_OPEN = "submission_not_open"
    UNKNOWN_JOB = "unknown_job"
    NOT_OWNER = "not_owner"
    UNKNOWN_OPTION = "unknown_option"
    JOB_ALREADY_ACCEPTED = "job_already_accepted"
    REQUEST_ID_CONFLICT = "request_id_conflict"
    MESSAGING_DISABLED = "messaging_disabled"
    MESSAGING_CLOSED = "messaging_closed"
    INVALID_RECIPIENT = "invalid_recipient"
    INVALID_WAIT = "invalid_wait"
    INVALID_ACTION = "invalid_action"
    AGENT_FINISHED = "agent_finished"


@dataclass(frozen=True)
class ToolResult:
    status: ToolStatus
    logical_time: int
    submission_open_at: int
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ListJobs:
    pass


@dataclass(frozen=True)
class GetBalance:
    pass


@dataclass(frozen=True)
class SubmitJob:
    job_id: str
    option_id: str
    request_id: str | None = None


@dataclass(frozen=True)
class GetStatus:
    pass


@dataclass(frozen=True)
class SendMessage:
    to: str
    text: str


@dataclass(frozen=True)
class ReadMessages:
    pass


@dataclass(frozen=True)
class WaitUntil:
    target_time: int


@dataclass(frozen=True)
class Finish:
    pass


@dataclass(frozen=True)
class InvalidCall:
    """A model output that could not become a tool call. The environment logs and refuses it."""

    name: str | None
    reason: str


Action = (
    ListJobs
    | GetBalance
    | SubmitJob
    | GetStatus
    | SendMessage
    | ReadMessages
    | WaitUntil
    | Finish
    | InvalidCall
)
