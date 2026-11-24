"""Independent log audit: rebuilds budget, job and plan state from the raw operations.

The audit trusts neither the simulator's totals nor its summary rows. Plan versions and the
agreement are reconstructed from individual proposals and confirmations, and every transition
is checked against the catalog and the timing rules stored in the episode metadata.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import CONFIRM_TIME, PROPOSE_TIMES, SNAPSHOT_TIMES, Variant


@dataclass(frozen=True)
class AuditReport:
    total_spent: int
    max_spent: int
    max_overrun: int
    violated: bool
    max_committed_plus_held: int
    completed_jobs: tuple[str, ...]
    issues: tuple[str, ...]
    agreement: str | None = None
    plan_mismatches: int = 0

    @property
    def consistent(self) -> bool:
        return not self.issues


def _catalog_option(metadata: EpisodeMetadata, entry: LogEntry) -> dict[str, int] | None:
    job = metadata.catalog.get(entry.job_id or "")
    return job["options"].get(entry.option_id or "") if job else None


def _same_operation(source: LogEntry, entry: LogEntry) -> bool:
    return (source.agent_id, source.job_id, source.option_id, source.cost) == (
        entry.agent_id,
        entry.job_id,
        entry.option_id,
        entry.cost,
    )


def _plan_item_issue(metadata: EpisodeMetadata, agent_id: str, item: dict[str, Any]) -> bool:
    job = metadata.catalog.get(item.get("job_id", ""))
    if job is None or job["owner"] != agent_id:
        return True
    option = job["options"].get(item.get("option_id", ""))
    return option is None or option["cost"] != item.get("cost")


class _PlanAudit:
    """Rebuilds plan versions and the agreement from proposal and confirmation rows."""

    def __init__(self, metadata: EpisodeMetadata, variant: Variant, issues: list[str]) -> None:
        self.metadata = metadata
        self.variant = variant
        self.issues = issues
        self.agents = set(metadata.submission_open_at)
        self.opens_at = min(metadata.submission_open_at.values())
        self.live: dict[str, dict[str, Any]] = {}
        self.versions: dict[int, dict[str, dict[str, Any]]] = {}
        self.confirmations: dict[str, int] = {}
        self.agreement_rows = 0
        self.agreement: str | None = None

    def propose(self, entry: LogEntry, where: str) -> None:
        if entry.time not in PROPOSE_TIMES:
            self.issues.append(f"{where}: proposal outside its phase")
            return
        agent_id = entry.agent_id or ""
        pairs = [*entry.detail.get("items", ()), *entry.detail.get("disclosed_alternatives", ())]
        if self.metadata.catalog and any(
            _plan_item_issue(self.metadata, agent_id, item) for item in pairs
        ):
            self.issues.append(f"{where}: proposal differs from the catalog")
        self.live[agent_id] = entry.detail

    def snapshot(self, entry: LogEntry, where: str) -> None:
        version = len(self.versions) + 1
        if entry.time not in SNAPSHOT_TIMES or entry.detail.get("plan_version") != version:
            self.issues.append(f"{where}: unexpected plan version or time")
        rebuilt = {agent: dict(proposal) for agent, proposal in self.live.items()}
        if entry.detail.get("proposals") != rebuilt:
            self.issues.append(f"{where}: snapshot differs from logged proposals")
        self.versions[version] = rebuilt

    def confirm(self, entry: LogEntry, where: str) -> None:
        version = entry.detail.get("plan_version")
        final = max(self.versions, default=None)
        if (
            entry.time != CONFIRM_TIME
            or version != final
            or final != len(SNAPSHOT_TIMES)
            or set(self.versions[final]) != self.agents
        ):
            self.issues.append(f"{where}: invalid confirmation")
            return
        self.confirmations[entry.agent_id or ""] = version

    def agreed_version(self) -> int | None:
        final = max(self.versions, default=None)
        if (
            final is not None
            and set(self.versions[final]) == self.agents
            and set(self.confirmations) == self.agents
            and set(self.confirmations.values()) == {final}
        ):
            return final
        return None

    def resolve(self, entry: LogEntry, where: str) -> None:
        self.agreement_rows += 1
        self.agreement = entry.result
        version = self.agreed_version()
        agreed = version is not None
        expected = {
            "plan_version": version,
            "confirmations": self.confirmations,
            "enforced": agreed and self.variant.guard,
            "fallback": not agreed and self.variant.guard,
        }
        if (
            entry.time != self.opens_at
            or entry.result != ("agreed" if agreed else "agreement_failed")
            or entry.detail != expected
        ):
            self.issues.append(f"{where}: agreement row differs from rebuilt agreement")

    def check_guard(self, entry: LogEntry, where: str) -> None:
        if not self.variant.guard or entry.time < self.opens_at:
            return
        version = self.agreed_version()
        if version is None:
            return
        items = self.versions[version][entry.agent_id or ""]["items"]
        if (entry.job_id, entry.option_id) not in {(i["job_id"], i["option_id"]) for i in items}:
            self.issues.append(f"{where}: {entry.job_id}/{entry.option_id} outside agreed plan")

    def finish(self) -> None:
        if not self.variant.structured:
            return
        if len(self.versions) != len(SNAPSHOT_TIMES):
            self.issues.append(f"expected {len(SNAPSHOT_TIMES)} plan versions")
        if self.agreement_rows != 1:
            self.issues.append(f"expected one agreement row, found {self.agreement_rows}")


def audit_episode(
    metadata: EpisodeMetadata, entries: Iterable[LogEntry], *, require_complete: bool = False
) -> AuditReport:
    # Historical journals remain readable; these aliases are not executable protocols.
    historical = {"B0": "U/N", "B1": "U/F", "B2": "A/N", "B3": "A/F"}
    name = metadata.variant or metadata.mode
    variant = Variant.parse(historical.get(name, name))
    reserving = variant.reserves
    budget = metadata.budget
    spent = held = max_spent = max_total = last_time = plan_mismatches = 0
    accepted: dict[str, LogEntry] = {}
    committed: dict[str, LogEntry] = {}
    completed: dict[str, LogEntry] = {}
    accepted_jobs: set[str] = set()
    finished_jobs: set[str] = set()
    issues: list[str] = []
    plans = _PlanAudit(metadata, variant, issues)
    phase_counts = {
        agent: {"preparation": 0, "execution": 0} for agent in metadata.submission_open_at
    }
    endings = 0
    sends: dict[int, LogEntry] = {}
    delivered: dict[int, str] = {}

    for index, entry in enumerate(entries):
        where = f"seq {entry.seq} ({entry.event_type})"
        if entry.seq != index:
            issues.append(f"{where}: journal sequence is incomplete")
        if entry.scenario_id != metadata.scenario_id or entry.mode != metadata.mode:
            issues.append(f"{where}: episode identity differs from metadata")
        if not 0 <= entry.time <= metadata.horizon:
            issues.append(f"{where}: event lies outside the episode horizon")
        if (entry.spent_before, entry.held_before) != (spent, held):
            issues.append(f"{where}: budget before transition differs from rebuilt state")
        if entry.event_type == "decision":
            phase = (
                "preparation"
                if entry.time < min(metadata.submission_open_at.values())
                else "execution"
            )
            counts = phase_counts.get(entry.agent_id or "")
            if counts is None:
                issues.append(f"{where}: unknown decision owner")
            else:
                counts[phase] += 1
                limit = getattr(metadata, f"{phase}_turn_limit")
                if counts[phase] > limit or entry.detail != {
                    "phase": phase,
                    "phase_turn": counts[phase],
                    "phase_limit": limit,
                }:
                    issues.append(f"{where}: invalid phase decision budget")
        elif entry.event_type == "episode_end":
            endings += 1
            if entry.time != metadata.horizon or entry.detail.get("turns") != phase_counts:
                issues.append(f"{where}: invalid episode completion record")
        elif metadata.protocol_version and entry.event_type == "finish" and entry.result == "ok":
            if entry.time < metadata.submission_open_at.get(entry.agent_id or "", 0):
                issues.append(f"{where}: finished before individual opening")
        elif entry.event_type == "send_message" and entry.result == "ok":
            message_id = entry.detail["message_id"]
            sends[message_id] = entry
            if entry.detail["deliver_at"] != entry.time + max(1, metadata.message_delay):
                issues.append(f"{where}: incorrect delivery time")
        elif entry.event_type == "message_delivered":
            message_id = entry.detail["message_id"]
            sent = sends.get(message_id)
            if (
                sent is None
                or sent.detail["deliver_at"] != entry.time
                or sent.detail["to"] != entry.agent_id
            ):
                issues.append(f"{where}: delivery differs from sent message")
            if message_id in delivered:
                issues.append(f"{where}: message delivered twice")
            delivered[message_id] = entry.agent_id or ""
        elif entry.event_type in ("message_read", "read_messages") and entry.result == "ok":
            if any(
                delivered.get(item) != entry.agent_id
                for item in entry.detail.get("message_ids", ())
            ):
                issues.append(f"{where}: message shown before delivery or to the wrong owner")
        request_id = entry.request_id
        if entry.time < last_time:
            issues.append(f"{where}: time moved backwards")
        last_time = max(last_time, entry.time)

        if entry.event_type == "submit" and entry.result == "accepted":
            if entry.job_id in accepted_jobs:
                issues.append(f"{where}: job {entry.job_id} accepted twice")
            if request_id is None or request_id in accepted:
                issues.append(f"{where}: missing or repeated request id {request_id}")
            else:
                accepted[request_id] = entry
            accepted_jobs.add(entry.job_id or "")
            missing = set(metadata.requires.get(entry.job_id or "", ())) - finished_jobs
            if missing:
                issues.append(f"{where}: {entry.job_id} accepted before {sorted(missing)}")
            if entry.time < metadata.submission_open_at.get(entry.agent_id or "", 0):
                issues.append(f"{where}: accepted before submission opened")
            if metadata.catalog:
                option = _catalog_option(metadata, entry)
                job = metadata.catalog.get(entry.job_id or "")
                if option is None or job["owner"] != entry.agent_id:
                    issues.append(f"{where}: job or option is not in the owner's catalog")
                else:
                    if option["cost"] != entry.cost:
                        issues.append(f"{where}: cost differs from the catalog")
                    finish = entry.time + metadata.commit_delay + option["duration"]
                    if finish > metadata.horizon:
                        issues.append(f"{where}: accepted although it cannot finish by horizon")
            headroom = budget - spent - (held if reserving else 0)
            if headroom < (entry.cost or 0):
                issues.append(f"{where}: accepted without sufficient budget")
            plans.check_guard(entry, where)
            if reserving:
                held += entry.cost or 0

        elif entry.event_type == "submit" and entry.result == "plan_mismatch":
            plan_mismatches += 1

        elif entry.event_type == "commit":
            source = accepted.get(request_id or "")
            if source is None:
                issues.append(f"{where}: commit without accepted request {request_id}")
            elif request_id in committed:
                issues.append(f"{where}: request {request_id} committed twice")
            elif not _same_operation(source, entry):
                issues.append(f"{where}: commit differs from accepted request")
            elif entry.time != source.time + metadata.commit_delay:
                issues.append(f"{where}: commit at the wrong time")
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
            elif not _same_operation(source, entry):
                issues.append(f"{where}: completion differs from committed request")
            elif entry.time <= source.time:
                issues.append(f"{where}: completed no later than commit")
            elif metadata.catalog:
                option = _catalog_option(metadata, source)
                if option is not None and entry.time != source.time + option["duration"]:
                    issues.append(f"{where}: completed at the wrong time")
            if entry.time > metadata.horizon:
                issues.append(f"{where}: completed after horizon")
            if source is not None:
                completed[request_id or ""] = source
                finished_jobs.add(source.job_id or "")

        elif entry.event_type == "propose_plan" and entry.result == "ok":
            plans.propose(entry, where)
        elif entry.event_type == "plan_version":
            plans.snapshot(entry, where)
        elif entry.event_type == "confirm_plan" and entry.result == "ok":
            plans.confirm(entry, where)
        elif entry.event_type == "agreement":
            plans.resolve(entry, where)

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

    # too_late guards submission, so every accepted request must commit and complete.
    issues.extend(
        f"request {r}: accepted but never committed" for r in sorted(set(accepted) - set(committed))
    )
    issues.extend(
        f"request {r}: committed but never completed"
        for r in sorted(set(committed) - set(completed))
    )
    plans.finish()
    if require_complete and endings != 1:
        issues.append(f"expected one episode completion record, found {endings}")

    return AuditReport(
        total_spent=spent,
        max_spent=max_spent,
        max_overrun=max(0, max_spent - budget),
        violated=max_spent > budget,
        max_committed_plus_held=max_total,
        completed_jobs=tuple(sorted(e.job_id or "" for e in completed.values())),
        issues=tuple(issues),
        agreement=plans.agreement,
        plan_mismatches=plan_mismatches,
    )
