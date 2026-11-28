from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

import pytest

from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.evaluation import annotation_analysis as analysis
from project_d.evaluation import annotation_data as data
from project_d.evaluation import annotation_review as review
from project_d.evaluation import annotation_workflow as workflow


@pytest.fixture(scope="module")
def samples():
    return data.select()


def test_frozen_samples_and_shared_assignment(samples) -> None:
    assert Counter(s for ep in samples for s in ep.row["samples"]) == {
        "original": 108,
        "exploratory_extension": 12,
        "target": 108,
    }
    shared = [e for e in samples if len(e.row["samples"]) == 2]
    assert len(shared) == 15
    assert {e.row["profile"] for e in shared} == {
        "test_s1_01",
        "test_s1_03",
        "test_s3_01",
        "test_s3_03",
        "test_s3_05",
    }
    assert len({ep.row["episode"] for ep in samples}) == len(samples) == 213
    required = workflow.required_features(["original", "target"])
    assert len(required["A"]) == len(set(required["A"])) == 9
    assert required["episode"] == ["submission_order_agreed"]
    rows = [ep.row for ep in samples]
    assigned = workflow.assignment(rows)
    assert assigned == workflow.assignment(rows[::-1])
    assert sum(row["fixed_shared"] for row in assigned) == 43
    assert Counter(rater for row in assigned for rater in row["raters"]) == {
        "seva": 128,
        "platon": 128,
    }


@pytest.mark.parametrize(
    ("variant", "visibility"),
    [
        ("A/F", "explicit_read"),
        ("A/R3", "automatic_show"),
        ("A/VBC-F", "automatic_show"),
    ],
)
def test_projection_of_actual_requests_and_journals(samples, variant, visibility) -> None:
    ep = next(
        e
        for e in samples
        if e.row["variant"] == variant and e.row["profile"] == "test_s3_01" and e.row["repeat"] == 0
    )
    raw = data.read_jsonl(ep.journal)
    metadata = EpisodeMetadata(**raw[0]["metadata"])
    events = [LogEntry(**line) for line in raw[1:]]
    turns = data.read_jsonl(ep.llm)
    sentinel = 987654321
    agents = tuple(
        replace(
            agent,
            jobs=tuple(
                replace(
                    job, options=tuple(replace(option, value=sentinel) for option in job.options)
                )
                for job in agent.jobs
            ),
        )
        for agent in ep.scenario.agents
    )
    scenario = replace(ep.scenario, agents=agents)
    text, _, evidence = data.negotiation(scenario, metadata, events, turns)
    send = next(e for e in events if e.event_type == "send_message" and e.result == "ok")
    assert data.evidence_id(send) in evidence
    assert data.json_text(send.detail["text"]) in text
    assert f'"kind":"{visibility}"' in text
    assert str(sentinel) not in text
    assert all(
        data.evidence_id(e) not in evidence
        for e in events
        if e.event_type in ("submit", "plan_released", "complete", "commit")
    )
    if variant == "A/VBC-F":
        assert '"feedback":true' in text and "agreement " in text
    source = next(e for e in events if e.event_type == "message_delivered")
    assert data.evidence_id(source) in evidence


def test_delivered_message_without_proof_of_show_is_not_visible(samples) -> None:
    ep = next(
        e
        for e in samples
        if e.row["variant"] == "A/F" and e.row["profile"] == "test_s3_01" and e.row["repeat"] == 0
    )
    raw = data.read_jsonl(ep.journal)
    metadata = EpisodeMetadata(**raw[0]["metadata"])
    events = [LogEntry(**line) for line in raw[1:] if line["event_type"] != "read_messages"]
    text, _, _ = data.negotiation(ep.scenario, metadata, events, data.read_jsonl(ep.llm))
    assert '"delivery":{"id":' in text
    assert '"visibility":[]' in text


def test_role_swap_uses_actual_owner_and_request(samples) -> None:
    ep = next(e for e in samples if e.row["role_swap"])
    raw = data.read_jsonl(ep.journal)
    resolved = ep.scenario.with_role_swap()
    text, catalog, _ = data.negotiation(
        ep.scenario,
        EpisodeMetadata(**raw[0]["metadata"]),
        [LogEntry(**line) for line in raw[1:]],
        data.read_jsonl(ep.llm),
    )
    for agent in resolved.agents:
        assert f"### Agent {agent.agent_id} [USER-{agent.agent_id}]\n\n{agent.user_request}" in text
        assert {pair[0] for pair in catalog[agent.agent_id]} == {job.job_id for job in agent.jobs}


