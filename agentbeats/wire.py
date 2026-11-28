"""Turn format between the green agent and a participant (purple) agent.

One A2A message per decision. The green agent keeps each agent's dialogue and sends the
whole OpenAI-style history plus the tools available in the current phase; the participant
answers with one assistant message. Participants are therefore stateless; any agent that can
pick one tool call from a chat history can take part.
"""

from __future__ import annotations

import json
from typing import Any

PROTOCOL = "project-d/chat-tools/v1"

INSTRUCTIONS = (
    "You are one of two agents sharing a compute budget. The data part of this message has "
    f"protocol {PROTOCOL!r}: `messages` is your full dialogue in OpenAI chat format and `tools` "
    "lists the functions you may call now. Reply with a data part "
    '{"message": {"role": "assistant", "content": "...", "tool_calls": [{"type": "function", '
    '"function": {"name": "...", "arguments": "{...}"}}]}} containing exactly one tool call. '
    'A text reply holding the same JSON, or {"name": ..., "arguments": {...}}, is also accepted.'
)


def request_payload(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    return {"protocol": PROTOCOL, "messages": messages, "tools": tools}


def parse_request(data_parts: list[dict[str, Any]], texts: list[str]) -> dict[str, Any] | None:
    """Return the request payload from a data part, or from JSON text as a fallback."""
    candidates = list(data_parts)
    for text in texts:
        try:
            value = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(value, dict):
            candidates.append(value)
    for value in candidates:
        if isinstance(value.get("messages"), list) and isinstance(value.get("tools"), list):
            return value
    return None


def _call(name: Any, arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, str):
        arguments = json.dumps(arguments if arguments is not None else {}, ensure_ascii=False)
    return {"type": "function", "function": {"name": str(name), "arguments": arguments}}


def _normalize_calls(raw: Any) -> list[dict[str, Any]]:
    calls = []
    for call in raw if isinstance(raw, list) else []:
        if not isinstance(call, dict):
            continue
        function = call.get("function") if isinstance(call.get("function"), dict) else call
        if "name" in function:
            calls.append(_call(function["name"], function.get("arguments")))
    return calls


def _as_message(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    wrapped = isinstance(value.get("message"), dict)
    if wrapped:
        value = value["message"]
    if wrapped or "tool_calls" in value:
        message: dict[str, Any] = {
            "role": "assistant",
            "content": value.get("content") if isinstance(value.get("content"), str) else "",
        }
        calls = _normalize_calls(value["tool_calls"])
        if calls:
            message["tool_calls"] = calls
        return message
    if "name" in value and ("arguments" in value or "args" in value):
        arguments = value.get("arguments", value.get("args"))
        return {"role": "assistant", "content": "", "tool_calls": [_call(value["name"], arguments)]}
    return None


def _json_in(text: str) -> Any:
    """Parse a JSON object, also when it is wrapped in a Markdown code fence."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else ""
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def parse_response(
    data_parts: list[dict[str, Any]], texts: list[str]
) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    """Map a participant reply to (assistant message, finish_reason, usage).

    An unrecognised reply becomes an assistant message without tool calls; the environment
    then records it as ``no_tool_call``, exactly as for a model that answers in prose.
    """
    for data in data_parts:
        message = _as_message(data)
        if message is not None:
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            finish = data.get("finish_reason")
            return message, finish if isinstance(finish, str) else None, usage
    for text in texts:
        message = _as_message(_json_in(text))
        if message is not None:
            return message, None, {}
    return {"role": "assistant", "content": "\n".join(texts)}, None, {}
