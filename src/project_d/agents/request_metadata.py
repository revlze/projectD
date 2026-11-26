"""Per-dialogue request attribution for Project D's Mistral API client."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class TelemetryRequestMetadata:
    call_type: Literal["main_call", "secondary_call"] = "main_call"
    call_source: str = "vibe_code"

    def to_payload(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items() if value is not None}


def build_request_metadata(
    *,
    call_type: Literal["main_call", "secondary_call"] = "main_call",
) -> dict[str, str]:
    return TelemetryRequestMetadata(
        call_type=call_type,
    ).to_payload()
