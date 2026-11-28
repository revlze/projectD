"""AgentBeats green/purple agents over real A2A HTTP servers, with a scripted model."""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("a2a")
import httpx
import uvicorn
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import DataPart, Message, Part, Role, TaskState, TextPart

from agentbeats import green, purple
from agentbeats.assessment import (
    DATA_ROOT,
    Assessment,
    AssessmentConfig,
    ConfigError,
    select_episodes,
)
from agentbeats.wire import parse_response
from project_d.agents.llm_client import ChatResponse
from project_d.experiments.matrix import load_manifest


class ScriptClient:
    """Deterministic, history-dependent choices that exercise valid and invalid calls."""

    def chat(self, messages, tools) -> ChatResponse:
        names = [tool["function"]["name"] for tool in tools]
        if "skip_round" in names:
            name, args = "skip_round", {}
        elif "submit_job" in names and len(messages) % 4 == 0:
            name, args = "finish", {}
        elif "send_message" in names and len(messages) % 5 == 0:
            name, args = "send_message", {"agent_id": "B", "text": "plan?"}
        elif "list_jobs" in names and len(messages) % 3 == 0:
            name, args = "list_jobs", {}
        else:
            name, args = "wait_until", {"target_time": 40}
        call = {
            "id": "x",
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)},
        }
        return ChatResponse(
            {"role": "assistant", "content": "", "tool_calls": [call]}, "tool_calls"
        )


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _serve(app) -> tuple[str, uvicorn.Server]:
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.monotonic() + 10
    while not server.started:
        assert time.monotonic() < deadline, "server did not start"
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}/", server


@pytest.fixture
def agents():
    servers = []

    def start(app_card, executor) -> str:
        handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
        url, server = _serve(
            A2AStarletteApplication(agent_card=app_card, http_handler=handler).build()
        )
        servers.append(server)
        return url

    yield start
    for server in servers:
        server.should_exit = True


async def _assess(green_url: str, request: dict) -> tuple[str, list[dict]]:
    async with httpx.AsyncClient(timeout=120) as http:
        card = await A2ACardResolver(httpx_client=http, base_url=green_url).get_agent_card()
        card.url = green_url
        client = ClientFactory(ClientConfig(httpx_client=http, streaming=True)).create(card)
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=json.dumps(request)))],
            message_id="m1",
        )
        task = None
        async for event in client.send_message(message):
            task = event[0] if isinstance(event, tuple) else task
        data = [
            p.root.data
            for a in task.artifacts or []
            for p in a.parts
            if isinstance(p.root, DataPart)
        ]
        return task.status.state, data


CONFIG = {
    "split": "dev",
    "profiles": ["dev_s1_01"],
    "variants": ["A/F", "U/VBC"],
    "repeats": [0, 2],
    "workers": 2,
}


def _local(config: dict, tmp_path: Path) -> dict:
    assessment = Assessment(
        AssessmentConfig.parse(config), {"A": "agent", "B": "agent"}, output_dir=tmp_path
    )
    return assessment.run({"agent": ScriptClient()})


def test_remote_episodes_match_local_run(agents, tmp_path: Path) -> None:
    purple_url = agents(
        purple.agent_card("http://unused/", "script"), purple.PurpleExecutor(ScriptClient())
    )
    green_url = agents(green.agent_card("http://unused/"), green.GreenExecutor())
    state, data = asyncio.run(
        _assess(green_url, {"participants": {"agent": purple_url}, "config": CONFIG})
    )
    assert state == TaskState.completed
    [result] = data
    local = _local(CONFIG, tmp_path)
    assert result["summary"]["episodes"] == 4
    assert result["summary"]["failed"] == 0
    # Same journals byte for byte: the A2A hop changes nothing in the environment.
    remote_journals = {r["episode"]: r["journal_sha256"] for r in result["episodes"]}
    local_journals = {r["episode"]: r["journal_sha256"] for r in local["episodes"]}
    assert remote_journals == local_journals
    assert all(r["U_star"] > 0 for r in result["episodes"])


def test_peer_role_and_unreachable_participant(agents) -> None:
    purple_url = agents(
        purple.agent_card("http://unused/", "script"), purple.PurpleExecutor(ScriptClient())
    )
    green_url = agents(green.agent_card("http://unused/"), green.GreenExecutor())
    dead = f"http://127.0.0.1:{_free_port()}/"
    config = CONFIG | {"variants": ["A/N"], "repeats": [0]}
    state, data = asyncio.run(
        _assess(green_url, {"participants": {"agent": purple_url, "peer": dead}, "config": config})
    )
    assert state == TaskState.completed
    [row] = data[0]["episodes"]
    assert row["failure_kind"] == "transport"
    assert row["score"] == 0.0
    assert data[0]["roles"] == {"A": "agent", "B": "peer"}


