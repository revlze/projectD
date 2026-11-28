"""Green (assessor) A2A agent: runs Project D episodes against participant agents.

Request (from the AgentBeats gateway): {"participants": {"agent": URL, "peer"?: URL},
"config": {...}}. With only ``agent``, the participant plays both users (self-play).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import threading

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    DataPart,
    InvalidRequestError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import get_message_text, new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from pydantic import BaseModel, HttpUrl, ValidationError

from agentbeats.assessment import (
    BENCHMARK,
    DEFAULT_VARIANTS,
    ROLES,
    Assessment,
    AssessmentConfig,
    Cancelled,
    ConfigError,
)
from agentbeats.remote import A2ASession, RemoteChatClient

log = logging.getLogger("project_d.green")
HEARTBEAT_S = 60.0
TERMINAL = {TaskState.completed, TaskState.canceled, TaskState.failed, TaskState.rejected}


class EvalRequest(BaseModel):
    participants: dict[str, HttpUrl]
    config: dict = {}


def parse_eval_request(text: str, data: list[dict]) -> EvalRequest:
    candidates = [*data]
    with contextlib.suppress(json.JSONDecodeError):
        candidates.append(json.loads(text))
    for value in candidates:
        if isinstance(value, dict) and "participants" in value:
            return EvalRequest.model_validate(value)
    raise ConfigError("expected {'participants': {...}, 'config': {...}}")


class GreenExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.stops: dict[str, threading.Event] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message = context.message
        if message is None:
            raise ServerError(error=InvalidRequestError(message="missing message"))
        task = context.current_task
        if task is not None and task.status.state in TERMINAL:
            raise ServerError(error=InvalidRequestError(message=f"task {task.id} is finished"))
        if task is None:
            task = new_task(message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        def say(text: str):
            return new_agent_text_message(text, task.context_id, task.id)

        data = [p.root.data for p in message.parts if isinstance(p.root, DataPart)]
        try:
            request = parse_eval_request(get_message_text(message), data)
            unknown = set(request.participants) - set(ROLES)
            if "agent" not in request.participants or unknown:
                roles = sorted(request.participants)
                raise ConfigError(f"participants must be 'agent' and optional 'peer', got {roles}")
            config = AssessmentConfig.parse(request.config)
            peer = "peer" if "peer" in request.participants else "agent"
            assessment = Assessment(config, roles={"A": "agent", "B": peer})
            planned = len(assessment.plan())
        except (ConfigError, ValidationError) as exc:
            await updater.reject(say(f"Invalid assessment request: {exc}"))
            return

        await updater.start_work(say(f"{BENCHMARK}: {planned} episodes, config {config}"))
        stop = self.stops.setdefault(task.id, threading.Event())
        session = await A2ASession.open()
        clients = {
            role: RemoteChatClient(session, str(url)) for role, url in request.participants.items()
        }
        loop = asyncio.get_running_loop()
        progress = asyncio.Queue()

        def on_episode(done: int, total: int, row: dict) -> None:
            text = f"[{done}/{total}] {row['episode']}: score={row['score']:.3f}"
            if row.get("failure"):
                text += f" failure={row['failure_kind']}: {row['failure']}"
            log.info(text)
            loop.call_soon_threadsafe(progress.put_nowait, text)

        async def report() -> None:
            # Progress for the run log; a 330 s silent run through gateway v0.3 also completed.
            while True:
                try:
                    text = await asyncio.wait_for(progress.get(), HEARTBEAT_S)
                except TimeoutError:
                    text = "running"
                await updater.update_status(TaskState.working, say(text))

        reporter = asyncio.create_task(report())
        try:
            result = await asyncio.to_thread(assessment.run, clients, on_episode, stop)
        except Cancelled:
            log.info("assessment %s cancelled", task.id)
            return
        except Exception as exc:
            log.exception("assessment failed")
            await updater.failed(say(f"Assessment failed: {exc!r}"))
            return
        finally:
            reporter.cancel()
            self.stops.pop(task.id, None)
            await session.close()
        summary = result["summary"]
        await updater.add_artifact(
            parts=[
                Part(
                    root=TextPart(
                        text=f"score={summary['score']} over {summary['episodes']} episodes"
                    )
                ),
                Part(root=DataPart(data=result)),
            ],
            name="Result",
        )
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Stop starting new episodes; running ones finish their current turns."""
        stop = self.stops.get(context.task_id or "")
        if stop is None:
            raise ServerError(error=UnsupportedOperationError(message="no running assessment"))
        stop.set()
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel(
            new_agent_text_message("Cancelled", context.context_id, context.task_id)
        )


def agent_card(url: str) -> AgentCard:
    skill = AgentSkill(
        id="shared-budget-coordination",
        name="Shared-budget coordination assessment",
        description=(
            "Two agents with private goals share one compute budget. Each episode runs a "
            "fixed scenario under a communication/execution protocol and is scored by an "
            "exact audit: safe utility U_safe / U* (zero if the budget is overrun)."
        ),
        tags=["coordination", "multi-agent", "safety", "benchmark"],
        examples=[
            json.dumps(
                {
                    "participants": {"agent": "http://purple:9009/"},
                    "config": {"variants": list(DEFAULT_VARIANTS), "split": "test"},
                }
            )
        ],
    )
    return AgentCard(
        name="Project D shared-budget assessor",
        description=(
            "Green agent for the Project D benchmark of LLM coordination over a shared budget."
        ),
        url=url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Project D green agent")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--card-url")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    handler = DefaultRequestHandler(agent_executor=GreenExecutor(), task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(
        agent_card=agent_card(args.card_url or f"http://{args.host}:{args.port}/"),
        http_handler=handler,
    )
    uvicorn.run(app.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
