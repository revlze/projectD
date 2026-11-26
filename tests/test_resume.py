from __future__ import annotations

import hashlib
import json
import threading
import urllib.error
from dataclasses import replace
from email.message import Message
from io import BytesIO
from pathlib import Path

import pytest

from project_d.agents.llm_client import (
    ChatResponse,
    LLMConfig,
    LLMTransportError,
    OpenAICompatibleClient,
)
from project_d.agents.providers import provider_config
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


@pytest.mark.parametrize("suffix", ("log.jsonl", "llm.jsonl", "prompts.json"))
def test_successful_summary_with_missing_artifact_is_not_reused(tmp_path, suffix):
    run(tmp_path)
    (tmp_path / f"{SPEC.name}.{suffix}").unlink()
    with pytest.raises(ValueError, match=r"missing|incomplete"):
        run(tmp_path)


def test_attempt_interrupted_before_its_receipt_is_archived_and_rerun(tmp_path):
    rows = run(tmp_path)
    (tmp_path / f"{SPEC.name}.receipt.json").unlink()
    assert run(tmp_path) == rows
    archived = tmp_path / "attempts" / SPEC.name / "attempt_001"
    assert (archived / f"{SPEC.name}.summary.json").exists()
    assert (tmp_path / f"{SPEC.name}.receipt.json").exists()


def test_resume_ignores_when_the_run_was_first_started(tmp_path):
    identity = {"model": "recording", "started_utc": "2026-11-25T08:00:00+00:00"}
    run(tmp_path, identity)
    original = (tmp_path / "run_manifest.json").read_bytes()
    later = {**identity, "started_utc": "2026-11-25T09:30:00+00:00"}
    run(tmp_path, later)
    # The saved manifest keeps the first start time.
    assert (tmp_path / "run_manifest.json").read_bytes() == original


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


def _update_receipt(root: Path, suffix: str, path: Path, spec: EpisodeSpec = SPEC) -> None:
    receipt_path = root / f"{spec.name}.receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["sha256"][suffix] = file_sha256(path)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")


def test_resume_rejects_changed_summary_even_with_updated_checksum(tmp_path):
    run(tmp_path)
    path = tmp_path / f"{SPEC.name}.summary.json"
    summary = json.loads(path.read_bytes())
    summary["U_safe"] = 999
    path.write_text(json.dumps(summary), encoding="utf-8")
    _update_receipt(tmp_path, "summary.json", path)
    with pytest.raises(ValueError, match="summary differs from the verified journals"):
        run(tmp_path)


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        ("duplicate_decision", "decisions differ by agent or time"),
        ("tool_outcome", "incomplete request or tool outcome"),
        ("wrong_phase", "observation differs from the decision"),
    ),
)
def test_resume_rejects_inconsistent_decisions_with_updated_checksum(tmp_path, mutation, error):
    from project_d.agents.prompts import prompt_sha256

    run(tmp_path)
    path = tmp_path / f"{SPEC.name}.llm.jsonl"
    turns = [json.loads(line) for line in path.read_bytes().splitlines()]
    if mutation == "duplicate_decision":
        turns[1] = turns[0]
    elif mutation == "tool_outcome":
        turns[0]["tool_result"]["status"] = "accepted"
    else:
        request = turns[0]["request"]
        observation = request["messages"][-1]
        observation["content"] = observation["content"].replace(
            "phase=preparation", "phase=confirm"
        )
        turns[0]["request_sha256"] = prompt_sha256(
            json.dumps(request, ensure_ascii=False, sort_keys=True)
        )
    path.write_text("".join(json.dumps(turn) + "\n" for turn in turns), encoding="utf-8")
    _update_receipt(tmp_path, "llm.jsonl", path)
    with pytest.raises(ValueError, match=error):
        run(tmp_path)


def test_resume_rejects_removed_alternatives_missing_from_the_journal(tmp_path):
    """vbc-4: the tool result and the journal must name the same removed alternatives."""
    spec = EpisodeSpec("E1", "dev/dev_s2_01.json", "A/VBC", 0)
    run(tmp_path, spec=spec)
    path = tmp_path / f"{spec.name}.llm.jsonl"
    turns = [json.loads(line) for line in path.read_bytes().splitlines()]
    proposal = next(t for t in turns if (t["parsed_action"] or "").startswith("ProposePlan"))
    pair = {"job_id": "x", "option_id": "y"}
    proposal["tool_result"]["data"]["removed_alternatives"] = [pair]
    path.write_text("".join(json.dumps(turn) + "\n" for turn in turns), encoding="utf-8")
    _update_receipt(tmp_path, "llm.jsonl", path, spec)
    with pytest.raises(ValueError, match="incomplete request or tool outcome"):
        run(tmp_path, spec=spec)


VBC_SPEC = EpisodeSpec("E1", "dev/dev_s2_01.json", "A/VBC", 0)