def test_bad_request_is_rejected(agents) -> None:
    green_url = agents(green.agent_card("http://unused/"), green.GreenExecutor())
    state, _ = asyncio.run(
        _assess(green_url, {"participants": {"agent": "http://x/"}, "config": {"variant": "A/F"}})
    )
    assert state == TaskState.rejected


def test_empty_shard_is_rejected(agents) -> None:
    green_url = agents(green.agent_card("http://unused/"), green.GreenExecutor())
    config = {"num_instances": 2, "num_shards": 4, "shard_index": 3}
    state, _ = asyncio.run(
        _assess(green_url, {"participants": {"agent": "http://x/"}, "config": config})
    )
    assert state == TaskState.rejected


class SlowClient(ScriptClient):
    def chat(self, messages, tools) -> ChatResponse:
        time.sleep(0.05)
        return super().chat(messages, tools)


def test_cancel_stops_new_episodes(agents) -> None:
    purple_url = agents(
        purple.agent_card("http://unused/", "slow"), purple.PurpleExecutor(SlowClient())
    )
    executor = green.GreenExecutor()
    green_url = agents(green.agent_card("http://unused/"), executor)
    config = CONFIG | {"repeats": [0, 1, 2, 3], "workers": 1}

    async def run() -> str:
        async with httpx.AsyncClient(timeout=60) as http:
            card = await A2ACardResolver(httpx_client=http, base_url=green_url).get_agent_card()
            card.url = green_url
            client = ClientFactory(ClientConfig(httpx_client=http, streaming=True)).create(card)
            request = {"participants": {"agent": purple_url}, "config": config}
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=json.dumps(request)))],
                message_id="c1",
            )
            async for event in client.send_message(message):
                task = event[0] if isinstance(event, tuple) else None
                if task is not None and task.status.state == TaskState.working:
                    from a2a.types import TaskIdParams

                    cancelled = await client.cancel_task(TaskIdParams(id=task.id))
                    return cancelled.status.state
        return "not-cancelled"

    assert asyncio.run(run()) == TaskState.canceled
    deadline = time.monotonic() + 30
    while executor.stops and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not executor.stops, "the assessment kept running after cancel"


def test_selection_truncates_then_shards() -> None:
    manifest = load_manifest(DATA_ROOT)
    full = select_episodes(AssessmentConfig(), manifest)
    assert len(full) == 28 * 4
    assert {s.split for s in full} == {"test"}
    cut = AssessmentConfig(num_instances=10, num_shards=3, shard_index=1)
    assert [s.name for s in select_episodes(cut, manifest)] == [s.name for s in full[:10][1::3]]
    shards = [
        select_episodes(AssessmentConfig(num_shards=4, shard_index=i), manifest) for i in range(4)
    ]
    assert sorted(s.name for shard in shards for s in shard) == sorted(s.name for s in full)


@pytest.mark.parametrize(
    "raw",
    [
        {"variants": ["A/X"]},
        {"split": "train"},
        {"repeats": [4]},
        {"shard_index": 2, "num_shards": 2},
        {"workers": 0},
        {"profiles": ["nope"]},
        {"extra": 1},
        {"profiles": [123]},
        {"profiles": ["test_s0_01", "test_s0_01"]},
        {"workers": True},
    ],
)
def test_invalid_config(raw: dict) -> None:
    with pytest.raises(ConfigError):
        select_episodes(AssessmentConfig.parse(raw), load_manifest(DATA_ROOT))


def test_response_parsing_accepts_common_shapes() -> None:
    expected = {"type": "function", "function": {"name": "finish", "arguments": "{}"}}
    shapes = [
        (
            [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{"function": {"name": "finish", "arguments": {}}}],
                    }
                }
            ],
            [],
        ),
        ([{"tool_calls": [{"name": "finish", "arguments": {}}]}], []),
        ([], ['{"name": "finish", "arguments": {}}']),
        ([], ['```json\n{"tool_calls": [{"name": "finish"}]}\n```']),
    ]
    for data, texts in shapes:
        message, _, _ = parse_response(data, texts)
        assert message["tool_calls"] == [expected]
    prose, _, _ = parse_response([], ["I will wait."])
    assert "tool_calls" not in prose and prose["content"] == "I will wait."


def test_purple_config_from_env() -> None:
    config = purple.config_from_env({"PURPLE_PROVIDER": "mistral"})
    assert config.api_key_env == "LLM_API_KEY"
    assert config.model == "deepseek-v4-1-flash-1017"
    assert config.base_url == "https://api.mistral.ai/v1"
    local = purple.config_from_env({"PURPLE_PROVIDER": "ollama", "PURPLE_MODEL": "m"})
    assert local.api_key_env is None
    with pytest.raises(ValueError):
        purple.config_from_env({"PURPLE_PROVIDER": "openai-compatible"})
