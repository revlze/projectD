# Project D

Research project on coordinating LLM agents that compete for a shared, limited resource. The goal is to study how coordination mechanisms (reservation, locking, negotiation, etc.) behave under concurrency, reproduce race conditions in a controlled simulator, and check the key safety properties with a formal TLA+ model.

The research design and target contracts are in [docs/protocol.md](docs/protocol.md), [docs/system_spec.md](docs/system_spec.md), and [docs/experiments.md](docs/experiments.md). Existing E1 logs are diagnostic development results, not the final comparison.

## Structure

```
project-d/
├── docs/               proposal, experiment protocol, design decisions
├── src/project_d/
│   ├── agents/         agent logic; acts on the environment only via tools
│   ├── environment/    shared resource and the effects of actions on it
│   ├── simulation/     event ordering and delays (reproducible interleavings)
│   ├── evaluation/     metrics and analysis of runs
│   └── experiments/    scenario generation, validation and experiment entrypoint
├── formal/tla/         TLA+ specifications of the abstract model
├── tests/              checks and historical unit-test fixtures
├── data/
│   └── scenarios/      10 dev + 28 test profiles and their SHA-256 manifest
├── results/e1/         preserved diagnostic dev logs (code fc44bab in master)
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

Validate the tracked scenarios without LLM calls or rewriting data:

```bash
uv run python -m project_d.experiments.generator --check data/scenarios
uv run python -m project_d.experiments.matrix E1 --dry-run
```

Dry runs describe the complete research matrix: E1=680, E2=1344, E3=240, E4-H1=144 and E4-delay=96 new episodes. The LLM runner accepts ten baseline and seven structured variants (`U/VBC` is full VBC without reservation). Select the development baseline subset with:

```bash
uv run python -m project_d.experiments.matrix E1 --baseline-only --dry-run
```

The research entrypoint is `project_d.experiments.matrix`. Test series require `--allow-test` and the full selection. Each output directory has an immutable configuration manifest. Resume verifies SHA-256 receipts, audits complete episodes, and recomputes their summaries. Failed attempts are retained under `attempts/`. Scenario JSON uses LF on every platform. Generate data only into a scratch directory with `generator --out PATH`; the tracked sample remains fixed.
