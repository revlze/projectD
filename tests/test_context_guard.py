from __future__ import annotations

from project_d.agents.runner import LLMEpisode, TurnRecord
from project_d.experiments.matrix import context_problem


def episode(*tokens: tuple[str, int]) -> LLMEpisode:
    turns = [
        TurnRecord(agent, time, {}, "tool_calls", {"prompt_tokens": size}, 0.0, "Finish()", None, 0)
        for time, (agent, size) in enumerate(tokens)
    ]
    return LLMEpisode(None, turns)


def test_growing_history_is_clean() -> None:
    assert context_problem(episode(("A", 900), ("B", 800), ("A", 1200)), 16384) is None


def test_falling_prompt_size_is_truncation() -> None:
    problem = context_problem(episode(("A", 4080), ("A", 3979)), 16384)
    assert problem is not None and problem.startswith("context_truncated")


def test_agents_are_compared_separately() -> None:
    assert context_problem(episode(("A", 4000), ("B", 1000), ("A", 4100)), 16384) is None


def test_prompt_near_limit_is_flagged() -> None:
    problem = context_problem(episode(("A", 15000)), 16384)
    assert problem is not None and problem.startswith("context_limit")
