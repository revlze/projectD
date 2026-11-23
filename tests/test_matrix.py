from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_d.agents.llm_client import ChatResponse
from project_d.agents.prompts import PROMPT_VERSION
from project_d.experiments.matrix import (
    DATA_ROOT,
    build_matrix,
    load_manifest,
    main,
    run_e0,
    run_specs,
    verify_profiles,
)

ROOT = Path(__file__).parents[1] / DATA_ROOT


class FinishClient:
    def chat(self, messages, tools) -> ChatResponse:
        call = {"id": "c", "function": {"name": "finish", "arguments": "{}"}}
        return ChatResponse({"role": "assistant", "content": "", "tool_calls": [call]})


@pytest.mark.parametrize(
    ("series", "episodes"),
    [("E1", 560), ("E2", 1008), ("E3", 240), ("E4-H1", 144), ("E4-delay", 144)],
)
def test_matrix_sizes_match_plan(series: str, episodes: int) -> None:
    specs = build_matrix(series, load_manifest(ROOT))
    assert len(specs) == episodes
    assert len({spec.name for spec in specs}) == episodes


def test_dev_series_never_uses_test_profiles() -> None:
    assert {s.split for s in build_matrix("E1", load_manifest(ROOT))} == {"dev"}


def test_test_split_requires_explicit_full_run(capsys) -> None:
    assert main(["E2", "--data-root", str(ROOT)]) == 2
    assert main(["E2", "--data-root", str(ROOT), "--allow-test", "--repeats", "1"]) == 2
    assert "full series" in capsys.readouterr().err


def test_modified_profile_is_refused(tmp_path: Path) -> None:
    manifest = load_manifest(ROOT)
    profile = next(p for p in manifest["files"] if p.startswith("dev/"))
    target = tmp_path / profile
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / profile).read_bytes() + b" ")
    with pytest.raises(ValueError, match="frozen manifest"):
        verify_profiles(tmp_path, manifest, [profile])


def test_runner_pairs_seeds_and_resumes(tmp_path: Path) -> None:
    specs = [
        s
        for s in build_matrix("E1", load_manifest(ROOT))
        if s.profile.endswith("dev_s2_01.json") and s.variant in ("A/R3P", "A/VBC")
    ]
    seeds: list[int] = []

    def factory(seed: int) -> FinishClient:
        seeds.append(seed)
        return FinishClient()

    rows = run_specs(specs, ROOT, tmp_path, factory, base_seed=10)
    assert len(rows) == 8
    assert sorted(seeds) == sorted([10, 11, 12, 13] * 2)
    assert all(row["audit_issues"] == 0 and row["U_safe"] == 0 for row in rows)
    assert (tmp_path / "summary.csv").exists()
    seeds.clear()
    run_specs(specs, ROOT, tmp_path, factory, base_seed=10)
    assert seeds == []
    saved = json.loads((tmp_path / f"{specs[0].name}.prompts.json").read_text(encoding="utf-8"))
    assert saved["version"] == PROMPT_VERSION


def test_e0_table(tmp_path: Path) -> None:
    rows = run_e0(tmp_path)
    assert len(rows) == 108
    assert not any(r["audit_issues"] for r in rows)
    assert not any(r["violated"] for r in rows if r["mode"] == "B2")
    assert any(r["violated"] for r in rows if r["mode"] == "B0")
