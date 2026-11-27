from __future__ import annotations

import json

import pytest

from project_d.evaluation import annotation_sample


@pytest.mark.parametrize("role_swap", (False, True))
@pytest.mark.parametrize("result", ("agreed", "agreement_failed"))
def test_transcript_includes_resolved_user_requests_and_agreement(tmp_path, role_swap, result):
    folder = tmp_path / "test"
    folder.mkdir()
    profile = "test_s3_01"
    source = annotation_sample.DATA / "test" / f"{profile}.json"
    scenario = json.loads(source.read_bytes())
    for agent in scenario["agents"]:
        agent["user_request"] = f"Original request for {agent['agent_id']}."
    (folder / source.name).write_text(json.dumps(scenario), encoding="utf-8")
    path = tmp_path / "recorded.log.jsonl"
    records = (
        {
            "metadata": {
                "scenario_id": profile,
                "budget": 12,
                "horizon": 80,
                "first_agent": "A",
                "role_swap": role_swap,
                "catalog": {},
            }
        },
        {"event_type": "agreement", "time": 40, "agent_id": None, "result": result, "detail": {}},
    )
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(annotation_sample, "DATA", tmp_path)
        text = annotation_sample.transcript(path)
    a, b = ("B", "A") if role_swap else ("A", "B")
    assert f"### Agent A\n\nOriginal request for {a}." in text
    assert f"### Agent B\n\nOriginal request for {b}." in text
    assert f"**t=40 env agreement**: {result}" in text
