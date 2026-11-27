"""Run short traces on the project's real Python Environment, without an LLM."""
from __future__ import annotations

import json
from pathlib import Path

from project_d.environment.actions import ConfirmPlan, ProposePlan, SkipRound, SubmitJob
from project_d.environment.env import Environment
from project_d.environment.model import AgentSpec, Job, Option, RunConfig, Scenario
from project_d.evaluation.audit import audit_episode

QA = ("qa", "full")
SHORT = ("qa", "short")
REPORT = ("report", "full")
REG = ("regression", "full")
ABL = ("ablation", "full")


def scenario(delay: int = 2, budget: int = 12) -> Scenario:
    def opt(name: str, cost: int) -> Option:
        return Option(name, cost, 2, 1)

    return Scenario(
        "formal_trace", "FORMAL", budget, 80, delay, 1, 24, 0,
        (
            AgentSpec("A", "A", (Job("qa", (opt("full", 7), opt("short", 4))),
                                Job("report", (opt("full", 2),), ("qa",)))),
            AgentSpec("B", "B", (Job("regression", (opt("full", 6),)),
                                Job("ablation", (opt("full", 1),), ("regression",)))),
        ),
    )


def env_for(variant: str, delay: int = 2, budget: int = 12) -> Environment:
    return Environment(scenario(delay, budget), RunConfig.for_protocol(variant))


def expect(env: Environment, agent: str, action, status: str) -> None:
    result = env.execute(agent, action)
    assert result.status.value == status, (agent, action, result)


def submit(env: Environment, agent: str, pair: tuple[str, str], status: str) -> None:
    expect(env, agent, SubmitJob(*pair), status)


def agree(env: Environment, a, b, *, confirm_a=True, confirm_b=True, revision_a=None) -> None:
    env.advance_to(6)
    if a is not None:
        expect(env, "A", ProposePlan(tuple(a)), "ok")
    if b is not None:
        expect(env, "B", ProposePlan(tuple(b)), "ok")
    env.advance_to(13)
    for agent in ("A", "B"):
        expect(env, agent, SkipRound(), "ok")
    env.advance_to(33)
    if revision_a is not None:
        expect(env, "A", ProposePlan(tuple(revision_a)), "ok")
    env.advance_to(37)
    for agent, confirms in (("A", confirm_a), ("B", confirm_b)):
        if confirms:
            expect(env, agent, ConfirmPlan(2), "ok" if a is not None and b is not None else "invalid_plan")
    env.advance_to(40)
    agreement = [e for e in env.log if e.event_type == "agreement"][-1]
    assert agreement.result == ("agreed" if a is not None and b is not None and confirm_a and confirm_b else "agreement_failed")


def finish(name: str, env: Environment, *, spent: int, releases: int, violated: bool) -> dict:
    env.advance_to(80)
    assert (env.spent, env.held) == (spent, 0)
    assert sum(e.event_type == "plan_released" for e in env.log) == releases
    audit = audit_episode(env.metadata, env.log)
    assert audit.violated == violated, (name, audit)
    assert not audit.issues, (name, audit.issues)
    events = [dict(time=e.time, event=e.event_type, result=e.result, agent=e.agent_id,
                   job=e.job_id, option=e.option_id, spent=e.spent_after, held=e.held_after)
              for e in env.log if e.event_type in {"agreement", "submit", "commit", "complete", "plan_released"}]
    return dict(case=name, spent=spent, released=releases, violated=violated, events=events)


