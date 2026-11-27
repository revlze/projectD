from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from project_d.agents.llm_client import HTTPTrace, LLMConfig, OpenAICompatibleClient
from project_d.experiments.matrix import DATA_ROOT, EpisodeSpec, run_specs
from project_d.experiments.replay_check import main
from test_baseline_contract import RecordingClient


class OfflineClient(RecordingClient):
    def __init__(self, config: LLMConfig) -> None:
        super().__init__()
        self.payload_builder = OpenAICompatibleClient(config)

    def chat(self, messages, tools):
        response = super().chat(messages, tools)
        body = json.dumps(self.payload_builder.build_payload(messages, tools), ensure_ascii=False)
        return replace(
            response, http=HTTPTrace(hashlib.sha256(body.encode("utf-8")).hexdigest(), (), 0)
        )


@pytest.fixture
def recorded_run(tmp_path: Path) -> EpisodeSpec:
    spec = EpisodeSpec("E5-dev", "dev/dev_s1_01.json", "A/VBC-F", 3)
    llm = LLMConfig(tool_call_id_style="alnum9", request_metadata=True)
    settings = asdict(llm)
    settings.pop("seed")

    def factory(seed: int) -> OfflineClient:
        return OfflineClient(replace(llm, seed=seed))

    def forbid_retry(seed: int) -> OfflineClient:
        pytest.fail(f"completed episode retried with seed {seed}")

    kwargs = {"run_identity": {"llm": settings}, "base_seed": 10}
    rows = run_specs([spec], DATA_ROOT, tmp_path, factory, **kwargs)
    assert not rows[0]["audit_issues"]
    assert run_specs([spec], DATA_ROOT, tmp_path, forbid_retry, **kwargs) == rows
    return spec


@pytest.mark.parametrize(
    ("suffix", "expected"),
    [
        ("llm", "request mismatch at turn 1 (A at t=0) request.messages[0].content"),
        ("log", "journal mismatch at line 1 $.metadata.budget"),
    ],
)
def test_replay_rejects_edited_copy(
    tmp_path: Path, recorded_run: EpisodeSpec, suffix: str, expected: str, capsys
) -> None:
    assert main([str(tmp_path)]) == 0
    assert (
        "Total: 1 episodes, 0 request mismatches, 0 journal mismatches" in capsys.readouterr().out
    )
    path = tmp_path / f"{recorded_run.name}.{suffix}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    first = json.loads(lines[0])
    if suffix == "llm":
        first["request"]["messages"][0]["content"] += " altered"
    else:
        first["metadata"]["budget"] += 1
    lines[0] = json.dumps(first, ensure_ascii=False) + "\n"
    path.write_text("".join(lines), encoding="utf-8")
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr()
    assert f"{recorded_run.name}: {expected}" in output.err