class StaleAlternativeClient(RecordingClient):
    """Proposes its chosen option also as an alternative, so every proposal is normalized."""

    def chat(self, messages, tools):
        reply = super().chat(messages, tools)
        call = reply.message["tool_calls"][0]["function"]
        if call["name"] == "propose_plan":
            arguments = json.loads(call["arguments"])
            arguments["disclosed_alternatives"] = list(arguments["items"])
            call["arguments"] = json.dumps(arguments)
        return reply


def _rewrite_turns(root: Path, spec: EpisodeSpec, change) -> None:
    from project_d.agents.prompts import prompt_sha256

    path = root / f"{spec.name}.llm.jsonl"
    turns = [json.loads(line) for line in path.read_bytes().splitlines()]
    change(turns)
    for turn in turns:
        turn["request_sha256"] = prompt_sha256(
            json.dumps(turn["request"], ensure_ascii=False, sort_keys=True)
        )
    path.write_text("".join(json.dumps(turn) + "\n" for turn in turns), encoding="utf-8")
    _update_receipt(root, "llm.jsonl", path, spec)


def _normalized_run(root: Path) -> None:
    run(root, spec=VBC_SPEC, client=StaleAlternativeClient())


def test_normalized_run_is_reused_on_resume(tmp_path):
    _normalized_run(tmp_path)
    turns = [
        json.loads(line)
        for line in (tmp_path / f"{VBC_SPEC.name}.llm.jsonl").read_bytes().splitlines()
    ]
    assert any(t["tool_result"]["data"].get("removed_alternatives") for t in turns)
    rows = run(tmp_path, spec=VBC_SPEC, client=StaleAlternativeClient())
    assert len(rows) == 1


def test_resume_rejects_history_without_the_shown_removal(tmp_path):
    _normalized_run(tmp_path)

    def drop_from_history(turns):
        for turn in turns:
            for message in turn["request"]["messages"]:
                if message["role"] == "tool" and "removed_alternatives" in message["content"]:
                    content = json.loads(message["content"])
                    del content["removed_alternatives"]
                    message["content"] = json.dumps(content, ensure_ascii=False)

    _rewrite_turns(tmp_path, VBC_SPEC, drop_from_history)
    with pytest.raises(ValueError, match="shown tool result differs from the record"):
        _normalized_run(tmp_path)


def test_resume_rejects_a_removal_the_model_did_not_request(tmp_path):
    """A consistent journal and tool result still must follow from the model's own call."""
    run(tmp_path, spec=VBC_SPEC)
    log_path = tmp_path / f"{VBC_SPEC.name}.log.jsonl"
    raw = [json.loads(line) for line in log_path.read_bytes().splitlines()]
    entry = next(e for e in raw[1:] if e.get("event_type") == "propose_plan")
    chosen = entry["detail"]["items"][0]
    pair = {"job_id": chosen["job_id"], "option_id": chosen["option_id"]}
    entry["detail"]["removed_alternatives"] = [pair]
    log_path.write_bytes("".join(json.dumps(item) + "\n" for item in raw).encode("utf-8"))
    _update_receipt(tmp_path, "log.jsonl", log_path, VBC_SPEC)

    def add_to_result(turns):
        turn = next(
            t
            for t in turns
            if t["agent_id"] == entry["agent_id"] and t["logical_time"] == entry["time"]
        )
        turn["tool_result"]["data"]["removed_alternatives"] = [pair]

    _rewrite_turns(tmp_path, VBC_SPEC, add_to_result)
    with pytest.raises(ValueError, match="removed alternatives differ from the proposal call"):
        run(tmp_path, spec=VBC_SPEC)


def _list_as_data(turns):
    turns[0]["tool_result"]["data"] = [1]


def _replace_reply(turns):
    """Change the assistant reply that the agent's second request carries in its history."""
    agent = turns[0]["agent_id"]
    first, second = [t for t in turns if t["agent_id"] == agent][:2]
    reply = second["request"]["messages"][len(first["request"]["messages"])]
    reply["content"] = "rewritten"


@pytest.mark.parametrize(
    ("change", "error"),
    [
        (_list_as_data, "incomplete request or tool outcome"),
        (_replace_reply, "request history differs from the recorded reply"),
    ],
)
def test_resume_rejects_malformed_or_rewritten_history(tmp_path, change, error):
    run(tmp_path)
    _rewrite_turns(tmp_path, SPEC, change)
    with pytest.raises(ValueError, match=error):
        run(tmp_path)


def test_independent_audit_rejects_damaged_journal_even_with_updated_checksum(tmp_path):
    run(tmp_path)
    path = tmp_path / f"{SPEC.name}.log.jsonl"
    raw = [json.loads(line) for line in path.read_bytes().splitlines()]
    raw = [item for item in raw if item.get("event_type") != "commit"]
    for index, item in enumerate(raw[1:]):
        item["seq"] = index
    path.write_bytes("".join(json.dumps(item) + "\n" for item in raw).encode("utf-8"))
    _update_receipt(tmp_path, "log.jsonl", path)
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
    assert rows[0]["failure_kind"] == "transport"
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


