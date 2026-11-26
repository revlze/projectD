from __future__ import annotations

import re
from pathlib import Path

from project_d.agents.prompts import (
    BASE,
    BUDGET_CHECK_INSTRUCTION,
    PLAN_INSTRUCTION,
    ROUND_INSTRUCTION,
    free_coordination,
    protocol_note,
)

PLAN = {"plan_version": 2, "proposals": {"A": {"items": []}, "B": {"items": []}}}


def test_round_note_directs_to_send_and_is_shared_by_round_variants() -> None:
    note = protocol_note("message_round", (), None, "B")
    assert "send_message агенту B" in note
    assert "read_messages не" in note
    assert "раунд 1" not in note.lower()
    assert "из 3" not in note


def test_propose_notes_distinguish_first_proposal_and_revision() -> None:
    first = protocol_note("propose", (), None, "B")
    revision = protocol_note("propose", (), PLAN, "B")
    assert "Фаза предложения" in first and "будет отсутствовать" in first
    assert "Фаза пересмотра" in revision and "последнее корректное предложение" in revision
    assert "confirm_plan" not in first + revision


def test_confirm_note_names_final_version_and_how_to_decline() -> None:
    note = protocol_note("confirm", (), PLAN, "B")
    assert "Окончательная версия плана: 2" in note
    assert "plan_version=2" in note
    assert "wait_until(40)" in note


def test_confirm_note_states_neutral_facts_identical_for_u_and_a() -> None:
    from project_d.agents.prompts import CONFIRM_FACTS

    note = protocol_note("confirm", (), PLAN, "B")
    assert CONFIRM_FACTS in note
    assert "можно подтвердить даже при превышении бюджета" in CONFIRM_FACTS
    assert "не гарантирует отказа" in CONFIRM_FACTS
    # The note has no execution argument, so U and A receive the same text by construction.
    assert CONFIRM_FACTS not in protocol_note("confirm", (), None, "B")


def test_guard_rule_names_its_scope_and_absence_without_agreement() -> None:
    from project_d.agents.prompts import GUARD_RULE

    assert "только пар из items" in GUARD_RULE
    assert "раскрытые альтернативы в план не входят" in GUARD_RULE
    assert "Без подтверждения обоими агентами ограничения нет" in GUARD_RULE


def test_incomplete_plan_cannot_be_confirmed_even_without_v_feedback() -> None:
    for view in (None, {"plan_version": 2, "proposals": {"A": {"items": []}}}):
        note = protocol_note("confirm", (), view, "B")
        assert "Совместный план неполный; подтверждение недоступно" in note
        assert "confirm_plan" not in note
        assert "wait_until(40)" in note


def test_notes_never_recommend_who_yields() -> None:
    for phase in ("message_round", "propose", "confirm"):
        note = protocol_note(phase, (), PLAN, "B").lower()
        assert "уступ" not in note
        assert "value" not in note


def test_protocol_prompt_forbids_finishing_before_submission_opens() -> None:
    from project_d.agents.prompts import build_protocol_prompt
    from project_d.environment.model import Variant
    from support import make_scenario

    agent = make_scenario().agents[0]
    for variant in ("U/N", "U/F", "A/R3", "A/VBC"):
        prompt = build_protocol_prompt(agent, "B", Variant.parse(variant), 40)
        assert "До времени 40 finish не вызывай" in prompt
        assert "submission_not_open, повтори после 40" in prompt


def test_prompt_fragments_match_approved_specification() -> None:
    spec = (Path(__file__).parents[1] / "docs/system_spec.md").read_text(encoding="utf-8")
    for label, actual in (
        ("BASE", BASE),
        ("F", free_coordination("B")[1]),
        ("R1", ROUND_INSTRUCTION),
        ("R3P", BUDGET_CHECK_INSTRUCTION),
    ):
        line = next(line for line in spec.splitlines() if line.startswith(f"**`{label}`"))
        approved = re.search(r'"([^"]+)"', line).group(1)
        assert actual.startswith(approved)
    s_line = next(line for line in spec.splitlines() if line.startswith("Используем `BASE`"))
    assert re.search(r'"([^"]+)"', s_line).group(1) == PLAN_INSTRUCTION
    assert BASE.index("До планирования вызови list_jobs") < BASE.index("затем get_balance")
    assert "обязательно согласуй план" not in free_coordination("B")[1]
