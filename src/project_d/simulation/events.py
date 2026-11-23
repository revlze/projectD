"""Deterministic future-event queue."""

from __future__ import annotations

import heapq
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class EventKind(IntEnum):
    """Tie-break order for events that fall on the same logical time."""

    COMMIT = 0
    COMPLETE = 1
    DELIVER = 2
    ROUND_CLOSE = 3
    PLAN_SNAPSHOT = 4
    PLAN_FEEDBACK = 5
    AGREEMENT = 6


@dataclass(frozen=True, order=True)
class Event:
    time: int
    kind: EventKind
    seq: int
    payload: Any = field(compare=False, default=None)


class EventQueue:
    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._next_seq = 0

    def __len__(self) -> int:
        return len(self._heap)

    def push(self, time: int, kind: EventKind, payload: Any = None) -> Event:
        event = Event(time, kind, self._next_seq, payload)
        self._next_seq += 1
        heapq.heappush(self._heap, event)
        return event

    def pop_due(self, time: int) -> Iterator[Event]:
        """Yield events with ``event.time <= time``, including ones pushed while iterating."""
        while self._heap and self._heap[0].time <= time:
            yield heapq.heappop(self._heap)