def test_environment_failure_stops_run_and_is_not_resumed_automatically(tmp_path):
    class BrokenClient:
        def chat(self, messages, tools):
            raise RuntimeError("test bench failure")

    with pytest.raises(RuntimeError, match="environment failure: test bench failure"):
        run(tmp_path, client=BrokenClient())
    path = tmp_path / f"{SPEC.name}.summary.json"
    assert json.loads(path.read_bytes())["failure_kind"] == "environment"
    assert not (tmp_path / f"{SPEC.name}.receipt.json").exists()
    with pytest.raises(ValueError, match="unresolved environment failure"):
        run(tmp_path)


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
    assert len(conditions) == 1824


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


def test_length_is_retained_and_never_retried_on_resume(tmp_path):
    class LengthClient(RecordingClient):
        def chat(self, messages, tools):
            if not self.requests:
                super().chat(messages, tools)
                return ChatResponse({"content": "incomplete"}, "length")
            return super().chat(messages, tools)

    rows = run(tmp_path, client=LengthClient())
    assert (rows[0]["failure_kind"], rows[0]["length_finishes"], rows[0]["parse_errors"]) == (
        None,
        1,
        1,
    )

    class NoCalls:
        def chat(self, messages, tools):
            pytest.fail("A completed episode with an LLM error must be reused")

    assert run(tmp_path, client=NoCalls()) == rows


def test_parallel_hosted_retry_and_resume_keep_attempts_and_started_utc(tmp_path, monkeypatch):
    specs = [SPEC, replace(SPEC, repeat=1)]
    first_pair = threading.Barrier(2, timeout=10)
    attempts = {0: [], 1: []}
    initial = True
    secret = "test-only-api-key"
    model = "deepseek-v4-1-flash-1017"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)

    def mock_post(request, timeout):
        payload = json.loads(request.data)
        seed = payload["random_seed"]
        attempts[seed].append(request.data)
        count = len(attempts[seed])
        assert request.get_header("Authorization") == f"Bearer {secret}"
        headers = Message()
        headers["x-request-id"] = f"request-{seed}-{count}"
        if initial and count == 1:
            first_pair.wait()
            if seed == 0:
                headers["Retry-After"] = "0"
                raise urllib.error.HTTPError(request.full_url, 429, "", headers, None)
            return BytesIO(b'{"choices":[]}')
        if initial and seed == 0 and count == 2:
            raise TimeoutError("mock timeout")
        text = payload["messages"][-1]["content"]
        logical_time = int(text.split(";", 1)[0].split("=")[1])
        tool = "wait_until" if logical_time < 40 else "finish"
        arguments = {"target_time": 40} if logical_time < 40 else {}
        if "phase=message_round;" in text:
            tool, arguments = "skip_round", {}
        message = {"tool_calls": [{"function": {"name": tool, "arguments": json.dumps(arguments)}}]}
        body = json.dumps(
            {"id": f"completion-{seed}-{count}", "model": model, "choices": [{"message": message}]}
        ).encode()
        reply = BytesIO(body)
        reply.headers = headers
        return reply

    monkeypatch.setattr("urllib.request.urlopen", mock_post)

    def factory(seed):
        return OpenAICompatibleClient(
            provider_config("mistral", LLMConfig(model=model, seed=seed), retry_backoff_s=0)
        )

    def go(started, workers=2):
        return run_specs(
            specs,
            ROOT,
            tmp_path,
            factory,
            workers=workers,
            run_identity={"provider": "mistral", "started_utc": started},
        )

    rows = go("2026-11-25T08:00:00+00:00")
    assert rows[0]["failure_kind"] is None and rows[1]["failure_kind"] == "transport"
    manifest = (tmp_path / "run_manifest.json").read_bytes()
    assert json.loads(manifest)["workers"] == 2
    turns = [
        json.loads(line) for line in (tmp_path / f"{SPEC.name}.llm.jsonl").read_bytes().splitlines()
    ]
    trace = next(turn["http"] for turn in turns if len(turn["http"]["attempts"]) == 3)
    assert trace["payload_sha256"] == hashlib.sha256(attempts[0][0]).hexdigest()
    assert attempts[0][0] == attempts[0][1] == attempts[0][2]
    assert [attempt["outcome"] for attempt in trace["attempts"]] == [
        "rate_limited",
        "timeout",
        "response",
    ]
    assert trace["attempts"][0]["request_id"] == "request-0-1"
    assert trace["response_id"] == "completion-0-3"
    assert trace["response_model"] == model
    assert secret not in json.dumps(turns)
    before = len(attempts[0])
    initial = False
    resumed = go("2026-11-25T09:00:00+00:00")
    assert resumed[0] == rows[0] and resumed[1]["failure_kind"] is None
    assert (tmp_path / "run_manifest.json").read_bytes() == manifest
    assert len(attempts[0]) == before
    archived = tmp_path / "attempts" / specs[1].name / "attempt_001"
    interrupted = json.loads((archived / f"{specs[1].name}.llm.jsonl").read_bytes())
    assert interrupted["http"]["attempts"][0]["outcome"] == "malformed_response"
    with pytest.raises(ValueError, match="configuration differs"):
        go("2026-11-25T09:00:00+00:00", workers=1)
