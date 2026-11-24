from __future__ import annotations

from project_d.agents.prompts import protocol_note

PLAN = {"plan_version": 2, "proposals": {}}


def test_round_note_directs_to_send_and_is_shared_by_round_variants() -> None:
    note = protocol_note("message_round", (), None, "B")
    assert "send_message агенту B" in note
    assert "read_messages не" in note
    assert "раунд 1" not in note.lower()
    assert "из 3" not in note


def test_propose_note_rules_out_confirmation() -> None:
    note = protocol_note("propose", (), PLAN, "B")
    assert "только propose_plan" in note
    assert "confirm_plan в этой фазе недоступен" in note


def test_confirm_note_names_current_version() -> None:
    note = protocol_note("confirm", (), PLAN, "B")
    assert "Актуальная версия плана: 2" in note
    assert "plan_version=2" in note


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
