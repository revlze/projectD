"""Produce descriptive E2/E5 qualitative statistics from the verified annotation."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean

from project_d.evaluation.annotation_data import OUT, json_text
from project_d.evaluation.annotation_review import final_csv, final_rows, resolve
from project_d.evaluation.annotation_workflow import (
    INTENTS,
    agent_objectives,
    csv_rows,
    csv_text,
    flat_labels,
    imported,
    load_tasks,
    write,
)
from project_d.evaluation.plots import GRID, MUTED, Svg

COLORS = ("#257de0", "#107b68", "#b24c25")
ASSOCIATED = {
    "conflict_detected",
    "cost_mentioned",
    "own_change_proposed",
    "final_plan_matches_submissions",
    "own_priority_correct",
    "partner_priority_understood",
    "explicit_root_yield",
    "decision_deferred_to_environment",
    "submission_order_agreed",
}


def _category(feature: str, value):
    if feature not in INTENTS:
        return value
    pairs = value["pairs"]
    return json_text(pairs) if isinstance(pairs, list) else pairs


def agreement(pairs: list[tuple[str, str]]) -> dict:
    """Cohen's kappa with unclear as a category, excluding either-side not-applicable."""
    applicable = [(a, b) for a, b in pairs if "not_applicable" not in (a, b)]
    n = len(applicable)
    numerator = sum(a == b for a, b in applicable)
    match = None
    kappa = None
    if n:
        match = numerator / n
        left = Counter(a for a, _ in applicable)
        right = Counter(b for _, b in applicable)
        expected = sum(amount * right[value] for value, amount in left.items())
        if expected != n * n:
            kappa = (numerator * n - expected) / (n * n - expected)
    return {
        "joint_observations": len(pairs),
        "applicable": n,
        "not_applicable": len(pairs) - n,
        "with_unclear": sum("unclear" in pair for pair in applicable),
        "agreement_count": numerator,
        "agreement_fraction": match,
        "cohen_kappa": kappa,
    }


def rates(tasks: dict, manifest: dict, rows: list[dict]) -> list[dict]:
    labels = {(r["episode"], r["subject"], r["feature"]): r["value"] for r in rows}
    counts = defaultdict(Counter)
    for episode, task in tasks.items():
        variant = manifest[episode]["variant"]
        for subject, fields in task["required"].items():
            all_fields = (
                [*fields, "final_plan_matches_submissions"] if "final_intent" in fields else fields
            )
            for feature in all_fields:
                value = labels.get((episode, subject, feature))
                if value is not None:
                    value = _category(feature, value)
                for scope in task["samples"]:
                    cell = counts[
                        scope, variant, "episode" if subject == "episode" else "agent", feature
                    ]
                    cell["expected"] += 1
                    if value is None:
                        cell["missing"] += 1
                    else:
                        cell["not_applicable"] += value == "not_applicable"
                        cell["unclear"] += value == "unclear"
                        cell["numerator"] += (
                            value != "unclear" if feature in INTENTS else value == "yes"
                        )
    records = []
    for (scope, variant, level, feature), c in sorted(counts.items()):
        applicable = c["expected"] - c["missing"] - c["not_applicable"]
        determinable = applicable - c["unclear"]
        denominator = applicable if feature in INTENTS else determinable
        records.append(
            {
                "sample": scope,
                "variant": variant,
                "level": level,
                "feature": feature,
                "expected": c["expected"],
                "missing": c["missing"],
                "applicable": applicable,
                "determinable": determinable,
                "unclear": c["unclear"],
                "not_applicable": c["not_applicable"],
                "numerator": c["numerator"],
                "fraction_denominator": denominator,
                "fraction": c["numerator"] / denominator if denominator else None,
            }
        )
    return records


