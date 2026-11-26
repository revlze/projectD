"""Shared-budget environment: what each action does to the state.

The scheduler decides when actions run. U checks at submission and charges later;
A checks and reserves in one indivisible operation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

from project_d.environment.actions import (
    Action,
    ConfirmPlan,
    Finish,
    GetBalance,
    GetStatus,
    ListJobs,
    ProposePlan,
    ReadMessages,
    SendMessage,
    SkipRound,
    SubmitJob,
    ToolResult,
    ToolStatus,
    WaitUntil,
)
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import (
    CONFIRM_TIME,
    FEEDBACK_TIMES,
    PROPOSE_TIMES,
    SNAPSHOT_TIMES,
    Comm,
    Job,
    JobStatus,
    Option,
    RunConfig,
    Scenario,
    ScenarioError,
)
from project_d.simulation.events import Event, EventKind, EventQueue


@dataclass
class _JobRecord:
    owner: str
    job: Job
    status: JobStatus = JobStatus.NOT_STARTED
    option_id: str | None = None


@dataclass(frozen=True)
class _Request:
    agent_id: str
    job_id: str
    option_id: str
    result: ToolResult


@dataclass(frozen=True)
class _Accepted:
    request_id: str
    agent_id: str
    job_id: str
    option: Option


@dataclass(frozen=True)
class _Message:
    message_id: int
    sender: str
    recipient: str
    text: str
    sent_at: int


def _well_formed(action: Any) -> bool:
    match action:
        case ListJobs() | GetBalance() | GetStatus() | ReadMessages() | Finish() | SkipRound():
            return True
        case SubmitJob():
            return (
                isinstance(action.job_id, str)
                and isinstance(action.option_id, str)
                and (action.request_id is None or isinstance(action.request_id, str))
            )
        case SendMessage():
            return isinstance(action.to, str) and isinstance(action.text, str)
        case WaitUntil():
            return isinstance(action.target_time, int) and not isinstance(action.target_time, bool)
        case ProposePlan():
            if not isinstance(action.items, tuple) or not isinstance(
                action.disclosed_alternatives, tuple
            ):
                return False
            pairs = (*action.items, *action.disclosed_alternatives)
            return isinstance(action.note, str) and all(
                isinstance(pair, tuple)
                and len(pair) == 2
                and all(isinstance(part, str) for part in pair)
                for pair in pairs
            )
        case ConfirmPlan():
            return isinstance(action.plan_version, int) and not isinstance(
                action.plan_version, bool
            )
        case _:
            return False


_FOREIGN_OR_UNKNOWN = "указана работа не из твоего каталога list_jobs."
# What the agent sees for an invalid proposal (system_spec.md, section 6).
PLAN_ERROR_TEXT = {
    "unknown_job": _FOREIGN_OR_UNKNOWN,
    "not_owner": _FOREIGN_OR_UNKNOWN,
    "unknown_option": "в твоей работе нет указанного option_id.",
    "two_options_for_job": "в items больше одного варианта одной работы.",
    "duplicate_alternative": "одна альтернатива указана дважды.",
    "chosen_option_as_alternative": (
        "вариант из items указан и в disclosed_alternatives; "
        "альтернативами указывай только невыбранные варианты."
    ),
}

PLAN_RELEASED_NOTICE = (
    "PLAN_RELEASED: ограничение согласованного плана снято из-за отказа по бюджету."
)


class Environment:
    def __init__(self, scenario: Scenario, config: RunConfig) -> None:
        self.scenario = config.apply(scenario)
        self.config = config
        self.mode = config.mode
        self.variant = config.variant

        agent_ids = [agent.agent_id for agent in self.scenario.agents]
        if config.first_agent not in agent_ids:
            raise ScenarioError(f"first_agent {config.first_agent!r} is not in {agent_ids}")
        self.processing_order: tuple[str, ...] = (
            config.first_agent,
            *(a for a in agent_ids if a != config.first_agent),
        )
        self.submission_open_at = config.open_times(agent_ids)
        limit = self.scenario.agent_turn_limit
        preparation = min(12, max(0, limit - min(12, limit)))
        if len(self.variant.slot_times) > preparation:
            raise ScenarioError(
                f"{self.variant.value} needs {len(self.variant.slot_times)} preparation decisions "
                f"for its slots, the turn limit leaves {preparation}"
            )

        self._jobs = {
            job.job_id: _JobRecord(agent.agent_id, job)
            for agent in self.scenario.agents
            for job in agent.jobs
        }
        self._queue = EventQueue()
        self._now = 0
        self._spent = 0
        self._held = 0
        self._log: list[LogEntry] = []
        self._requests: dict[str, _Request] = {}
        self._next_request: dict[str, int] = {}
        self._next_message = 0
        self._inboxes: dict[str, list[_Message]] = {a: [] for a in agent_ids}
        self._surfaced: dict[str, set[int]] = {a: set() for a in agent_ids}
        self._sent_counts: dict[str, int] = dict.fromkeys(agent_ids, 0)
        self._waiting: dict[str, int] = {}
        self._finished: set[str] = set()
        self._last_request: dict[str, dict[str, str]] = {}
        self._round_senders: dict[int, set[str]] = {t: set() for t in self.variant.round_times}
        self._round_skippers: dict[int, set[str]] = {t: set() for t in self.variant.round_times}
        self._proposals: dict[str, dict[str, Any]] = {}
        self._versions: dict[int, dict[str, dict[str, Any]]] = {}
        self._feedback: dict[int, dict[str, Any]] = {}
        self._confirmations: dict[str, int] = {}
        # G stops binding once an agreed submission is refused for lack of budget.
        self._plan_released = False
        # Protocol state shown at each agent's next decision (agreement, release of G).
        self._notices: dict[str, list[str]] = {agent: [] for agent in self.processing_order}
        # Agreed pairs per agent. Recorded with and without G; only G enforces them.
        self._agreed: dict[str, set[tuple[str, str]]] | None = None
        self._agreed_version: int | None = None
        self._schedule_phases()

    def _schedule_phases(self) -> None:
        for time in self.variant.round_times:
            self._queue.push(time + 1, EventKind.ROUND_CLOSE, time)
        if self.variant.structured:
            for time in SNAPSHOT_TIMES:
                self._queue.push(time, EventKind.PLAN_SNAPSHOT)
            if self.variant.verify:
                for time in FEEDBACK_TIMES:
                    self._queue.push(time, EventKind.PLAN_FEEDBACK)
            self._queue.push(self.config.submission_open_at, EventKind.AGREEMENT)

    @property
    def now(self) -> int:
        return self._now

    @property
    def spent(self) -> int:
        return self._spent

    @property
    def held(self) -> int:
        return self._held

    @property
    def available(self) -> int:
        return self.scenario.budget - self._spent - self._held

    @property
    def log(self) -> list[LogEntry]:
        return list(self._log)

    @property
    def metadata(self) -> EpisodeMetadata:
        seed = self.config.environment_seed
        return EpisodeMetadata(
            scenario_id=self.scenario.scenario_id,
            mode=self.mode.value,
            budget=self.scenario.budget,
            horizon=self.scenario.horizon,
            commit_delay=self.scenario.commit_delay,
            message_delay=self.scenario.message_delay,
            agent_turn_limit=self.scenario.agent_turn_limit,
            environment_seed=self.scenario.seed if seed is None else seed,
            first_agent=self.config.first_agent,
            role_swap=self.config.role_swap,
            start_gap=self.config.start_gap,
            submission_open_at=dict(self.submission_open_at),
            variant=self.variant.value,
            preparation_turn_limit=min(12, max(0, self.scenario.agent_turn_limit - 12)),
            execution_turn_limit=min(12, self.scenario.agent_turn_limit),
            protocol_version="vbc-3" if self.variant.structured else "baseline-phases-1",
            requires={
                job_id: list(record.job.requires)
                for job_id, record in self._jobs.items()
                if record.job.requires
            },
            catalog={
                job_id: {
                    "owner": record.owner,
                    "options": {
                        o.option_id: {"cost": o.cost, "duration": o.duration}
                        for o in record.job.options
                    },
                }
                for job_id, record in self._jobs.items()
            },
        )

    def job_status(self, job_id: str) -> JobStatus:
        return self._jobs[job_id].status

    def is_ready(self, agent_id: str) -> bool:
        return agent_id not in self._finished and agent_id not in self._waiting

    def record_decision(self, agent_id: str, phase: str, used: int, limit: int) -> None:
        self._record(
            "decision",
            "issued",
            agent_id=agent_id,
            detail={"phase": phase, "phase_turn": used + 1, "phase_limit": limit},
        )

    def suspend_until(self, agent_id: str, target: int, reason: str) -> None:
        """Advance scheduling without manufacturing a policy action or spending a decision."""
        if agent_id not in self._finished and target > self._now:
            self._waiting[agent_id] = target
            self._record("auto_wait", reason, agent_id=agent_id, detail={"until": target})

    def finish_episode(self, turns: dict[str, dict[str, int]]) -> None:
        self._record("episode_end", "complete", detail={"turns": turns})

    def unread_count(self, agent_id: str) -> int:
        surfaced = self._surfaced[agent_id]
        return sum(m.message_id not in surfaced for m in self._inboxes[agent_id])

    def advance_to(self, time: int) -> None:
        """Run every event due by ``time``, then wake agents whose wait has expired."""
        if time < self._now:
            raise ValueError(f"time cannot move backwards: {time} < {self._now}")
        # Step through each tick so that wakes are resolved at their earliest time on a jump.
        for tick in range(self._now + 1, time + 1) or (time,):
            for event in self._queue.pop_due(tick):
                self._now = event.time
                self._dispatch(event)
            self._now = tick
            for agent_id, target in list(self._waiting.items()):
                if target <= tick:
                    del self._waiting[agent_id]
                    self._record("wake", "target_reached", agent_id=agent_id)
                elif tick in (
                    *self.variant.wake_times,
                    self.config.submission_open_at,
                    self.submission_open_at[agent_id],
                ):
                    del self._waiting[agent_id]
                    self._record("wake", "phase", agent_id=agent_id)

    def execute(self, agent_id: str, action: Action) -> ToolResult:
        if agent_id not in self._inboxes:
            raise KeyError(f"unknown agent {agent_id!r}")
        if agent_id in self._finished:
            return self._refuse(agent_id, "tool_call", ToolStatus.AGENT_FINISHED)
        if not _well_formed(action):
            return self._refuse(
                agent_id, "invalid_action", ToolStatus.INVALID_ACTION, {"action": repr(action)}
            )
        if isinstance(action, Finish) and self._now < self.submission_open_at[agent_id]:
            return self._refuse(agent_id, "finish", ToolStatus.FINISH_NOT_OPEN)
        if isinstance(action, SubmitJob) and self._now < self.submission_open_at[agent_id]:
            return self._submit(agent_id, action)
        slot_actions = {
            "message_round": SendMessage | SkipRound,
            # Waiting in a plan slot keeps the last proposal or withholds confirmation.
            "propose": ProposePlan | WaitUntil,
            "confirm": ConfirmPlan | WaitUntil,
        }
        allowed = slot_actions.get(self.phase() or "")
        if allowed is not None and not isinstance(action, allowed):
            return self._refuse(agent_id, "tool_call", ToolStatus.WRONG_PHASE)
        match action:
            case ListJobs():
                return self._list_jobs(agent_id)
            case GetBalance():
                return self._respond(
                    agent_id,
                    "get_balance",
                    # One pool for both agents; the field names say so (decision D02).
                    {
                        "shared_budget": self.scenario.budget,
                        "shared_available": self.available,
                        "shared_with": [a for a in self.processing_order if a != agent_id],
                    },
                )
            case SubmitJob():
                return self._submit(agent_id, action)
            case GetStatus():
                return self._get_status(agent_id)
            case SendMessage():
                return self._send(agent_id, action)
            case ReadMessages():
                return self._read(agent_id)
            case WaitUntil():
                return self._wait(agent_id, action.target_time)
            case ProposePlan():
                return self._propose(agent_id, action)
            case ConfirmPlan():
                return self._confirm(agent_id, action.plan_version)
            case Finish():
                self._finished.add(agent_id)
                self._waiting.pop(agent_id, None)
                return self._respond(agent_id, "finish")
            case SkipRound():
                if self._now not in self._round_skippers:
                    return self._refuse(agent_id, "skip_round", ToolStatus.WRONG_PHASE)
                if agent_id in self._round_senders[self._now] | self._round_skippers[self._now]:
                    return self._refuse(agent_id, "skip_round", ToolStatus.WRONG_PHASE)
                self._round_skippers[self._now].add(agent_id)
                return self._respond(agent_id, "round_skipped")
        raise AssertionError(f"unhandled action: {action!r}")  # pragma: no cover

    def own_jobs(self, agent_id: str) -> list[dict[str, Any]]:
        """Automatic observations expose only own identifiers and actual states."""
        return [
            {
                "job_id": record.job.job_id,
                "status": record.status.value,
                "option_id": record.option_id,
            }
            for record in self._jobs.values()
            if record.owner == agent_id
        ]

    def _catalog(self, agent_id: str) -> list[dict[str, Any]]:
        """Only list_jobs exposes own variants, costs, durations and dependencies."""
        return [
            {
                "job_id": record.job.job_id,
                "status": record.status.value,
                "options": [
                    {"option_id": o.option_id, "cost": o.cost, "duration": o.duration}
                    for o in record.job.options
                ],
                **({"requires": list(record.job.requires)} if record.job.requires else {}),
            }
            for record in self._jobs.values()
            if record.owner == agent_id
        ]

    def phase(self, time: int | None = None) -> str | None:
        """The scheduled phase at ``time``. It never reveals how many rounds a variant has left."""
        now = self._now if time is None else time
        if now in self.variant.round_times:
            return "message_round"
        if self.variant.structured and now in PROPOSE_TIMES:
            return "propose"
        if self.variant.structured and now == CONFIRM_TIME:
            return "confirm"
        if now >= self.config.submission_open_at:
            return "execution"
        if self.variant.slot_times and now >= self.variant.slot_times[0]:
            return "negotiation_wait"
        return "preparation"

    def take_inbox(self, agent_id: str, *, mark_read: bool = True) -> tuple[dict[str, Any], ...]:
        """Show newly delivered messages in round protocols. read_messages() still returns them."""
        if not self.variant.round_times:
            return ()
        surfaced = self._surfaced[agent_id]
        messages = [m for m in self._inboxes[agent_id] if m.message_id not in surfaced]
        if not messages:
            return ()
        if mark_read:
            surfaced.update(m.message_id for m in messages)
            self._record(
                "message_read",
                ToolStatus.OK.value,
                agent_id=agent_id,
                detail={"message_ids": [m.message_id for m in messages]},
            )
        return tuple({"from": m.sender, "text": m.text, "sent_at": m.sent_at} for m in messages)

    def plan_view(self) -> dict[str, Any] | None:
        """Latest shared revision: disclosed proposals only, plus feedback for that revision."""
        if not self._versions:
            return None
        version = max(self._versions)
        view: dict[str, Any] = {"plan_version": version, "proposals": self._versions[version]}
        if version in self._feedback:
            view["plan_feedback"] = self._feedback[version]
        return deepcopy(view)

    def _list_jobs(self, agent_id: str) -> ToolResult:
        return self._respond(agent_id, "list_jobs", {"jobs": self._catalog(agent_id)})

    def _get_status(self, agent_id: str) -> ToolResult:
        jobs = {
            job_id: {"status": record.status.value, "option_id": record.option_id}
            for job_id, record in self._jobs.items()
            if record.owner == agent_id
        }
        data = {"jobs": jobs, "last_request": self._last_request.get(agent_id)}
        return self._respond(agent_id, "get_status", data)

    def _submit(self, agent_id: str, action: SubmitJob) -> ToolResult:
        if action.request_id is not None and action.request_id in self._requests:
            return self._replay(agent_id, action)

        request_id = action.request_id or self._new_request_id(agent_id)
        record = self._jobs.get(action.job_id)
        option = record.job.option(action.option_id) if record else None
        refusal = self._refusal(agent_id, record, option)

        if refusal is not None:
            # The journal keeps the true reason; the agent must not learn that a foreign job exists.
            visible = ToolStatus.UNKNOWN_JOB if refusal is ToolStatus.NOT_OWNER else refusal
            data: dict[str, Any] = {"request_id": request_id}
            if refusal is ToolStatus.INSUFFICIENT_BUDGET:
                data["shared_available"] = self.available
            elif refusal is ToolStatus.PREREQUISITE_NOT_COMPLETED:
                assert record is not None
                data["waiting_for"] = [
                    required
                    for required in record.job.requires
                    if self._jobs[required].status is not JobStatus.COMPLETED
                ]
            result = self._result(agent_id, visible, data)
            if (
                refusal is ToolStatus.INSUFFICIENT_BUDGET
                and self.variant.guard
                and self._agreed is not None
                and not self._plan_released
                and (action.job_id, action.option_id) in self._agreed[agent_id]
            ):
                self._plan_released = True
                data["plan_released"] = True
            self._record(
                "submit",
                refusal.value,
                agent_id=agent_id,
                request_id=request_id,
                job_id=action.job_id,
                option_id=action.option_id,
                cost=option.cost if option else None,
                detail=self._plan_detail(agent_id, action.job_id, action.option_id),
            )
            if data.get("plan_released"):
                self._record("plan_released", ToolStatus.OK.value, agent_id=agent_id)
                for agent in self.processing_order:
                    self._notices[agent].append(PLAN_RELEASED_NOTICE)
        else:
            assert record is not None and option is not None
            result = self._accept(agent_id, request_id, record, option)

        self._requests[request_id] = _Request(agent_id, action.job_id, action.option_id, result)
        self._last_request[agent_id] = {"request_id": request_id, "result": result.status.value}
        return result

    def _refusal(
        self, agent_id: str, record: _JobRecord | None, option: Option | None
    ) -> ToolStatus | None:
        if record is None:
            return ToolStatus.UNKNOWN_JOB
        if record.owner != agent_id:
            return ToolStatus.NOT_OWNER
        if option is None:
            return ToolStatus.UNKNOWN_OPTION
        # G is checked before the other rules, so an earlier acceptance cannot mask a mismatch.
        if (
            self.variant.guard
            and self._agreed is not None
            and not self._plan_released
            and (record.job.job_id, option.option_id) not in self._agreed[agent_id]
        ):
            return ToolStatus.PLAN_MISMATCH
        if record.status is not JobStatus.NOT_STARTED:
            return ToolStatus.JOB_ALREADY_ACCEPTED
        if self._now < self.submission_open_at[agent_id]:
            return ToolStatus.SUBMISSION_NOT_OPEN
        if any(self._jobs[r].status is not JobStatus.COMPLETED for r in record.job.requires):
            return ToolStatus.PREREQUISITE_NOT_COMPLETED
        if self._now + self.scenario.commit_delay + option.duration > self.scenario.horizon:
            return ToolStatus.TOO_LATE
        headroom = self.scenario.budget - self._spent
        if self.mode.reserves:
            headroom -= self._held
        if headroom < option.cost:
            return ToolStatus.INSUFFICIENT_BUDGET
        return None

    def _accept(
        self, agent_id: str, request_id: str, record: _JobRecord, option: Option
    ) -> ToolResult:
        spent_before, held_before = self._spent, self._held
        if self.mode.reserves:
            self._held += option.cost
        record.status = JobStatus.PENDING
        record.option_id = option.option_id
        commit_at = self._now + self.scenario.commit_delay
        self._record(
            "submit",
            ToolStatus.ACCEPTED.value,
            agent_id=agent_id,
            request_id=request_id,
            job_id=record.job.job_id,
            option_id=option.option_id,
            cost=option.cost,
            spent_before=spent_before,
            held_before=held_before,
            detail={
                "commit_at": commit_at,
                **self._plan_detail(agent_id, record.job.job_id, option.option_id),
            },
        )
        accepted = _Accepted(request_id, agent_id, record.job.job_id, option)
        if self.scenario.commit_delay == 0:
            self._commit(accepted)
        else:
            self._queue.push(commit_at, EventKind.COMMIT, accepted)
        return self._result(
            agent_id,
            ToolStatus.ACCEPTED,
            {
                "request_id": request_id,
                "job_id": record.job.job_id,
                "option_id": option.option_id,
                "cost": option.cost,
                "commit_at": commit_at,
                "completes_at": commit_at + option.duration,
            },
        )

    def _plan_detail(self, agent_id: str, job_id: str, option_id: str) -> dict[str, Any]:
        """Mark submissions against an agreed plan; G=0 records the mismatch without refusing.

        Only own, existing job/option pairs are compared (system_spec.md, section 7).
        """
        record = self._jobs.get(job_id)
        valid = record is not None and record.owner == agent_id and record.job.option(option_id)
        if self._agreed is None or not valid:
            return {}
        return {
            "plan_version": self._agreed_version,
            "off_plan": (job_id, option_id) not in self._agreed.get(agent_id, set()),
        }

    def _replay(self, agent_id: str, action: SubmitJob) -> ToolResult:
        request_id = action.request_id
        assert request_id is not None
        prior = self._requests[request_id]
        same_call = (prior.agent_id, prior.job_id, prior.option_id) == (
            agent_id,
            action.job_id,
            action.option_id,
        )
        if not same_call:
            self._record(
                "submit",
                ToolStatus.REQUEST_ID_CONFLICT.value,
                agent_id=agent_id,
                request_id=request_id,
                job_id=action.job_id,
                option_id=action.option_id,
            )
            return self._result(
                agent_id, ToolStatus.REQUEST_ID_CONFLICT, {"request_id": request_id}
            )
        self._record(
            "submit_replayed",
            prior.result.status.value,
            agent_id=agent_id,
            request_id=request_id,
            job_id=action.job_id,
            option_id=action.option_id,
        )
        return replace(
            prior.result,
            logical_time=self._now,
            data={**prior.result.data, "replayed": True},
        )

    def _send(self, agent_id: str, action: SendMessage) -> ToolResult:
        if not self.mode.messaging:
            return self._refuse(agent_id, "send_message", ToolStatus.MESSAGING_DISABLED)
        if action.to == agent_id or action.to not in self._inboxes:
            return self._refuse(agent_id, "send_message", ToolStatus.INVALID_RECIPIENT)
        if self._now >= self.config.submission_open_at:
            return self._refuse(agent_id, "send_message", ToolStatus.MESSAGING_CLOSED)
        round_number = None
        if self.variant.round_times:
            senders = self._round_senders.get(self._now)
            if senders is None or agent_id in senders | self._round_skippers[self._now]:
                return self._refuse(agent_id, "send_message", ToolStatus.MESSAGING_ROUND_CLOSED)
            senders.add(agent_id)
            round_number = self.variant.round_times.index(self._now) + 1

        deliver_at = self._now + max(1, self.scenario.message_delay)
        message = _Message(self._next_message, agent_id, action.to, action.text, self._now)
        self._next_message += 1
        self._queue.push(deliver_at, EventKind.DELIVER, message)
        # A global id would reveal whether the other agent has already sent something.
        visible_id = self._sent_counts[agent_id]
        self._sent_counts[agent_id] += 1
        data = {"message_id": visible_id, "deliver_at": deliver_at}
        self._record(
            "send_message",
            ToolStatus.OK.value,
            agent_id=agent_id,
            detail={
                "message_id": message.message_id,
                "deliver_at": deliver_at,
                "to": action.to,
                "text": action.text,
                **({"round": round_number} if round_number is not None else {}),
            },
        )
        return self._result(agent_id, ToolStatus.OK, data)

    def _read(self, agent_id: str) -> ToolResult:
        if not self.mode.messaging:
            return self._refuse(agent_id, "read_messages", ToolStatus.MESSAGING_DISABLED)
        if self.variant.comm is not Comm.F:
            return self._refuse(agent_id, "read_messages", ToolStatus.WRONG_PHASE)
        messages = [
            {"from": m.sender, "text": m.text, "sent_at": m.sent_at}
            for m in self._inboxes[agent_id]
        ]
        message_ids = [m.message_id for m in self._inboxes[agent_id]]
        self._inboxes[agent_id] = []
        self._surfaced[agent_id].update(message_ids)
        self._record(
            "read_messages",
            ToolStatus.OK.value,
            agent_id=agent_id,
            detail={"message_ids": message_ids},
        )
        return self._result(agent_id, ToolStatus.OK, {"messages": messages})

    def _plan_entry(self, job_id: str, option_id: str) -> dict[str, Any]:
        option = self._jobs[job_id].job.option(option_id)
        assert option is not None
        return {"job_id": job_id, "option_id": option_id, "cost": option.cost}

    def _plan_error(self, agent_id: str, action: ProposePlan) -> str | None:
        """Journal reason of an invalid proposal; ``PLAN_ERROR_TEXT`` is what the agent sees."""
        for job_id, option_id in (*action.items, *action.disclosed_alternatives):
            record = self._jobs.get(job_id)
            if record is None:
                return "unknown_job"
            if record.owner != agent_id:
                return "not_owner"
            if record.job.option(option_id) is None:
                return "unknown_option"
        item_jobs = [job_id for job_id, _ in action.items]
        if len(item_jobs) != len(set(item_jobs)):
            return "two_options_for_job"
        alternatives = list(action.disclosed_alternatives)
        if len(alternatives) != len(set(alternatives)):
            return "duplicate_alternative"
        if set(alternatives) & set(action.items):
            return "chosen_option_as_alternative"
        return None

    def _propose(self, agent_id: str, action: ProposePlan) -> ToolResult:
        if not self.variant.structured or self._now not in PROPOSE_TIMES:
            return self._refuse(agent_id, "propose_plan", ToolStatus.WRONG_PHASE)
        error = self._plan_error(agent_id, action)
        if error is not None:
            # The journal keeps the true reason. The agent gets the reason too, but unknown and
            # foreign jobs share one text, so it does not learn that a foreign job exists.
            return self._refuse(
                agent_id,
                "propose_plan",
                ToolStatus.INVALID_PLAN,
                {"reason": error},
                data={"error": PLAN_ERROR_TEXT[error]},
            )
        proposal = {
            "items": [self._plan_entry(*pair) for pair in action.items],
            "disclosed_alternatives": [
                self._plan_entry(*pair) for pair in action.disclosed_alternatives
            ],
            "note": action.note,
        }
        self._proposals[agent_id] = proposal
        self._record("propose_plan", ToolStatus.OK.value, agent_id=agent_id, detail=proposal)
        return self._result(agent_id, ToolStatus.OK, {"recorded": True})

    def _confirm(self, agent_id: str, plan_version: int) -> ToolResult:
        if not self.variant.structured or self._now != CONFIRM_TIME:
            return self._refuse(agent_id, "confirm_plan", ToolStatus.WRONG_PHASE)
        final = max(self._versions, default=None)
        if (
            plan_version != final
            or final != len(SNAPSHOT_TIMES)
            or set(self._versions[final]) != set(self.processing_order)
        ):
            return self._refuse(
                agent_id, "confirm_plan", ToolStatus.INVALID_PLAN, {"plan_version": plan_version}
            )
        self._confirmations[agent_id] = plan_version
        data = {"plan_version": plan_version}
        self._record("confirm_plan", ToolStatus.OK.value, agent_id=agent_id, detail=data)
        return self._result(agent_id, ToolStatus.OK, data)

    def _snapshot_plans(self) -> None:
        version = len(self._versions) + 1
        self._versions[version] = {
            agent_id: {
                "items": [dict(item) for item in proposal["items"]],
                "disclosed_alternatives": [
                    dict(item) for item in proposal["disclosed_alternatives"]
                ],
                "note": proposal["note"],
            }
            for agent_id, proposal in self._proposals.items()
        }
        self._record(
            "plan_version",
            ToolStatus.OK.value,
            detail={"plan_version": version, "proposals": self._versions[version]},
        )

    def _publish_feedback(self) -> None:
        version = max(self._versions)
        feedback = self._compute_feedback(version)
        self._feedback[version] = feedback
        self._record("plan_feedback", ToolStatus.OK.value, detail=feedback)

    def _compute_feedback(self, version: int) -> dict[str, Any]:
        """Arithmetic over disclosed proposals only: no value, no ranking, no recommendation."""
        proposals = self._versions[version]
        agent_totals = {
            agent_id: sum(item["cost"] for item in proposal["items"])
            for agent_id, proposal in proposals.items()
        }
        requested = sum(agent_totals.values())
        missing = [agent for agent in self.processing_order if agent not in proposals]
        if missing:
            status = "INCOMPLETE"
        else:
            status = "OVER_BUDGET" if requested > self.scenario.budget else "WITHIN_BUDGET"
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
            for job_id in chosen:
                # Only a flag: the missing prerequisite may be a job its owner has not disclosed.
                if any(
                    required not in chosen
                    and self._jobs[required].status is not JobStatus.COMPLETED
                    for required in self._jobs[job_id].job.requires
                ):
                    unmet.append({"agent_id": agent_id, "job_id": job_id})
        return {
            "plan_version": version,
            "budget": self.scenario.budget,
            "requested_total": requested,
            "overage": max(requested - self.scenario.budget, 0),
            "agent_totals": agent_totals,
            "disclosed_savings": savings,
            "unmet_requires": unmet,
            "missing_plans": missing,
            "status": status,
        }

    def _resolve_agreement(self) -> None:
        final = max(self._versions)
        agents = set(self.processing_order)
        agreed = (
            set(self._versions[final]) == agents
            and set(self._confirmations) == agents
            and set(self._confirmations.values()) == {final}
        )
        if agreed:
            self._agreed_version = final
            self._agreed = {
                agent_id: {(item["job_id"], item["option_id"]) for item in proposal["items"]}
                for agent_id, proposal in self._versions[final].items()
            }
        self._record(
            "agreement",
            "agreed" if agreed else "agreement_failed",
            detail={
                "plan_version": final if agreed else None,
                "confirmations": dict(self._confirmations),
                "enforced": agreed and self.variant.guard,
                "fallback": not agreed and self.variant.guard,
            },
        )
        if agreed:
            notice = f"AGREED: оба агента подтвердили версию #{final}."  # noqa: RUF001
            if self.variant.guard:
                notice += " С открытия подачи среда принимает только заявки из этого плана."  # noqa: RUF001
        else:
            notice = "AGREEMENT_FAILED: общий план не подтверждён."
        for agent in self.processing_order:
            self._notices[agent].append(notice)

    def take_notices(self, agent_id: str) -> tuple[str, ...]:
        notices, self._notices[agent_id] = self._notices[agent_id], []
        return tuple(notices)

    def _wait(self, agent_id: str, target: int) -> ToolResult:
        if not self._now < target <= self.scenario.horizon:
            return self._refuse(agent_id, "wait_until", ToolStatus.INVALID_WAIT)
        self._waiting[agent_id] = target
        return self._respond(
            agent_id,
            "wait_until",
            {"target_time": target, "unread_messages": self.unread_count(agent_id)},
        )

    def _dispatch(self, event: Event) -> None:
        match event.kind:
            case EventKind.COMMIT:
                self._commit(event.payload)
            case EventKind.COMPLETE:
                self._complete(event.payload)
            case EventKind.DELIVER:
                self._deliver(event.payload)
            case EventKind.ROUND_CLOSE:
                for agent_id in self.processing_order:
                    if agent_id not in (
                        self._round_senders[event.payload] | self._round_skippers[event.payload]
                    ):
                        self._record(
                            "round_missed",
                            ToolStatus.OK.value,
                            agent_id=agent_id,
                            detail={"round_time": event.payload},
                        )
            case EventKind.PLAN_SNAPSHOT:
                self._snapshot_plans()
            case EventKind.PLAN_FEEDBACK:
                self._publish_feedback()
            case EventKind.AGREEMENT:
                self._resolve_agreement()

    def _commit(self, accepted: _Accepted) -> None:
        spent_before, held_before = self._spent, self._held
        if self.mode.reserves:
            self._held -= accepted.option.cost
        self._spent += accepted.option.cost
        self._jobs[accepted.job_id].status = JobStatus.RUNNING
        self._record(
            "commit",
            ToolStatus.OK.value,
            agent_id=accepted.agent_id,
            request_id=accepted.request_id,
            job_id=accepted.job_id,
            option_id=accepted.option.option_id,
            cost=accepted.option.cost,
            spent_before=spent_before,
            held_before=held_before,
        )
        self._queue.push(self._now + accepted.option.duration, EventKind.COMPLETE, accepted)

    def _complete(self, accepted: _Accepted) -> None:
        self._jobs[accepted.job_id].status = JobStatus.COMPLETED
        self._record(
            "complete",
            ToolStatus.OK.value,
            agent_id=accepted.agent_id,
            request_id=accepted.request_id,
            job_id=accepted.job_id,
            option_id=accepted.option.option_id,
            cost=accepted.option.cost,
        )

    def _deliver(self, message: _Message) -> None:
        self._inboxes[message.recipient].append(message)
        self._record(
            "message_delivered",
            ToolStatus.OK.value,
            agent_id=message.recipient,
            detail={"message_id": message.message_id, "from": message.sender},
        )
        # Round protocols surface messages at the next slot, so delivery does not spend a turn.
        if (
            self.variant.comm is Comm.F
            and self._now < self.config.submission_open_at
            and self._waiting.pop(message.recipient, None) is not None
        ):
            self._record("wake", "message", agent_id=message.recipient)

    def _new_request_id(self, agent_id: str) -> str:
        # Per-agent numbering: a shared counter would reveal how often the partner submitted.
        while True:
            number = self._next_request.get(agent_id, 0)
            self._next_request[agent_id] = number + 1
            request_id = f"{agent_id}-r{number}"
            if request_id not in self._requests:
                return request_id

    def _result(
        self, agent_id: str, status: ToolStatus, data: dict[str, Any] | None = None
    ) -> ToolResult:
        return ToolResult(status, self._now, self.submission_open_at[agent_id], data or {})

    def _respond(
        self, agent_id: str, event_type: str, data: dict[str, Any] | None = None
    ) -> ToolResult:
        self._record(event_type, ToolStatus.OK.value, agent_id=agent_id)
        return self._result(agent_id, ToolStatus.OK, data)

    def _refuse(
        self,
        agent_id: str,
        event_type: str,
        status: ToolStatus,
        detail: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> ToolResult:
        self._record(event_type, status.value, agent_id=agent_id, detail=detail)
        return self._result(agent_id, status, data)

    def _record(
        self,
        event_type: str,
        result: str,
        *,
        agent_id: str | None = None,
        request_id: str | None = None,
        job_id: str | None = None,
        option_id: str | None = None,
        cost: int | None = None,
        spent_before: int | None = None,
        held_before: int | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self._log.append(
            LogEntry(
                seq=len(self._log),
                scenario_id=self.scenario.scenario_id,
                mode=self.mode.value,
                time=self._now,
                agent_id=agent_id,
                request_id=request_id,
                event_type=event_type,
                job_id=job_id,
                option_id=option_id,
                cost=cost,
                spent_before=self._spent if spent_before is None else spent_before,
                spent_after=self._spent,
                held_before=self._held if held_before is None else held_before,
                held_after=self._held,
                result=result,
                detail=deepcopy(detail) if detail else {},
            )
        )
