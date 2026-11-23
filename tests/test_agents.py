from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import ClassVar

import pytest

from project_d.agents.llm_client import (
    ChatResponse,
    LLMConfig,
    LLMTransportError,
    OpenAICompatibleClient,
)
from project_d.agents.runner import (
    PILOT_SCENARIOS,
    pilot_config,
    run_llm_episode,
    run_pilot,
    smoke_check,
)
from project_d.agents.tools import parse_tool_call, tool_schemas
from project_d.environment.actions import InvalidCall, SubmitJob, ToolStatus, WaitUntil
from project_d.environment.model import JobStatus, Mode, RunConfig
from project_d.evaluation.audit import audit_episode
from support import make_config, make_scenario

EXAMPLES = Path(__file__).parents[1] / "data" / "examples"


def call(name: str, arguments: object = None, call_id: str = "c") -> ChatResponse:
    text = arguments if isinstance(arguments, str) else json.dumps(arguments or {})
    return ChatResponse(
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": call_id, "function": {"name": name, "arguments": text}}],
        },
        usage={"prompt_tokens": 10, "completion_tokens": 2},
    )


class AgentAwareClient:
    """Plays a per-agent script, identified from the system prompt."""

    def __init__(self, scripts: dict[str, list[ChatResponse]]) -> None:
        self.scripts = {agent: list(script) for agent, script in scripts.items()}
        self.requests: list[tuple[str, list[dict]]] = []

    def chat(self, messages, tools) -> ChatResponse:
        agent = "A" if "агент A и" in messages[0]["content"] else "B"
        self.requests.append((agent, json.loads(json.dumps(messages))))
        script = self.scripts[agent]
        return script.pop(0) if script else call("finish")


class HonestClient:
    """Reads its catalog, waits for the window and submits the first option."""

    def chat(self, messages, tools) -> ChatResponse:
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        if not results:
            return call("list_jobs")
        if len(results) == 1:
            return call("wait_until", {"target_time": results[0]["submission_open_at"]})
        if len(results) == 2:
            job = next(r for r in results if "jobs" in r)["jobs"][0]
            return call(
                "submit_job",
                {"job_id": job["job_id"], "option_id": job["options"][0]["option_id"]},
            )
        return call("finish")


@pytest.mark.parametrize(
    ("name", "arguments", "reason"),
    [
        ("missing_tool", {}, "unknown_tool"),
        ("submit_job", "{bad", "arguments_not_json"),
        ("submit_job", "[1]", "arguments_not_object"),
        ("submit_job", {"job_id": "a"}, "expected_arguments:job_id,option_id"),
        ("submit_job", {"job_id": "a", "option_id": "b", "cost": 0}, "expected_arguments"),
        ("submit_job", {"job_id": 1, "option_id": "b"}, "arguments_must_be_strings"),
        ("wait_until", {"target_time": "13"}, "target_time_must_be_integer"),
        ("wait_until", {"target_time": True}, "target_time_must_be_integer"),
    ],
)
def test_malformed_calls_become_invalid(name, arguments, reason) -> None:
    action = parse_tool_call(name, arguments)
    assert isinstance(action, InvalidCall)
    assert action.reason.startswith(reason)


def test_valid_calls_parse_from_string_and_object() -> None:
    assert parse_tool_call("wait_until", '{"target_time": 13}') == WaitUntil(13)
    assert parse_tool_call("submit_job", {"job_id": "j", "option_id": "o"}) == SubmitJob("j", "o")


def test_model_cannot_supply_request_id() -> None:
    action = parse_tool_call("submit_job", {"job_id": "j", "option_id": "o", "request_id": "x"})
    assert isinstance(action, InvalidCall)


@pytest.mark.parametrize("mode", list(Mode))
def test_message_tools_only_in_communication_modes(mode: Mode) -> None:
    names = {tool["function"]["name"] for tool in tool_schemas(mode)}
    assert ("send_message" in names) is mode.messaging
    assert ("read_messages" in names) is mode.messaging
    assert "wait_until" in names


