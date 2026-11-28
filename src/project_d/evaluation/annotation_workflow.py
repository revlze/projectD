"""Prepare and import qualitative annotation without making model requests."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.evaluation.annotation_data import (
    AGENTS,
    EPISODE_FEATURES,
    MAIN_FEATURES,
    OUT,
    TARGET_FEATURES,
    digest,
    json_text,
    negotiation,
    objective,
    read_jsonl,
    select,
)

SCHEMA_VERSION = "1"
INSTRUCTION_VERSION = "1"
RATERS = ("seva", "platon")
INTENTS = {"first_intent", "final_intent"}
VALUES = ("yes", "no", "unclear", "not_applicable")
LABEL_FIELDS = ("episode", "subject", "feature", "value", "reason", "evidence")
FROZEN_FILES = (
    "llm/tasks.jsonl",
    "objective/agents.csv",
    "objective/episodes.csv",
    "verification/assignment.csv",
)


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_text(rows: list[dict], fields: tuple[str, ...] | None = None) -> str:
    columns = fields if fields is not None else tuple(rows[0])
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        {
            key: json_text(value) if isinstance(value, (dict, list, tuple)) else value
            for key, value in row.items()
        }
        for row in rows
    )
    return handle.getvalue()


def write(path: Path, content: str, *, immutable: bool = False) -> None:
    data = content.encode()
    if path.exists():
        previous = path.read_bytes()
        if previous.replace(b"\r\n", b"\n") == data:
            return
        if immutable:
            raise ValueError(
                f"{path}: frozen input differs. Use an empty output directory for a new version."
            )
    _replace(path, data)


def _replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def jsonl_text(rows) -> str:
    return "".join(json_text(row) + "\n" for row in rows)


def required_features(samples: list[str]) -> dict[str, list[str]]:
    features = list(MAIN_FEATURES) if set(samples) & {"original", "exploratory_extension"} else []
    if "target" in samples:
        features = list(dict.fromkeys((*features, *TARGET_FEATURES)))
    return {
        **{agent: features for agent in AGENTS},
        "episode": list(EPISODE_FEATURES) if "target" in samples else [],
    }


def assignment(rows: list[dict]) -> list[dict]:
    strata: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in rows:
        strata[tuple([row["variant"], *row["samples"]])].append(row)
    count = round(len(rows) * 0.20)
    quotas = {key: divmod(count * len(group), len(rows)) for key, group in strata.items()}
    remainder = count - sum(whole for whole, _ in quotas.values())
    extras = set(sorted(quotas, key=lambda k: (-quotas[k][1], k))[:remainder])
    assignments = []
    workload = dict.fromkeys(RATERS, 0)
    for key, group in sorted(strata.items()):
        ordered = sorted(group, key=lambda row: digest(f"review-v1/{row['episode']}".encode()))
        common = quotas[key][0] + (key in extras)
        for index, row in enumerate(ordered):
            both = index < common
            raters = list(RATERS) if both else [min(RATERS, key=workload.__getitem__)]
            for rater in raters:
                workload[rater] += 1
            assignments.append(
                {
                    "episode": row["episode"],
                    "variant": row["variant"],
                    "samples": row["samples"],
                    "fixed_shared": both,
                    "raters": raters,
                }
            )
    return sorted(assignments, key=lambda row: row["episode"])


def prepare(out: Path, batch_size: int) -> None:
    if batch_size < 1:
        raise ValueError("Batch size must be positive")
    episodes = select()
    rows = [ep.row for ep in episodes]
    manifest = csv_text(rows)
    schema = (OUT / "schema.json").read_text(encoding="utf-8")
    rubric = (OUT / "rubric.md").read_text(encoding="utf-8")
    identity = {
        "schema_version": SCHEMA_VERSION,
        "instruction_version": INSTRUCTION_VERSION,
        "manifest_sha256": digest(manifest.encode()),
        "schema_sha256": digest(schema.encode()),
        "instruction_sha256": digest(rubric.encode()),
    }
    for name, text in (
        ("schema.json", schema),
        ("rubric.md", rubric),
        ("sample_manifest.csv", manifest),
    ):
        target = out / name
        if target.exists() and target.read_text(encoding="utf-8") != text:
            raise ValueError(f"{target}: frozen schema, instruction or manifest differs")
    if (out / "sample_identity.json").exists():
        load_tasks(out)
    tasks = []
    agent_rows, episode_rows = [], []
    for episode in episodes:
        raw = read_jsonl(episode.journal)
        metadata = EpisodeMetadata(**raw[0]["metadata"])
        log = [LogEntry(**e) for e in raw[1:]]
        episode_id = episode.row["episode"]
        if (metadata.scenario_id, metadata.variant, metadata.role_swap, metadata.first_agent) != (
            episode.row["profile"],
            episode.row["variant"],
            episode.row["role_swap"],
            episode.row["first_agent"],
        ):
            raise ValueError(f"{episode_id}: journal metadata differs from run manifest")
        text, catalog, evidence = negotiation(
            episode.scenario, metadata, log, read_jsonl(episode.llm)
        )
        write(out / "transcripts" / f"{episode_id}.md", text, immutable=True)
        tasks.append(
            {
                "episode": episode_id,
                "samples": episode.row["samples"],
                "schema_version": SCHEMA_VERSION,
                "instruction_version": INSTRUCTION_VERSION,
                "manifest_sha256": identity["manifest_sha256"],
                "required": required_features(episode.row["samples"]),
                "transcript": text,
                "catalog": catalog,
                "evidence_ids": evidence,
                "response_format": {"schema": "schema.json", "instruction": "rubric.md"},
            }
        )
        agents, facts = objective(episode_id, episode.scenario, metadata, log)
        agent_rows.extend(agents)
        episode_rows.append(facts)
    for path, text in (
        (out / "schema.json", schema),
        (out / "rubric.md", rubric),
        (out / "sample_manifest.csv", manifest),
        (out / "llm/tasks.jsonl", jsonl_text(tasks)),
        (out / "objective/agents.csv", csv_text(agent_rows)),
        (out / "objective/episodes.csv", csv_text(episode_rows)),
        (out / "verification/assignment.csv", csv_text(assignment(rows))),
    ):
        write(path, text, immutable=True)
    identity["files"] = _frozen_hashes(out)
    write(out / "sample_identity.json", json_text(identity) + "\n", immutable=True)
    batch_dir, count = batches(out, tasks, batch_size)
    print(f"{len(tasks)} episodes, {count} batches in {batch_dir}")


def batches(out: Path, tasks: list[dict], size: int) -> tuple[Path, int]:
    if size < 1:
        raise ValueError("Batch size must be positive")
    parent = out / "llm/batches" / f"size-{size:02d}"
    count = 0
    for count, index in enumerate(range(0, len(tasks), size), 1):
        write(
            parent / f"batch-{count:03d}.jsonl",
            jsonl_text(tasks[index : index + size]),
            immutable=True,
        )
    return parent, count


def _frozen_hashes(out: Path) -> dict[str, str]:
    return {
        name: digest((out / name).read_text(encoding="utf-8").encode()) for name in FROZEN_FILES
    }


def load_tasks(out: Path) -> dict[str, dict]:
    identity = json.loads((out / "sample_identity.json").read_bytes())
    expected = {
        "schema_version": SCHEMA_VERSION,
        "instruction_version": INSTRUCTION_VERSION,
        "files": _frozen_hashes(out),
        **{
            key: digest((out / name).read_text(encoding="utf-8").encode())
            for key, name in (
                ("manifest_sha256", "sample_manifest.csv"),
                ("schema_sha256", "schema.json"),
                ("instruction_sha256", "rubric.md"),
            )
        },
    }
    if identity != expected:
        raise ValueError(f"{out}: annotation version or frozen manifest mismatch")
    tasks = read_jsonl(out / "llm/tasks.jsonl")
    manifest = csv_rows(out / "sample_manifest.csv")
    if [t["episode"] for t in tasks] != [row["episode"] for row in manifest]:
        raise ValueError(f"{out}: tasks differ from the frozen manifest")
    return {task["episode"]: task for task in tasks}


def _require_keys(value: Any, expected, label: str) -> None:
    if not isinstance(value, dict) or set(value) != set(expected):
        actual = set(value) if isinstance(value, dict) else set()
        missing, extra = sorted(set(expected) - actual), sorted(actual - set(expected))
        raise ValueError(f"{label}: expected fields missing={missing}, unexpected={extra}")


def validate_label(task: dict, subject: str, feature: str, label: dict) -> dict:
    where = f"{task['episode']}/{subject}/{feature}"
    _require_keys(label, ("value", "reason", "evidence"), where)
    value, reason, evidence = (label[k] for k in ("value", "reason", "evidence"))
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"{where}: empty rationale")
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) and item in task["evidence_ids"] for item in evidence
    ):
        raise ValueError(f"{where}: invalid evidence IDs")
    if len(evidence) != len(set(evidence)):
        raise ValueError(f"{where}: repeated evidence IDs")
    positive = value == "yes"
    if feature in INTENTS:
        _require_keys(value, ("pairs", "source", "contradiction"), where)
        pairs = value["pairs"]
        if (
            value["source"] not in ("message", "structured_proposal", "both", "unknown")
            or type(value["contradiction"]) is not bool
        ):
            raise ValueError(f"{where}: invalid intent source or contradiction value")
        if isinstance(pairs, list):
            if (
                not pairs
                or not all(pair in task["catalog"][subject] for pair in pairs)
                or len({tuple(p) for p in pairs}) != len(pairs)
            ):
                raise ValueError(f"{where}: invalid, foreign or repeated job/option pair")
            value = {**value, "pairs": sorted(pairs)}
        elif pairs not in ("none", "unclear"):
            raise ValueError(f"{where}: use pairs, none or unclear")
        positive = pairs != "unclear" or value["contradiction"]
        if value["source"] == "unknown" and pairs != "unclear":
            raise ValueError(f"{where}: declared intent needs a source")
    elif value not in VALUES:
        raise ValueError(f"{where}: invalid categorical value")
    if positive and not evidence:
        raise ValueError(f"{where}: explicit claims must cite evidence")
    return {"value": value, "reason": reason.strip(), "evidence": sorted(evidence)}


def validate_response(record: dict, tasks: dict[str, dict]) -> dict:
    _require_keys(
        record,
        (
            "episode",
            "schema_version",
            "instruction_version",
            "manifest_sha256",
            "provenance",
            "labels",
        ),
        "response",
    )
    episode = record["episode"]
    if not isinstance(episode, str) or episode not in tasks:
        raise ValueError(f"{episode}: episode is not in the manifest")
    task = tasks[episode]
    if any(
        record[key] != task[key]
        for key in ("schema_version", "instruction_version", "manifest_sha256")
    ):
        raise ValueError(f"{episode}: response schema, instruction or manifest mismatch")
    provenance = record["provenance"]
    _require_keys(provenance, ("model", "date", "method"), f"{episode}/provenance")
    if any(not isinstance(value, str) or not value.strip() for value in provenance.values()):
        raise ValueError(f"{episode}: provenance must use nonempty strings or 'unknown'")
    if provenance["date"] != "unknown":
        try:
            date.fromisoformat(provenance["date"])
        except ValueError as exc:
            raise ValueError(f"{episode}: expected ISO date or 'unknown'") from exc
    labels = record["labels"]
    required = {key: fields for key, fields in task["required"].items() if fields}
    _require_keys(labels, required, f"{episode}/labels")
    normalized = {}
    for subject, fields in required.items():
        _require_keys(labels[subject], fields, f"{episode}/{subject}")
        normalized[subject] = {
            name: validate_label(task, subject, name, labels[subject][name]) for name in fields
        }
    return {**record, "labels": normalized}


def _read_responses(paths: list[Path], tasks: dict[str, dict]) -> dict[str, dict]:
    accepted = {}
    for path in paths:
        records = read_jsonl(path)
        if not records:
            raise ValueError(f"{path}: response file is empty")
        for record in records:
            normalized = validate_response(record, tasks)
            episode = normalized["episode"]
            if episode in accepted:
                kind = "Duplicate" if accepted[episode] == normalized else "Conflicting"
                raise ValueError(f"{path}: {kind} response for {episode}")
            accepted[episode] = normalized
    return accepted


def imported(out: Path, tasks: dict[str, dict]) -> dict[str, dict]:
    return _read_responses(sorted((out / "llm/responses/imported").glob("*.jsonl")), tasks)


def flat_labels(
    responses: dict[str, dict], objective_agents: dict[tuple[str, str], dict]
) -> list[dict]:
    rows = []
    for episode, response in sorted(responses.items()):
        for subject, labels in response["labels"].items():
            rows.extend(
                {"episode": episode, "subject": subject, "feature": name, **label}
                for name, label in labels.items()
            )
            if "final_intent" in labels:
                rows.append(
                    derived_match(
                        episode, subject, labels["final_intent"], objective_agents[episode, subject]
                    )
                )
    return rows


def derived_match(episode: str, subject: str, label: dict, agent: dict) -> dict:
    pairs = label["value"]["pairs"]
    submitted = {tuple(pair) for pair in json.loads(agent["submitted_pairs"])}
    declared = set() if pairs in ("unclear", "none") else {tuple(pair) for pair in pairs}
    value = "unclear" if pairs == "unclear" else ("yes" if declared == submitted else "no")
    return {
        "episode": episode,
        "subject": subject,
        "feature": "final_plan_matches_submissions",
        "value": value,
        "reason": "Set comparison with all submitted pairs",
        "evidence": label["evidence"],
    }


def import_answers(out: Path, tasks: dict[str, dict], paths: list[Path]) -> None:
    target = out / "llm/responses/imported"
    raw = {path: path.read_bytes() for path in paths}
    pending = [
        path for path, content in raw.items() if not (target / f"{digest(content)}.jsonl").exists()
    ]
    if len(pending) != len(paths):
        print("Previously imported identical files were kept unchanged.")
    combined = _read_responses([*sorted(target.glob("*.jsonl")), *pending], tasks)
    for path in pending:
        content = raw[path]
        _replace(target / f"{digest(content)}.jsonl", content)
    draft = flat_labels(combined, agent_objectives(out))
    for name, level in (("agents", False), ("episodes", True)):
        write(
            out / f"llm/draft_{name}.csv",
            csv_text(
                [row for row in draft if (row["subject"] == "episode") == level], LABEL_FIELDS
            ),
        )
    write(
        out / "llm/provenance.json",
        json_text({key: item["provenance"] for key, item in combined.items()}) + "\n",
    )
    print(f"Imported {len(combined)}/{len(tasks)} episodes")


def agent_objectives(out: Path) -> dict[tuple[str, str], dict]:
    return {(r["episode"], r["agent"]): r for r in csv_rows(out / "objective/agents.csv")}


def import_legacy(out: Path, source: Path) -> None:
    data = source.read_bytes()
    rows = csv_rows(source)
    if not rows:
        raise ValueError("Legacy CSV has no data rows")
    path = out / "legacy" / f"draft-{digest(data)[:16]}.csv"
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"{path}: conflicting legacy import")
    _replace(path, data)
    print(f"Archived {len(rows)} legacy rows at {path} (excluded from current labels)")


def main(argv: list[str] | None = None) -> int:
    from project_d.evaluation import annotation_review as review

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "batch", "import", "import-legacy", "status", "verify", "merge"):
        sub.add_parser(name).add_argument("--out", type=Path, default=OUT)
    for name in ("prepare", "batch"):
        sub.choices[name].add_argument("--batch-size", type=int, default=10)
    sub.choices["import"].add_argument("files", nargs="+", type=Path)
    sub.choices["import-legacy"].add_argument("file", type=Path)
    args = parser.parse_args(argv)
    out = args.out
    try:
        if args.command == "prepare":
            prepare(out, args.batch_size)
            return 0
        tasks = load_tasks(out)
        if args.command == "batch":
            path, count = batches(out, list(tasks.values()), args.batch_size)
            print(f"{count} batches in {path}")
        elif args.command == "import":
            import_answers(out, tasks, args.files)
            review.create_sheets(out, imported(out, tasks), tasks)
        elif args.command == "import-legacy":
            import_legacy(out, args.file)
        else:
            responses = imported(out, tasks)
            if args.command == "verify":
                review.create_sheets(out, responses, tasks)
            elif args.command == "merge":
                return review.merge(out, tasks, responses)
            else:
                print(
                    json.dumps(review.status(out, tasks, responses), ensure_ascii=False, indent=2)
                )
    except (ValueError, KeyError, OSError) as exc:
        print(f"Annotation: {exc}", file=sys.stderr)
        return 1
    return 0