def run() -> list[dict]:
    out = []
    for name, variant, delay, second, total, violation in (
        ("unsafe_overlap", "U/N", 2, "accepted", 13, True),
        ("atomic_overlap", "A/N", 2, "insufficient_budget", 7, False),
        ("unsafe_immediate", "U/N", 0, "insufficient_budget", 7, False),
    ):
        env = env_for(variant, delay)
        env.advance_to(40)
        submit(env, "A", QA, "accepted")
        submit(env, "B", REG, second)
        out.append(finish(name, env, spent=total, releases=0, violated=violation))

    env = env_for("A/VBC")
    agree(env, [QA], [REG])
    submit(env, "A", SHORT, "plan_mismatch")
    env.advance_to(41)
    submit(env, "A", QA, "accepted")
    submit(env, "B", REG, "insufficient_budget")
    assert all(any("PLAN_RELEASED" in notice for notice in env.take_notices(a)) for a in ("A", "B"))
    env.advance_to(45)
    submit(env, "A", REPORT, "accepted")
    out.append(finish("atomic_release_and_fallback", env, spent=9, releases=1, violated=False))

    env = env_for("A/VBC")
    agree(env, [QA, REPORT], [REG], revision_a=[SHORT, REPORT])
    submit(env, "A", REPORT, "prerequisite_not_completed")
    submit(env, "B", REG, "accepted")
    env.advance_to(41)
    submit(env, "A", SHORT, "accepted")
    env.advance_to(45)
    submit(env, "A", REPORT, "accepted")
    out.append(finish("feasible_revised_plan", env, spent=12, releases=0, violated=False))

    env = env_for("A/VBC")
    agree(env, [REPORT], [])
    submit(env, "A", REPORT, "prerequisite_not_completed")
    env.advance_to(41)
    submit(env, "A", QA, "plan_mismatch")
    out.append(finish("dependency_blocks_guarded_plan", env, spent=0, releases=0, violated=False))

    env = env_for("A/S")
    agree(env, [SHORT], [REG])
    submit(env, "A", QA, "accepted")
    submit(env, "B", REG, "insufficient_budget")
    out.append(finish("agreement_without_guard", env, spent=7, releases=0, violated=False))

    env = env_for("U/VBC")
    agree(env, [QA], [REG])
    submit(env, "A", QA, "accepted")
    submit(env, "B", REG, "accepted")
    out.append(finish("unsafe_agreement_over_budget", env, spent=13, releases=0, violated=True))

    for variant in ("U/VBC", "A/VBC"):
        env = env_for(variant)
        agree(env, [QA], None, confirm_b=False)
        submit(env, "A", QA, "accepted")
        submit(env, "B", REG, "accepted" if variant.startswith("U") else "insufficient_budget")
        out.append(finish("missing_plan_" + variant[0], env, spent=13 if variant.startswith("U") else 7,
                          releases=0, violated=variant.startswith("U")))
    # Replay the two structured TLC counterexamples, including the initial
    # empty plans, the second version and the actual confirmation decisions.
    for agreed in (False, True):
        env = env_for("U/VBC")
        env.advance_to(6)
        for agent in ("A", "B"):
            expect(env, agent, ProposePlan(()), "ok")
        env.advance_to(13)
        for agent in ("A", "B"):
            expect(env, agent, SkipRound(), "ok")
        env.advance_to(33)
        expect(env, "A", ProposePlan((QA,) if agreed else ()), "ok")
        expect(env, "B", ProposePlan((REG,) if agreed else ()), "ok")
        env.advance_to(37)
        expect(env, "A", ConfirmPlan(2), "ok")
        if agreed:
            expect(env, "B", ConfirmPlan(2), "ok")
        env.advance_to(40)
        agreement = [e for e in env.log if e.event_type == "agreement"][-1]
        assert agreement.result == ("agreed" if agreed else "agreement_failed")
        assert agreement.detail["enforced"] == agreed
        submit(env, "A", QA, "accepted")
        submit(env, "B", REG, "accepted")
        trace = finish("tlc_u_vbc_agreed" if agreed else "tlc_u_vbc_fallback", env,
                       spent=13, releases=0, violated=True)
        events = [e for e in env.log if e.event_type in {
            "propose_plan", "plan_version", "confirm_plan", "agreement", "submit", "commit"
        }]
        trace["counterexample_projection"] = [
            dict(time=e.time, event=e.event_type, result=e.result, agent=e.agent_id,
                 job=e.job_id, option=e.option_id, spent=e.spent_after, held=e.held_after,
                 detail=e.detail) for e in events
        ]
        assert [(e.event_type, e.job_id, e.spent_after, e.held_after)
                for e in events if e.event_type in {"submit", "commit"}] == [
                    ("submit", "qa", 0, 0), ("submit", "regression", 0, 0),
                    ("commit", "qa", 7, 0), ("commit", "regression", 13, 0)
                ]
        out.append(trace)
    return out


if __name__ == "__main__":
    traces = run()
    output = Path(__file__).resolve().parents[1] / "results" / "python" / "python_traces.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(traces, indent=2) + "\n", encoding="utf-8")
    for trace in traces:
        print(trace["case"], trace["spent"], trace["released"], trace["violated"])
