"""Immutable run identity and checked, atomic episode completion records."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project_d.agents.runner import TurnRecord
from project_d.environment.journal import EpisodeMetadata, LogEntry
from project_d.environment.model import CONFIRM_TIME, PROPOSE_TIMES, Variant
from project_d.evaluation.audit import audit_episode


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# When a run was first started is a record, not configuration: a resumed run keeps it.
VOLATILE_RUNTIME_KEYS = ("started_utc",)


def _comparable(identity: dict[str, Any]) -> dict[str, Any]:
    runtime = identity.get("runtime")
    if not isinstance(runtime, dict):
        return identity
    stable = {key: value for key, value in runtime.items() if key not in VOLATILE_RUNTIME_KEYS}
    return {**identity, "runtime": stable}


@dataclass(frozen=True)
class SavedEpisode:
    metadata: EpisodeMetadata
    log: list[LogEntry]
    turns: list[TurnRecord]
    prompt_version: str
    summary: dict[str, Any]


def _calls(message: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (call["function"]["name"], call["function"]["arguments"])
        for call in message.get("tool_calls") or []
    ]


def _expected_removed(turn: TurnRecord) -> list[dict[str, str]] | None:
    """Alternatives an accepted proposal must drop, rebuilt from the model's own call."""
    calls = _calls(turn.message)
    # Only the first call is executed; extra calls are dropped or make the action invalid.
    if not calls or calls[0][0] != "propose_plan" or turn.tool_result["status"] != "ok":
        return None
    arguments = json.loads(calls[0][1])
    chosen = {(item["job_id"], item["option_id"]) for item in arguments.get("items", [])}
    removed = [
        {"job_id": item["job_id"], "option_id": item["option_id"]}
        for item in arguments.get("disclosed_alternatives") or []
        if (item["job_id"], item["option_id"]) in chosen
    ]
    return removed or None


