"""Immutable run identity and checked, atomic episode completion records."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any

from project_d.environment.journal import EpisodeMetadata, LogEntry
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

    def load(self, name: str) -> dict[str, Any] | None:
        summary_path = self.root / f"{name}.summary.json"
        if not summary_path.exists():
            self._archive_attempt(name)
            return None
        summary = json.loads(summary_path.read_bytes())
        if summary.get("failure") is not None:
            self._archive_attempt(name)
            return None
        receipt_path = self.root / f"{name}.receipt.json"
        if not receipt_path.exists():
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
        turns = [
            json.loads(line) for line in (self.root / f"{name}.llm.jsonl").read_bytes().splitlines()
        ]
        if len(turns) != summary["llm_turns"] or len(turns) != sum(
            entry.event_type == "decision" for entry in log
        ):
            raise ValueError(f"{name}: LLM journal and environment decision counts differ")
        for turn in turns:
            request = turn.get("request")
            # Request hashes use the same canonical text as LLMPolicy's exact snapshot.
            digest = hashlib.sha256(
                json.dumps(request, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            if (
                not request
                or digest != turn.get("request_sha256")
                or turn.get("tool_result") is None
            ):
                raise ValueError(f"{name}: incomplete request or tool outcome")
            if (
                hashlib.sha256(request["messages"][0]["content"].encode("utf-8")).hexdigest()
                != expected["system_sha256"][turn["agent_id"]]
            ):
                raise ValueError(f"{name}: request system prompt differs from the manifest")
            if fingerprint(request["tools"]) not in expected["tools_sha256"].values():
                raise ValueError(f"{name}: request tools differ from the manifest")
        return summary

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
