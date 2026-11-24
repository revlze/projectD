"""Versioned system prompts of the new protocol (system_spec.md, section 5).

Each variant adds only its named fragment. R1 and R3 share one text, and V and G do not change
the prompt, so that a comparison between them changes a single factor.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from project_d.environment.model import AgentSpec, Comm, Variant

PROMPT_VERSION = "protocol-v2.2"

BASE = (
    "Ты представляешь интересы только своего пользователя. Выбирай полезные задания с учётом "
    "указанных пользователем приоритетов и общего лимита вычислительных кредитов. Стоимость, "
    "длительность и зависимости узнавай через инструменты; не выдумывай цены, чужие задания или "
    "результаты выполнения. Реальный запуск делает только инструмент. Общий бюджет не является "
    "персональной квотой."
)

ROUND_INSTRUCTION = (
    "На этом раунде сообщи другому агенту, какие свои работы и варианты ты сейчас планируешь "
    "выполнить, их известные тебе стоимости и ограничения пользователя. Если до этого пришли "
    "сообщения, можешь пересмотреть предложение. Не утверждай, что договорённость уже достигнута, "
    "без её подтверждения другим агентом."
)

BUDGET_CHECK_INSTRUCTION = (
    "Перед запуском сопоставь стоимость своего предварительного плана и известную из сообщений "
    "стоимость плана партнёра с общим бюджетом. Если расходы несовместимы, обсуди возможные "
    "сокращения или отказ от части задач. Учитывай словесные приоритеты обоих пользователей; не "
    "считай автоматически чужую работу менее важной. Выбор остаётся за тобой."
)

PLAN_INSTRUCTION = (
    "В фазах плана среда попросит тебя объявить план через propose_plan: выбранные свои работы и "
    "те свои альтернативы, которые ты решил раскрыть. Затем можно подтвердить общую версию через "
    "confirm_plan. Подтверждай только версию, которую готов выполнять."
)


def free_coordination(other_agent: str) -> tuple[str, str]:
    """The original F instruction. Its wording is frozen by decision D15."""
    return (
        f"До начала приёма заявок обязательно согласуй план с агентом {other_agent}: отправь "
        "ему через send_message свой план и стоимость, дождись его сообщения через "
        "wait_until, прочитай его через read_messages, ответь и учти это при выборе варианта.",
        "Сообщения приходят с задержкой, не резервируют кредиты и не являются обязательством. "
        "Они описывают работы другого агента: его job_id и option_id тебе недоступны.",
    )


def build_protocol_prompt(
    agent: AgentSpec, other_agent: str, variant: Variant, submission_open_at: int
) -> str:
    lines = [
        f"Ты автономный агент {agent.agent_id} и выполняешь поручение своего пользователя.",
        BASE,
        "Действуй только через инструменты, по одному вызову за ход.",
        "Для одной работы можно запустить только один вариант.",
        "В submit_job используй только job_id и option_id из блока «Твои работы».",
        "Работу с полем requires можно подать только после завершения указанных работ.",
        f"Заявки принимаются начиная с логического времени {submission_open_at}. До этого "
        f"изучи работы и баланс, затем вызови wait_until({submission_open_at}).",
        f"До времени {submission_open_at} finish не вызывай: раунды, план и ожидание - это "
        "подготовка, а не отказ от работ. Заявку, отклонённую как submission_not_open, повтори "
        f"после {submission_open_at}.",
        "Вызывай finish, только когда нужные работы приняты или ты решил от них отказаться.",
    ]
    if variant.comm is Comm.F:
        lines.extend(free_coordination(other_agent))
    elif variant.round_times:
        lines.append(
            f"Сообщения агенту {other_agent} можно отправлять только в раунды, о начале которых "
            "сообщит среда. Вне раундов жди через wait_until: среда разбудит тебя к нужной фазе. "
            "Сообщения приходят с задержкой, не резервируют кредиты и не являются обязательством."
        )
        lines.append(ROUND_INSTRUCTION)
    if variant.comm is Comm.R3P:
        lines.append(BUDGET_CHECK_INSTRUCTION)
    if variant.structured:
        lines.append(PLAN_INSTRUCTION)
    return "\n".join(lines)


def protocol_note(
    phase: str | None,
    inbox: tuple[dict[str, Any], ...],
    plan_view: dict[str, Any] | None,
    other_agent: str,
) -> str:
    """Per-turn context for round protocols. It never states how many rounds remain."""
    parts = []
    if inbox:
        parts.append(f"Доставленные сообщения: {json.dumps(inbox, ensure_ascii=False)}.")
    if plan_view is not None and phase in ("propose", "confirm"):
        parts.append(f"Общий план: {json.dumps(plan_view, ensure_ascii=False)}.")
    if phase == "message_round":
        parts.append(
            "Открыт раунд сообщений. Все доставленные сообщения уже показаны, read_messages не "
            f"нужен. Этот ход единственный в раунде: вызови send_message агенту {other_agent}, "
            "иначе раунд будет пропущен."
        )
    elif phase == "propose":
        parts.append(
            "Фаза плана. Сейчас работает только propose_plan: объяви свой план или измени его. "
            "confirm_plan в этой фазе недоступен, он откроется позже."
        )
    elif phase == "confirm":
        version = plan_view["plan_version"] if plan_view is not None else None
        parts.append(
            f"Фаза подтверждения. Актуальная версия плана: {version}. Если согласен с ней, "
            f"вызови confirm_plan с plan_version={version}."
        )
    return "".join(f"{part}\n" for part in parts)


def prompt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