def _fixture(out: Path) -> dict:
    rows = [
        {"episode": e, "variant": "A/VBC", "samples": ["original", "target"]}
        for e in ("one", "two")
    ]
    manifest = workflow.csv_text(rows)
    tasks = {
        row["episode"]: {
            "episode": row["episode"],
            "samples": row["samples"],
            "schema_version": "1",
            "instruction_version": workflow.INSTRUCTION_VERSION,
            "manifest_sha256": data.digest(manifest.encode()),
            "catalog": {"A": [["qa", "full"]], "B": [["regression", "test"]]},
            "required": {
                "A": ["first_intent", "final_intent", "conflict_detected"],
                "B": ["partner_priority_understood"],
                "episode": ["submission_order_agreed"],
            },
            "evidence_ids": ["E0001", "E0002", "USER-A", "USER-B"],
        }
        for row in rows
    }
    files = {
        "sample_manifest.csv": manifest,
        "schema.json": "{}\n",
        "rubric.md": "# Fixture\n",
        "llm/tasks.jsonl": workflow.jsonl_text(tasks.values()),
        "objective/agents.csv": workflow.csv_text(
            [
                {
                    "episode": e,
                    "agent": a,
                    "submitted_pairs": [["qa", "full"]] if a == "A" else [],
                    "root_outcome": "completed" if a == "A" else "not_submitted",
                    "first_root_submit_t": 40 if a == "A" else None,
                }
                for e in tasks
                for a in ("A", "B")
            ]
        ),
        "objective/episodes.csv": workflow.csv_text(
            [
                {
                    "episode": e,
                    "root_conflict": True,
                    "root_submit_gap": None,
                    "higher_value_root_completed": True,
                }
                for e in tasks
            ]
        ),
        "verification/assignment.csv": workflow.csv_text(
            [
                {"episode": "one", "raters": ["seva", "platon"], "fixed_shared": True},
                {"episode": "two", "raters": ["platon"], "fixed_shared": False},
            ]
        ),
    }
    for name, content in files.items():
        workflow.write(out / name, content)
    identity = {
        "schema_version": "1",
        "instruction_version": workflow.INSTRUCTION_VERSION,
        "manifest_sha256": data.digest(manifest.encode()),
        "schema_sha256": data.digest(files["schema.json"].encode()),
        "instruction_sha256": data.digest(files["rubric.md"].encode()),
        "files": workflow._frozen_hashes(out),
    }
    workflow.write(out / "sample_identity.json", data.json_text(identity))
    return workflow.load_tasks(out)


def _answer(task: dict) -> dict:
    def label(value):
        return {"value": value, "reason": "Fixture evidence", "evidence": ["E0001"]}

    return {
        **{
            k: task[k]
            for k in ("episode", "schema_version", "instruction_version", "manifest_sha256")
        },
        "provenance": {"model": "synthetic", "date": "unknown", "method": "fixture"},
        "labels": {
            "A": {
                "first_intent": label(
                    {"pairs": "unclear", "source": "both", "contradiction": True}
                ),
                "final_intent": label(
                    {"pairs": "none", "source": "message", "contradiction": False}
                ),
                "conflict_detected": label("no"),
            },
            "B": {"partner_priority_understood": label("not_applicable")},
            "episode": {"submission_order_agreed": label("unclear")},
        },
    }


