import hashlib
import json
import re
import shutil
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from project_d.environment.model import Scenario, load_scenario
from project_d.evaluation.metrics import optimal_utility
from project_d.experiments.generator import generate, profile_key, validate_dataset
from project_d.experiments.matrix import DATA_ROOT


@pytest.fixture(scope="module", params=("generated", "repository"))
def dataset(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, dict]:
    if request.param == "repository":
        path = Path(__file__).resolve().parents[1] / DATA_ROOT
        return path, json.loads((path / "manifest.json").read_bytes())
    path = tmp_path_factory.mktemp("protocol")
    return path, generate(path)


def test_determinism(dataset: tuple[Path, dict], tmp_path: Path) -> None:
    path, manifest = dataset
    same = tmp_path / "same"
    generate(same, seed=manifest["seed"])
    for relative in (*manifest["files"], "manifest.json"):
        assert (path / relative).read_bytes() == (same / relative).read_bytes()

    other = generate(tmp_path / "other", seed=manifest["seed"] + 1)
    assert other["e3_subset"] == manifest["e3_subset"]
    assert other["files"] != manifest["files"]


def test_manifest_counts_hashes_and_e3_subset(dataset: tuple[Path, dict]) -> None:
    path, manifest = dataset
    assert json.loads((path / "manifest.json").read_bytes()) == manifest
    assert {file.relative_to(path).as_posix() for file in path.glob("*/*.json")} == set(
        manifest["files"]
    )
    counts = Counter()
    e3_counts = Counter()
    e3_strata: dict[str, set[tuple[int, ...]]] = {}
    for relative, record in manifest["files"].items():
        split = relative.split("/")[0]
        scenario = load_scenario(path / relative)
        assert record["sha256"] == hashlib.sha256((path / relative).read_bytes()).hexdigest()
        assert scenario.family == record["family"]
        assert relative == f"{split}/{scenario.scenario_id}.json"
        counts[split, scenario.family] += 1
        if relative in manifest["e3_subset"]:
            assert split == "test"
            e3_counts[scenario.family] += 1
            shape = tuple(record["features"]["jobs_per_agent"])
            e3_strata.setdefault(scenario.family, set()).add(shape)
    assert counts == {
        ("dev", "S0"): 2,
        ("dev", "S1"): 2,
        ("dev", "S2"): 2,
        ("dev", "S3"): 2,
        ("dev", "S4"): 2,
        ("test", "S0"): 4,
        ("test", "S1"): 6,
        ("test", "S2"): 6,
        ("test", "S3"): 6,
        ("test", "S4"): 6,
    }
    assert len(manifest["e3_subset"]) == 12
    assert e3_counts == {"S1": 3, "S2": 3, "S3": 3, "S4": 3}
    assert all(strata == {(1, 1), (2, 2), (3, 3)} for strata in e3_strata.values())
    assert manifest["e4_message_delays"] == [1, 4, 8]
    assert validate_dataset(path) == manifest


def test_constraints_and_no_duplicates_or_leakage(dataset: tuple[Path, dict]) -> None:
    path, manifest = dataset
    seen = set()
    job_counts, option_counts, edge_counts = set(), set(), set()
    for relative, record in manifest["files"].items():
        scenario = load_scenario(path / relative)
        assert (scenario.horizon, scenario.agent_turn_limit) == (80, 24)
        assert (scenario.commit_delay, scenario.message_delay) == (2, 1)
        assert manifest["submission_open_at"] == 40
        key = profile_key(scenario)
        assert key == profile_key(scenario.with_role_swap())
        assert key not in seen
        seen.add(key)

        jobs = [job for agent in scenario.agents for job in agent.jobs]
        features = record["features"]
        assert features["jobs_per_agent"] == [len(agent.jobs) for agent in scenario.agents]
        assert features["options_per_job"] == [len(job.options) for job in jobs]
        assert features["dependency_edges"] == sum(len(job.requires) for job in jobs)
        edge_counts.add(features["dependency_edges"])
        for agent in scenario.agents:
            job_counts.add(len(agent.jobs))
            assert re.search(r"[\u0400-\u04ff]", agent.user_request)
            assert not re.search(r"\d|value|стоимост|кредит", agent.user_request, re.I)
            for job in agent.jobs:
                assert set(job.requires) <= {item.job_id for item in agent.jobs}
                option_counts.add(len(job.options))
                assert all(1 <= option.duration <= 6 for option in job.options)
                if len(job.options) > 1:
                    assert "сокращённ" in agent.user_request.lower()
                    assert job.options[0].value > job.options[-1].value
    assert job_counts == option_counts == {1, 2, 3}
    assert 0 in edge_counts and max(edge_counts) >= 2


