"""Human verification sheets, explicit consensus and annotation readiness."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from project_d.evaluation.annotation_data import json_text
from project_d.evaluation.annotation_workflow import (
    INTENTS,
    LABEL_FIELDS,
    RATERS,
    agent_objectives,
    csv_rows,
    csv_text,
    derived_match,
    digest,
    validate_label,
    write,
)

Key = tuple[str, str, str]
KEY = ("episode", "subject", "feature")
DRAFT = ("llm_value", "llm_reason", "llm_evidence")
DECISION = ("status", "value", "reason", "evidence")
REVIEW_FIELDS = (
    *KEY,
    *DRAFT,
    *(f"review_{name}" for name in DECISION),
)
CONSENSUS_FIELDS = (
    *KEY,
    *DRAFT,
    "review_decisions",
    *(f"resolution_{name}" for name in DECISION),
)


def _key(row: dict) -> Key:
    return row["episode"], row["subject"], row["feature"]


def _read_keyed(path: Path) -> dict[Key, dict]:
    result = {}
    if not path.exists():
        return result
    for row in csv_rows(path):
        key = _key(row)
        if key in result:
            raise ValueError(f"{path}: repeated row {key}")
        result[key] = row
    return result


def _assignments(out: Path, tasks: dict[str, dict]) -> dict[str, dict]:
    rows = csv_rows(out / "verification/assignment.csv")
    result = {}
    for row in rows:
        episode = row["episode"]
        raters = json.loads(row["raters"])
        shared = row["fixed_shared"] == "True"
        if (
            not raters
            or len(raters) != len(set(raters))
            or not set(raters) <= set(RATERS)
            or len(raters) != (2 if shared else 1)
            or episode in result
        ):
            raise ValueError(f"{episode}: invalid reviewer assignment")
        result[episode] = {"raters": raters, "fixed_shared": shared}
    if result.keys() != tasks.keys():
        raise ValueError("Reviewer assignment differs from the frozen manifest")
    return result


def _drafts(responses: dict[str, dict]) -> dict[Key, dict]:
    return {
        (episode, subject, feature): label
        for episode, response in sorted(responses.items())
        for subject, features in response["labels"].items()
        for feature, label in features.items()
    }


def _draft_columns(key: Key, label: dict) -> dict[str, str]:
    value = label["value"]
    return {
        **dict(zip(KEY, key, strict=True)),
        "llm_value": json_text(value) if isinstance(value, dict) else value,
        "llm_reason": label["reason"],
        "llm_evidence": json_text(label["evidence"]),
    }


def _sheet(out: Path, rater: str, episode_level: bool) -> Path:
    name = "episode_sheet" if episode_level else "sheet"
    return out / "verification" / f"{name}_{rater}.csv"


def _expected(drafts, assigned, rater, episode_level=None):
    return {
        key: _draft_columns(key, label)
        for key, label in drafts.items()
        if rater in assigned[key[0]]["raters"]
        and (episode_level is None or (key[1] == "episode") == episode_level)
    }


def _check_drafts(path, rows, expected):
    for key, row in rows.items():
        if key not in expected or any(row[field] != expected[key][field] for field in DRAFT):
            raise ValueError(f"{path}: unknown or changed LLM draft {key}")


def create_sheets(out: Path, responses: dict[str, dict], tasks: dict[str, dict]) -> None:
    assigned, drafts = _assignments(out, tasks), _drafts(responses)
    updated = []
    for rater in RATERS:
        for episode_level in (False, True):
            path = _sheet(out, rater, episode_level)
            current = _read_keyed(path)
            expected = _expected(drafts, assigned, rater, episode_level)
            _check_drafts(path, current, expected)
            new = [
                current.get(key)
                or {
                    **row,
                    "review_status": "pending",
                    "review_value": "",
                    "review_reason": "",
                    "review_evidence": "",
                }
                for key, row in expected.items()
            ]
            updated.append((path, csv_text(new, REVIEW_FIELDS)))
    for path, text in updated:
        write(path, text)
    print(f"Prepared individual sheets for {len(responses)}/{len(tasks)} imported episodes")


def _human_label(task: dict, key: Key, row: dict, prefix: str) -> dict:
    try:
        value = json.loads(row[f"{prefix}_value"]) if key[2] in INTENTS else row[f"{prefix}_value"]
        evidence = json.loads(row[f"{prefix}_evidence"])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{'/'.join(key)}: invalid {prefix} JSON value/evidence") from exc
    return validate_label(
        task,
        key[1],
        key[2],
        {
            "value": value,
            "reason": row[f"{prefix}_reason"],
            "evidence": evidence,
        },
    )


def _human_reviews(out, tasks, drafts, assigned):
    reviews = {}
    for rater in RATERS:
        human = {}
        for episode_level in (False, True):
            path = _sheet(out, rater, episode_level)
            rows = _read_keyed(path)
            _check_drafts(path, rows, _expected(drafts, assigned, rater, episode_level))
            for key, row in rows.items():
                status = row["review_status"].strip() or "pending"
                other = [row[f"review_{f}"].strip() for f in DECISION[1:]]
                if status in ("pending", "confirmed"):
                    if any(other):
                        raise ValueError(
                            f"{path}/{key}: {status} must leave correction fields blank"
                        )
                    label = drafts[key] if status == "confirmed" else None
                elif status == "corrected":
                    label = _human_label(tasks[key[0]], key, row, "review")
                elif status == "disputed":
                    if not other[1] or other[0] or other[2]:
                        raise ValueError(f"{path}/{key}: disputed needs a reason only")
                    label = None
                else:
                    raise ValueError(f"{path}/{key}: invalid review status {status}")
                human[key] = {"status": status, "label": label, "reason": other[1]}
        reviews[rater] = human
    return reviews


@dataclass
class ReviewResult:
    drafts: dict[Key, dict]
    assignments: dict[str, dict]
    reviews: dict[str, dict[Key, dict]]
    final: dict[Key, dict]
    disagreements: dict[Key, dict]
    pending: int
    unresolved: int


def resolve(out: Path, tasks: dict[str, dict], responses: dict[str, dict]) -> ReviewResult:
    assigned, drafts = _assignments(out, tasks), _drafts(responses)
    reviews = _human_reviews(out, tasks, drafts, assigned)
    path = out / "verification/disagreements.csv"
    disagreements = _read_keyed(path)
    final = {}
    pending = unresolved = 0
    for key, draft in drafts.items():
        raters = assigned[key[0]]["raters"]
        decisions = {r: reviews[r].get(key, {"status": "pending"}) for r in raters}
        if any(d["status"] == "pending" for d in decisions.values()):
            pending += 1
            continue
        labels = [d["label"] for d in decisions.values()]
        if all(label is not None for label in labels) and all(
            label["value"] == labels[0]["value"] for label in labels
        ):
            final[key] = {
                "value": labels[0]["value"],
                "reason": " | ".join(dict.fromkeys(label["reason"] for label in labels)),
                "evidence": sorted({e for label in labels for e in label["evidence"]}),
            }
            continue
        snapshot = json_text(decisions)
        row = disagreements.get(key)
        if row is None or row["review_decisions"] != snapshot:
            if row is not None and (
                row["resolution_status"] == "resolved"
                or any(row[f"resolution_{field}"].strip() for field in DECISION[1:])
            ):
                raise ValueError(f"{path}/{key}: reviews changed after resolution was entered")
            row = {
                **_draft_columns(key, draft),
                "review_decisions": snapshot,
                "resolution_status": "pending",
                "resolution_value": "",
                "resolution_reason": "",
                "resolution_evidence": "",
            }
        disagreements[key] = row
        if row["resolution_status"] == "resolved":
            final[key] = _human_label(tasks[key[0]], key, row, "resolution")
        elif row["resolution_status"] in ("", "pending"):
            unresolved += 1
        else:
            raise ValueError(f"{path}/{key}: invalid resolution status")
    return ReviewResult(drafts, assigned, reviews, final, disagreements, pending, unresolved)


def final_rows(out: Path, labels: dict[Key, dict]) -> list[dict]:
    agents = agent_objectives(out)
    output = []
    for (episode, subject, feature), label in sorted(labels.items()):
        output.append({"episode": episode, "subject": subject, "feature": feature, **label})
        if feature == "final_intent":
            output.append(derived_match(episode, subject, label, agents[episode, subject]))
    return output


def final_csv(rows: list[dict], episode_level: bool) -> str:
    return csv_text(
        [row for row in rows if (row["subject"] == "episode") == episode_level], LABEL_FIELDS
    )


def merge(out: Path, tasks: dict[str, dict], responses: dict[str, dict]) -> int:
    result = resolve(out, tasks, responses)
    write(
        out / "verification/disagreements.csv",
        csv_text(list(result.disagreements.values()), CONSENSUS_FIELDS),
    )
    if len(responses) != len(tasks) or result.pending or result.unresolved:
        print(
            f"Final labels blocked: {len(tasks) - len(responses)} missing episodes, "
            f"{result.pending} pending features, {result.unresolved} unresolved disagreements"
        )
        return 1
    rows = final_rows(out, result.final)
    for name, episode_level in (("agents", False), ("episodes", True)):
        write(out / f"final/{name}.csv", final_csv(rows, episode_level))
    print(f"Final labels exported for {len(tasks)} episodes")
    return 0


def status(out: Path, tasks: dict[str, dict], responses: dict[str, dict]) -> dict:
    from project_d.evaluation.annotation_data import read_jsonl
    from project_d.evaluation.annotation_workflow import validate_response

    issues = []
    for path in sorted((out / "llm/responses").glob("*.jsonl")):
        archived = out / "llm/responses/imported" / f"{digest(path.read_bytes())}.jsonl"
        if archived.exists():
            continue
        try:
            for row in read_jsonl(path):
                validate_response(row, tasks)
        except (ValueError, KeyError, OSError) as exc:
            issues.append(f"{path.name}: {exc}")
    missing = sorted(set(tasks) - set(responses))
    result = resolve(out, tasks, responses)
    decisions = Counter(d["status"] for sheet in result.reviews.values() for d in sheet.values())
    ready = not (missing or result.pending or result.unresolved)
    exported = False
    if ready:
        rows = final_rows(out, result.final)
        exported = all(
            (path := out / f"final/{name}.csv").exists()
            and path.read_text(encoding="utf-8") == final_csv(rows, level)
            for name, level in (("agents", False), ("episodes", True))
        )
    return {
        "expected_episodes": len(tasks),
        "received_episodes": len(responses),
        "missing_responses": missing,
        "missing_response_fields": sum(
            len(fields) for e in missing for fields in tasks[e]["required"].values()
        ),
        "invalid_responses": issues,
        "review_statuses": dict(decisions),
        "fixed_shared_episodes": sum(row["fixed_shared"] for row in result.assignments.values()),
        "pending_features": result.pending,
        "unresolved_disagreements": result.unresolved,
        "ready_to_merge": ready,
        "final_analytics_ready": exported,
    }
