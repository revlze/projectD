"""Send one assessment request to a green agent and save its result artifact.

  uv run --group agentbeats python -m agentbeats.client http://127.0.0.1:9009/ \
      --agent http://127.0.0.1:9019/ --config '{"split": "dev", "profiles": ["dev_s1_01"]}'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role, TaskState, TextPart


async def assess(green_url: str, request: dict) -> tuple[str, list[dict]]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(600, connect=30)) as http:
        card = await A2ACardResolver(httpx_client=http, base_url=green_url).get_agent_card()
        card.url = green_url
        client = ClientFactory(ClientConfig(httpx_client=http, streaming=True)).create(card)
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=json.dumps(request)))],
            message_id=uuid4().hex,
        )
        task = None
        async for event in client.send_message(message):
            if isinstance(event, tuple):
                task, update = event
                status = getattr(update, "status", None)
                if status is not None and status.message is not None:
                    for part in status.message.parts:
                        if isinstance(part.root, TextPart):
                            print(f"[{status.state.value}] {part.root.text}", file=sys.stderr)
        if task is None:
            raise RuntimeError("green agent returned no task")
        data = [
            p.root.data
            for artifact in task.artifacts or []
            for p in artifact.parts
            if isinstance(p.root, DataPart)
        ]
        return task.status.state.value, data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("green_url")
    parser.add_argument("--agent", required=True, help="participant URL")
    parser.add_argument("--peer", help="optional second participant URL")
    parser.add_argument("--config", default="{}", help="assessment config as JSON")
    parser.add_argument("--out", type=Path, help="write the result JSON here")
    args = parser.parse_args(argv)
    participants = {"agent": args.agent} | ({"peer": args.peer} if args.peer else {})
    request = {"participants": participants, "config": json.loads(args.config)}
    state, data = asyncio.run(assess(args.green_url, request))
    output = {"status": state, "results": data}
    text = json.dumps(output, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    for result in data:
        print(json.dumps(result.get("summary"), indent=2))
    return 0 if state == TaskState.completed.value else 1


if __name__ == "__main__":
    raise SystemExit(main())
