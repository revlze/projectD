"""Frozen episode selection, negotiation evidence and independent execution facts."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project_d.agents.plan_text import render_plan
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import CONFIRM_TIME, PROPOSE_TIMES, Scenario, load_scenario
from project_d.evaluation.annotation_sample import VARIANTS
from project_d.evaluation.metrics import episode_metrics, root_conflict

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/scenarios"
OUT = ROOT / "results/test-32abf0e/annotation"
MODEL = "deepseek-v4-1-flash-1017"
RUNS = {"E2": OUT.parent / "e2" / MODEL, "E5": ROOT / "results/e5-6a5b6f70" / MODEL}
EXTENSION = "A/VBC-F"
TARGET = ("A/F", "A/VBC", EXTENSION)
AGENTS = ("A", "B")
MAIN_FEATURES = (
    "first_intent",
    "final_intent",
    "cost_mentioned",
    "conflict_detected",
    "own_change_proposed",
    "own_priority_correct",
    "partner_priority_understood",
)
TARGET_FEATURES = (
    "conflict_detected",
    "own_priority_correct",
    "partner_priority_understood",
    "explicit_root_yield",
    "decision_deferred_to_environment",
)
EPISODE_FEATURES = ("submission_order_agreed",)


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_jsonl(path: Path) -> list[dict]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.strip():
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("expected a JSON object")
            except ValueError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
            records.append(record)
    return records


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


@dataclass(frozen=True)
class Episode:
    row: dict
    scenario: Scenario
    journal: Path
    llm: Path


def select() -> list[Episode]:
    manifest = json.loads((DATA / "manifest.json").read_bytes())
    paths = {Path(p).stem: DATA / p for p in manifest["files"] if p.startswith("test/")}
    scenarios = {profile: load_scenario(path) for profile, path in paths.items()}
    main = {Path(p).stem for p in manifest["e3_subset"]}
    contested = {
        profile
        for profile, scenario in scenarios.items()
        if sum(min(o.cost for o in a.jobs[0].options) for a in scenario.agents) > scenario.budget
    }
    if (len(main), len(contested)) != (12, 9):
        raise ValueError("Unexpected frozen sample sizes")
    members: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    for profile in sorted(main):
        for variant in (*VARIANTS, EXTENSION):
            members[profile, variant, 0].append(
                "exploratory_extension" if variant == EXTENSION else "original"
            )
    for profile in sorted(contested):
        for variant in TARGET:
            for repeat in range(4):
                members[profile, variant, repeat].append("target")
    manifests = {k: json.loads((p / "run_manifest.json").read_bytes()) for k, p in RUNS.items()}
    episodes = []
    for (profile, variant, repeat), cohorts in sorted(members.items()):
        series = "E5" if variant == EXTENSION else "E2"
        episode = f"{series}__{profile}__{variant.replace('/', '-')}__r{repeat}"
        run, manifest = RUNS[series], manifests[series]
        record = manifest["episodes"][episode]
        metadata = record["metadata"]
        spec = record["spec"]
        if (spec["variant"], Path(spec["profile"]).stem, spec["repeat"]) != (
            variant,
            profile,
            repeat,
        ):
            raise ValueError(f"{episode}: archived manifest key mismatch")
        if record["scenario_sha256"] != digest(paths[profile].read_bytes()):
            raise ValueError(f"{episode}: scenario differs from frozen run")
        journal = run / f"{episode}.log.jsonl"
        llm = run / f"{episode}.llm.jsonl"
        row = {
            "episode": episode,
            "series": series,
            "variant": variant,
            "profile": profile,
            "repeat": repeat,
            "role_swap": metadata["role_swap"],
            "first_agent": metadata["first_agent"],
            "commit": manifest["runtime"]["git_commit"],
            "journal": _path(journal),
            "llm": _path(llm),
            "samples": cohorts,
        }
        episodes.append(Episode(row, scenarios[profile], journal, llm))
    if len(episodes) != 213:
        raise ValueError("Unexpected union size")
    return episodes


def evidence_id(entry: LogEntry) -> str:
    return f"E{entry.seq:04d}"


def _wire_message(send: LogEntry) -> dict:
    return {"from": send.agent_id, "text": send.detail["text"], "sent_at": send.time}


def _auto_messages(turn: dict) -> list[dict]:
    observation = turn["request"]["messages"][-1]["content"]
    marker = "\nДоставленные сообщения: "  # noqa: RUF001 - literal in the archived request
    at = observation.find(marker)
    return [] if at < 0 else json.JSONDecoder().raw_decode(observation[at + len(marker) :])[0]


def _tool_messages(turn: dict) -> list[dict]:
    messages = []
    for message in turn["request"]["messages"]:
        if message["role"] != "tool":
            continue
        value = json.loads(message["content"])
        messages.extend(value.get("messages", ()))
    return messages


def _availability(
    entries: list[LogEntry], turns: list[dict], opens: dict[str, int]
) -> tuple[dict[int, list[dict]], dict[int, LogEntry]]:
    sends = {
        entry.detail["message_id"]: entry
        for entry in entries
        if entry.event_type == "send_message"
        and entry.result == "ok"
        and entry.time < min(opens.values())
    }
    delivery = {
        entry.detail["message_id"]: entry
        for entry in entries
        if entry.event_type == "message_delivered" and entry.time <= opens[entry.agent_id]
    }
    visibility: dict[int, list[dict]] = defaultdict(list)
    by_agent = {a: [t for t in turns if t["agent_id"] == a] for a in opens}
    for entry in entries:
        agent = entry.agent_id
        if entry.event_type not in ("read_messages", "message_read") or entry.result != "ok":
            continue
        explicit = entry.event_type == "read_messages"
        if entry.time > opens[agent] or (explicit and entry.time == opens[agent]):
            continue
        ids = entry.detail["message_ids"]
        for message_id in ids:
            send, delivered = sends[message_id], delivery[message_id]
            if delivered.agent_id != agent or delivered.time > entry.time:
                raise ValueError(f"{evidence_id(entry)}: message unavailable to {agent}")
            expected = _wire_message(send)
            if explicit:
                read_turn = next(t for t in by_agent[agent] if t["logical_time"] == entry.time)
                if expected not in read_turn["tool_result"]["data"]["messages"]:
                    raise ValueError(
                        f"{evidence_id(entry)}: missing from read_messages tool result"
                    )
                shown = next(
                    (
                        t["logical_time"]
                        for t in by_agent[agent]
                        if entry.time < t["logical_time"] <= opens[agent]
                        and expected in _tool_messages(t)
                    ),
                    None,
                )
            else:
                turn = next(t for t in by_agent[agent] if t["logical_time"] == entry.time)
                if expected not in _auto_messages(turn):
                    raise ValueError(f"{evidence_id(entry)}: missing from saved observation")
                shown = entry.time
            visibility[message_id].append(
                {
                    "id": evidence_id(entry),
                    "kind": "explicit_read" if explicit else "automatic_show",
                    "recipient": agent,
                    "event_t": entry.time,
                    "shown_t": shown,
                }
            )
    return visibility, delivery


def _plan_shows(turns: list[dict], plans: dict[int, dict], opens: dict[str, int]) -> dict:
    shown: dict[int, list[dict]] = defaultdict(list)
    for turn in turns:
        info = turn.get("shown_plan")
        agent, tick = turn["agent_id"], turn["logical_time"]
        if not info or tick > opens[agent]:
            continue
        version = info["plan_version"]
        partner = next(a for a in opens if a != agent)
        view = dict(plans[version])
        if not info["feedback_shown"]:
            view.pop("plan_feedback", None)
        text = render_plan(view, agent, partner)
        if (
            digest(text.encode()) != info["text_sha256"]
            or text not in turn["request"]["messages"][-1]["content"]
        ):
            raise ValueError(f"Plan {version} is missing from {agent}'s saved request at {tick}")
        shown[version].append({"agent": agent, "t": tick, "feedback": info["feedback_shown"]})
    return shown


def negotiation(
    scenario: Scenario, metadata: EpisodeMetadata, entries: list[LogEntry], turns: list[dict]
) -> tuple[str, dict[str, list[list[str]]], list[str]]:
    """Project pre-action evidence only. No execution events or complete request histories."""
    opens = metadata.submission_open_at
    open_at = min(opens.values())
    resolved = scenario.with_role_swap() if metadata.role_swap else scenario
    lines = [
        f"Shared budget: {metadata.budget}. Individual execution opens at {json_text(opens)}.",
        "The catalog below is reference material for the annotator. Each agent can inspect its own "
        "catalog only. Peer information comes from evidence explicitly shown to that agent.",
        "",
        "## User requests and catalog",
        "",
    ]
    catalog = {}
    ids = []
    for agent in resolved.agents:
        agent_id = agent.agent_id
        request_id = f"USER-{agent_id}"
        ids.append(request_id)
        lines.extend(
            (
                f"### Agent {agent_id} [{request_id}]",
                "",
                agent.user_request,
                "",
                f"Main job: `{agent.jobs[0].job_id}`",
            )
        )
        catalog[agent_id] = []
        for job in agent.jobs:
            options = ", ".join(
                f"`{job.job_id}/{option.option_id}`: {option.cost} credits, {option.duration} ticks"
                for option in job.options
            )
            dependencies = ", ".join(job.requires) or "none"
            lines.append(f"- {options}. Prerequisites: {dependencies}.")
            catalog[agent_id].extend([job.job_id, option.option_id] for option in job.options)
        lines.append("")
    visibility, deliveries = _availability(entries, turns, opens)
    plans = {
        entry.detail["plan_version"]: dict(entry.detail)
        for entry in entries
        if entry.event_type == "plan_version"
    }
    for e in entries:
        if e.event_type == "plan_feedback":
            plans[e.detail["plan_version"]]["plan_feedback"] = e.detail
    shows = _plan_shows(turns, plans, opens)
    lines.extend(
        (
            "## Negotiation evidence",
            "",
            "Delivery and appearance in a model request are separate. A null shown_t means "
            "the message was not shown at a decision before execution began. "
            "Environment-added prices in structured items are reference facts.",
            "",
        )
    )
    latest: dict[str, str] = {}
    by_turn = {(turn["agent_id"], turn["logical_time"]): turn for turn in turns}
    events = {
        "send_message",
        "round_skipped",
        "round_missed",
        "propose_plan",
        "plan_version",
        "plan_feedback",
        "confirm_plan",
        "agreement",
    }
    for entry in entries:
        kind, event_id = entry.event_type, evidence_id(entry)
        if entry.time >= open_at and kind != "agreement":
            continue
        if kind == "wait_until" and plans and entry.time in (*PROPOSE_TIMES, CONFIRM_TIME):
            kind = "confirmation_skipped" if entry.time == CONFIRM_TIME else "proposal_skipped"
        elif kind not in events:
            continue
        if kind == "send_message" and entry.result != "ok":
            continue
        detail = entry.detail
        if kind == "send_message":
            message_id = detail["message_id"]
            delivery = deliveries.get(message_id)
            shown = visibility[message_id]
            detail = {
                "recipient": detail["to"],
                "text": detail["text"],
                "scheduled_t": detail["deliver_at"],
                "delivery": (
                    {"id": evidence_id(delivery), "t": delivery.time} if delivery else None
                ),
                "visibility": shown,
            }
            if delivery:
                ids.append(evidence_id(delivery))
            ids.extend(read["id"] for read in shown)
        elif kind == "propose_plan" and entry.result == "ok":
            latest[entry.agent_id] = event_id
            detail = {
                **detail,
                "stage": "revision" if entry.time == PROPOSE_TIMES[-1] else "initial",
            }
        elif kind == "propose_plan":
            turn = by_turn.get((entry.agent_id, entry.time), {})
            calls = turn.get("message", {}).get("tool_calls") or []
            arguments = next(
                (
                    call["function"]["arguments"]
                    for call in calls
                    if call["function"]["name"] == "propose_plan"
                ),
                None,
            )
            detail = {**detail, "attempted_arguments": arguments}
        elif kind == "plan_version":
            version = detail["plan_version"]
            detail = {
                "plan_version": version,
                "proposal_ids": dict(latest),
                "shown": shows[version],
            }
        elif kind == "plan_feedback":
            detail = {
                **detail,
                "shown": [s for s in shows[detail["plan_version"]] if s["feedback"]],
            }
        ids.append(event_id)
        actor = entry.agent_id or "environment"
        lines.append(
            f"- [{event_id}] t={entry.time} {actor} {kind} {entry.result}: {json_text(detail)}"
        )
    return "\n".join(lines) + "\n", catalog, sorted(set(ids))


def objective(
    episode: str, scenario: Scenario, metadata: EpisodeMetadata, entries: list[LogEntry]
) -> tuple[list[dict], dict]:
    scored = episode_metrics(scenario, metadata, entries)
    if scored.audit.issues:
        raise ValueError(f"{episode}: journal audit failed: {scored.audit.issues}")
    conflict = root_conflict(scenario, metadata, entries)
    resolved = scenario.with_role_swap() if metadata.role_swap else scenario
    versions = {
        e.detail["plan_version"]: e.detail["proposals"]
        for e in entries
        if e.event_type == "plan_version"
    }
    agreement = next((e for e in entries if e.event_type == "agreement"), None)
    agreed_version = (
        agreement.detail["plan_version"] if agreement and agreement.result == "agreed" else None
    )
    total = {
        v: sum(item["cost"] for proposal in plans.values() for item in proposal["items"])
        for v, plans in versions.items()
    }
    submitted_at = {}
    root_outcomes = {}
    agents = []
    for agent in resolved.agents:
        a = agent.agent_id
        main = agent.jobs[0].job_id
        submitted = [e for e in entries if e.event_type == "submit" and e.agent_id == a]
        pairs = sorted({(e.job_id, e.option_id) for e in submitted})
        submitted_at[a] = next((e.time for e in submitted if e.job_id == main), None)
        root_results = {e.result for e in submitted if e.job_id == main}
        completed = [e for e in entries if e.agent_id == a and e.event_type == "complete"]
        if conflict.outcomes is not None:
            root_outcomes[a] = conflict.outcomes[a]
        elif any(e.job_id == main for e in completed):
            root_outcomes[a] = "completed"
        elif "accepted" in root_results:
            root_outcomes[a] = "accepted_incomplete"
        elif "insufficient_budget" in root_results:
            root_outcomes[a] = "budget_refused"
        else:
            root_outcomes[a] = "other_refusal" if root_results else "not_submitted"
        agreed = (
            None
            if agreed_version is None
            else {
                (item["job_id"], item["option_id"]) for item in versions[agreed_version][a]["items"]
            }
        )
        agents.append(
            {
                "episode": episode,
                "agent": a,
                "main_job": main,
                "structured_plans": {v: plans.get(a) for v, plans in versions.items()},
                "submitted_pairs": pairs,
                "first_root_submit_t": submitted_at[a],
                "submissions": [
                    {
                        "id": evidence_id(e),
                        "t": e.time,
                        "pair": [e.job_id, e.option_id],
                        "result": e.result,
                    }
                    for e in submitted
                ],
                "completions": [
                    {"id": evidence_id(e), "t": e.time, "pair": [e.job_id, e.option_id]}
                    for e in completed
                ],
                "root_outcome": root_outcomes[a],
                "agreed_plan_matches_submissions": agreed == set(pairs)
                if agreed is not None
                else None,
            }
        )
    won = [a for a, value in root_outcomes.items() if value == "completed"]
    root_values = {a.agent_id: max(o.value for o in a.jobs[0].options) for a in resolved.agents}
    higher_root = (
        root_values[won[0]] == max(root_values.values())
        if len(won) == 1 and len(set(root_values.values())) > 1
        else None
    )
    return agents, {
        "episode": episode,
        "budget": metadata.budget,
        "plan_totals": total,
        "plan_within_budget": {
            v: value <= metadata.budget if set(versions[v]) == set(AGENTS) else None
            for v, value in total.items()
        },
        "agreement": agreement.result if agreement else None,
        "agreed_version": agreed_version,
        "plan_released": any(e.event_type == "plan_released" for e in entries),
        "root_conflict": conflict.conflict,
        "root_submit_gap": abs(submitted_at["B"] - submitted_at["A"])
        if all(t is not None for t in submitted_at.values())
        else None,
        "higher_value_root_completed": higher_root,
        "U": scored.raw_utility,
        "U_safe": scored.safe_utility,
        "U_star": scored.optimal_utility,
        "safe_fraction": scored.safe_fraction,
        "violated": scored.audit.violated,
    }