def _association_rows(rows, manifest, agents, episodes):
    groups = defaultdict(list)
    for row in rows:
        episode, subject, feature = row["episode"], row["subject"], row["feature"]
        facts = episodes[episode]
        if facts["root_conflict"] != "True" or feature not in ASSOCIATED:
            continue
        level = "episode" if subject == "episode" else "agent"
        if level == "agent":
            agent = agents[episode, subject]
            outcome = agent["root_outcome"]
            submit_t = agent["first_root_submit_t"]
        else:
            outcome = json_text({a: agents[episode, a]["root_outcome"] for a in ("A", "B")})
            submit_t = ""
        for scope in json.loads(manifest[episode]["samples"]):
            groups[
                scope, manifest[episode]["variant"], level, feature, row["value"], outcome
            ].append(
                (episode, submit_t, facts["root_submit_gap"], facts["higher_value_root_completed"])
            )
    records = []
    for (scope, variant, level, feature, label, outcome), group in sorted(groups.items()):
        unique = {episode: (gap, higher) for episode, _, gap, higher in group}
        submission = [int(t) for _, t, _, _ in group if t]
        gaps = [int(gap) for gap, _ in unique.values() if gap]
        defined = [v for _, v in unique.values() if v != ""]
        records.append(
            {
                "sample": scope,
                "variant": variant,
                "level": level,
                "feature": feature,
                "label": label,
                "root_outcome": outcome,
                "observations": len(group),
                "distinct_episodes": len(unique),
                "first_submit_observations": len(submission),
                "mean_first_submit_t": fmean(submission) if submission else None,
                "both_submitted_episodes": len(gaps),
                "staggered_episodes": sum(gap > 0 for gap in gaps),
                "mean_submit_gap": fmean(gaps) if gaps else None,
                "higher_value_root_completed": sum(v == "True" for v in defined),
                "higher_value_root_defined": len(defined),
            }
        )
    return records


def _verification_tables(result, tasks, manifest):
    edits = defaultdict(Counter)
    pairs = defaultdict(list)
    expected_pairs = Counter()
    for key, draft in result.drafts.items():
        episode, subject, feature = key
        level = "episode" if subject == "episode" else "agent"
        assigned = result.assignments[episode]
        human = {
            r: result.reviews[r].get(key, {"status": "pending", "label": None})
            for r in assigned["raters"]
        }
        for scope in tasks[episode]["samples"]:
            for rater, decision in human.items():
                cell = edits[scope, manifest[episode]["variant"], level, feature, rater]
                cell[decision["status"]] += 1
                if decision["label"] is not None:
                    cell["value_changed"] += decision["label"]["value"] != draft["value"]
            if assigned["fixed_shared"]:
                cell = scope, level, feature
                expected_pairs[cell] += 1
                if all(d["label"] is not None for d in human.values()):
                    pairs[cell].append(
                        tuple(_category(feature, d["label"]["value"]) for d in human.values())
                    )
    corrections = []
    for (scope, variant, level, feature, rater), c in sorted(edits.items()):
        decided = c["confirmed"] + c["corrected"]
        corrections.append(
            {
                "sample": scope,
                "variant": variant,
                "level": level,
                "feature": feature,
                "rater": rater,
                "confirmed": c["confirmed"],
                "corrected": c["corrected"],
                "disputed": c["disputed"],
                "pending": c["pending"],
                "decided": decided,
                "value_changed": c["value_changed"],
                "correction_fraction": c["corrected"] / decided if decided else None,
            }
        )
    comparisons = [
        {
            "sample": scope,
            "level": level,
            "feature": feature,
            "expected_shared": n,
            **agreement(pairs[scope, level, feature]),
        }
        for (scope, level, feature), n in sorted(expected_pairs.items())
    ]
    return corrections, comparisons


