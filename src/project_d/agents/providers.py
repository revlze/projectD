"""Named LLM endpoints. Keys come from the environment (for example `uv run --env-file .env`)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from project_d.agents.llm_client import DEFAULT_BASE_URL, LLMConfig

PROVIDERS: dict[str, dict[str, Any]] = {
    # The frozen local baseline: weights and context are checked through Ollama's own API.
    "ollama": {"base_url": DEFAULT_BASE_URL},
    "mimo": {
        "base_url": "https://token-plan-sgp.xiaomimimo.com/v1",
        "api_key_env": "MIMO_API_KEY",
        "max_tokens": 2048,
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "api_key_env": "MISTRAL_API_KEY",
        "max_tokens": 2048,
        "seed_field": "random_seed",
        "tool_call_id_style": "alnum9",
    },
}


def is_local(provider: str) -> bool:
    return provider == "ollama"


def provider_config(provider: str, base: LLMConfig, **overrides: Any) -> LLMConfig:
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}; known: {', '.join(PROVIDERS)}")
    settings = {**PROVIDERS[provider], **{k: v for k, v in overrides.items() if v is not None}}
    return replace(base, **settings)
