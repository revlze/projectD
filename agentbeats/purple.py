"""Baseline participant (purple) agent: one OpenAI-compatible chat call per decision.

This is the LLM policy of the Project D experiments behind A2A. Configuration comes from the
environment so that keys never enter manifests or logs:

  PURPLE_PROVIDER   ollama | mimo | mistral | openai-compatible (default: mistral)
  PURPLE_MODEL      model name (default: deepseek-v4-1-flash-1017, as in E2)
  PURPLE_BASE_URL   override the provider endpoint
  LLM_API_KEY       API key for hosted providers
  PURPLE_TEMPERATURE, PURPLE_REASONING_EFFORT, PURPLE_SEED   as in the experiments
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from dataclasses import replace

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    DataPart,
    Part,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_parts_message
from a2a.utils.errors import ServerError

from agentbeats.remote import parts_content
from agentbeats.wire import PROTOCOL, parse_request
from project_d.agents.llm_client import (
    ChatClient,
    LLMConfig,
    LLMTransportError,
    OpenAICompatibleClient,
)
from project_d.agents.providers import PROVIDERS, provider_config

log = logging.getLogger("project_d.purple")
API_KEY_ENV = "LLM_API_KEY"


def config_from_env(env: dict[str, str] | None = None) -> LLMConfig:
    env = dict(os.environ if env is None else env)
    provider = env.get("PURPLE_PROVIDER", "mistral")
    effort = env.get("PURPLE_REASONING_EFFORT", "none")
    base = LLMConfig(
        model=env.get("PURPLE_MODEL", "deepseek-v4-1-flash-1017"),
        temperature=float(env.get("PURPLE_TEMPERATURE", "0.3")),
        reasoning_effort=None if effort in ("", "omit") else effort,
        seed=int(env["PURPLE_SEED"]) if env.get("PURPLE_SEED") else None,
    )
    if provider == "openai-compatible":
        if not env.get("PURPLE_BASE_URL"):
            raise ValueError("openai-compatible requires PURPLE_BASE_URL")
        config = replace(base, base_url=env["PURPLE_BASE_URL"], max_tokens=2048)
    elif provider in PROVIDERS:
        config = provider_config(provider, base, base_url=env.get("PURPLE_BASE_URL"))
    else:
        raise ValueError(f"unknown PURPLE_PROVIDER {provider!r}")
    if provider != "ollama":
        config = replace(config, api_key_env=API_KEY_ENV)
    return config


class PurpleExecutor(AgentExecutor):
    def __init__(self, client: ChatClient) -> None:
        self.client = client

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message = context.message
        data, texts = parts_content(message.parts) if message else ([], [])
        request = parse_request(data, texts)
        if request is None:
            reply = [Part(root=TextPart(text=f"Expected a {PROTOCOL} request."))]
        else:
            try:
                response = await asyncio.to_thread(
                    self.client.chat, request["messages"], request["tools"]
                )
            except LLMTransportError as exc:
                # Let the assessor record a transport failure instead of an agent decision.
                log.warning("model call failed: %s", exc)
                raise
            reply = [
                Part(
                    root=DataPart(
                        data={
                            "message": response.message,
                            "finish_reason": response.finish_reason,
                            "usage": response.usage,
                        }
                    )
                )
            ]
        await event_queue.enqueue_event(
            new_agent_parts_message(reply, context.context_id, context.task_id)
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())


def agent_card(url: str, model: str) -> AgentCard:
    return AgentCard(
        name="Project D baseline LLM agent",
        description=(
            f"Stateless tool-calling agent ({model}) for the Project D shared-budget benchmark."
        ),
        url=url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="chat-tools",
                name="Choose one tool call",
                description=f"Answers a {PROTOCOL} request with one assistant message.",
                tags=["tool-use", "coordination"],
            )
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Project D baseline purple agent")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9019)
    parser.add_argument("--card-url")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    config = config_from_env()
    handler = DefaultRequestHandler(
        agent_executor=PurpleExecutor(OpenAICompatibleClient(config)),
        task_store=InMemoryTaskStore(),
    )
    app = A2AStarletteApplication(
        agent_card=agent_card(args.card_url or f"http://{args.host}:{args.port}/", config.model),
        http_handler=handler,
    )
    uvicorn.run(app.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
