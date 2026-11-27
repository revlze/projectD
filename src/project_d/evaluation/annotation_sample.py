"""Manual-annotation sample for free and structured messages (docs/experiments.md, section 4).

Usage: python -m project_d.evaluation.annotation_sample <test results dir> --out <dir>

The sample is fixed before reading any transcript: the 12 `e3_subset` profiles, repeat 0,
the eight communicating baselines and A/VBC, all from E2 (108 episodes). For each episode it
writes a transcript of messages and plan proposals followed by the submissions. Outcome
metrics are left out so that the annotation is not steered by the result. It also writes
one empty sheet per annotator, with one row per agent and `yes|no|unclear` fields.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from project_d.environment.model import load_scenario

DATA = Path(__file__).resolve().parents[3] / "data" / "scenarios"
VARIANTS = ("U/F", "A/F", "U/R1", "A/R1", "U/R3", "A/R3", "U/R3P", "A/R3P", "A/VBC")
ANNOTATORS = ("platon", "seva")
FIELDS = (
    "first_intent",
    "final_intent",
    "cost_mentioned",
    "conflict_detected",
    "own_change_proposed",
    "final_plan_matches_submissions",
    "comment",
)
SHOWN = ("send_message", "propose_plan", "plan_feedback", "confirm_plan", "agreement")


def sample(results: Path) -> list[Path]:
    manifest = json.loads((DATA / "manifest.json").read_bytes())
    profiles = [Path(entry).stem for entry in manifest["e3_subset"]]
    (run,) = sorted((results / "e2").glob("*/summary.csv"))
    paths = [
        run.parent / f"E2__{profile}__{variant.replace('/', '-')}__r0.log.jsonl"
        for profile in profiles
        for variant in VARIANTS
    ]
    missing = [path.name for path in paths if not path.exists()]
    if missing or len(paths) != 108:
        raise ValueError(f"sample incomplete: {missing[:5]}")
    return paths


def transcript(path: Path) -> str:
    raw = [json.loads(line) for line in path.read_bytes().splitlines()]
    metadata, events = raw[0]["metadata"], raw[1:]
    scenario = load_scenario(DATA / "test" / f"{metadata['scenario_id']}.json")
    if metadata["role_swap"]:
        scenario = scenario.with_role_swap()
    lines = [
        f"# {path.name.removesuffix('.log.jsonl')}",
        "",
        f"Budget {metadata['budget']}, horizon {metadata['horizon']}, "
        f"first_agent {metadata['first_agent']}, role_swap {metadata['role_swap']}.",
        "",
        "## Original user requests",
        "",
    ]
    for agent in scenario.agents:
        lines += [f"### Agent {agent.agent_id}", "", agent.user_request, ""]
    lines += ["## Catalog (visible to the owner only)", ""]
    for job_id, job in metadata["catalog"].items():
        options = ", ".join(f"{o} cost {v['cost']}" for o, v in job["options"].items())
        requires = metadata.get("requires", {}).get(job_id)
        suffix = f"; requires {', '.join(requires)}" if requires else ""
        lines.append(f"- {job['owner']}: `{job_id}` ({options}{suffix})")
    lines += ["", "## Messages and plans", ""]
    for event in events:
        kind, detail = event["event_type"], event["detail"]
        expected = ("agreed", "agreement_failed") if kind == "agreement" else ("ok",)
        if kind not in SHOWN or event["result"] not in expected:
            continue
        head = f"**t={event['time']} {event['agent_id'] or 'env'} {kind}**"
        if kind == "send_message":
            lines.append(f"{head} -> {detail['to']} (deliver t={detail['deliver_at']}):")
            lines += [f"> {line}" for line in str(detail["text"]).splitlines() or [""]]
        elif kind == "propose_plan":
            items = ", ".join(
                f"{i['job_id']}/{i['option_id']} ({i['cost']})" for i in detail["items"]
            )
            alternatives = ", ".join(
                f"{i['job_id']}/{i['option_id']} ({i['cost']})"
                for i in detail.get("disclosed_alternatives", [])
            )
            lines.append(f"{head}: {items or 'empty'}; alternatives: {alternatives or 'none'}")
            if detail.get("note"):
                lines.append(f"> {detail['note']}")
        elif kind == "plan_feedback":
            lines.append(
                f"{head}: v{detail['plan_version']} {detail['status']}, "
                f"total {detail['requested_total']} of {detail['budget']}"
            )
        elif kind == "agreement":
            lines.append(f"{head}: {event['result']} {json.dumps(detail, ensure_ascii=False)}")
        else:
            lines.append(f"{head}: {json.dumps(detail, ensure_ascii=False)}")
        lines.append("")
    lines += ["## Submissions", ""]
    for event in events:
        if event["event_type"] == "submit":
            lines.append(
                f"- t={event['time']} {event['agent_id']}: `{event['job_id']}/{event['option_id']}`"
                f" cost {event['cost']} -> {event['result']}"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    transcripts = args.out / "transcripts"
    transcripts.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sample(args.results):
        episode = path.name.removesuffix(".log.jsonl")
        (transcripts / f"{episode}.md").write_text(transcript(path), encoding="utf-8")
        rows += [{"episode": episode, "agent": agent} for agent in ("A", "B")]
    for annotator in ANNOTATORS:
        sheet = args.out / f"sheet_{annotator}.csv"
        if sheet.exists():
            continue  # never overwrite a started annotation
        with sheet.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("episode", "agent", *FIELDS))
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