def _check_shown_results(name: str, turns: list[TurnRecord]) -> None:
    """The next request of each agent must show exactly the recorded reply and tool result."""
    by_agent: dict[str, list[TurnRecord]] = {}
    for turn in turns:
        by_agent.setdefault(turn.agent_id, []).append(turn)
    for agent_turns in by_agent.values():
        agent_turns.sort(key=lambda turn: turn.logical_time)
        for turn in agent_turns:
            try:
                expected_removed = _expected_removed(turn)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise ValueError(f"{name}: unreadable proposal call") from exc
            if turn.tool_result["data"].get("removed_alternatives") != expected_removed:
                raise ValueError(f"{name}: removed alternatives differ from the proposal call")
        for previous, current in itertools.pairwise(agent_turns):
            before = previous.request["messages"]
            after = current.request["messages"]
            if after[: len(before)] != before or len(after) < len(before) + 3:
                raise ValueError(f"{name}: request history is not a continuation")
            reply, *shown, _observation = after[len(before) :]
            result = previous.tool_result
            payload = {
                "status": result["status"],
                "logical_time": result["logical_time"],
                "submission_open_at": result["submission_open_at"],
                **result["data"],
            }
            if (
                reply.get("role") != "assistant"
                or (reply.get("content") or "") != (previous.message.get("content") or "")
                or _calls(reply) != _calls(previous.message)
            ):
                raise ValueError(f"{name}: request history differs from the recorded reply")
            for message in shown:
                try:
                    content = json.loads(message["content"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(f"{name}: unreadable tool result in history") from exc
                # A parse error replaces "error" in the rendered result; otherwise it is exact.
                ignored = {"error"} if previous.parse_error else set()
                if (
                    message.get("role") not in ("tool", "user")
                    or not isinstance(content, dict)
                    or {k: v for k, v in content.items() if k not in ignored}
                    != {k: v for k, v in payload.items() if k not in ignored}
                ):
                    raise ValueError(f"{name}: shown tool result differs from the record")


class RunStore:
    def __init__(self, root: Path, identity: dict[str, Any]) -> None:
        self.root = root
        self.identity = identity
        self.lock = root / ".run.lock"

    def __enter__(self) -> RunStore:
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            with self.lock.open("x", encoding="utf-8") as handle:
                json.dump({"pid": os.getpid(), "host": platform.node()}, handle)
        except FileExistsError as exc:
            raise ValueError(
                f"Run directory is locked; inspect {self.lock} before retrying"
            ) from exc
        try:
            path = self.root / "run_manifest.json"
            if path.exists():
                if _comparable(json.loads(path.read_bytes())) != _comparable(self.identity):
                    raise ValueError("Run configuration differs from the saved manifest")
            else:
                if any(item != self.lock for item in self.root.iterdir()):
                    raise ValueError(
                        "Output directory contains artifacts without a matching manifest"
                    )
                write_json(path, self.identity)
        except BaseException:
            self.lock.unlink()
            raise
        return self

    def __exit__(self, *_: Any) -> None:
        self.lock.unlink()

    def load(self, name: str) -> SavedEpisode | None:
        summary_path = self.root / f"{name}.summary.json"
        receipt_path = self.root / f"{name}.receipt.json"
        if not receipt_path.exists():
            if (
                summary_path.exists()
                and json.loads(summary_path.read_bytes()).get("failure_kind") == "environment"
            ):
                raise ValueError(f"{name}: unresolved environment failure")
            # Interrupted between the summary and its receipt: the attempt is not trusted.
            self._archive_attempt(name)
            return None
        receipt = json.loads(receipt_path.read_bytes())
        expected = self.identity["episodes"][name]
        if receipt.get("identity_sha256") != fingerprint(expected):
            raise ValueError(f"{name}: episode configuration differs from the manifest")
        suffixes = ("log.jsonl", "llm.jsonl", "prompts.json", "summary.json")
        if set(receipt.get("sha256", {})) != set(suffixes):
            raise ValueError(f"{name}: incomplete artifact inventory")
        for suffix in suffixes:
            path = self.root / f"{name}.{suffix}"
            if not path.exists() or file_sha256(path) != receipt["sha256"][suffix]:
                raise ValueError(f"{name}: missing or modified {suffix}")
        summary = json.loads(summary_path.read_bytes())
        raw = [
            json.loads(line) for line in (self.root / f"{name}.log.jsonl").read_bytes().splitlines()
        ]
        if not raw or raw[0].get("metadata") != expected["metadata"]:
            raise ValueError(f"{name}: journal metadata differs from the intended episode")
        metadata = EpisodeMetadata(**raw[0]["metadata"])
        log = [LogEntry(**entry) for entry in raw[1:]]
        report = audit_episode(metadata, log, require_complete=True)
        if not report.consistent:
            raise ValueError(f"{name}: journal audit failed: {report.issues}")
        prompts = json.loads((self.root / f"{name}.prompts.json").read_bytes())
        if prompts != {
            "version": self.identity["prompt_version"],
            "system_sha256": expected["system_sha256"],
        }:
            raise ValueError(f"{name}: prompts artifact differs from the manifest")
        turns = [
            TurnRecord(**json.loads(line))
            for line in (self.root / f"{name}.llm.jsonl").read_bytes().splitlines()
        ]
        keys = {(turn.agent_id, turn.logical_time) for turn in turns}
        if len(keys) != len(turns) or keys != report.tool_statuses.keys():
            raise ValueError(f"{name}: LLM and environment decisions differ by agent or time")
        variant = Variant.parse(metadata.variant)
        opens_at = min(metadata.submission_open_at.values())
        for turn in turns:
            request = turn.request
            # Request hashes use the same canonical text as LLMPolicy's exact snapshot.
            digest = hashlib.sha256(
                json.dumps(request, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            if (
                not request
                or digest != turn.request_sha256
                or not isinstance(turn.tool_result, dict)
                or not isinstance(turn.tool_result.get("data", {}), dict)
                or turn.tool_result.get("logical_time") != turn.logical_time
                or turn.tool_result.get("status")
                != report.tool_statuses[turn.agent_id, turn.logical_time]
                or (turn.tool_result.get("data") or {}).get("removed_alternatives")
                != report.removed_alternatives.get((turn.agent_id, turn.logical_time))
                or turn.transport_error is not None
            ):
                raise ValueError(f"{name}: incomplete request or tool outcome")
            system, user = request["messages"][:2]
            if (
                hashlib.sha256(system["content"].encode("utf-8")).hexdigest()
                != expected["system_sha256"][turn.agent_id]
                or hashlib.sha256(user["content"].encode("utf-8")).hexdigest()
                != expected["user_sha256"][turn.agent_id]
            ):
                raise ValueError(f"{name}: request prompts differ from the manifest")
            time = turn.logical_time
            if time in variant.round_times:
                phase = "message_round"
            elif variant.structured and time in PROPOSE_TIMES:
                phase = "propose"
            elif variant.structured and time == CONFIRM_TIME:
                phase = "confirm"
            elif time < opens_at:
                phase = "preparation"
            elif time < metadata.submission_open_at[turn.agent_id]:
                phase = "execution_wait"
            else:
                phase = "execution"
            prefix = (
                f"logical_time={turn.logical_time}; "
                f"submission_open_at={metadata.submission_open_at[turn.agent_id]}; "
                f"phase={phase}; "
            )
            if not request["messages"][-1]["content"].startswith(prefix):
                raise ValueError(f"{name}: request observation differs from the decision")
            if fingerprint(request["tools"]) != expected["tools_sha256"][phase]:
                raise ValueError(f"{name}: request tools differ from the manifest")
        _check_shown_results(name, turns)
        return SavedEpisode(metadata, log, turns, prompts["version"], summary)

    def complete(self, name: str, summary: dict[str, Any]) -> None:
        write_json(self.root / f"{name}.summary.json", summary)
        if summary["failure"] is not None:
            return
        suffixes = ("log.jsonl", "llm.jsonl", "prompts.json", "summary.json")
        write_json(
            self.root / f"{name}.receipt.json",
            {
                "identity_sha256": fingerprint(self.identity["episodes"][name]),
                "sha256": {
                    suffix: file_sha256(self.root / f"{name}.{suffix}") for suffix in suffixes
                },
            },
        )
        try:
            self.load(name)
        except ValueError:
            (self.root / f"{name}.receipt.json").unlink()
            raise

    def _archive_attempt(self, name: str) -> None:
        files = [
            self.root / f"{name}.{suffix}"
            for suffix in ("log.jsonl", "llm.jsonl", "prompts.json", "summary.json", "receipt.json")
        ]
        files = [path for path in files if path.exists()]
        if not files:
            return
        parent = self.root / "attempts" / name
        index = 1
        while (parent / f"attempt_{index:03d}").exists():
            index += 1
        destination = parent / f"attempt_{index:03d}"
        destination.mkdir(parents=True)
        for path in files:
            path.rename(destination / path.name)
