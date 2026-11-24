"""Thin client for OpenAI-compatible chat completions (Ollama by default)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


class LLMTransportError(RuntimeError):
    """The model server failed. This is never an agent decision or a budget refusal."""


@dataclass(frozen=True)
class LLMConfig:
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.3
    seed: int | None = None
    max_tokens: int = 512
    reasoning_effort: str | None = "none"
    timeout_s: float = 300.0
    retries: int = 2
    retry_backoff_s: float = 1.0


@dataclass(frozen=True)
class ChatResponse:
    message: dict[str, Any]
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    latency_s: float = 0.0


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse: ...


class OpenAICompatibleClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def build_payload(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        # tool_choice is deliberately absent: Ollama's compatibility endpoint does not support it.
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "tools": tools,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }
        if self.config.seed is not None:
            payload["seed"] = self.config.seed
        if self.config.reasoning_effort is not None:
            payload["reasoning_effort"] = self.config.reasoning_effort
        return payload

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse:
        body = json.dumps(self.build_payload(messages, tools), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.config.retries + 1):
            if attempt:
                time.sleep(self.config.retry_backoff_s * attempt)
            started = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout_s) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                return self._parse(raw, time.monotonic() - started)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code < 500:
                    detail = exc.read().decode("utf-8", errors="replace")[:500]
                    raise LLMTransportError(f"HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                last_error = exc
        raise LLMTransportError(f"model server failed: {last_error!r}") from last_error

    @staticmethod
    def _parse(raw: dict[str, Any], latency_s: float) -> ChatResponse:
        try:
            choice = raw["choices"][0]
            message = choice["message"]
            if not isinstance(message, dict):
                raise TypeError("message must be an object")
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMTransportError(f"malformed response: {str(raw)[:300]}") from exc
        return ChatResponse(message, choice.get("finish_reason"), raw.get("usage") or {}, latency_s)
