"""Deterministic compact text of a shared plan version (system_spec.md, section 6, "V").

Both agents receive the same facts for the same version; only the order and the labels of the
two plan blocks differ. Agent notes are shown as their messages, apart from checked numbers.
"""

from __future__ import annotations

from typing import Any


def credits(amount: int) -> str:
    tail, last = amount % 100, amount % 10
    if last == 1 and tail != 11:
        word = "кредит"
    elif 2 <= last <= 4 and not 12 <= tail <= 14:
        word = "кредита"
    else:
        word = "кредитов"
    return f"{amount} {word}"


def _plan_block(
    agent_id: str, proposal: dict[str, Any] | None, feedback: dict[str, Any] | None
) -> list[str]:
    if proposal is None:
        return ["- план не передан"]
    lines = []
    if not proposal["items"]:
        lines.append("- пустой план: работы не выбраны")
    savings = {
        (s["job_id"], s["option_id"]): s["saving"]
        for s in (feedback or {}).get("disclosed_savings", ())
        if s["agent_id"] == agent_id
    }
    unmet = {
        u["job_id"] for u in (feedback or {}).get("unmet_requires", ()) if u["agent_id"] == agent_id
    }
    for item in proposal["items"]:
        lines.append(f"- {item['job_id']}/{item['option_id']}: {credits(item['cost'])}")
    for alternative in proposal["disclosed_alternatives"]:
        pair = (alternative["job_id"], alternative["option_id"])
        saving = f" (экономия {savings[pair]})" if pair in savings else ""
        lines.append(f"- Альтернатива {pair[0]}/{pair[1]}: {credits(alternative['cost'])}{saving}")
    for item in proposal["items"]:
        if item["job_id"] in unmet:
            lines.append(
                f"- Для {item['job_id']}/{item['option_id']} в плане нет необходимой "
                "предшествующей работы"
            )
    return lines


def _check_block(feedback: dict[str, Any], viewer: str, other: str) -> list[str]:
    budget, requested = feedback["budget"], feedback["requested_total"]
    if feedback["status"] == "INCOMPLETE":
        missing = sorted(feedback["missing_plans"])
        absent = (
            f"нет плана агента {missing[0]}"
            if len(missing) == 1
            else f"нет планов агентов {' и '.join(missing)}"
        )
        return [
            f"- Бюджет: {budget}; запрошено по переданным планам: {requested}",
            f"- INCOMPLETE: {absent}",
        ]
    # The same line for both agents (T34): totals are named by agent, not "yours"/"theirs".
    totals = feedback["agent_totals"]
    split = ", ".join(f"план {agent}: {totals.get(agent, 0)}" for agent in sorted((viewer, other)))
    return [
        f"- Бюджет: {budget}; запрошено: {requested} ({split}); превышение: {feedback['overage']}",
        f"- {feedback['status']}",
    ]


def render_plan(view: dict[str, Any], viewer: str, other: str) -> str:
    proposals = view["proposals"]
    feedback = view.get("plan_feedback")
    lines = [f"Совместный план #{view['plan_version']}", f"ТВОЙ ПЛАН ({viewer})"]
    lines += _plan_block(viewer, proposals.get(viewer), feedback)
    lines.append(f"ПЛАН ДРУГОГО АГЕНТА ({other})")
    lines += _plan_block(other, proposals.get(other), feedback)
    if feedback is not None:
        lines.append("ПРОВЕРКА БЮДЖЕТА")
        lines += _check_block(feedback, viewer, other)
    notes = [
        (agent, proposals[agent]["note"])
        for agent in (viewer, other)
        if agent in proposals and proposals[agent]["note"]
    ]
    if notes:
        lines.append("ПОЯСНЕНИЯ АГЕНТОВ (их сообщения, не проверены средой)")
        lines += [f"- {agent}: {note}" for agent, note in notes]
    return "\n".join(lines)