def _bars(path: Path, title: str, series: list[str], panels: dict, *, preliminary: bool) -> None:
    line_count = sum(1 + len(values) for values in panels.values())
    svg = Svg(750, max(170, 82 + 25 * line_count), title)
    svg.text(16, 25, title, 16, weight="bold")
    note = "PRELIMINARY - imported LLM labels" if preliminary else "Human-verified labels"
    svg.text(16, 46, note + " | Fractions among determinable observations", 11, color=MUTED)
    for index, label in enumerate(series):
        x = 24 + 230 * index
        svg.rect(x, 57, 10, 10, COLORS[index])
        svg.text(x + 14, 66, label, 10, color=MUTED)
    y = 87
    for scope, variants in panels.items():
        svg.text(16, y, scope.replace("_", " "), 11, weight="bold")
        y += 13
        for label, values in variants.items():
            svg.text(125, y + 11, label, 10, "end")
            for i, value in enumerate(values):
                x = 137 + 202 * i
                svg.rect(x, y, 125, 12, GRID, stroke="none")
                if value is not None:
                    svg.rect(x, y, 125 * value, 12, COLORS[i], stroke="none")
                svg.text(x + 132, y + 10, "n/a" if value is None else f"{value:.0%}", 10)
            y += 21
        y += 7
    if not panels:
        svg.text(16, 100, "No observations yet", 11, color=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    svg.save(path)


def _graphics(folder, summaries, associations, preliminary):
    for file, title, names in (
        (
            "negotiation_behaviors",
            "Conflict, cost and plan changes",
            ("conflict_detected", "cost_mentioned", "own_change_proposed"),
        ),
        (
            "root_negotiation",
            "Choices during main-job conflicts",
            ("explicit_root_yield", "submission_order_agreed", "decision_deferred_to_environment"),
        ),
        (
            "intent_matches",
            "Final intentions and submitted work",
            ("final_plan_matches_submissions",),
        ),
    ):
        cells = defaultdict(dict)
        for row in summaries:
            feature = row["feature"]
            if feature in names and (row["sample"] == "target") == (file == "root_negotiation"):
                cells[row["sample"], row["variant"]][feature] = row["fraction"]
        panels = defaultdict(dict)
        for (scope, method), values in cells.items():
            panels[scope][method] = [values.get(feature) for feature in names]
        _bars(
            folder / f"{file}.svg",
            title,
            [key.replace("_", " ") for key in names],
            panels,
            preliminary=preliminary,
        )

    outcome_counts = defaultdict(Counter)
    for row in associations:
        if (
            row["sample"] == "target"
            and row["feature"] == "explicit_root_yield"
            and row["label"] in ("yes", "no")
        ):
            outcome_counts[row["variant"], row["label"]][row["root_outcome"]] += row["observations"]
    panels = defaultdict(dict)
    for (method, label), counts in sorted(outcome_counts.items()):
        total = sum(counts.values())
        refused = counts["budget_refused"] + counts["other_refusal"]
        panels[f"Explicit root yield = {label}"][method] = [
            counts["not_submitted"] / total,
            refused / total,
            counts["completed"] / total,
        ]
    _bars(
        folder / "root_outcome_association.svg",
        "Main-job outcomes by explicit yield",
        ["Not submitted", "Refused", "Completed"],
        panels,
        preliminary=preliminary,
    )


def analyse(out: Path, *, preliminary: bool) -> Path:
    tasks = load_tasks(out)
    responses = imported(out, tasks)
    if preliminary:
        if not responses:
            raise ValueError("Preliminary analysis requires imported responses")
        rows = flat_labels(responses, agent_objectives(out))
        result = None
    else:
        result = resolve(out, tasks, responses)
        if len(responses) != len(tasks) or result.pending or result.unresolved:
            raise ValueError(
                "Final analytics require all episodes and completed human verification"
            )
        rows = final_rows(out, result.final)
        for name, level in (("agents", False), ("episodes", True)):
            path = out / f"final/{name}.csv"
            if not path.exists() or path.read_text(encoding="utf-8") != final_csv(rows, level):
                raise ValueError("Final export is missing or stale. Run merge.")
    folder = out / "analysis" / ("preliminary" if preliminary else "final")
    manifest = {r["episode"]: r for r in csv_rows(out / "sample_manifest.csv")}
    episodes = {r["episode"]: r for r in csv_rows(out / "objective/episodes.csv")}
    summaries = rates(tasks, manifest, rows)
    associations = _association_rows(rows, manifest, agent_objectives(out), episodes)
    write(folder / "feature_rates.csv", csv_text(summaries))
    if associations:
        write(folder / "root_associations.csv", csv_text(associations))
    if result is not None:
        corrections, comparisons = _verification_tables(result, tasks, manifest)
        write(folder / "human_corrections.csv", csv_text(corrections))
        if comparisons:
            write(folder / "reviewer_agreement.csv", csv_text(comparisons))
    write(
        folder / "status.json",
        json_text(
            {
                "mode": "preliminary" if preliminary else "final",
                "imported_episodes": len(responses),
                "expected_episodes": len(tasks),
            }
        )
        + "\n",
    )
    _graphics(folder, summaries, associations, preliminary)
    return folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--preliminary", action="store_true")
    args = parser.parse_args(argv)
    try:
        folder = analyse(args.out, preliminary=args.preliminary)
    except (ValueError, KeyError, OSError) as exc:
        print(f"Annotation analysis: {exc}", file=sys.stderr)
        return 1
    print(f"Annotation analysis written to {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
