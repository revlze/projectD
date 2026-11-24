# Project D

Research project on coordinating LLM agents that compete for a shared, limited resource. The goal is to study how coordination mechanisms (reservation, locking, negotiation, etc.) behave under concurrency, reproduce race conditions in a controlled simulator, and check the key safety properties with a formal TLA+ model.

The research design and target contracts are in [docs/protocol.md](docs/protocol.md), [docs/system_spec.md](docs/system_spec.md), and [docs/experiments.md](docs/experiments.md). The current implementation does not yet satisfy all of these contracts; the experiment document distinguishes the planned matrix from the implemented one. Existing E1 logs are diagnostic development results, not the final comparison.

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
├── tests/
├── data/
│   ├── scenarios/      10 dev + 28 test profiles and their SHA-256 manifest
│   └── examples/       historical pilot inputs still used by tests and the pilot CLI
├── results/e1/         preserved diagnostic dev logs from commit fcca9f7
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

The dry run currently reports 560 episodes; the target E1 has 640. It does not establish readiness to run the target protocol. Do not launch E2-E4 until the contract, matrix and resume checks described in the experiment document are implemented and reviewed. Regenerate data only into a separate scratch directory with `generator --out PATH`; do not overwrite the tracked sample to fix a validation failure. Scenario JSON uses LF on every platform, enforced by `.gitattributes`.
