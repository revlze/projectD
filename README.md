# Project D

Research project on coordinating LLM agents that compete for a shared, limited resource. The goal is to study how coordination mechanisms (reservation, locking, negotiation, etc.) behave under concurrency, reproduce race conditions in a controlled simulator, and check the key safety properties with a formal TLA+ model.

The structure deliberately does not commit to a particular coordination mechanism or LLM framework yet.

## Structure

```
project-d/
├── docs/               proposal, experiment protocol, design decisions
├── src/project_d/
│   ├── agents/         agent logic; acts on the environment only via tools
│   ├── environment/    shared resource and the effects of actions on it
│   ├── simulation/     event ordering and delays (reproducible interleavings)
│   └── evaluation/     metrics and analysis of runs
├── experiments/
│   └── configs/        experiment configurations
├── formal/tla/         TLA+ specifications of the abstract model
├── tests/
├── data/
│   ├── examples/       small hand-written inputs (tracked)
│   └── generated/      generated data (ignored by git)
└── outputs/            run outputs (ignored by git)
```

Agents never touch the resource directly; they go through environment tools, so coordination mechanisms can change without rewriting agent logic. The environment defines what an action does; the simulator decides when it happens. The TLA+ model describes the agreed abstract system, not a translation of the Python code.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # fill in API keys locally, never commit .env
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
