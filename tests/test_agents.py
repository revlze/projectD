from __future__ import annotations

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

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        type(self).payloads.append(json.loads(self.rfile.read(length)))
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
