"""Replay recorded LLM episodes offline and check their requests and journals."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from itertools import zip_longest
from pathlib import Path
from typing import Any

from project_d.agents.llm_client import (
    ChatResponse,
    LLMConfig,
    LLMTransportError,
    OpenAICompatibleClient,
)
from project_d.agents.runner import LLMEpisode, TurnRecord, run_llm_episode
from project_d.environment.journal import journal_lines
from project_d.environment.model import RunConfig, Variant, load_scenario
from project_d.experiments.matrix import DATA_ROOT
from project_d.experiments.storage import file_sha256


def _first_key(expected: Any, actual: Any, path: str) -> str | None:
    if type(expected) is not type(actual):
        return path
    if isinstance(expected, dict):
        for key in expected:
            if key not in actual:
                return f"{path}.{key}"
            if difference := _first_key(expected[key], actual[key], f"{path}.{key}"):
                return difference
        for key in actual:
            if key not in expected:
                return f"{path}.{key}"
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}.length"
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            if difference := _first_key(left, right, f"{path}[{index}]"):
                return difference
    elif expected != actual:
        return path
    return None


def _turn_label(index: int, turn: TurnRecord) -> str:
    return f"turn {index} ({turn.agent_id} at t={turn.logical_time})"


class _ReplayClient(OpenAICompatibleClient):
    """Build the live client's HTTP payload, then substitute the stored response."""

    def __init__(self, config: LLMConfig, turns: list[TurnRecord]) -> None:
        super().__init__(config)
        self.turns = iter(turns)
        self.calls = 0
        self.wire_mismatches: set[tuple[str, int]] = set()

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse:
        self.calls += 1
        turn = next(self.turns, None)
        if turn is None:
            raise ValueError(f"extra call at turn {self.calls}")
        if turn.http:
            body = json.dumps(self.build_payload(messages, tools), ensure_ascii=False)
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != turn.http["payload_sha256"]:
                self.wire_mismatches.add((turn.agent_id, turn.logical_time))
        if turn.transport_error is not None:
            raise LLMTransportError(turn.transport_error)
        return ChatResponse(turn.message, turn.finish_reason, turn.usage, turn.latency_s)


def _request_difference(
    expected: list[TurnRecord], actual: list[TurnRecord], wire_mismatches: set[tuple[str, int]]
) -> str | None:
    for index, (left, right) in enumerate(zip_longest(expected, actual), 1):
        if left is None or right is None:
            turn = right if left is None else left
            return f"{_turn_label(index, turn)} {'extra' if left is None else 'missing'} request"
        label = _turn_label(index, left)
        for key in ("agent_id", "logical_time"):
            if getattr(left, key) != getattr(right, key):
                return f"{label} {key}"
        if json.dumps(left.request, ensure_ascii=False) != json.dumps(
            right.request, ensure_ascii=False
        ):
            key = _first_key(left.request, right.request, "request")
            return f"{label} {key or 'request JSON bytes'}"
        if left.request_sha256 != right.request_sha256:
            return f"{label} request_sha256"
        if (left.agent_id, left.logical_time) in wire_mismatches:
            return f"{label} http.payload_sha256"
    return None


def _journal_difference(path: Path, episode: LLMEpisode) -> str | None:
    if episode.result is None:
        return "line 1 missing regenerated metadata"
    actual = journal_lines(episode.result.metadata, episode.result.log)
    with path.open(encoding="utf-8", newline="") as expected:
        for index, (left, right) in enumerate(zip_longest(expected, actual), 1):
            if left == right:
                continue
            if left is None or right is None:
                return f"line {index} {'extra' if left is None else 'missing'} regenerated row"
            try:
                key = _first_key(json.loads(left), json.loads(right), "$")
            except json.JSONDecodeError:
                return f"line {index} invalid recorded JSON"
            return f"line {index} {key or 'JSON bytes'}"
    return None


def _replay(
    root: Path,
    name: str,
    identity: dict[str, Any],
    llm_settings: dict[str, Any],
    data_root: Path,
) -> tuple[str | None, str | None]:
    profile = data_root / identity["spec"]["profile"]
    if file_sha256(profile) != identity["scenario_sha256"]:
        raise ValueError(f"{profile}: scenario differs from the run manifest")
    scenario = load_scenario(profile)
    # The manifest keeps the original run settings and a copy of the journal header.
    mode = Variant.parse(identity["metadata"]["variant"])
    config = RunConfig(**(identity["config"] | {"mode": mode}))
    with (root / f"{name}.llm.jsonl").open(encoding="utf-8") as handle:
        recorded = [TurnRecord(**json.loads(line)) for line in handle]
    # The artifact sorts by (time, agent ID); the scheduler calls the first agent first.
    call_order = sorted(
        recorded, key=lambda turn: (turn.logical_time, turn.agent_id != config.first_agent)
    )
    client = _ReplayClient(LLMConfig(**llm_settings, seed=identity["llm_seed"]), call_order)
    episode = run_llm_episode(scenario, config, client)
    request = _request_difference(recorded, episode.turns, client.wire_mismatches)
    if request is None and client.calls > len(recorded):
        request = f"turn {client.calls} extra request"
    return request, _journal_difference(root / f"{name}.log.jsonl", episode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    args = parser.parse_args(argv)
    total = total_requests = total_journals = errors = 0
    for root in args.run_dirs:
        try:
            manifest = json.loads((root / "run_manifest.json").read_bytes())
            identities = manifest["episodes"]
            llm_settings = manifest["runtime"].get("llm", {})
            names = set(identities)
            for suffix in (".log.jsonl", ".llm.jsonl"):
                names.update(path.name.removesuffix(suffix) for path in root.glob(f"*{suffix}"))
            if not names:
                raise ValueError("no episodes")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"{root}: {exc}", file=sys.stderr)
            errors += 1
            continue

        requests = journals = 0
        for name in sorted(names):
            try:
                request, journal = _replay(
                    root, name, identities[name], llm_settings, args.data_root
                )
            except (OSError, ValueError, KeyError, TypeError) as exc:
                print(f"{root}/{name}: {exc}", file=sys.stderr)
                errors += 1
                continue
            if request:
                if not requests:
                    print(f"{root}/{name}: request mismatch at {request}", file=sys.stderr)
                requests += 1
            if journal:
                if not journals:
                    print(f"{root}/{name}: journal mismatch at {journal}", file=sys.stderr)
                journals += 1
        print(
            f"{root}: {len(names)} episodes, {requests} request mismatches, "
            f"{journals} journal mismatches"
        )
        total += len(names)
        total_requests += requests
        total_journals += journals

    print(
        f"Total: {total} episodes, {total_requests} request mismatches, "
        f"{total_journals} journal mismatches"
    )
    if errors:
        print(f"Replay errors: {errors}", file=sys.stderr)
    return int(bool(total_requests or total_journals or errors))


if __name__ == "__main__":
    raise SystemExit(main())
