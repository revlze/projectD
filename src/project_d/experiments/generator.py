"""Generate or validate the development and test scenario dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, replace
from itertools import permutations
from pathlib import Path
from random import Random

from project_d.environment.model import (
    PROTOCOL_HORIZON,
    PROTOCOL_SUBMISSION_OPEN_AT,
    PROTOCOL_TURN_LIMIT,
    ROUND_TIMES,
    AgentSpec,
    Job,
    Option,
    Scenario,
    load_scenario,
)
from project_d.evaluation.metrics import optimal_utility

DEFAULT_SEED = 20261123
FAMILIES = ("S0", "S1", "S2", "S3", "S4")
DEV_SHAPES = ((1, 2), (3, 2))
TEST_SHAPES = ((1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 1))
E3_SLOTS = (0, 2, 4)
E4_DELAYS = (1, 4, 8)

TASKS = (
    (
        ("qa", "проверить качество модели"),
        ("qa_report", "подготовить отчёт для обсуждения"),
        ("error_review", "разобрать типичные ошибки"),
    ),
    (
        ("regression", "провести регрессионную проверку"),
        ("ablation", "проверить влияние доработок"),
        ("release_notes", "подготовить заметки к релизу"),
    ),
)


def _options(rng: Random, cost: int, value: int, savings: int = 0) -> tuple[Option, ...]:
    full = Option("full", cost, rng.randint(1, 6), value)
    if not savings:
        return (full,)
    short = Option(
        "short", cost - savings, rng.randint(1, full.duration), value - rng.randint(2, 4)
    )
    return full, short


def _agent(rng: Random, index: int, count: int, family: str, pattern: int) -> AgentSpec:
    tasks = TASKS[index]
    root_id, root_label = tasks[0]
    if family == "S3":
        value = rng.randint(26, 32) if index == 0 else rng.randint(7, 10)
        priority = "Обязательно" if index == 0 else "По возможности"
    else:
        value = rng.randint(13, 20)
        priority = "Прежде всего нужно"
    savings = rng.randint(4, 6) if family == "S4" or (family == "S2" and index == 0) else 0
    root_options = _options(rng, rng.randint(10, 14), value, savings)
    jobs = [Job(root_id, root_options)]
    request = [f"{priority} {root_label}."]
    if savings:
        request.append(
            "Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый."
        )

    for job_index, (job_id, label) in enumerate(tasks[1:count], start=1):
        option_count = 1 + (pattern + index + job_index) % 3
        strengths = (("full", 3), ("medium", 2), ("short", 1))
        allowed = {1: (0,), 2: (0, 2), 3: (0, 1, 2)}[option_count]
        options = tuple(
            Option(strengths[i][0], strengths[i][1], rng.randint(1, 6), strengths[i][1])
            for i in allowed
        )
        requires = ()
        if pattern % 3 == 1:
            requires = (root_id,)
        elif pattern % 3 == 2:
            requires = (jobs[-1].job_id,)
        jobs.append(Job(job_id, options, requires))

        when = ""
        if requires:
            when = "После основной проверки " if requires == (root_id,) else "После этой работы "
        if when:
            request.append(f"{when}по возможности стоит {label}.")
        else:
            request.append(f"Если останется возможность, стоит {label}.")
        if option_count == 2:
            request.append("Для этой дополнительной работы подойдёт и сокращённый вариант.")
        elif option_count == 3:
            request.append(
                "Для этой дополнительной работы полный вариант предпочтителен, "
                "промежуточный тоже подходит. Сокращённый оставь на крайний случай."
            )
    return AgentSpec(("A", "B")[index], " ".join(request), tuple(jobs))


def _candidate(
    rng: Random, scenario_id: str, family: str, shape: tuple[int, int], pattern: int
) -> Scenario:
    a, b = agents = tuple(
        _agent(rng, index, count, family, pattern) for index, count in enumerate(shape)
    )
    jobs = (*a.jobs, *b.jobs)
    preferred_cost = sum(job.options[0].cost for job in jobs)
    cheapest_cost = sum(min(o.cost for o in job.options) for job in jobs)
    primary_cost = a.jobs[0].options[0].cost + b.jobs[0].options[0].cost
    deficit = rng.randint(1, 2) if pattern % 2 == 0 else rng.randint(3, 4)
    match family:
        case "S0":
            budget = preferred_cost + rng.randint(0, 7)
        case "S1":
            budget = cheapest_cost - deficit
        case _:
            budget = primary_cost - deficit
    return Scenario(
        scenario_id,
        family,
        budget,
        PROTOCOL_HORIZON,
        2,
        1,
        PROTOCOL_TURN_LIMIT,
        rng.randrange(2**32),
        agents,
    )


def _optimize(scenario: Scenario) -> tuple[int, set[tuple[str, str]]]:
    value, plan = optimal_utility(scenario, PROTOCOL_SUBMISSION_OPEN_AT)
    return value, {(item.job_id, item.option_id) for item in plan}


def _preferred_only(scenario: Scenario) -> Scenario:
    return replace(
        scenario,
        agents=tuple(
            replace(agent, jobs=tuple(replace(job, options=job.options[:1]) for job in agent.jobs))
            for agent in scenario.agents
        ),
    )


def _family_holds(scenario: Scenario, optimum: int, plan: set[tuple[str, str]]) -> bool:
    a, b = scenario.agents
    a_root, b_root = a.jobs[0], b.jobs[0]
    solo_a, _ = _optimize(replace(scenario, agents=(a,)))
    solo_b, _ = _optimize(replace(scenario, agents=(b,)))
    preferred = _preferred_only(scenario)
    preferred_optimum, _ = _optimize(preferred)
    a_full, b_full = a_root.options[0], b_root.options[0]
    preferred_values = [sum(j.options[0].value for j in agent.jobs) for agent in (a, b)]

    if scenario.family == "S0":
        return optimum == sum(preferred_values)
    if scenario.family == "S1":
        return (
            (solo_a, solo_b) == tuple(preferred_values)
            and sum(min(o.cost for o in j.options) for j in (*a.jobs, *b.jobs)) > scenario.budget
            and optimum < solo_a + solo_b
        )

    # Both primary work items are feasible separately, but their full forms conflict.
    if not max(a_full.cost, b_full.cost) <= scenario.budget < a_full.cost + b_full.cost:
        return False
    if scenario.family == "S3":
        return a_full.value > solo_b and (a_root.job_id, "full") in plan

    primary_jobs = {a_root.job_id, b_root.job_id}
    if not (optimum > preferred_optimum and primary_jobs <= {job for job, _ in plan}):
        return False
    if scenario.family == "S2":
        no_short = replace(
            scenario,
            agents=(
                replace(a, jobs=(replace(a_root, options=(a_full,)), *a.jobs[1:])),
                b,
            ),
        )
        return _optimize(no_short)[0] < optimum

    # Either user can revise an individually feasible full plan to make room for
    # the other's full primary job. The E4 grid spans timely and stale delivery.
    round_gap = ROUND_TIMES[1] - ROUND_TIMES[0]
    return (
        a_root.options[-1].cost + b_full.cost <= scenario.budget
        and b_root.options[-1].cost + a_full.cost <= scenario.budget
        and max(E4_DELAYS[:2]) <= round_gap < E4_DELAYS[-1]
    )


def profile_key(scenario: Scenario) -> tuple:
    """Canonicalize the economic profile under agent, job and option renaming."""
    agent_keys = []
    for agent in scenario.agents:
        orders = []
        for order in permutations(agent.jobs):
            indices = {job.job_id: i for i, job in enumerate(order)}
            orders.append(
                tuple(
                    (
                        tuple(sorted((o.cost, o.duration, o.value) for o in job.options)),
                        tuple(sorted(indices[r] for r in job.requires)),
                    )
                    for job in order
                )
            )
        agent_keys.append(min(orders))
    return scenario.budget, tuple(sorted(agent_keys))


def _features(scenario: Scenario) -> dict:
    jobs = [job for agent in scenario.agents for job in agent.jobs]
    preferred_cost = sum(job.options[0].cost for job in jobs)
    a, b = (agent.jobs[0].options[0] for agent in scenario.agents)
    return {
        "jobs_per_agent": [len(agent.jobs) for agent in scenario.agents],
        "options_per_job": [len(job.options) for job in jobs],
        "dependency_edges": sum(len(job.requires) for job in jobs),
        "preferred_total_cost": preferred_cost,
        "cheapest_total_cost": sum(min(o.cost for o in job.options) for job in jobs),
        "primary_cost_over_budget": max(0, a.cost + b.cost - scenario.budget),
        "preferred_cost_over_budget": max(0, preferred_cost - scenario.budget),
        "primary_priority_gap": abs(a.value - b.value),
    }


def _write_json(path: Path, payload: dict) -> str:
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def generate(out: str | Path, seed: int = DEFAULT_SEED) -> dict:
    """Write both splits and return the manifest."""
    out = Path(out)
    rng = Random(seed)
    seen: set[tuple] = set()
    files = {}
    e3_subset = []
    for split in ("dev", "test"):
        (out / split).mkdir(parents=True, exist_ok=True)
        for family_index, family in enumerate(FAMILIES):
            shapes = DEV_SHAPES if split == "dev" else TEST_SHAPES
            if split == "test" and family == "S0":
                shapes = shapes[:4]
            for slot, shape in enumerate(shapes):
                scenario_id = f"{split}_{family.lower()}_{slot + 1:02d}"
                path = f"{split}/{scenario_id}.json"
                if split == "test" and family != "S0" and slot in E3_SLOTS:
                    e3_subset.append(path)
                pattern = slot + family_index + (1 if split == "dev" else 0)
                for _ in range(200):
                    scenario = _candidate(rng, scenario_id, family, shape, pattern)
                    key = profile_key(scenario)
                    if key in seen:
                        continue
                    optimum, plan = _optimize(scenario)
                    if _family_holds(scenario, optimum, plan):
                        break
                else:
                    raise RuntimeError(f"could not construct a distinct {scenario_id} profile")
                seen.add(key)
                payload = asdict(scenario)
                for agent in payload["agents"]:
                    for job in agent["jobs"]:
                        if not job["requires"]:
                            del job["requires"]
                files[path] = {
                    "sha256": _write_json(out / path, payload),
                    "family": family,
                    "features": _features(scenario),
                    "u_star": optimum,
                }
    manifest = {
        "seed": seed,
        "submission_open_at": PROTOCOL_SUBMISSION_OPEN_AT,
        "e3_selection_rule": "Within each of S1-S4, select fixed job-count strata "
        "(1,1), (2,2), and (3,3).",
        "e3_subset": e3_subset,
        "e4_message_delays": list(E4_DELAYS),
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def validate_dataset(root: str | Path) -> dict:
    """Check the actual dataset without rewriting inputs or their manifest.

    Family and utility checks share the generator's definitions. An independent
    portfolio oracle and executable schedule checks live in test_scenarios.py.
    """
    root = Path(root)
    manifest_path = root / "manifest.json"
    manifest_data = manifest_path.read_bytes()
    if b"\r" in manifest_data:
        raise ValueError("manifest.json must use LF line endings")
    manifest = json.loads(manifest_data)
    expected_files = {
        f"{split}/{split}_{family.lower()}_{slot + 1:02d}.json": (family, shape)
        for split in ("dev", "test")
        for family in FAMILIES
        for slot, shape in enumerate(
            DEV_SHAPES if split == "dev" else TEST_SHAPES[:4] if family == "S0" else TEST_SHAPES
        )
    }
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*.json")}
    if actual_files != set(expected_files) | {"manifest.json"}:
        raise ValueError("dataset must contain exactly the 10 dev and 28 test profiles")
    if set(manifest["files"]) != set(expected_files):
        raise ValueError("manifest profile inventory differs from the dataset contract")
    expected_e3 = [
        f"test/test_{family.lower()}_{slot + 1:02d}.json"
        for family in FAMILIES[1:]
        for slot in E3_SLOTS
    ]
    if manifest["e3_subset"] != expected_e3:
        raise ValueError("E3 subset must use the fixed (1,1), (2,2), (3,3) strata")
    if manifest["submission_open_at"] != PROTOCOL_SUBMISSION_OPEN_AT:
        raise ValueError("manifest has an unexpected submission opening")
    if manifest["e4_message_delays"] != list(E4_DELAYS):
        raise ValueError("manifest has unexpected E4 message delays")

    seen = set()
    for relative, (family, shape) in expected_files.items():
        data = (root / relative).read_bytes()
        record = manifest["files"][relative]
        if b"\r" in data or hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"{relative}: bytes differ from the LF manifest SHA-256")
        scenario = load_scenario(root / relative)
        if scenario.scenario_id != Path(relative).stem or scenario.family != family:
            raise ValueError(f"{relative}: scenario ID or family differs from its path")
        if tuple(agent.agent_id for agent in scenario.agents) != ("A", "B"):
            raise ValueError(f"{relative}: expected two agents A and B")
        if tuple(len(agent.jobs) for agent in scenario.agents) != shape:
            raise ValueError(f"{relative}: unexpected job-count stratum")
        if any(
            not 1 <= option.duration <= 6
            for agent in scenario.agents
            for job in agent.jobs
            for option in job.options
        ):
            raise ValueError(f"{relative}: option duration must be between 1 and 6")
        timing = (
            scenario.horizon,
            scenario.agent_turn_limit,
            scenario.commit_delay,
            scenario.message_delay,
        )
        if timing != (PROTOCOL_HORIZON, PROTOCOL_TURN_LIMIT, 2, 1):
            raise ValueError(f"{relative}: unexpected base timing or turn limit")
        if record["family"] != family or record["features"] != _features(scenario):
            raise ValueError(f"{relative}: manifest features differ from the profile")
        optimum, plan = _optimize(scenario)
        if record["u_star"] != optimum or optimum <= 0:
            raise ValueError(f"{relative}: manifest U* differs from the computed optimum")
        if not _family_holds(scenario, optimum, plan):
            raise ValueError(f"{relative}: family constraints do not hold")
        key = profile_key(scenario)
        if key in seen:
            raise ValueError(f"{relative}: duplicate economic profile across dev/test")
        seen.add(key)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--out", type=Path)
    operation.add_argument("--check", type=Path, help="Validate existing files without rewriting")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.check is not None:
        manifest = validate_dataset(args.check)
        print(json.dumps({"profiles": len(manifest["files"]), "status": "valid"}))
    else:
        generate(args.out, args.seed)


if __name__ == "__main__":
    main()