def test_import_review_reconciliation_and_final_gate(tmp_path) -> None:
    tasks = _fixture(tmp_path)
    answers = {e: _answer(task) for e, task in tasks.items()}
    first = tmp_path / "partial.jsonl"
    workflow.write(first, workflow.jsonl_text([answers["one"]]))
    assert workflow.main(["import", str(first), "--out", str(tmp_path)]) == 0
    assert (tmp_path / "verification/sheet_seva.csv").exists()
    workflow.import_answers(tmp_path, tasks, [first])
    imported = workflow.imported(tmp_path, tasks)
    assert list(imported) == ["one"]
    available = analysis.analyse(tmp_path, preliminary=True)
    assert available.name == "preliminary"
    with pytest.raises(ValueError, match="require all episodes"):
        analysis.analyse(tmp_path, preliminary=False)
    review.create_sheets(tmp_path, imported, tasks)
    path = tmp_path / "verification/sheet_seva.csv"
    rows = workflow.csv_rows(path)
    rows[0]["review_status"] = "confirmed"
    workflow.write(path, workflow.csv_text(rows))
    before = path.read_bytes()

    second = tmp_path / "more.jsonl"
    workflow.write(second, workflow.jsonl_text([answers["two"]]))
    workflow.import_answers(tmp_path, tasks, [second])
    imported = workflow.imported(tmp_path, tasks)
    review.create_sheets(tmp_path, imported, tasks)
    assert path.read_bytes() == before
    for sheet in (tmp_path / "verification").glob("*sheet_*.csv"):
        rows = workflow.csv_rows(sheet)
        for row in rows:
            row["review_status"] = "confirmed"
            if sheet.stem == "sheet_seva" and row["feature"] == "conflict_detected":
                row.update(
                    review_status="corrected",
                    review_value="yes",
                    review_reason="Human correction",
                    review_evidence='["E0002"]',
                )
        workflow.write(sheet, workflow.csv_text(rows))
    assert review.merge(tmp_path, tasks, imported) == 1
    assert not (tmp_path / "final/agents.csv").exists()
    disagreements = tmp_path / "verification/disagreements.csv"
    rows = workflow.csv_rows(disagreements)
    assert len(rows) == 1 and rows[0]["feature"] == "conflict_detected"
    rows[0].update(
        resolution_status="resolved",
        resolution_value="yes",
        resolution_reason="Joint resolution",
        resolution_evidence='["E0002"]',
    )
    workflow.write(disagreements, workflow.csv_text(rows))
    assert review.merge(tmp_path, tasks, imported) == 0
    assert review.status(tmp_path, tasks, imported)["final_analytics_ready"]
    final = analysis.analyse(tmp_path, preliminary=False)
    figures = list(final.glob("*.svg"))
    assert len(figures) == 4
    assert all(ElementTree.parse(path).getroot().tag.endswith("}svg") for path in figures)
    rates = workflow.csv_rows(final / "feature_rates.csv")
    order = next(r for r in rates if r["feature"] == "submission_order_agreed")
    assert (order["level"], order["expected"], order["unclear"]) == ("episode", "2", "2")
    own = workflow.csv_rows(tmp_path / "final/agents.csv")
    assert [r["value"] for r in own if r["feature"] == "final_plan_matches_submissions"] == [
        "no",
        "no",
    ]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("invalid_id", "evidence"),
        ("invalid_value", "categorical"),
        ("missing", "missing"),
        ("foreign_pair", "foreign"),
        ("duplicate", "Duplicate"),
        ("conflict", "Conflicting"),
        ("version", "manifest mismatch"),
    ],
)
def test_invalid_response_does_not_enter_archive(tmp_path, change, message) -> None:
    tasks = _fixture(tmp_path)
    record = _answer(tasks["one"])
    prompt = record["labels"]["A"]
    records = [record]
    if change == "invalid_id":
        prompt["conflict_detected"]["evidence"] = ["E9999"]
    elif change == "invalid_value":
        prompt["conflict_detected"]["value"] = ""
    elif change == "missing":
        del prompt["conflict_detected"]
    elif change == "foreign_pair":
        prompt["final_intent"]["value"]["pairs"] = [["regression", "test"]]
    elif change in ("duplicate", "conflict"):
        repeated = _answer(tasks["one"])
        if change == "conflict":
            repeated["labels"]["A"]["conflict_detected"]["value"] = "yes"
        records.append(repeated)
    else:
        record["manifest_sha256"] = "different"
    path = tmp_path / "reply.jsonl"
    workflow.write(path, workflow.jsonl_text(records))
    with pytest.raises(ValueError, match=message):
        workflow.import_answers(tmp_path, tasks, [path])
    assert not list((tmp_path / "llm/responses/imported").glob("*.jsonl"))


def test_kappa_denominators_and_degenerate_distribution() -> None:
    result = analysis.agreement(
        [
            ("yes", "yes"),
            ("no", "no"),
            ("unclear", "yes"),
            ("not_applicable", "no"),
        ]
    )
    assert (result["applicable"], result["agreement_count"], result["with_unclear"]) == (3, 2, 1)
    assert result["cohen_kappa"] == pytest.approx(0.5)
    assert analysis.agreement([("yes", "yes")])["cohen_kappa"] is None


def test_changed_frozen_manifest_and_archived_response_are_rejected(tmp_path) -> None:
    tasks = _fixture(tmp_path)
    file = tmp_path / "return.jsonl"
    workflow.write(file, workflow.jsonl_text([_answer(tasks["one"])]))
    workflow.import_answers(tmp_path, tasks, [file])
    archived = next((tmp_path / "llm/responses/imported").glob("*.jsonl"))
    archived.write_bytes(archived.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="archive checksum"):
        workflow.imported(tmp_path, tasks)
    manifest = tmp_path / "sample_manifest.csv"
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="frozen manifest"):
        workflow.load_tasks(tmp_path)
