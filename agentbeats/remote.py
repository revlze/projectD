"""A ChatClient whose answers come from a remote A2A agent.

The simulator and LLMPolicy are synchronous and run in worker threads; A2A calls are
coroutines scheduled on the server's event loop, so one HTTP client serves every episode.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import AgentCard, DataPart, Message, Part, Role, Task, TaskState, TextPart

from agentbeats.wire import INSTRUCTIONS, parse_response, request_payload
from project_d.agents.llm_client import ChatResponse, HTTPAttempt, HTTPTrace, LLMTransportError

CALL_TIMEOUT_S = 300.0


def parts_content(parts: list[Part]) -> tuple[list[dict[str, Any]], list[str]]:
    data, texts = [], []
    for part in parts:
        if isinstance(part.root, DataPart):
            data.append(part.root.data)
        elif isinstance(part.root, TextPart):
            texts.append(part.root.text)
    return data, texts


@dataclass
class A2ASession:
    """Shared HTTP client and resolved agent cards for one assessment."""

    loop: asyncio.AbstractEventLoop
    http: httpx.AsyncClient
    cards: dict[str, AgentCard]
    card_lock: asyncio.Lock

    @classmethod
    async def open(cls, timeout_s: float = CALL_TIMEOUT_S) -> A2ASession:
        http = httpx.AsyncClient(timeout=httpx.Timeout(timeout_s, connect=30.0))
        return cls(asyncio.get_running_loop(), http, {}, asyncio.Lock())

    async def close(self) -> None:
        await self.http.aclose()

    async def card(self, url: str) -> AgentCard:
        async with self.card_lock:
            return await self._card(url)

    async def _card(self, url: str) -> AgentCard:
        if url not in self.cards:
            card = await A2ACardResolver(httpx_client=self.http, base_url=url).get_agent_card()
            # Keep talking to the address we were given: behind the AgentBeats gateway the
            # card may advertise an internal container address.
            card.url = url
            self.cards[url] = card
        return self.cards[url]

    async def ask(self, url: str, payload: dict[str, Any]) -> tuple[list[dict], list[str]]:
        card = await self.card(url)
        client = ClientFactory(ClientConfig(httpx_client=self.http, streaming=False)).create(card)
        message = Message(
            role=Role.user,
            parts=[
                Part(root=TextPart(text=INSTRUCTIONS)),
                Part(root=DataPart(data=payload)),
            ],
            message_id=uuid4().hex,
        )
        last = None
        async for event in client.send_message(message):
            last = event
        if isinstance(last, Message):
            return parts_content(last.parts)
        if isinstance(last, tuple) and isinstance(last[0], Task):
            task = last[0]
            if task.status.state not in (TaskState.completed, TaskState.input_required):
                raise LLMTransportError(f"participant task ended in {task.status.state.value}")
            parts = [p for artifact in task.artifacts or [] for p in artifact.parts]
            if task.status.message is not None:
                parts += task.status.message.parts
            return parts_content(parts)
        raise LLMTransportError("participant sent no message or task")


class RemoteChatClient:
    """Sync ChatClient bound to one participant URL; retries transient failures."""

    def __init__(self, session: A2ASession, url: str, retries: int = 2) -> None:
        self.session = session
        self.url = url
        self.retries = retries

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse:
        payload = request_payload(messages, tools)
        digest = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        attempts: list[HTTPAttempt] = []
        started = time.monotonic()
        for attempt in range(self.retries + 1):
            begin = time.monotonic()
            future = asyncio.run_coroutine_threadsafe(
                self.session.ask(self.url, payload), self.session.loop
            )
            try:
                data, texts = future.result(CALL_TIMEOUT_S + 30)
            except Exception as exc:  # network, protocol or participant failure
                future.cancel()
                # A timed-out call may still finish later; consume its outcome silently.
                future.add_done_callback(lambda f: f.cancelled() or f.exception())
                retry = 2.0 * (attempt + 1) if attempt < self.retries else None
                attempts.append(
                    HTTPAttempt(type(exc).__name__, time.monotonic() - begin, retry_delay_s=retry)
                )
                if retry is None:
                    trace = HTTPTrace(digest, tuple(attempts), time.monotonic() - started)
                    raise LLMTransportError(
                        f"participant {self.url} failed: {exc!r}", trace
                    ) from exc
                time.sleep(retry)
                continue
            latency = time.monotonic() - begin
            attempts.append(HTTPAttempt("response", latency))
            message, finish, usage = parse_response(data, texts)
            trace = HTTPTrace(digest, tuple(attempts), time.monotonic() - started)
            return ChatResponse(message, finish, usage, latency, trace)
        raise AssertionError("unreachable")
