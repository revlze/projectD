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

## Results of record

| Directory | Content |
| --- | --- |
| `results/e0-08b2675` | E0, 108 scripted runs without an LLM |
| `results/e1-7a475c0`, `results/e1s-9ad7d2e` | E1 on `dev`: 400 baseline and 280 structured episodes |
| `results/test-32abf0e` | E2, E3, E4-H1 and E4-delay on `test`, 1824 episodes, one frozen configuration |
| `results/test-32abf0e/analysis` | Paired bootstrap, family and profile tables, E3/E4 joins, plan metrics, root conflict, usage, figures |
| `results/test-32abf0e/annotation` | Fixed 108-episode sample for manual annotation, with rules and empty sheets |
| `results/e5-6a5b6f70` | E5, post-hoc exploratory: A/VBC-F on `test`, 112 episodes, compared with E2 on the same keys |

Every series directory has a README with the exact run command, configuration and outcome.

## Reproducing the test analysis

These steps make no model calls; they recompute everything from the committed journals and summaries:

```bash
# statistics and tables (E2 bootstrap, E3 and E4-delay joined with E2 keys, E4-H1 journals)
uv run python -m project_d.evaluation.test_analysis results/test-32abf0e --out results/test-32abf0e/analysis
# main-job conflict outcomes, audited per journal
uv run python -m project_d.evaluation.root_report results/test-32abf0e/e2 results/test-32abf0e/e3 \
  results/test-32abf0e/e4-h1 results/test-32abf0e/e4-delay > results/test-32abf0e/analysis/root_conflict.csv
# SVG figures from the tables above
uv run python -m project_d.evaluation.plots results/test-32abf0e/analysis
# one contrast, as in docs/experiments.md
uv run python -m project_d.evaluation.bootstrap results/test-32abf0e/e2/deepseek-v4-1-flash-1017/summary.csv A/VBC A/R3P
# E5 (A/VBC-F) against E2 on the same keys
uv run python -m project_d.evaluation.e5_analysis results/e5-6a5b6f70/deepseek-v4-1-flash-1017/summary.csv \
  results/test-32abf0e/e2/deepseek-v4-1-flash-1017/summary.csv --out results/e5-6a5b6f70/analysis
# requests and journals of recorded episodes rebuilt through the current code
uv run python -m project_d.experiments.replay_check results/test-32abf0e/e2/deepseek-v4-1-flash-1017
# transcripts for manual annotation (existing sheets are never overwritten)
uv run python -m project_d.evaluation.annotation_sample results/test-32abf0e --out results/test-32abf0e/annotation
```

The bootstrap uses 10 000 draws with seed 20261124, so the numbers reproduce exactly. To rerun a series itself (API key required), use the command in that series' README; for example, E2:

```bash
uv run python -m project_d.experiments.matrix E2 --allow-test --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --output-dir outputs/e2-32abf0e/deepseek-v4-1-flash-1017
```

Hosted weights cannot be pinned, so a rerun reproduces the procedure, not the exact model outputs. The saved journals are the record.
