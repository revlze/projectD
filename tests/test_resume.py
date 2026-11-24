from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from project_d.agents.llm_client import LLMTransportError
from project_d.experiments.matrix import (
    DATA_ROOT,
    EpisodeSpec,
    build_matrix,
    load_manifest,
    run_specs,
)
from project_d.experiments.storage import file_sha256
from test_baseline_contract import RecordingClient

ROOT = Path(__file__).resolve().parents[1] / DATA_ROOT
SPEC = EpisodeSpec("E1", "dev/dev_s2_01.json", "A/R3", 0)


def run(root: Path, identity: dict | None = None, *, spec=SPEC, seed=0, client=None):
    return run_specs(
        [spec],
        ROOT,
        root,
        lambda _: client or RecordingClient(),
        base_seed=seed,
        run_identity=identity
        or {"model": "recording", "digest": "weights", "template": "template"},
    )


@pytest.mark.parametrize("change", ("model", "digest", "template", "seed", "delay", "prompt"))
def test_resume_rejects_changed_configuration_without_rewriting_manifest(
    tmp_path, monkeypatch, change
):
    run(tmp_path)
    original = (tmp_path / "run_manifest.json").read_bytes()
    identity = {"model": "recording", "digest": "weights", "template": "template"}
    spec, seed = SPEC, 0
    if change in identity:
        identity[change] = "different"
    elif change == "seed":
        seed = 1
    elif change == "delay":
        spec = replace(SPEC, message_delay=8)
    else:
        monkeypatch.setattr("project_d.experiments.matrix.PROMPT_VERSION", "different")
    with pytest.raises(ValueError, match="configuration differs"):
        run(tmp_path, identity, spec=spec, seed=seed)
    assert (tmp_path / "run_manifest.json").read_bytes() == original


@pytest.mark.parametrize("suffix", ("log.jsonl", "llm.jsonl", "prompts.json", "receipt.json"))
def test_successful_summary_with_missing_artifact_is_not_reused(tmp_path, suffix):
    run(tmp_path)
    (tmp_path / f"{SPEC.name}.{suffix}").unlink()
    with pytest.raises(ValueError, match=r"missing|incomplete"):
        run(tmp_path)


@pytest.mark.parametrize("suffix", ("log.jsonl", "llm.jsonl", "prompts.json", "summary.json"))
def test_changed_artifact_is_not_reused(tmp_path, suffix):
    run(tmp_path)
    path = tmp_path / f"{SPEC.name}.{suffix}"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="modified"):
        run(tmp_path)


def test_successful_resume_makes_no_requests(tmp_path):
    rows = run(tmp_path)

    class NoCalls:
        def chat(self, messages, tools):
            raise AssertionError("Completed episode must be reused")

    assert run(tmp_path, client=NoCalls()) == rows


def test_independent_audit_rejects_damaged_journal_even_with_updated_checksum(tmp_path):
    run(tmp_path)
    path = tmp_path / f"{SPEC.name}.log.jsonl"
    raw = [json.loads(line) for line in path.read_bytes().splitlines()]
    raw = [item for item in raw if item.get("event_type") != "commit"]
    for index, item in enumerate(raw[1:]):
        item["seq"] = index
    path.write_bytes("".join(json.dumps(item) + "\n" for item in raw).encode("utf-8"))
    receipt_path = tmp_path / f"{SPEC.name}.receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["sha256"]["log.jsonl"] = file_sha256(path)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="journal audit failed"):
        run(tmp_path)


def test_existing_writer_lock_is_preserved(tmp_path):
    lock = tmp_path / ".run.lock"
    lock.write_text('{"pid": 1234, "host": "other"}', encoding="utf-8")
    with pytest.raises(ValueError, match="locked"):
        run(tmp_path)
    assert lock.read_text(encoding="utf-8") == '{"pid": 1234, "host": "other"}'


def test_transport_failure_preserves_exact_attempt_before_retry(tmp_path):
    class BrokenClient(RecordingClient):
        def chat(self, messages, tools):
            if len(self.requests) == 2:
                raise LLMTransportError("test transport interruption")
            return super().chat(messages, tools)

    rows = run(tmp_path, client=BrokenClient())
    assert rows[0]["failure"] == "test transport interruption"
    assert (tmp_path / f"{SPEC.name}.log.jsonl").exists()
    turns = [
        json.loads(line) for line in (tmp_path / f"{SPEC.name}.llm.jsonl").read_bytes().splitlines()
    ]
    assert turns[-1]["transport_error"] and turns[-1]["request"]
    assert not (tmp_path / f"{SPEC.name}.receipt.json").exists()
    assert run(tmp_path)[0]["failure"] is None
    archived = tmp_path / "attempts" / SPEC.name / "attempt_001"
    assert (archived / f"{SPEC.name}.log.jsonl").exists()
    assert (archived / f"{SPEC.name}.llm.jsonl").exists()


def test_matrix_contains_only_unique_new_test_conditions():
    manifest = load_manifest(ROOT)
    conditions = set()
    for series in ("E2", "E3", "E4-H1", "E4-delay"):
        for spec in build_matrix(series, manifest):
            key = (
                spec.profile,
                spec.variant,
                spec.repeat,
                spec.commit_delay if spec.commit_delay is not None else 2,
                spec.start_gap,
                spec.message_delay if spec.message_delay is not None else 1,
            )
            assert key not in conditions
            conditions.add(key)
    assert len(conditions) == 1712


def test_duplicate_keys_are_rejected_before_any_request(tmp_path):
    with pytest.raises(ValueError):
        run_specs(
            [SPEC, SPEC],
            ROOT,
            tmp_path,
            lambda _: pytest.fail("No client creation"),
            run_identity={},
        )
    assert not list(tmp_path.iterdir())


def test_parallel_workers_match_sequential_run(tmp_path):
    specs = [replace(SPEC, repeat=r) for r in range(3)] + [replace(SPEC, variant="A/N")]
    identity = {"model": "recording", "digest": "weights", "template": "template"}

    def go(root: Path, workers: int):
        return run_specs(
            specs, ROOT, root, lambda _: RecordingClient(), run_identity=identity, workers=workers
        )

    sequential = go(tmp_path / "seq", 1)
    parallel = go(tmp_path / "par", 4)
    assert [r["episode"] for r in parallel] == [s.name for s in specs]
    assert parallel == sequential
    for spec in specs:
        for suffix in ("log.jsonl", "llm.jsonl"):
            name = f"{spec.name}.{suffix}"
            assert file_sha256(tmp_path / "par" / name) == file_sha256(tmp_path / "seq" / name)
