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
uv run python -m project_d.experiments.matrix E5-dev --dry-run
uv run python -m project_d.experiments.matrix E5 --allow-test --dry-run
```

Dry runs describe the research matrix: E1=680, E2=1344, E3=240, E4-H1=144, E4-delay=96, E5-dev=40 and E5=112 new episodes. The runner implements 18 variants (12 atomic and 6 non-atomic): ten baselines, seven original structured variants and the exploratory `A/VBC-F`. Select the development baseline subset with:

```bash
uv run python -m project_d.experiments.matrix E1 --baseline-only --dry-run
```

The research entrypoint is `project_d.experiments.matrix`. Test series require `--allow-test` and the full selection. Each output directory has an immutable configuration manifest. Resume verifies SHA-256 receipts, audits complete episodes, and recomputes their summaries. Failed attempts are retained under `attempts/`. Scenario JSON uses LF on every platform. Generate data only into a scratch directory with `generator --out PATH`; the tracked sample remains fixed.

## Results of record

| Directory | Content |
| --- | --- |
| `results/e0-08b2675` | E0, 108 scripted runs without an LLM |
| `results/e1-7a475c0`, `results/e1s-9ad7d2e` | Final DeepSeek E1 on `dev`: 400 baseline and 280 structured episodes across 17 variants |
| `results/e1-9e36e07` | Historical Mistral Small and DeepSeek E1 across 16 variants |
| `results/test-32abf0e` | E2, E3, E4-H1 and E4-delay on `test`, 1824 episodes, one frozen configuration |
| `results/test-32abf0e/analysis` | Paired bootstrap, family and profile tables, E3/E4 joins, plan metrics, root conflict, usage, figures |
| `results/test-32abf0e/annotation` | Fixed 108-episode sample for manual annotation, with rules and empty sheets |
| `results/e5-dev-6a5b6f70` | E5-dev, 40 diagnostic episodes of A/VBC-F on `dev` |
| `results/e5-6a5b6f70` | E5, post-hoc exploratory: A/VBC-F on `test`, 112 episodes, compared with E2 on the same keys |

Every series directory has a README with the exact run command, configuration and outcome.

[Formal validation](formal/tla/validation.md) is complete. TLC checked two pilot models and nine configurations of the extended U/A/G model, including `U/VBC`. The checks produced four expected counterexamples and seven successful exhaustive searches. Twelve Python control traces include replays of the key transitions of all three extended counterexamples. The verification covers enforcement while G is active, the conditions for releasing G, the fact that it stays released, and budget safety during fallback under A. These results apply to the checked finite abstraction and selected Python traces.

The remaining stages are negotiation annotation, AgentBeats, the research report and the defense.

## External evaluation (AgentBeats)

`agentbeats/` holds the green agent that serves this benchmark on [AgentBeats](https://agentbeats.dev/), the baseline purple agent, Docker images and Amber manifests; see [agentbeats/README.md](agentbeats/README.md).

## Reproducing the test analysis

These steps make no model calls; they recompute everything from the committed journals and summaries:

```bash
# statistics and tables (E2 bootstrap, E3 and E4-delay joined with E2 keys, E4-H1 journals)
uv run python -m project_d.evaluation.test_analysis results/test-32abf0e --out results/test-32abf0e/analysis
# main-job conflict outcomes, audited per journal
uv run python -m project_d.evaluation.root_report results/test-32abf0e/e2 results/test-32abf0e/e3 \
  results/test-32abf0e/e4-h1 results/test-32abf0e/e4-delay > results/test-32abf0e/analysis/root_conflict.csv
# root outcomes and per-agent first main-job submission times for E2 and E5
uv run python -m project_d.evaluation.root_report results/test-32abf0e/e2 results/e5-6a5b6f70 \
  --out results/test-32abf0e/analysis/root_conflict_e2_e5.csv \
  --timings-out results/test-32abf0e/analysis/root_submission_times_e2_e5.csv
# SVG figures, including matched E2/E3/E5 comparisons
uv run python -m project_d.evaluation.plots results/test-32abf0e/analysis \
  --test-results results/test-32abf0e \
  --e5-summary results/e5-6a5b6f70/deepseek-v4-1-flash-1017/summary.csv
# one contrast, as in docs/experiments.md
uv run python -m project_d.evaluation.bootstrap results/test-32abf0e/e2/deepseek-v4-1-flash-1017/summary.csv A/VBC A/R3P
# E5 (A/VBC-F) against E2 on the same keys
uv run python -m project_d.evaluation.e5_analysis results/e5-6a5b6f70/deepseek-v4-1-flash-1017/summary.csv \
  results/test-32abf0e/e2/deepseek-v4-1-flash-1017/summary.csv --out results/e5-6a5b6f70/analysis
# requests and journals of recorded episodes rebuilt through the current code
uv run python -m project_d.experiments.replay_check results/test-32abf0e/e2/deepseek-v4-1-flash-1017
# transcripts for manual annotation in a scratch directory
uv run python -m project_d.evaluation.annotation_sample results/test-32abf0e --out outputs/annotation
```

The bootstrap uses 10 000 draws with seed 20261124, so the numbers reproduce exactly. To rerun a series itself (API key required), use the command in that series' README; for example, E2:

```bash
uv run python -m project_d.experiments.matrix E2 --allow-test --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --output-dir outputs/e2-32abf0e/deepseek-v4-1-flash-1017
```

Hosted weights cannot be pinned, so a rerun reproduces the procedure, not the exact model outputs. The saved journals are the record.
