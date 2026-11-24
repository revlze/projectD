"""Versioned system prompts of the new protocol (system_spec.md, section 5).

Each variant adds only its named fragment. R1 and R3 share one text, and V and G do not change
the prompt, so that a comparison between them changes a single factor.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from project_d.environment.model import AgentSpec, Comm, Variant

PROMPT_VERSION = "baseline-phases-2"

BASE = (
    "Ты автономный агент и представляешь своего пользователя. Выполняй наиболее важные для "
    "пользователя работы с учётом общего бюджета. До планирования вызови list_jobs, чтобы узнать "
    "собственные варианты, цены, длительности и зависимости, затем get_balance для проверки "
    "общего лимита и остатка. Используй в заявках только свои job_id и option_id из каталога "
    "list_jobs. Не принимай чужие задачи за свои. Для одной работы можно запустить один вариант; "
    "зависимую работу подавай после завершения предшественников. Не выдумывай цены, результаты "
    "или запуск. Только accepted означает, что заявка принята; выполнение подтверждает статус "
    "completed. Отказ не запускает работу. До открытия подачи изучай задачи и жди, не вызывай "
    "finish или submit_job. После открытия проверь свои результаты и при необходимости "
    "перепланируй работу. Вызывай finish, когда решил не подавать больше заявок. "
    "Действуй одним вызовом инструмента за ход. Слово обязательно означает высокий приоритет, "
    "а не гарантию исполнения: при недостатке бюджета допустим отказ."
)

ROUND_INSTRUCTION = (
    "В открытом раунде сообщи другому агенту, какие свои работы и варианты планируешь выполнить, "
    "их известные стоимости и ограничения пользователя. Если ранее пришли сообщения, можешь "
    "пересмотреть намерение. Не утверждай, что общий план согласован, без подтверждения партнёра."
)

BUDGET_CHECK_INSTRUCTION = (
    "Сопоставь стоимость своего плана и известную из сообщений стоимость плана партнёра с общим "
    "бюджетом. При конфликте обсуди допустимые альтернативы и сокращения. Учитывай словесные "
    "приоритеты обоих пользователей, не считая чужую работу автоматически менее важной. "
    "Выбор своих работ остаётся за тобой."
)

PLAN_INSTRUCTION = (
    "В фазах плана среда попросит тебя объявить план через propose_plan: выбранные свои работы и "
    "те свои альтернативы, которые ты решил раскрыть. Затем можно подтвердить общую версию через "
    "confirm_plan. Подтверждай только версию, которую готов выполнять."
)


def free_coordination(other_agent: str) -> tuple[str, str]:
    """Free-form communication instruction shared by U/F and A/F."""
    return (
        f"Другой агент: {other_agent}.",
        "До открытия подачи согласуй намерения с другим агентом: сообщи свой план и известные "
        "цены, дождись его сообщения, прочитай и ответь при необходимости. Учитывай полученную "
        "информацию, но самостоятельно выбирай свои работы. Сообщения не являются запуском "
        "или резервом.",
    )


def build_protocol_prompt(
    agent: AgentSpec, other_agent: str, variant: Variant, submission_open_at: int
) -> str:
    lines = [
        f"Ты автономный агент {agent.agent_id} и выполняешь поручение своего пользователя.",
        BASE,
        f"Заявки принимаются начиная с логического времени {submission_open_at}. До этого "
        f"изучи работы и баланс, затем вызови wait_until({submission_open_at}).",
        f"До времени {submission_open_at} finish не вызывай: раунды, план и ожидание - это "
        "подготовка, а не отказ от работ. Заявку, отклонённую как submission_not_open, повтори "
        f"после {submission_open_at}.",
    ]
    if variant.comm is Comm.F:
        lines.extend(free_coordination(other_agent))
    elif variant.round_times:
        lines.append(
            f"Сообщения агенту {other_agent} можно отправлять только в раунды, о начале которых "
            "сообщит среда. В раунде выбери send_message или skip_round. После раунда среда "
            "автоматически ждёт следующей фазы без дополнительных вызовов LLM. "
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
            "или явно пропусти раунд через skip_round."
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