@pytest.mark.parametrize("mode", list(Mode))
def test_full_llm_episode_with_waiting(mode: Mode) -> None:
    config = RunConfig(mode=mode, submission_open_at=13)
    episode = run_llm_episode(make_scenario(), config, HonestClient())
    assert episode.failure is None
    report = audit_episode(episode.result.metadata, episode.result.log)
    assert report.consistent, report.issues
    assert report.violated is (not mode.reserves)
    assert episode.result.turns_used == {"A": 4, "B": 4}


def test_tool_results_are_threaded_and_value_never_reaches_model() -> None:
    client = AgentAwareClient({"A": [call("list_jobs", call_id="x1")], "B": []})
    run_llm_episode(make_scenario(), make_config(Mode.B0), client)
    a_requests = [messages for agent, messages in client.requests if agent == "A"]
    tool_message = next(m for m in a_requests[1] if m["role"] == "tool")
    assert tool_message["tool_call_id"] == "x1"
    assert "cost" in tool_message["content"]
    assert all("value" not in json.dumps(m) for _, msgs in client.requests for m in msgs)


def test_no_tool_call_is_an_agent_error_without_budget_effect() -> None:
    text = ChatResponse({"role": "assistant", "content": "думаю"})
    client = AgentAwareClient({"A": [text, call("finish")], "B": [call("finish")]})
    episode = run_llm_episode(make_scenario(), make_config(Mode.B2), client)
    assert episode.turns[0].parse_error == "no_tool_call"
    assert episode.result.spent == 0
    assert episode.result.calls_by("A")[0].result.status is ToolStatus.INVALID_ACTION
    second = next(msgs for agent, msgs in client.requests[1:] if agent == "A")
    assert any("не содержал" in str(m["content"]) for m in second)


def test_only_first_of_several_tool_calls_runs() -> None:
    response = ChatResponse(
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "submit_job",
                        "arguments": '{"job_id":"job_a","option_id":"full"}',
                    },
                },
                {"id": "2", "function": {"name": "finish", "arguments": "{}"}},
            ],
        }
    )
    client = AgentAwareClient({"A": [response, call("finish")], "B": [call("finish")]})
    episode = run_llm_episode(make_scenario(), make_config(Mode.B0), client)
    assert episode.turns[0].dropped_tool_calls == 1
    assert episode.result.job_statuses["job_a"] is JobStatus.COMPLETED


def test_transport_failure_voids_episode() -> None:
    class Broken:
        def chat(self, messages, tools):
            raise LLMTransportError("down")

    episode = run_llm_episode(make_scenario(), make_config(Mode.B0), Broken())
    assert episode.result is None
    assert episode.failure == "down"


def test_messages_flow_between_llm_agents() -> None:
    client = AgentAwareClient(
        {
            "A": [
                call("send_message", {"agent_id": "B", "text": "беру 7"}),
                call("finish"),
            ],
            "B": [
                call("wait_until", {"target_time": 13}),
                call("read_messages"),
                call("finish"),
            ],
        }
    )
    config = RunConfig(mode=Mode.B1, submission_open_at=13)
    episode = run_llm_episode(make_scenario(message_delay=2), config, client)
    b_calls = episode.result.calls_by("B")
    assert b_calls[1].time == 2
    assert b_calls[1].result.data["messages"][0]["text"] == "беру 7"


def test_pilot_runs_all_twenty_episodes(tmp_path: Path) -> None:
    summaries = run_pilot(EXAMPLES, tmp_path, HonestClient())
    assert len(summaries) == len(PILOT_SCENARIOS) * 4 == 20
    assert all(s["failure"] is None and not s["audit_issues"] for s in summaries)
    assert not any(s["violated"] for s in summaries if s["episode"].endswith(("B2", "B3")))
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "s1_01_B0.log.jsonl").exists()
    assert (tmp_path / "s1_01_B0.llm.jsonl").exists()


def test_pilot_config_overrides_stale_json_limits() -> None:
    config = pilot_config(Mode.B0)
    assert (config.horizon, config.agent_turn_limit, config.submission_open_at) == (30, 16, 13)


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
