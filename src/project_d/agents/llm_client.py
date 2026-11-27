"""Thin client for OpenAI-compatible chat completions (Ollama by default)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from typing import Any, Protocol


DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


@dataclass(frozen=True)
class HTTPAttempt:
    outcome: str
    latency_s: float
    status_code: int | None = None
    request_id: str | None = None
    retry_delay_s: float | None = None


@dataclass(frozen=True)
class HTTPTrace:
    payload_sha256: str
    attempts: tuple[HTTPAttempt, ...]
    elapsed_s: float
    response_id: str | None = None
    response_model: str | None = None
    metadata: dict[str, str] | None = None


class LLMTransportError(RuntimeError):
    """The model server failed before yielding an agent response."""

    def __init__(self, message: str, trace: HTTPTrace | None = None) -> None:
        super().__init__(message)
        self.trace = trace


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
    # Hosted providers. Only the variable name is stored, so manifests cannot leak the key.
    api_key_env: str | None = None
    seed_field: str | None = "seed"
    tool_call_id_style: str = "plain"
    rate_limit_retries: int = 8
    rate_limit_backoff_s: float = 2.0
    request_metadata: bool = False


@dataclass(frozen=True)
class ChatResponse:
    message: dict[str, Any]
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    latency_s: float = 0.0
    http: HTTPTrace | None = None


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse: ...


class OpenAICompatibleClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def build_payload(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        # tool_choice is deliberately absent: Ollama's compatibility endpoint does not support it.
        if self.config.tool_call_id_style == "alnum9":
            messages = _alnum9_call_ids(messages)
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "tools": tools,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }
        if self.config.seed is not None and self.config.seed_field:
            payload[self.config.seed_field] = self.config.seed
        if self.config.reasoning_effort is not None:
            payload["reasoning_effort"] = self.config.reasoning_effort
        if self.config.request_metadata:
            # mistral metadata
            payload["metadata"] = {"call_source": "vibe_code"}
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key_env:
            key = os.environ.get(self.config.api_key_env)
            if not key:
                raise LLMTransportError(f"{self.config.api_key_env} is not set")
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse:
        payload = self.build_payload(messages, tools)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        payload_sha256 = hashlib.sha256(body).hexdigest()
        attempts: list[HTTPAttempt] = []
        request_started = time.monotonic()

        def trace(raw: dict[str, Any] | None = None) -> HTTPTrace:
            return HTTPTrace(
                payload_sha256,
                tuple(attempts),
                time.monotonic() - request_started,
                raw.get("id") if raw else None,
                raw.get("model") if raw else None,
                payload.get("metadata"),
            )

        try:
            headers = self._headers()
        except LLMTransportError as exc:
            raise LLMTransportError(str(exc), trace()) from exc
        request = urllib.request.Request(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        failures = 0
        throttled = 0
        while True:
            started = time.monotonic()
            status_code = None
            request_id = None
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout_s) as response:
                    status_code = getattr(response, "status", 200)
                    request_id = getattr(response, "headers", {}).get("x-request-id")
                    raw = json.loads(response.read().decode("utf-8"))
                latency = time.monotonic() - started
                parsed = self._parse(raw, latency)
                attempts.append(HTTPAttempt("response", latency, status_code, request_id))
                return replace(parsed, http=trace(raw))
            except urllib.error.HTTPError as exc:
                status_code = exc.code
                request_id = exc.headers.get("x-request-id") if exc.headers else None
                if exc.code == 429:
                    throttled += 1
                    delay = self.config.rate_limit_backoff_s * 2 ** (throttled - 1)
                    retry = (
                        _retry_after(exc, delay)
                        if throttled <= self.config.rate_limit_retries
                        else None
                    )
                    attempts.append(
                        HTTPAttempt(
                            "rate_limited",
                            time.monotonic() - started,
                            status_code,
                            request_id,
                            retry,
                        )
                    )
                    if retry is None:
                        raise LLMTransportError("HTTP 429: rate limit persisted", trace()) from exc
                    time.sleep(retry)
                    continue
                if exc.code < 500:
                    attempts.append(
                        HTTPAttempt(
                            "http_error", time.monotonic() - started, status_code, request_id
                        )
                    )
                    detail = exc.read().decode("utf-8", errors="replace")
                    print(f"HTTP {exc.code}: {detail}")
                    raise LLMTransportError(f"HTTP {exc.code}: {detail}", trace()) from exc
                outcome, cause = "http_error", exc
            except LLMTransportError as exc:
                attempts.append(
                    HTTPAttempt(
                        "malformed_response", time.monotonic() - started, status_code, request_id
                    )
                )
                raise LLMTransportError(
                    str(exc), trace(raw if isinstance(raw, dict) else None)
                ) from exc
            except (
                urllib.error.URLError,
                TimeoutError,
                UnicodeDecodeError,
                json.JSONDecodeError,
                OSError,
            ) as exc:
                if isinstance(exc, TimeoutError) or (
                    isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, TimeoutError)
                ):
                    outcome = "timeout"
                elif isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError)):
                    outcome = "invalid_encoding"
                else:
                    outcome = "network_error"
                cause = exc
            failures += 1
            retry = (
                self.config.retry_backoff_s * failures if failures <= self.config.retries else None
            )
            attempts.append(
                HTTPAttempt(outcome, time.monotonic() - started, status_code, request_id, retry)
            )
            if retry is None:
                detail = f"HTTP {status_code}" if outcome == "http_error" else outcome
                raise LLMTransportError(f"model server failed: {detail}", trace()) from cause
            time.sleep(retry)

    @staticmethod
    def _parse(raw: dict[str, Any], latency_s: float) -> ChatResponse:
        try:
            choice = raw["choices"][0]
            message = choice["message"]
            usage = raw.get("usage") or {}
            if not isinstance(message, dict) or not isinstance(usage, dict):
                raise TypeError("message and usage must be objects")
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMTransportError("malformed model response") from exc
        return ChatResponse(message, choice.get("finish_reason"), usage, latency_s)


def _retry_after(exc: urllib.error.HTTPError, fallback: float) -> float:
    try:
        delay = float(exc.headers.get("Retry-After", "")) if exc.headers else fallback
        return max(delay, 0.0) if math.isfinite(delay) else fallback
    except (TypeError, ValueError):
        return fallback


def _alnum9(call_id: str) -> str:
    return hashlib.sha256(call_id.encode("utf-8")).hexdigest()[:9]


def _alnum9_call_ids(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mistral accepts only 9-character alphanumeric call ids; map ours deterministically."""
    mapped = []
    for message in messages:
        message = dict(message)
        if message.get("tool_calls"):
            message["tool_calls"] = [
                {**call, "id": _alnum9(str(call.get("id", "")))} for call in message["tool_calls"]
            ]
        if "tool_call_id" in message:
            message["tool_call_id"] = _alnum9(str(message["tool_call_id"]))
        mapped.append(message)
    return mapped
