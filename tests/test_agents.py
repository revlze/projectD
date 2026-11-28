from __future__ import annotations

import dataclasses
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest

from project_d.agents.llm_client import (
    LLMConfig,
    LLMTransportError,
    OpenAICompatibleClient,
)
from project_d.agents.providers import provider_config
from project_d.agents.runner import smoke_check
from project_d.agents.tools import parse_tool_call
from project_d.environment.actions import InvalidCall, SubmitJob, WaitUntil


def test_submit_parser_does_not_accept_cost_or_request_id() -> None:
    assert parse_tool_call("submit_job", {"job_id": "a", "option_id": "full"}) == SubmitJob(
        "a", "full"
    )
    for extra in ({"cost": 0}, {"request_id": "forged"}):
        assert isinstance(
            parse_tool_call("submit_job", {"job_id": "a", "option_id": "full", **extra}),
            InvalidCall,
        )


@pytest.mark.parametrize("arguments", ({"target_time": True}, {"target_time": 1.5}, "broken"))
def test_wait_parser_rejects_bad_types(arguments) -> None:
    assert isinstance(parse_tool_call("wait_until", arguments), InvalidCall)
    assert parse_tool_call("wait_until", {"target_time": 40}) == WaitUntil(40)


class _Handler(BaseHTTPRequestHandler):
    payloads: ClassVar[list[dict]] = []
    statuses: ClassVar[list[int]] = []
    auth: ClassVar[list[str | None]] = []

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        type(self).payloads.append(json.loads(self.rfile.read(length)))
        type(self).auth.append(self.headers.get("Authorization"))
        status = type(self).statuses.pop(0) if type(self).statuses else 200
        body = json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "function": {"name": "list_jobs", "arguments": "{}"},
                                }
                            ],
                        },
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 1},
            }
        ).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def server():
    _Handler.payloads = []
    _Handler.statuses = []
    _Handler.auth = []
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}/v1"
    httpd.shutdown()
    httpd.server_close()


def test_client_sends_supported_fields_only(server: str) -> None:
    client = OpenAICompatibleClient(LLMConfig(base_url=server, seed=7, temperature=0.3))
    outcome = smoke_check(client)
    payload = _Handler.payloads[0]
    assert outcome["ok"] is True
    assert (payload["seed"], payload["temperature"], payload["stream"]) == (7, 0.3, False)
    assert payload["reasoning_effort"] == "none"
    assert "tool_choice" not in payload


def test_client_retries_server_errors(server: str) -> None:
    _Handler.statuses = [500]
    client = OpenAICompatibleClient(LLMConfig(base_url=server, retry_backoff_s=0))
    assert client.chat([], []).usage["prompt_tokens"] == 5
    assert len(_Handler.payloads) == 2


def test_client_does_not_retry_client_errors(server: str) -> None:
    _Handler.statuses = [404]
    client = OpenAICompatibleClient(LLMConfig(base_url=server, retry_backoff_s=0))
    with pytest.raises(LLMTransportError, match="HTTP 404"):
        client.chat([], [])
    assert len(_Handler.payloads) == 1


def test_client_reports_unreachable_server() -> None:
    config = LLMConfig(base_url="http://127.0.0.1:9/v1", retries=0, timeout_s=1)
    with pytest.raises(LLMTransportError):
        OpenAICompatibleClient(config).chat([], [])


def test_client_sends_key_from_environment(server: str, monkeypatch) -> None:
    monkeypatch.setenv("TEST_PROVIDER_KEY", "secret")
    config = LLMConfig(base_url=server, api_key_env="TEST_PROVIDER_KEY")
    OpenAICompatibleClient(config).chat([], [])
    assert _Handler.auth == ["Bearer secret"]
    assert "secret" not in json.dumps(dataclasses.asdict(config))


def test_client_requires_configured_key(server: str, monkeypatch) -> None:
    monkeypatch.delenv("TEST_PROVIDER_KEY", raising=False)
    config = LLMConfig(base_url=server, api_key_env="TEST_PROVIDER_KEY")
    with pytest.raises(LLMTransportError, match="TEST_PROVIDER_KEY"):
        OpenAICompatibleClient(config).chat([], [])
    assert _Handler.payloads == []


def test_local_client_sends_no_key(server: str) -> None:
    OpenAICompatibleClient(LLMConfig(base_url=server)).chat([], [])
    assert _Handler.auth == [None]


def test_client_waits_out_rate_limits(server: str) -> None:
    _Handler.statuses = [429, 429]
    config = LLMConfig(base_url=server, retries=0, rate_limit_backoff_s=0)
    assert OpenAICompatibleClient(config).chat([], []).usage["prompt_tokens"] == 5
    assert len(_Handler.payloads) == 3


def test_client_gives_up_on_persistent_rate_limit(server: str) -> None:
    _Handler.statuses = [429, 429, 429]
    config = LLMConfig(base_url=server, rate_limit_retries=2, rate_limit_backoff_s=0)
    with pytest.raises(LLMTransportError, match="429"):
        OpenAICompatibleClient(config).chat([], [])


def test_mistral_profile_adapts_seed_and_call_ids() -> None:
    config = provider_config("mistral", LLMConfig(seed=3))
    history = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_0_0",
                    "type": "function",
                    "function": {"name": "list_jobs", "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_0_0", "content": "{}"},
    ]
    payload = OpenAICompatibleClient(config).build_payload(history, [])
    call_id = payload["messages"][0]["tool_calls"][0]["id"]
    assert payload["random_seed"] == 3 and "seed" not in payload
    assert payload["max_tokens"] == 2048
    assert len(call_id) == 9 and call_id.isalnum()
    assert payload["messages"][1]["tool_call_id"] == call_id
    assert history[0]["tool_calls"][0]["id"] == "call_0_0"


def test_ollama_profile_keeps_baseline_payload() -> None:
    config = provider_config("ollama", LLMConfig(seed=3))
    assert config == LLMConfig(seed=3)


def test_mistral_metadata_marks_call_source_only() -> None:
    client = OpenAICompatibleClient(provider_config("mistral", LLMConfig()))
    for messages in ([{"role": "user", "content": "test"}], [{"role": "tool", "content": "t"}], []):
        assert client.build_payload(messages, [])["metadata"] == {"call_source": "vibe_code"}
    local = OpenAICompatibleClient(provider_config("ollama", LLMConfig()))
    assert "metadata" not in local.build_payload([{"role": "user", "content": "test"}], [])


@pytest.mark.parametrize("provider", ("ollama", "mimo"))
def test_other_providers_do_not_send_metadata(provider: str) -> None:
    client = OpenAICompatibleClient(provider_config(provider, LLMConfig()))
    assert "metadata" not in client.build_payload([], [])


def test_mistral_metadata_is_sent_and_reused_on_retry(server: str, monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-only")
    config = provider_config(
        "mistral", LLMConfig(), base_url=server, retry_backoff_s=0, rate_limit_backoff_s=0
    )
    _Handler.statuses = [429, 500]
    response = OpenAICompatibleClient(config).chat([], [])
    assert len(_Handler.payloads) == 3
    assert _Handler.payloads[0] == _Handler.payloads[1] == _Handler.payloads[2]
    assert response.http is not None
    assert response.http.metadata == _Handler.payloads[0]["metadata"]