def _u_star(scenario: Scenario) -> int:
    return optimal_utility(scenario, submission_open_at=40)[0]


def test_family_properties(dataset: tuple[Path, dict]) -> None:
    path, manifest = dataset
    for relative, record in manifest["files"].items():
        scenario = load_scenario(path / relative)
        a, b = scenario.agents
        jobs = (*a.jobs, *b.jobs)
        optimum, plan = optimal_utility(scenario, 40)
        assert optimum == record["u_star"] > 0
        chosen = {item.job_id: item.option_id for item in plan}
        a_root, b_root = a.jobs[0], b.jobs[0]
        a_full, b_full = a_root.options[0], b_root.options[0]
        if scenario.family == "S0":
            assert optimum == sum(max(o.value for o in j.options) for j in jobs)
            assert len(chosen) == len(jobs)
        elif scenario.family == "S1":
            assert scenario.budget < sum(min(o.cost for o in j.options) for j in jobs)
            for agent in (a, b):
                assert _u_star(replace(scenario, agents=(agent,))) == sum(
                    max(o.value for o in j.options) for j in agent.jobs
                )
        else:
            assert max(a_full.cost, b_full.cost) <= scenario.budget < a_full.cost + b_full.cost
            if scenario.family == "S2":
                restricted = replace(a, jobs=(replace(a_root, options=(a_full,)), *a.jobs[1:]))
                assert _u_star(replace(scenario, agents=(restricted, b))) < optimum
                assert chosen[a_root.job_id] == "short" and b_root.job_id in chosen
            elif scenario.family == "S3":
                assert a_full.value > _u_star(replace(scenario, agents=(b,)))
                assert chosen[a_root.job_id] == "full"
            else:
                assert a_root.options[1].cost + b_full.cost <= scenario.budget
                assert b_root.options[1].cost + a_full.cost <= scenario.budget
                assert {a_root.job_id, b_root.job_id} <= chosen.keys()
                assert "short" in (chosen[a_root.job_id], chosen[b_root.job_id])


@pytest.mark.parametrize("mutation", ("bytes", "extra_file", "features", "u_star", "e3"))
def test_validation_rejects_changed_dataset(
    dataset: tuple[Path, dict], tmp_path: Path, mutation: str
) -> None:
    source, _ = dataset
    root = tmp_path / "scenarios"
    shutil.copytree(source, root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    relative = "dev/dev_s0_01.json"
    if mutation == "bytes":
        profile = root / relative
        profile.write_bytes(profile.read_bytes().replace(b"\n", b"\r\n"))
    elif mutation == "extra_file":
        (root / "dev/extra.json").write_bytes(b"{}\n")
    else:
        if mutation == "features":
            manifest["files"][relative]["features"]["dependency_edges"] += 1
        elif mutation == "u_star":
            manifest["files"][relative]["u_star"] += 1
        else:
            manifest["e3_subset"] = manifest["e3_subset"][1:]
        manifest_path.write_bytes((json.dumps(manifest) + "\n").encode("utf-8"))
    with pytest.raises(ValueError):
        validate_dataset(root)
