"""Tool schemas shown to the model and conversion between model calls and environment actions."""

from __future__ import annotations

import json
from typing import Any

from project_d.environment.actions import (
    Action,
    ConfirmPlan,
    Finish,
    GetBalance,
    GetStatus,
    InvalidCall,
    ListJobs,
    ProposePlan,
    ReadMessages,
    SendMessage,
    SubmitJob,
    ToolResult,
    WaitUntil,
)
from project_d.environment.model import Mode, Variant


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
    required: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    properties = properties or {}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties if required is None else required),
            },
        },
    }


_BASE_TOOLS = (
    _tool("list_jobs", "Показать свои работы, их варианты, стоимость и длительность."),
    _tool("get_balance", "Показать доступный остаток общего бюджета на текущий момент."),
    _tool(
        "submit_job",
        "Подать заявку на запуск одного варианта своей работы.",
        {
            "job_id": {"type": "string", "description": "Идентификатор работы"},
            "option_id": {"type": "string", "description": "Идентификатор варианта"},
        },
    ),
    _tool("get_status", "Показать состояние своих работ и последней заявки."),
    _tool(
        "wait_until",
        "Ждать до указанного логического времени. Новое сообщение может прервать ожидание.",
        {"target_time": {"type": "integer", "description": "Время позже текущего"}},
    ),
    _tool("finish", "Завершить участие в эпизоде."),
)

_MESSAGE_TOOLS = (
    _tool(
        "send_message",
        "Отправить сообщение другому агенту. Оно придёт с задержкой и не резервирует кредиты.",
        {
            "agent_id": {"type": "string", "description": "Идентификатор получателя"},
            "text": {"type": "string", "description": "Текст сообщения"},
        },
    ),
    _tool("read_messages", "Прочитать доставленные непрочитанные сообщения."),
)

_PLAN_PAIRS = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"job_id": {"type": "string"}, "option_id": {"type": "string"}},
        "required": ["job_id", "option_id"],
    },
}

_PLAN_TOOLS = (
    _tool(
        "propose_plan",
        "Объявить план из своих работ. Стоимость подставляет среда.",
        {
            "items": {**_PLAN_PAIRS, "description": "Выбранные свои работы и варианты"},
            "disclosed_alternatives": {
                **_PLAN_PAIRS,
                "description": "Свои альтернативы, которые ты решил раскрыть",
            },
            "note": {"type": "string", "description": "Короткий комментарий"},
        },
        required=("items",),
    ),
    _tool(
        "confirm_plan",
        "Подтвердить общую версию плана.",
        {"plan_version": {"type": "integer", "description": "Номер версии плана"}},
    ),
)

_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "list_jobs": (),
    "get_balance": (),
    "submit_job": ("job_id", "option_id"),
    "get_status": (),
    "send_message": ("agent_id", "text"),
    "read_messages": (),
    "wait_until": ("target_time",),
    "finish": (),
    "propose_plan": ("items",),
    "confirm_plan": ("plan_version",),
}

_OPTIONAL_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "propose_plan": ("disclosed_alternatives", "note"),
}


def tool_schemas(mode: Mode | Variant) -> list[dict[str, Any]]:
    variant = mode.variant if isinstance(mode, Mode) else mode
    return [
        *_BASE_TOOLS,
        *(_MESSAGE_TOOLS if variant.messaging else ()),
        *(_PLAN_TOOLS if variant.structured else ()),
    ]


def _parse_pairs(raw: Any) -> tuple[tuple[str, str], ...] | None:
    if not isinstance(raw, list):
        return None
    pairs = []
    for entry in raw:
        if not isinstance(entry, dict) or set(entry) != {"job_id", "option_id"}:
            return None
        if not all(isinstance(part, str) for part in entry.values()):
            return None
        pairs.append((entry["job_id"], entry["option_id"]))
    return tuple(pairs)


def parse_tool_call(name: Any, raw_arguments: Any) -> Action:
    """Turn a model call into an action. Anything malformed becomes ``InvalidCall``."""
    if not isinstance(name, str) or name not in _ARGUMENTS:
        return InvalidCall(name if isinstance(name, str) else None, "unknown_tool")

    arguments = raw_arguments
    if arguments is None or arguments == "":
        arguments = {}
    elif isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return InvalidCall(name, "arguments_not_json")
    if not isinstance(arguments, dict):
        return InvalidCall(name, "arguments_not_object")
    required = set(_ARGUMENTS[name])
    allowed = required | set(_OPTIONAL_ARGUMENTS.get(name, ()))
    if not required <= set(arguments) <= allowed:
        return InvalidCall(name, f"expected_arguments:{','.join(_ARGUMENTS[name]) or 'none'}")

    match name:
        case "list_jobs":
            return ListJobs()
        case "get_balance":
            return GetBalance()
        case "get_status":
            return GetStatus()
        case "read_messages":
            return ReadMessages()
        case "finish":
            return Finish()
        case "submit_job":
            if not all(isinstance(v, str) for v in arguments.values()):
                return InvalidCall(name, "arguments_must_be_strings")
            return SubmitJob(arguments["job_id"], arguments["option_id"])
        case "send_message":
            if not all(isinstance(v, str) for v in arguments.values()):
                return InvalidCall(name, "arguments_must_be_strings")
            return SendMessage(arguments["agent_id"], arguments["text"])
        case "wait_until":
            target = arguments["target_time"]
            if not isinstance(target, int) or isinstance(target, bool):
                return InvalidCall(name, "target_time_must_be_integer")
            return WaitUntil(target)
        case "propose_plan":
            items = _parse_pairs(arguments["items"])
            alternatives = _parse_pairs(arguments.get("disclosed_alternatives", []))
            note = arguments.get("note", "")
            if items is None or alternatives is None or not isinstance(note, str):
                return InvalidCall(name, "malformed_plan")
            return ProposePlan(items, alternatives, note)
        case "confirm_plan":
            version = arguments["plan_version"]
            if not isinstance(version, int) or isinstance(version, bool):
                return InvalidCall(name, "plan_version_must_be_integer")
            return ConfirmPlan(version)
    raise AssertionError(f"unhandled tool: {name}")  # pragma: no cover


def render_result(result: ToolResult, error: str | None = None) -> str:
    payload: dict[str, Any] = {
        "status": result.status.value,
        "logical_time": result.logical_time,
        "submission_open_at": result.submission_open_at,
        **result.data,
    }
    if error:
        payload["error"] = error
    return json.dumps(payload, ensure_ascii=False)
