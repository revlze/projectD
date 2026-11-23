"""Independent log audit: rebuilds budget state without trusting the simulator's totals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from project_d.environment.journal import EpisodeMetadata, LogEntry

_RESERVING_MODES = {"B2", "B3"}


@dataclass(frozen=True)
class AuditReport:
    total_spent: int
    max_spent: int
    max_overrun: int
    violated: bool
    max_committed_plus_held: int
    completed_jobs: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def consistent(self) -> bool:
        return not self.issues


def audit_episode(metadata: EpisodeMetadata, entries: Iterable[LogEntry]) -> AuditReport:
    reserving = metadata.mode in _RESERVING_MODES
    budget = metadata.budget
    spent = held = max_spent = max_total = 0
    accepted: dict[str, LogEntry] = {}
    committed: dict[str, LogEntry] = {}
    completed: dict[str, LogEntry] = {}
    accepted_jobs: set[str] = set()
    issues: list[str] = []

    for entry in entries:
        where = f"seq {entry.seq} ({entry.event_type})"
        request_id = entry.request_id

        if entry.event_type == "submit" and entry.result == "accepted":
            if entry.job_id in accepted_jobs:
                issues.append(f"{where}: job {entry.job_id} accepted twice")
            if request_id is None or request_id in accepted:
                issues.append(f"{where}: missing or repeated request id {request_id}")
            else:
                accepted[request_id] = entry
            accepted_jobs.add(entry.job_id or "")
            if reserving:
                held += entry.cost or 0

        elif entry.event_type == "commit":
            source = accepted.get(request_id or "")
            if source is None:
                issues.append(f"{where}: commit without accepted request {request_id}")
            elif request_id in committed:
                issues.append(f"{where}: request {request_id} committed twice")
            elif (source.job_id, source.option_id, source.cost) != (
                entry.job_id,
                entry.option_id,
                entry.cost,
            ):
                issues.append(f"{where}: commit differs from accepted request")
            committed[request_id or ""] = entry
            spent += entry.cost or 0
            if reserving:
                held -= entry.cost or 0

        elif entry.event_type == "complete":
            source = committed.get(request_id or "")
            if source is None:
                issues.append(f"{where}: completion without commit")
            elif request_id in completed:
                issues.append(f"{where}: request {request_id} completed twice")
            elif entry.time <= source.time:
                issues.append(f"{where}: completed no later than commit")
            if entry.time > metadata.horizon:
                issues.append(f"{where}: completed after horizon")
            completed[request_id or ""] = entry

        if (entry.spent_after, entry.held_after) != (spent, held):
            issues.append(
                f"{where}: logged spent/held {entry.spent_after}/{entry.held_after}, "
                f"rebuilt {spent}/{held}"
            )
        if held < 0:
            issues.append(f"{where}: negative held {held}")
        if reserving and spent + held > budget:
            issues.append(f"{where}: spent + held = {spent + held} exceeds budget {budget}")
        max_spent = max(max_spent, spent)
        max_total = max(max_total, spent + held)

    missing_commits = sorted(set(accepted) - set(committed))
    # An accepted request always commits before the horizon, because too_late guards submission.
    issues.extend(f"request {r}: accepted but never committed" for r in missing_commits)

    return AuditReport(
        total_spent=spent,
        max_spent=max_spent,
        max_overrun=max(0, max_spent - budget),
        violated=max_spent > budget,
        max_committed_plus_held=max_total,
        completed_jobs=tuple(sorted(e.job_id or "" for e in completed.values())),
        issues=tuple(issues),
    )
