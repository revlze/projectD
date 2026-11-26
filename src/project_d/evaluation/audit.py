"""Independent log audit: rebuilds budget, job and plan state from the raw operations.

The audit trusts neither the simulator's totals nor its summary rows. Plan versions and the
agreement are reconstructed from individual proposals and confirmations, and every transition
is checked against the catalog and the timing rules stored in the episode metadata.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from project_d.environment.actions import ToolStatus
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import (
    CONFIRM_TIME,
    FEEDBACK_TIMES,
    PROPOSE_TIMES,
    SNAPSHOT_TIMES,
    Comm,
    Variant,
)


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
    tool_statuses: dict[tuple[str, int], str] = field(default_factory=dict)
    # vbc-4: alternatives dropped from an accepted proposal, by (agent, time).
    removed_alternatives: dict[tuple[str, int], list[dict[str, str]]] = field(default_factory=dict)

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


def _same_submission(first: LogEntry, second: LogEntry) -> bool:
    return (first.agent_id, first.job_id, first.option_id) == (
        second.agent_id,
        second.job_id,
        second.option_id,
    )


def _plan_item_issue(metadata: EpisodeMetadata, agent_id: str, item: dict[str, Any]) -> bool:
    job = metadata.catalog.get(item.get("job_id", ""))
    if job is None or job["owner"] != agent_id:
        return True
    option = job["options"].get(item.get("option_id", ""))
    return option is None or option["cost"] != item.get("cost")


_ACTIONS = {
    "confirm_plan",
    "finish",
    "get_balance",
    "get_status",
    "invalid_action",
    "list_jobs",
    "propose_plan",
    "read_messages",
    "round_skipped",
    "send_message",
    "skip_round",
    "submit",
    "submit_replayed",
    "tool_call",
    "wait_until",
}
_SLOT_ACTIONS = {
    "round": {"send_message", "round_skipped", "skip_round"},
    "proposal": {"propose_plan", "wait_until"},
    "confirmation": {"confirm_plan", "wait_until"},
}


class _ScheduleAudit:
    def __init__(
        self,
        metadata: EpisodeMetadata,
        variant: Variant,
        issues: list[str],
        *,
        scheduled: bool,
    ) -> None:
        self.metadata = metadata
        self.variant = variant
        self.issues = issues
        self.scheduled = scheduled
        self.opens_at = min(metadata.submission_open_at.values())
        self.agents = set(metadata.submission_open_at)
        self.finished: set[str] = set()
        self.decisions: set[tuple[str, int]] = set()
        self.actions: dict[tuple[str, int], str] = {}
        self.sends: dict[int, LogEntry] = {}
        self.delivered: set[int] = set()
        self.inbox: dict[str, list[int]] = {agent: [] for agent in self.agents}
        self.round_participation: set[tuple[str, int]] = set()
        self.round_misses: set[tuple[str, int]] = set()
        self.last_action: LogEntry | None = None

    def observe(self, entry: LogEntry, where: str) -> None:
        event, time, agent = entry.event_type, entry.time, entry.agent_id or ""
        key = (agent, time)
        if not self.scheduled:
            return
        if event == "decision":
            if key in self.decisions or (self.last_action and self.last_action.time == time):
                self.issues.append(f"{where}: repeated or late decision in the same tick")
            self.decisions.add(key)
            if agent in self.finished or not self._decision_window(time):
                self.issues.append(f"{where}: decision outside its phase or after finish")
            if self.variant.round_times and self.inbox.get(agent):
                self.issues.append(f"{where}: delivered messages not shown at decision")
        elif event in _ACTIONS:
            if agent not in self.agents:
                self.issues.append(f"{where}: unknown action owner")
                return
            self._action(entry, where, key)
        elif event == "message_delivered":
            self._deliver(entry, where)
        elif event == "message_read":
            self._read(entry, where)
        elif event == "round_missed":
            missed = (agent, entry.detail.get("round_time"))
            if (
                time - 1 not in self.variant.round_times
                or missed != (agent, time - 1)
                or agent not in self.agents
                or missed in self.round_misses | self.round_participation
                or entry.result != "ok"
            ):
                self.issues.append(f"{where}: incorrect missed round")
            self.round_misses.add(missed)
        elif (
            event in {"agreement", "plan_version", "plan_feedback", "complete"}
            or (event == "commit" and self.metadata.commit_delay > 0)
        ) and any((peer, time) in self.decisions for peer in self.agents):
            self.issues.append(f"{where}: scheduled event occurs after a decision in its tick")

    def _decision_window(self, time: int) -> bool:
        slots = self.variant.slot_times
        return time < self.metadata.horizon and (
            not slots or time < slots[0] or time in slots or time >= self.opens_at
        )

    def _action(self, entry: LogEntry, where: str, key: tuple[str, int]) -> None:
        agent, time = key
        event, result = entry.event_type, entry.result
        if key in self.actions or agent in self.finished or not self._decision_window(time):
            self.issues.append(
                f"{where}: repeated action, action after finish or outside its phase"
            )
        if (
            self.last_action is not None
            and self.last_action.time == time
            and agent == self.metadata.first_agent
        ):
            self.issues.append(f"{where}: action order differs from the processing order")
        self.actions[key] = "unknown_job" if result == "not_owner" else result
        self.last_action = entry
        if time in self.variant.round_times:
            slot = "round"
        elif self.variant.structured and time in PROPOSE_TIMES:
            slot = "proposal"
        elif self.variant.structured and time == CONFIRM_TIME:
            slot = "confirmation"
        else:
            slot = None
        early = time < self.metadata.submission_open_at[agent]
        # Wrongly typed calls and early finish/submit attempts have explicit refusal rows.
        exceptional = (
            event in ("invalid_action", "tool_call")
            or (early and event in ("submit", "submit_replayed"))
            or (early and event == "finish" and result == "finish_not_open")
        )
        if slot and event not in _SLOT_ACTIONS[slot] and not exceptional:
            self.issues.append(f"{where}: action is not allowed in the {slot} slot")
        if event == "finish" and result != ("finish_not_open" if early else "ok"):
            self.issues.append(f"{where}: finish result differs from the individual opening")
        if event == "finish" and result == "ok":
            self.finished.add(agent)
        if result != "ok":
            return
        if event == "send_message":
            self._send(entry, where)
        elif event == "read_messages":
            self._read(entry, where)
        elif event == "round_skipped":
            if slot != "round":
                self.issues.append(f"{where}: skip outside a message round")
            self.round_participation.add(key)
        elif event in ("propose_plan", "confirm_plan") and not slot:
            self.issues.append(f"{where}: successful plan action outside its slot")

    def _send(self, entry: LogEntry, where: str) -> None:
        message_id = entry.detail.get("message_id")
        recipient = entry.detail.get("to")
        expected_delay = max(1, self.metadata.message_delay)
        rounds = self.variant.round_times
        if (
            not self.variant.messaging
            or entry.time >= self.opens_at
            or recipient not in self.agents - {entry.agent_id}
            or not isinstance(message_id, int)
            or message_id in self.sends
            or entry.detail.get("deliver_at") != entry.time + expected_delay
            or (
                rounds
                and (
                    entry.time not in rounds
                    or entry.detail.get("round") != rounds.index(entry.time) + 1
                )
            )
        ):
            self.issues.append(f"{where}: invalid message send or delivery schedule")
            return
        self.sends[message_id] = entry
        if rounds:
            self.round_participation.add((entry.agent_id or "", entry.time))

    def _deliver(self, entry: LogEntry, where: str) -> None:
        message_id = entry.detail.get("message_id")
        sent = self.sends.get(message_id)
        agent = entry.agent_id or ""
        if (
            sent is None
            or sent.detail["deliver_at"] != entry.time
            or sent.detail["to"] != agent
            or entry.detail.get("from") != sent.agent_id
            or message_id in self.delivered
            or entry.result != "ok"
            or any((peer, entry.time) in self.decisions for peer in self.agents)
        ):
            self.issues.append(
                f"{where}: delivery differs from sent message or arrives after a decision"
            )
            return
        self.delivered.add(message_id)
        self.inbox[agent].append(message_id)

    def _read(self, entry: LogEntry, where: str) -> None:
        agent = entry.agent_id or ""
        automatic = entry.event_type == "message_read"
        inbox = self.inbox.get(agent)
        if (
            not (self.variant.round_times if automatic else self.variant.comm is Comm.F)
            or inbox is None
            or entry.result != "ok"
            or entry.detail.get("message_ids") != inbox
            or (automatic and (not inbox or (agent, entry.time) in self.decisions))
        ):
            self.issues.append(f"{where}: message shown before delivery or to the wrong owner")
            return
        inbox.clear()

    def finish(self) -> None:
        for message_id, sent in self.sends.items():
            if (
                sent.detail["deliver_at"] <= self.metadata.horizon
                and message_id not in self.delivered
            ):
                self.issues.append(f"message {message_id}: missing scheduled delivery")
        if self.decisions != self.actions.keys():
            self.issues.append("decisions and actions differ by agent and time")
        for time in self.variant.round_times:
            if time < self.metadata.horizon:
                for agent in self.agents:
                    if (agent, time) not in self.round_participation | self.round_misses:
                        self.issues.append(f"{agent} at {time}: missing round outcome")
        slots = self.variant.slot_times
        if self.metadata.preparation_turn_limit >= len(slots):
            for time in slots:
                if time < self.metadata.horizon:
                    for agent in self.agents:
                        if (agent, time) not in self.decisions:
                            self.issues.append(f"{agent} at {time}: missing scheduled decision")


class _PlanAudit:
    """Rebuilds plan versions and the agreement from proposal and confirmation rows."""

    def __init__(
        self,
        metadata: EpisodeMetadata,
        variant: Variant,
        issues: list[str],
        vbc1_guard_release: bool | None,
    ) -> None:
        self.metadata = metadata
        self.variant = variant
        self.issues = issues
        self.agents = set(metadata.submission_open_at)
        self.opens_at = min(metadata.submission_open_at.values())
        self.live: dict[str, dict[str, Any]] = {}
        self.removed: dict[tuple[str, int], list[dict[str, str]]] = {}
        self.versions: dict[int, dict[str, dict[str, Any]]] = {}
        self.confirmations: dict[str, int] = {}
        self.agreement_rows = 0
        self.agreement: str | None = None
        self.agreed_items: dict[str, set[tuple[str, str]]] | None = None
        self.feedback_versions: list[int] = []
        self.released = False
        self.pending_release: LogEntry | None = None
        self.vbc1_guard_release = vbc1_guard_release

    def propose(self, entry: LogEntry, where: str) -> None:
        if not self.variant.structured or entry.time not in PROPOSE_TIMES:
            self.issues.append(f"{where}: proposal outside its phase")
            return
        agent_id = entry.agent_id or ""
        proposal = {k: v for k, v in entry.detail.items() if k != "removed_alternatives"}
        has_removed = "removed_alternatives" in entry.detail
        removed = entry.detail.get("removed_alternatives")
        chosen = proposal.get("items")
        alternatives = proposal.get("disclosed_alternatives")
        if (
            agent_id not in self.agents
            or not isinstance(chosen, list)
            or not isinstance(alternatives, list)
            or not isinstance(proposal.get("note"), str)
            or not all(
                isinstance(item, dict)
                and isinstance(item.get("job_id"), str)
                and isinstance(item.get("option_id"), str)
                and type(item.get("cost")) is int
                for item in (*chosen, *alternatives)
            )
        ):
            self.issues.append(f"{where}: invalid proposal contents")
            return
        if self.metadata.catalog and any(
            _plan_item_issue(self.metadata, agent_id, item) for item in (*chosen, *alternatives)
        ):
            self.issues.append(f"{where}: proposal differs from the catalog")
            return
        chosen_pairs = {(item["job_id"], item["option_id"]) for item in chosen}
        alternate_pairs = {(item["job_id"], item["option_id"]) for item in alternatives}
        if (
            len({item["job_id"] for item in chosen}) != len(chosen)
            or len(alternate_pairs) != len(alternatives)
            or chosen_pairs & alternate_pairs
        ):
            self.issues.append(f"{where}: repeated job or alternative in proposal")
            return
        # Only vbc-4 drops chosen options from the alternatives; it logs a nonempty list of
        # distinct chosen pairs, the same list it returned to the agent.
        if has_removed:
            well_formed = (
                self.metadata.protocol_version == "vbc-4"
                and isinstance(removed, list)
                and bool(removed)
                and all(
                    isinstance(pair, dict)
                    and set(pair) == {"job_id", "option_id"}
                    and all(isinstance(value, str) for value in pair.values())
                    for pair in removed
                )
            )
            pairs = [(pair["job_id"], pair["option_id"]) for pair in removed] if well_formed else []
            if not well_formed or len(set(pairs)) != len(pairs) or not set(pairs) <= chosen_pairs:
                self.issues.append(f"{where}: removed alternatives are not chosen options")
                return
            self.removed[agent_id, entry.time] = removed
        self.live[agent_id] = proposal

    def snapshot(self, entry: LogEntry, where: str) -> None:
        version = len(self.versions) + 1
        expected_time = SNAPSHOT_TIMES[version - 1] if version <= len(SNAPSHOT_TIMES) else None
        if entry.time != expected_time or entry.detail.get("plan_version") != version:
            self.issues.append(f"{where}: unexpected plan version or time")
        rebuilt = {agent: dict(proposal) for agent, proposal in self.live.items()}
        if entry.detail.get("proposals") != rebuilt:
            self.issues.append(f"{where}: snapshot differs from logged proposals")
        self.versions[version] = rebuilt

    def feedback(self, entry: LogEntry, where: str) -> None:
        """Each V row belongs to the latest version, at its own time, with rebuilt arithmetic."""
        version = entry.detail.get("plan_version")
        if (
            not self.variant.verify
            or type(version) is not int
            or version not in range(1, len(FEEDBACK_TIMES) + 1)
            or version != max(self.versions, default=None)
            or version in self.feedback_versions
            or entry.time != FEEDBACK_TIMES[version - 1]
        ):
            self.issues.append(f"{where}: unexpected V feedback")
            return
        self.feedback_versions.append(version)
        proposals = self.versions[version]
        requested = sum(item["cost"] for p in proposals.values() for item in p["items"])
        missing = sorted(self.agents - set(proposals))
        if missing:
            status = "INCOMPLETE"
        else:
            status = "OVER_BUDGET" if requested > self.metadata.budget else "WITHIN_BUDGET"
        savings = []
        unmet = []
        for agent_id, proposal in proposals.items():
            chosen = {item["job_id"]: item for item in proposal["items"]}
            for alternative in proposal["disclosed_alternatives"]:
                item = chosen.get(alternative["job_id"])
                if item is not None and alternative["cost"] < item["cost"]:
                    savings.append(
                        {
                            "agent_id": agent_id,
                            "job_id": alternative["job_id"],
                            "option_id": alternative["option_id"],
                            "saving": item["cost"] - alternative["cost"],
                        }
                    )
            # V runs before submission opens, so no prerequisite can have completed yet.
            unmet += [
                {"agent_id": agent_id, "job_id": job_id}
                for job_id in chosen
                if any(r not in chosen for r in self.metadata.requires.get(job_id, ()))
            ]
        rebuilt = {
            "plan_version": version,
            "budget": self.metadata.budget,
            "requested_total": requested,
            "overage": max(requested - self.metadata.budget, 0),
            "agent_totals": {
                agent: sum(item["cost"] for item in p["items"]) for agent, p in proposals.items()
            },
            "disclosed_savings": savings,
            "unmet_requires": unmet,
            "missing_plans": missing,
            "status": status,
        }

        def canonical(value: dict[str, Any]) -> str:
            return json.dumps(
                {
                    k: sorted(map(json.dumps, v)) if isinstance(v, list) else v
                    for k, v in value.items()
                },
                sort_keys=True,
            )

        if canonical(dict(entry.detail)) != canonical(rebuilt):
            self.issues.append(f"{where}: V feedback differs from the rebuilt version")

    def check_off_plan(self, entry: LogEntry, where: str) -> None:
        """Rebuild the off-plan mark of every own, valid submission after an agreement."""
        if not self.variant.structured:
            return
        expected: dict[str, Any] = {}
        agent_id = entry.agent_id or ""
        job = self.metadata.catalog.get(entry.job_id or "")
        valid = job is not None and job["owner"] == agent_id and entry.option_id in job["options"]
        if self.agreed_items is not None and valid:
            expected = {
                "plan_version": max(self.versions),
                "off_plan": (entry.job_id, entry.option_id) not in self.agreed_items[agent_id],
            }
        logged = {
            key: entry.detail[key] for key in ("plan_version", "off_plan") if key in entry.detail
        }
        if logged != expected:
            self.issues.append(f"{where}: off-plan mark differs from the agreed plan")

    def confirm(self, entry: LogEntry, where: str) -> None:
        version = entry.detail.get("plan_version")
        final = max(self.versions, default=None)
        if (
            entry.time != CONFIRM_TIME
            or type(version) is not int
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
        if agreed:
            self.agreed_items = {
                agent: {(i["job_id"], i["option_id"]) for i in proposal["items"]}
                for agent, proposal in self.versions[version].items()
            }
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

    def expect_release(self, refusal: LogEntry) -> None:
        """Under G, a budget refusal of a pair in the agreed plan must release the plan."""
        if (
            self.variant.guard
            and self.agreed_items is not None
            and not self.released
            and (refusal.job_id, refusal.option_id)
            in self.agreed_items.get(refusal.agent_id or "", ())
        ):
            self.pending_release = refusal

    @property
    def release_required(self) -> bool:
        # The release rule of G (decisions.md, 25.11.2026) came within vbc-1: older vbc-1
        # journals have no releases, later ones do. From vbc-2 on a release is mandatory.
        return self.metadata.protocol_version != "vbc-1" or self.vbc1_guard_release is True

    def require_pending_release(self, entry: LogEntry, where: str) -> None:
        if self.pending_release is not None and entry.event_type != "plan_released":
            if self.release_required:
                self.issues.append(f"{where}: agreed plan was not released after a budget refusal")
            self.pending_release = None

    def release(self, entry: LogEntry, where: str) -> None:
        cause = self.pending_release
        if (
            cause is None
            or (self.metadata.protocol_version == "vbc-1" and self.vbc1_guard_release is False)
            or entry.agent_id != cause.agent_id
            or entry.seq != cause.seq + 1
            or entry.time != cause.time
            or entry.result != "ok"
            or entry.detail
            or any(
                v is not None for v in (entry.request_id, entry.job_id, entry.option_id, entry.cost)
            )
        ):
            self.issues.append(f"{where}: plan released without a budget refusal of the plan")
        else:
            self.released = True
        self.pending_release = None

    def guard_blocks(self, entry: LogEntry) -> bool:
        return (
            self.variant.guard
            and self.agreed_items is not None
            and not self.released
            and (entry.job_id, entry.option_id)
            not in self.agreed_items.get(entry.agent_id or "", ())
        )

    def finish(self) -> None:
        if self.pending_release is not None and self.release_required:
            self.issues.append("agreed plan was not released after a budget refusal")
        if not self.variant.structured:
            return
        if len(self.versions) != len(SNAPSHOT_TIMES):
            self.issues.append(f"expected {len(SNAPSHOT_TIMES)} plan versions")
        if self.agreement_rows != 1:
            self.issues.append(f"expected one agreement row, found {self.agreement_rows}")
        if self.variant.verify and self.feedback_versions != [1, 2]:
            self.issues.append(
                f"expected V feedback for versions 1 and 2, found {self.feedback_versions}"
            )


def _submission_result(
    entry: LogEntry,
    metadata: EpisodeMetadata,
    plans: _PlanAudit,
    accepted_jobs: set[str],
    finished_jobs: set[str],
    headroom: int,
) -> ToolStatus:
    job_id = entry.job_id or ""
    job = metadata.catalog.get(job_id)
    if job is None:
        return ToolStatus.UNKNOWN_JOB
    if job["owner"] != entry.agent_id:
        return ToolStatus.NOT_OWNER
    option = _catalog_option(metadata, entry)
    if option is None:
        return ToolStatus.UNKNOWN_OPTION
    if plans.guard_blocks(entry):
        return ToolStatus.PLAN_MISMATCH
    if job_id in accepted_jobs:
        return ToolStatus.JOB_ALREADY_ACCEPTED
    if entry.time < metadata.submission_open_at[job["owner"]]:
        return ToolStatus.SUBMISSION_NOT_OPEN
    if not finished_jobs.issuperset(metadata.requires.get(job_id, ())):
        return ToolStatus.PREREQUISITE_NOT_COMPLETED
    if entry.time + metadata.commit_delay + option["duration"] > metadata.horizon:
        return ToolStatus.TOO_LATE
    if option["cost"] > headroom:
        return ToolStatus.INSUFFICIENT_BUDGET
    return ToolStatus.ACCEPTED


def audit_episode(
    metadata: EpisodeMetadata,
    entries: Iterable[LogEntry],
    *,
    require_complete: bool = False,
    vbc1_guard_release: bool | None = None,
) -> AuditReport:
    """Check current journals or declare the guard rule of a known vbc-1 cohort."""
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
    log = tuple(entries)
    plans = _PlanAudit(metadata, variant, issues, vbc1_guard_release)
    # The environment can also be driven directly, without scheduler decision limits.
    scheduled = bool(metadata.protocol_version) and (
        require_complete or any(entry.event_type in ("decision", "episode_end") for entry in log)
    )
    schedule = _ScheduleAudit(metadata, variant, issues, scheduled=scheduled)
    submissions: dict[str, LogEntry] = {}
    phase_counts = {
        agent: {"preparation": 0, "execution": 0} for agent in metadata.submission_open_at
    }
    endings = 0
    for index, entry in enumerate(log):
        where = f"seq {entry.seq} ({entry.event_type})"
        plans.require_pending_release(entry, where)
        schedule.observe(entry, where)
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
            if (
                entry.time != metadata.horizon
                or entry.result != "complete"
                or entry.detail.get("turns") != phase_counts
            ):
                issues.append(f"{where}: invalid episode completion record")
        if endings and entry.event_type != "episode_end":
            issues.append(f"{where}: event after episode completion")
        request_id = entry.request_id
        if entry.time < last_time:
            issues.append(f"{where}: time moved backwards")
        last_time = max(last_time, entry.time)

        verified_result = None
        if entry.event_type in ("submit", "submit_replayed"):
            prior = submissions.get(request_id or "")
            if entry.event_type == "submit_replayed":
                visible = (
                    "unknown_job"
                    if prior is not None and prior.result == "not_owner"
                    else prior.result
                    if prior is not None
                    else None
                )
                if prior is None or not _same_submission(prior, entry) or entry.result != visible:
                    issues.append(f"{where}: replay differs from the original submission")
            elif prior is not None or entry.result == "request_id_conflict":
                if (
                    prior is None
                    or _same_submission(prior, entry)
                    or entry.result != "request_id_conflict"
                    or entry.cost is not None
                ):
                    issues.append(f"{where}: incorrect request-id conflict")
            else:
                if request_id is None:
                    issues.append(f"{where}: missing submission request id")
                else:
                    submissions[request_id] = entry
                if metadata.catalog and metadata.protocol_version:
                    option = _catalog_option(metadata, entry)
                    expected_cost = option["cost"] if option is not None else None
                    if entry.cost != expected_cost:
                        issues.append(f"{where}: cost differs from the catalog")
                    headroom = budget - spent - (held if reserving else 0)
                    verified_result = _submission_result(
                        entry, metadata, plans, accepted_jobs, finished_jobs, headroom
                    )
                    if entry.result != verified_result:
                        if verified_result is ToolStatus.PLAN_MISMATCH:
                            issues.append(
                                f"{where}: {entry.job_id}/{entry.option_id} outside agreed plan"
                            )
                        issues.append(
                            f"{where}: submission result {entry.result} differs from "
                            f"rebuilt {verified_result.value}"
                        )
            if entry.event_type == "submit" and entry.result != "request_id_conflict":
                plans.check_off_plan(entry, where)
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
            if reserving:
                held += entry.cost or 0

        elif entry.event_type == "submit" and entry.result == "plan_mismatch":
            plan_mismatches += 1

        elif entry.event_type == "submit" and entry.result == "insufficient_budget":
            headroom = budget - spent - (held if reserving else 0)
            if entry.cost is None or entry.cost <= headroom:
                issues.append(f"{where}: budget refusal although the cost fits the remainder")
            if verified_result is ToolStatus.INSUFFICIENT_BUDGET:
                plans.expect_release(entry)

        elif entry.event_type == "plan_released":
            plans.release(entry, where)

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
        elif entry.event_type == "plan_feedback":
            plans.feedback(entry, where)
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
    if (require_complete or endings) and metadata.protocol_version:
        schedule.finish()
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
        tool_statuses=schedule.actions,
        removed_alternatives=plans.removed,
    )
