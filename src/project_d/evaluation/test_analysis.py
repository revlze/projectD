"""Analysis of the frozen test series, recomputed from saved summaries and journals.

Usage: python -m project_d.evaluation.test_analysis <test results dir> --out <dir>

The results dir holds e2/, e3/, e4-h1/ and e4-delay/, each with one model run
directory. No model is called. Statistics follow docs/experiments.md, section 4:
repeats are averaged within a profile, paired differences are taken per profile,
and only E2 gets the stratified profile bootstrap. E3 and E4 numbers are descriptive.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from statistics import fmean

from project_d.evaluation.bootstrap import REPEATS, paired_stratified_bootstrap

Row = dict[str, str]

PROTOCOLS = ("N", "F", "R1", "R3", "R3P", "VBC")
H2_PAIRS = (("F", "N"), ("R1", "F"), ("R3", "R1"), ("R3P", "R3"))
H4_REFERENCES = ("A/N", "A/F", "A/R1", "A/R3", "A/R3P")
FAMILIES = ("S0", "S1", "S2", "S3", "S4")

# Derived numeric columns. `violation` is 0/1, `utility_fraction` is U/U* without the safety cut.
METRICS = ("safe_fraction", "utility_fraction", "violation")
DESCRIPTIVE = (
    "safe_fraction",
    "utility_fraction",
    "violation",
    "max_overrun",
    "completed_jobs",
    "budget_refusals",
    "unused_budget",
    "messages",
    "tool_calls",
    "llm_turns",
    "prompt_tokens",
    "completion_tokens",
    "cached_prompt_tokens",
    "llm_seconds",
    "parse_errors",
    "length_finishes",
    "early_finish_attempts",
    "rounds_missed",
)
STRUCTURED_FLAGS = (
    "agreed",
    "agreed_within_budget",
    "agreed_over_budget",
    "agreed_dependencies_satisfied",
)


# --------------------------------------------------------------------------- loading


def load_series(root: Path, series: str) -> tuple[Path, list[Row]]:
    runs = sorted(path.parent for path in (root / series).glob("*/summary.csv"))
    if len(runs) != 1:
        raise ValueError(f"{root / series}: expected exactly one run directory, got {runs}")
    with (runs[0] / "summary.csv").open(encoding="utf-8", newline="") as handle:
        rows = [_derive(row) for row in csv.DictReader(handle)]
    failed = [
        row["episode"] for row in rows if row["failure"] or row["audit_issues"] not in ("", "0")
    ]
    if failed:
        raise ValueError(f"{series}: failed or unaudited episodes {failed[:5]}")
    return runs[0], rows


def _derive(row: Row) -> Row:
    row = dict(row)
    row["violation"] = "1" if row["violated"] == "True" else "0"
    row["utility_fraction"] = repr(float(row["U"]) / float(row["U_star"]))
    return row


def _num(value: str) -> float:
    if value in ("", "None"):
        return 0.0
    if value in ("True", "False"):
        return float(value == "True")
    return float(value)


# --------------------------------------------------------------------------- profile means


def profile_means(rows: Iterable[Row], variant: str, metric: str) -> dict[str, float]:
    scores: dict[str, dict[int, float]] = defaultdict(dict)
    for row in rows:
        if row["variant"] == variant:
            scores[row["profile"]][int(row["repeat"])] = _num(row[metric])
    for profile, by_repeat in scores.items():
        if by_repeat.keys() != REPEATS:
            raise ValueError(f"{profile}/{variant}: repeats {sorted(by_repeat)}")
    return {profile: fmean(by_repeat.values()) for profile, by_repeat in sorted(scores.items())}


def family_of(rows: Iterable[Row]) -> dict[str, str]:
    return {row["profile"]: row["family"] for row in rows}


def paired_summary(
    rows: Sequence[Row], variant: str, reference: str, metric: str
) -> dict[str, object]:
    """Descriptive paired difference: overall, per family, and the sign count over profiles."""
    candidate = profile_means(rows, variant, metric)
    baseline = profile_means(rows, reference, metric)
    if candidate.keys() != baseline.keys():
        raise ValueError(f"{variant} vs {reference}: profile sets differ")
    families = family_of(rows)
    diffs = {profile: candidate[profile] - baseline[profile] for profile in candidate}
    by_family: dict[str, list[float]] = defaultdict(list)
    for profile, diff in diffs.items():
        by_family[families[profile]].append(diff)
    eps = 1e-12
    return {
        "variant": variant,
        "reference": reference,
        "metric": metric,
        "profiles": len(diffs),
        "variant_mean": fmean(candidate.values()),
        "reference_mean": fmean(baseline.values()),
        "mean_difference": fmean(diffs.values()),
        "profiles_better": sum(d > eps for d in diffs.values()),
        "profiles_worse": sum(d < -eps for d in diffs.values()),
        "profiles_tied": sum(abs(d) <= eps for d in diffs.values()),
        "family_mean_difference": {f: fmean(v) for f, v in sorted(by_family.items())},
    }


# --------------------------------------------------------------------------- E2


def e2_contrasts() -> list[tuple[str, str, str]]:
    contrasts: list[tuple[str, str, str]] = []
    for mode in ("U", "A"):
        for variant, reference in H2_PAIRS:
            contrasts.append(("H2", f"{mode}/{variant}", f"{mode}/{reference}"))
    for protocol in PROTOCOLS:
        contrasts.append(("H3", f"A/{protocol}", f"U/{protocol}"))
    for reference in H4_REFERENCES:
        contrasts.append(("H4", "A/VBC", reference))
    contrasts.append(("H4", "U/VBC", "U/R3P"))
    return contrasts


def analyse_e2(rows: Sequence[Row]) -> dict[str, object]:
    bootstrap = []
    for hypothesis, variant, reference in e2_contrasts():
        for metric in METRICS:
            result = asdict(paired_stratified_bootstrap(rows, variant, reference, metric))
            described = paired_summary(rows, variant, reference, metric)
            bootstrap.append(
                {
                    "hypothesis": hypothesis,
                    **described,
                    "lower": result["lower"],
                    "upper": result["upper"],
                    "draws": result["draws"],
                    "seed": result["seed"],
                }
            )
    return {
        "variants": variant_table(rows),
        "families": family_table(rows, "safe_fraction"),
        "bootstrap": bootstrap,
    }


def variant_table(rows: Sequence[Row]) -> list[dict[str, object]]:
    by_variant: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        by_variant[row["variant"]].append(row)
    table = []
    for variant, group in sorted(by_variant.items(), key=lambda item: _variant_order(item[0])):
        record: dict[str, object] = {"variant": variant, "episodes": len(group)}
        for metric in DESCRIPTIVE:
            record[metric] = fmean(_num(row[metric]) for row in group)
        record["violations"] = sum(row["violation"] == "1" for row in group)
        table.append(record)
    return table


def family_table(rows: Sequence[Row], metric: str) -> list[dict[str, object]]:
    families = family_of(rows)
    table = []
    for variant in sorted({row["variant"] for row in rows}, key=_variant_order):
        means = profile_means(rows, variant, metric)
        record: dict[str, object] = {"variant": variant}
        for family in FAMILIES:
            values = [v for p, v in means.items() if families[p] == family]
            record[family] = fmean(values) if values else None
        record["all"] = fmean(means.values())
        table.append(record)
    return table


def profile_table(rows: Sequence[Row], metric: str) -> list[dict[str, object]]:
    variants = sorted({row["variant"] for row in rows}, key=_variant_order)
    means = {variant: profile_means(rows, variant, metric) for variant in variants}
    families = family_of(rows)
    return [
        {
            "profile": profile,
            "family": families[profile],
            **{v: means[v][profile] for v in variants},
        }
        for profile in sorted(families)
    ]


def _variant_order(variant: str) -> tuple[int, int, str]:
    mode, _, protocol = variant.partition("/")
    order = ("N", "F", "R1", "R3", "R3P", "S", "S+V", "S+G", "VBC-r0", "VBC", "VBC-r2")
    return (order.index(protocol) if protocol in order else 99, mode != "U", variant)


# --------------------------------------------------------------------------- joins with E2


def join_from_e2(
    rows: Sequence[Row], e2: Sequence[Row], variants: Iterable[str], label: str
) -> list[Row]:
    """Take E2 episodes with the same (profile, repeat) keys as `rows`; check the episode setup."""
    keys = {(row["profile"], row["repeat"]): row for row in rows}
    wanted = set(variants)
    taken = []
    for row in e2:
        if row["variant"] not in wanted or (row["profile"], row["repeat"]) not in keys:
            continue
        reference = keys[(row["profile"], row["repeat"])]
        for field in ("first_agent", "role_swap", "commit_delay", "start_gap"):
            if row[field] != reference[field]:
                raise ValueError(f"{row['episode']}: {field} differs from {reference['episode']}")
        taken.append({**row, "series": label})
    for variant in wanted:
        got = {(r["profile"], r["repeat"]) for r in taken if r["variant"] == variant}
        if got != set(keys):
            raise ValueError(f"{variant}: E2 lacks some keys of {label}")
    return taken


def analyse_e3(e3: Sequence[Row], e2: Sequence[Row]) -> dict[str, object]:
    joined = [*e3, *join_from_e2(e3, e2, ("A/VBC", "A/R3P", "A/N"), "E3")]
    factorial = {
        "V_without_G": ("A/S+V", "A/S"),
        "V_with_G": ("A/VBC", "A/S+G"),
        "G_without_V": ("A/S+G", "A/S"),
        "G_with_V": ("A/VBC", "A/S+V"),
        "rounds_1_vs_0": ("A/VBC", "A/VBC-r0"),
        "rounds_2_vs_1": ("A/VBC-r2", "A/VBC"),
        "S_vs_R3P_protocol": ("A/S", "A/R3P"),
    }
    contrasts = {
        name: paired_summary(joined, variant, reference, "safe_fraction")
        for name, (variant, reference) in factorial.items()
    }
    return {
        "variants": variant_table(joined),
        "families": family_table(joined, "safe_fraction"),
        "contrasts": contrasts,
        "structured": structured_table(joined),
        "rows": joined,
    }


def analyse_e4_delay(delay: Sequence[Row], e2: Sequence[Row]) -> dict[str, object]:
    base = join_from_e2(delay, e2, ("A/R3P", "A/VBC"), "E4-delay")
    joined = [*delay, *base]
    table = []
    for variant in ("A/R3P", "A/VBC"):
        for value in ("1", "4", "8"):
            cell = [r for r in joined if r["variant"] == variant and r["message_delay"] == value]
            record: dict[str, object] = {
                "variant": variant,
                "message_delay": int(value),
                "episodes": len(cell),
            }
            for metric in ("safe_fraction", "violation", "completed_jobs", "messages"):
                record[metric] = fmean(_num(r[metric]) for r in cell)
            if variant == "A/VBC":
                record["agreed"] = sum(r["agreed"] == "True" for r in cell)
                record["agreed_over_budget"] = sum(r["agreed_over_budget"] == "True" for r in cell)
            table.append(record)
    paired = []
    for variant in ("A/R3P", "A/VBC"):
        for value in ("4", "8"):
            tagged = [
                {**r, "variant": f"{variant}@{r['message_delay']}"}
                for r in joined
                if r["variant"] == variant and r["message_delay"] in ("1", value)
            ]
            paired.append(
                paired_summary(tagged, f"{variant}@{value}", f"{variant}@1", "safe_fraction")
            )
    return {"cells": table, "paired_vs_delay_1": paired}


# --------------------------------------------------------------------------- structured plans


def structured_table(rows: Sequence[Row]) -> list[dict[str, object]]:
    table = []
    variants = {r["variant"] for r in rows if "VBC" in r["variant"] or "/S" in r["variant"]}
    for variant in sorted(variants, key=_variant_order):
        group = [r for r in rows if r["variant"] == variant]
        agreed = [r for r in group if r["agreed"] == "True"]
        record: dict[str, object] = {"variant": variant, "episodes": len(group)}
        for flag in STRUCTURED_FLAGS:
            record[flag] = sum(r[flag] == "True" for r in group)
        record["over_budget_share_of_agreed"] = (
            record["agreed_over_budget"] / len(agreed) if agreed else None  # type: ignore[operator]
        )
        record["agreed_missing_prerequisites"] = sum(
            _num(r["agreed_missing_prerequisites"]) > 0 for r in agreed
        )
        record["empty_agreements"] = sum(_num(r["agreed_jobs"]) == 0 for r in agreed)
        record["agreed_jobs"] = sum(_num(r["agreed_jobs"]) for r in agreed)
        record["agreed_jobs_completed"] = sum(_num(r["agreed_jobs_completed"]) for r in agreed)
        record["agreed_plan_completed"] = sum(r["agreed_plan_completed"] == "True" for r in agreed)
        record["off_plan_attempts"] = sum(_num(r["off_plan_attempts"]) for r in group)
        record["off_plan_accepted"] = sum(_num(r["off_plan_accepted"]) for r in group)
        record["plan_released"] = sum(r["plan_released"] == "True" for r in group)
        record["v_warning_status"] = dict(Counter(r["v_warning_status"] or "-" for r in group))
        record["violations"] = sum(r["violation"] == "1" for r in group)
        record["violations_when_agreed_over_budget"] = sum(
            r["violation"] == "1" for r in agreed if r["agreed_over_budget"] == "True"
        )
        record["safe_fraction"] = fmean(_num(r["safe_fraction"]) for r in group)
        table.append(record)
    return table


# --------------------------------------------------------------------------- E4-H1 journals


def h1_episode(path: Path) -> dict[str, object]:
    raw = [json.loads(line) for line in path.read_bytes().splitlines()]
    metadata, events = raw[0]["metadata"], raw[1:]
    budget = metadata["budget"]
    pending: dict[str, int] = {}  # request_id -> cost, accepted but not committed
    first_submit: dict[str, int] = {}
    admissions = []
    finished: set[str] = set()
    observed_spend: set[str] = set()
    read_message: set[str] = set()
    submitted: set[str] = set()
    for event in events:
        kind, agent = event["event_type"], event["agent_id"]
        if kind == "submit":
            submitted.add(agent)
            first_submit.setdefault(agent, event["time"])
            if event["result"] == "accepted":
                admissions.append(
                    {
                        "time": event["time"],
                        "agent": agent,
                        "cost": event["cost"],
                        "spent_before": event["spent_before"],
                        "pending_uncommitted": len(pending),
                        "pending_cost": sum(pending.values()),
                    }
                )
                pending[event["request_id"]] = event["cost"]
        elif kind == "commit":
            pending.pop(event["request_id"], None)
        elif kind in ("get_balance", "get_status") and event["spent_before"] > 0:
            if agent not in submitted:
                observed_spend.add(agent)
        elif kind == "message_read" and agent not in submitted:
            read_message.add(agent)
        elif kind == "finish":
            finished.add(agent)
    agents = sorted(metadata["submission_open_at"])
    summary_path = path.with_name(path.name.removesuffix(".log.jsonl") + ".summary.json")
    root_conflict = json.loads(summary_path.read_bytes())["root_conflict"]
    not_submitted = [agent for agent in agents if agent not in submitted]
    return {
        "episode": path.name.removesuffix(".log.jsonl"),
        "variant": metadata["variant"],
        "commit_delay": metadata["commit_delay"],
        "start_gap": metadata["start_gap"],
        "budget": budget,
        "root_conflict": bool(root_conflict),
        "first_submit": first_submit,
        "actual_offset": (
            abs(first_submit[agents[0]] - first_submit[agents[1]])
            if len(first_submit) == 2
            else None
        ),
        "admissions": admissions,
        "overlapping_admissions": sum(a["pending_uncommitted"] > 0 for a in admissions),
        "max_spent": max((e["spent_after"] for e in events), default=0),
        "not_submitted": not_submitted,
        "not_submitted_saw_spend": [a for a in not_submitted if a in observed_spend],
        "not_submitted_read_message": [a for a in not_submitted if a in read_message],
        "not_submitted_finished": [a for a in not_submitted if a in finished],
    }


def analyse_e4_h1(run: Path) -> dict[str, object]:
    episodes = [h1_episode(path) for path in sorted(run.glob("*.log.jsonl"))]
    cells: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for episode in episodes:
        key = (str(episode["variant"]), int(episode["commit_delay"]), int(episode["start_gap"]))  # type: ignore[call-overload]
        cells[key].append(episode)
    table = []
    for (variant, delay, gap), group in sorted(cells.items()):
        offsets = [e["actual_offset"] for e in group if e["actual_offset"] is not None]
        table.append(
            {
                "variant": variant,
                "commit_delay": delay,
                "start_gap": gap,
                "episodes": len(group),
                "root_conflict_episodes": sum(bool(e["root_conflict"]) for e in group),
                "violations": sum(e["max_spent"] > e["budget"] for e in group),  # type: ignore[operator]
                "both_submitted": sum(not e["not_submitted"] for e in group),
                "episodes_with_overlap": sum(e["overlapping_admissions"] > 0 for e in group),  # type: ignore[operator]
                "mean_actual_offset": fmean(offsets) if offsets else None,  # type: ignore[arg-type]
                "offsets": dict(Counter(offsets)),  # type: ignore[arg-type]
                "agents_not_submitted": sum(len(e["not_submitted"]) for e in group),  # type: ignore[arg-type]
                "of_which_saw_spend": sum(len(e["not_submitted_saw_spend"]) for e in group),  # type: ignore[arg-type]
                "of_which_read_message": sum(len(e["not_submitted_read_message"]) for e in group),  # type: ignore[arg-type]
                "of_which_finished": sum(len(e["not_submitted_finished"]) for e in group),  # type: ignore[arg-type]
            }
        )
    return {"cells": table, "episodes": episodes}


# --------------------------------------------------------------------------- E4-delay journals


def message_timing(run: Path, e2_run: Path, keys: Iterable[str]) -> list[dict[str, object]]:
    """Send -> read latency of delivered messages; E2 journals stand in for delay 1."""
    paths = [*run.glob("*.log.jsonl")]
    paths += [e2_run / f"{key}.log.jsonl" for key in keys]
    cells: dict[tuple[str, int], list[float]] = defaultdict(list)
    unread: Counter[tuple[str, int]] = Counter()
    sent: Counter[tuple[str, int]] = Counter()
    for path in paths:
        raw = [json.loads(line) for line in path.read_bytes().splitlines()]
        metadata = raw[0]["metadata"]
        key = (metadata["variant"], metadata["message_delay"])
        sent_at: dict[str, int] = {}
        for event in raw[1:]:
            if event["event_type"] == "send_message" and event["result"] == "ok":
                sent_at[event["detail"]["message_id"]] = event["time"]
                sent[key] += 1
            elif event["event_type"] == "message_read":
                for message_id in event["detail"]["message_ids"]:
                    if message_id in sent_at:
                        cells[key].append(event["time"] - sent_at.pop(message_id))
        unread[key] += len(sent_at)
    return [
        {
            "variant": variant,
            "message_delay": delay,
            "sent": sent[(variant, delay)],
            "read": len(latencies),
            "never_read": unread[(variant, delay)],
            "mean_send_to_read": fmean(latencies) if latencies else None,
        }
        for (variant, delay), latencies in sorted(cells.items())
    ]


# --------------------------------------------------------------------------- output


def write_csv(path: Path, records: Sequence[Mapping[str, object]]) -> None:
    fields: list[str] = []
    for record in records:
        fields.extend(k for k in record if k not in fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow({k: _cell(v) for k, v in record.items()})


def _cell(value: object) -> object:
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, dict | list):
        return json.dumps(value, sort_keys=True)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    e2_run, e2 = load_series(args.results, "e2")
    _, e3 = load_series(args.results, "e3")
    h1_run, h1 = load_series(args.results, "e4-h1")
    delay_run, delay = load_series(args.results, "e4-delay")

    e2_result = analyse_e2(e2)
    write_csv(args.out / "e2_variants.csv", e2_result["variants"])  # type: ignore[arg-type]
    write_csv(args.out / "e2_families_safe_fraction.csv", e2_result["families"])  # type: ignore[arg-type]
    write_csv(args.out / "e2_bootstrap.csv", e2_result["bootstrap"])  # type: ignore[arg-type]
    write_csv(args.out / "e2_profiles_safe_fraction.csv", profile_table(e2, "safe_fraction"))
    write_csv(args.out / "e2_structured.csv", structured_table(e2))

    e3_result = analyse_e3(e3, e2)
    write_csv(args.out / "e3_variants.csv", e3_result["variants"])  # type: ignore[arg-type]
    write_csv(args.out / "e3_families_safe_fraction.csv", e3_result["families"])  # type: ignore[arg-type]
    write_csv(
        args.out / "e3_contrasts.csv",
        [{"contrast": k, **v} for k, v in e3_result["contrasts"].items()],  # type: ignore[union-attr]
    )
    write_csv(args.out / "e3_structured.csv", e3_result["structured"])  # type: ignore[arg-type]
    write_csv(
        args.out / "e3_profiles_safe_fraction.csv",
        profile_table(e3_result["rows"], "safe_fraction"),  # type: ignore[arg-type]
    )

    h1_result = analyse_e4_h1(h1_run)
    write_csv(args.out / "e4_h1_cells.csv", h1_result["cells"])  # type: ignore[arg-type]
    write_csv(args.out / "e4_h1_episodes.csv", h1_result["episodes"])  # type: ignore[arg-type]
    if len(h1_result["episodes"]) != len(h1):  # type: ignore[arg-type]
        raise ValueError("E4-H1: journals and summary rows differ")

    delay_result = analyse_e4_delay(delay, e2)
    write_csv(args.out / "e4_delay_cells.csv", delay_result["cells"])  # type: ignore[arg-type]
    write_csv(args.out / "e4_delay_paired.csv", delay_result["paired_vs_delay_1"])  # type: ignore[arg-type]
    base_keys = [r["episode"] for r in join_from_e2(delay, e2, ("A/R3P", "A/VBC"), "E4-delay")]
    write_csv(args.out / "e4_delay_messages.csv", message_timing(delay_run, e2_run, base_keys))

    usage = [
        {"series": name, **record}
        for name, rows in (("E2", e2), ("E3", e3), ("E4-H1", h1), ("E4-delay", delay))
        for record in _usage(rows)
    ]
    write_csv(args.out / "usage.csv", usage)
    return 0


def _usage(rows: Sequence[Row]) -> list[dict[str, object]]:
    groups: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        groups[row["variant"]].append(row)
    fields = (
        "llm_turns",
        "tool_calls",
        "prompt_tokens",
        "completion_tokens",
        "cached_prompt_tokens",
        "reasoning_tokens",
        "http_attempts",
        "llm_seconds",
        "parse_errors",
        "length_finishes",
    )
    return [
        {
            "variant": variant,
            "episodes": len(group),
            **{f"sum_{f}": sum(_num(r[f]) for r in group) for f in fields},
            "mean_prompt_tokens": fmean(_num(r["prompt_tokens"]) for r in group),
            "max_prompt_tokens": max(_num(r["max_prompt_tokens"]) for r in group),
        }
        for variant, group in sorted(groups.items(), key=lambda item: _variant_order(item[0]))
    ]


if __name__ == "__main__":
    raise SystemExit(main())
