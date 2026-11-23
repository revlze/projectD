"""Shared-budget environment: what each action does to the state.

The scheduler decides when actions run. B0/B1 check the balance at submission and charge later
without re-checking; B2/B3 check and reserve in one indivisible operation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from project_d.environment.actions import (
    Action,
    Finish,
    GetBalance,
    GetStatus,
    ListJobs,
    ReadMessages,
    SendMessage,
    SubmitJob,
    ToolResult,
    ToolStatus,
    WaitUntil,
)
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import Job, JobStatus, Option, RunConfig, Scenario, ScenarioError
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
        case ListJobs() | GetBalance() | GetStatus() | ReadMessages() | Finish():
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
        case _:
            return False


class Environment:
    def __init__(self, scenario: Scenario, config: RunConfig) -> None:
        self.scenario = config.apply(scenario)
        self.config = config
        self.mode = config.mode

        agent_ids = [agent.agent_id for agent in self.scenario.agents]
        if config.first_agent not in agent_ids:
            raise ScenarioError(f"first_agent {config.first_agent!r} is not in {agent_ids}")
        self.processing_order: tuple[str, ...] = (
            config.first_agent,
            *(a for a in agent_ids if a != config.first_agent),
        )
        self.submission_open_at = config.open_times(agent_ids)

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
        self._next_request = 0
        self._next_message = 0
        self._inboxes: dict[str, list[_Message]] = {a: [] for a in agent_ids}
        self._waiting: dict[str, int] = {}
        self._finished: set[str] = set()
        self._last_request: dict[str, dict[str, str]] = {}

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
        )

    def job_status(self, job_id: str) -> JobStatus:
        return self._jobs[job_id].status

    def is_ready(self, agent_id: str) -> bool:
        return agent_id not in self._finished and agent_id not in self._waiting

    def unread_count(self, agent_id: str) -> int:
        return len(self._inboxes[agent_id])

    def advance_to(self, time: int) -> None:
        """Run every event due by ``time``, then wake agents whose wait has expired."""
        if time < self._now:
            raise ValueError(f"time cannot move backwards: {time} < {self._now}")
        for event in self._queue.pop_due(time):
            self._now = event.time
            self._dispatch(event)
        self._now = time
        for agent_id, target in list(self._waiting.items()):
            if target <= time:
                del self._waiting[agent_id]
                self._record("wake", "target_reached", agent_id=agent_id)

    def execute(self, agent_id: str, action: Action) -> ToolResult:
        if agent_id not in self._inboxes:
            raise KeyError(f"unknown agent {agent_id!r}")
        if agent_id in self._finished:
            return self._refuse(agent_id, "tool_call", ToolStatus.AGENT_FINISHED)
        if not _well_formed(action):
            return self._refuse(
                agent_id, "invalid_action", ToolStatus.INVALID_ACTION, {"action": repr(action)}
            )
        match action:
            case ListJobs():
                return self._list_jobs(agent_id)
            case GetBalance():
                return self._respond(agent_id, "get_balance", {"available": self.available})
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
            case Finish():
                self._finished.add(agent_id)
                self._waiting.pop(agent_id, None)
                return self._respond(agent_id, "finish")
        raise AssertionError(f"unhandled action: {action!r}")  # pragma: no cover

    def own_jobs(self, agent_id: str) -> list[dict[str, Any]]:
        """The agent's catalog and job statuses, without hidden values."""
        return [
            {
                "job_id": record.job.job_id,
                "status": record.status.value,
                "options": [
                    {"option_id": o.option_id, "cost": o.cost, "duration": o.duration}
                    for o in record.job.options
                ],
            }
            for record in self._jobs.values()
            if record.owner == agent_id
        ]

    def _list_jobs(self, agent_id: str) -> ToolResult:
        return self._respond(agent_id, "list_jobs", {"jobs": self.own_jobs(agent_id)})

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

        request_id = action.request_id or self._new_request_id()
        record = self._jobs.get(action.job_id)
        option = record.job.option(action.option_id) if record else None
        refusal = self._refusal(agent_id, record, option)

        if refusal is not None:
            # The journal keeps the true reason; the agent must not learn that a foreign job exists.
            visible = ToolStatus.UNKNOWN_JOB if refusal is ToolStatus.NOT_OWNER else refusal
            result = self._result(agent_id, visible, {"request_id": request_id})
            self._record(
                "submit",
                refusal.value,
                agent_id=agent_id,
                request_id=request_id,
                job_id=action.job_id,
                option_id=action.option_id,
                cost=option.cost if option else None,
            )
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
        if record.status is not JobStatus.NOT_STARTED:
            return ToolStatus.JOB_ALREADY_ACCEPTED
        if self._now < self.submission_open_at[agent_id]:
            return ToolStatus.SUBMISSION_NOT_OPEN
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
            detail={"commit_at": commit_at},
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
            },
        )

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

        deliver_at = self._now + max(1, self.scenario.message_delay)
        message = _Message(self._next_message, agent_id, action.to, action.text, self._now)
        self._next_message += 1
        self._queue.push(deliver_at, EventKind.DELIVER, message)
        data = {"message_id": message.message_id, "deliver_at": deliver_at}
        self._record(
            "send_message",
            ToolStatus.OK.value,
            agent_id=agent_id,
            detail={**data, "to": action.to, "text": action.text},
        )
        return self._result(agent_id, ToolStatus.OK, data)

    def _read(self, agent_id: str) -> ToolResult:
        if not self.mode.messaging:
            return self._refuse(agent_id, "read_messages", ToolStatus.MESSAGING_DISABLED)
        messages = [
            {"from": m.sender, "text": m.text, "sent_at": m.sent_at}
            for m in self._inboxes[agent_id]
        ]
        self._inboxes[agent_id] = []
        return self._respond(agent_id, "read_messages", {"messages": messages})

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
        if self._waiting.pop(message.recipient, None) is not None:
            self._record("wake", "message", agent_id=message.recipient)

    def _new_request_id(self) -> str:
        while True:
            request_id = f"r{self._next_request}"
            self._next_request += 1
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
    ) -> ToolResult:
        self._record(event_type, status.value, agent_id=agent_id, detail=detail)
        return self._result(agent_id, status)

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
                detail=detail or {},
            )
        )
