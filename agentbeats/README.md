# AgentBeats integration

External evaluation of Project D on [AgentBeats](https://agentbeats.dev/). The green agent (assessor) runs the frozen Project D scenarios against participant (purple) agents over A2A and scores them with the same audit and metrics as the research series. The purple agent here is the baseline: the LLM policy of the experiments, served over A2A.

## Design

Each episode is an `EpisodeSpec` of `project_d.experiments.matrix` with series `AB`. The prompts, tools, environment, scheduler, audit and metrics are the same as in E2. The only change is the chat client. `RemoteChatClient` sends every decision to a participant as one A2A message: the agent's full OpenAI-style dialogue and the tools of the current phase (`agentbeats/wire.py`, protocol `project-d/chat-tools/v1`). The participant answers with one assistant message. So participants are stateless, and the green agent keeps every dialogue and every hidden scenario detail.

`tests/test_agentbeats.py` runs real A2A servers with a scripted model. It checks that the episode journals are byte-identical to a local run without A2A. A live run against `deepseek-v4-1-flash-1017` on four `test` keys (`test_s1_01`, `test_s3_02` × `U/F`, `A/VBC`, repeat 0) reproduced the stored E2 outcomes: the same `safe_fraction`, violations and completed jobs.

Assessment request (sent by the AgentBeats gateway):

```json
{"participants": {"agent": "http://...", "peer": "http://..."}, "config": {...}}
```

`agent` is required. With `peer`, the two participants play users A and B; without it, `agent` plays both (self-play). Config keys, all optional:

| Key | Default | Meaning |
| --- | --- | --- |
| `variants` | `["U/F", "U/VBC", "A/F", "A/VBC"]` | protocols, any name accepted by `Variant.parse` |
| `split` | `"test"` | `dev` or `test` profiles |
| `profiles` | all of the split | profile stems, e.g. `["test_s1_01"]` |
| `repeats` | `[0]` | indices into `REPEATS` (order and role swap) |
| `workers` | `8` | episodes in parallel (≤ 32) |
| `shard_index`, `num_shards`, `num_instances` | `0`, `1`, all | set by the leaderboard workflow |

Episodes are ordered by (repeat, profile, variant), truncated to `num_instances`, then sharded. The default is 112 episodes, about 45 s of model time each.

Score: an episode scores `U_safe / U*` (zero if the shared budget was overrun). A failed episode, for example when the participant is unreachable, scores zero. The result artifact holds the summary, per-variant blocks, and one row per episode with the SHA-256 of its journal. Unknown or inconsistent config keys and an empty shard are rejected before any episode starts.

## Run locally

```bash
uv sync --group agentbeats
export LLM_API_KEY=...   # key of the purple agent's provider
uv run --group agentbeats python -m agentbeats.purple --port 9019 &
uv run --group agentbeats python -m agentbeats.green --port 9009 &
uv run --group agentbeats python -m agentbeats.client http://127.0.0.1:9009/ \
  --agent http://127.0.0.1:9019/ \
  --config '{"split": "test", "profiles": ["test_s1_01"], "variants": ["U/F", "A/VBC"]}' \
  --out outputs/agentbeats-result.json
```

Purple configuration comes from the environment: `PURPLE_PROVIDER` (`mistral` by default, also `ollama`, `mimo`, `openai-compatible` with `PURPLE_BASE_URL`), `PURPLE_MODEL`, `PURPLE_TEMPERATURE`, `PURPLE_REASONING_EFFORT`, `PURPLE_SEED`, and the key in `LLM_API_KEY`. The green agent writes full journals to `AGENTBEATS_OUTPUT` (by default a temporary directory).

## Images and manifests

`.github/workflows/agentbeats.yml` tests the code. It then builds `Dockerfile.agentbeats` twice for `linux/amd64` (`AGENT_ROLE=green|purple`) and starts each container. Each container must pass the A2A conformance tests of the official `green-agent-template` (pinned commit). Finally the workflow pushes `ghcr.io/revlze/project-d-green` and `ghcr.io/revlze/project-d-purple` with tags `sha-<commit>` and `latest`. The build itself fails if `data/scenarios` does not match its manifest.

`agentbeats/amber/green.json5` and `agentbeats/amber/purple.json5` are the Amber component manifests used by the leaderboard repository's `scenario.json5`.

Leaderboard repository: [revlze/project-d-agentbeats-leaderboard](https://github.com/revlze/project-d-agentbeats-leaderboard). The scenario there pins both images to `sha-6937a6d`. A local Amber rehearsal of that scenario ran through gateway v0.3 on four episodes against the live model and completed (`amber compile` + `docker compose`).

## Submission of record

| Item | Value |
| --- | --- |
| Green agent | [revlze/project-d-shared-budget-assessor](https://agentbeats.dev/revlze/project-d-shared-budget-assessor), id `01a22048-c3ac-76f2-a5db-6604b8f2375e` |
| Baseline participant | [revlze/project-d-baseline-deepseek-v4-1-flash](https://agentbeats.dev/revlze/project-d-baseline-deepseek-v4-1-flash), id `01a2204a-e138-7133-9685-b69458c86831` |
| Assessment run | https://github.com/revlze/project-d-agentbeats-leaderboard/actions/runs/46105296499 |
| Results | [PR #1](https://github.com/revlze/project-d-agentbeats-leaderboard/pull/1), merged as `06bd0a5`; provenance pins both image digests |

Default assessment: 112 episodes, 0 failed. Score 0.799 overall; A/F 0.981, A/VBC 0.976, U/F 0.679, U/VBC 0.563. Against E2 repeat 0 with the same model (0.958, 0.960, 0.745, 0.567), the violation outcome is identical in all 56 atomic episodes and in 44 of 56 unreserved ones; the remaining differences are compatible with stochastic hosted-model behavior at temperature 0.3. Their cause was not isolated in a controlled experiment. The common absence of atomic budget violations establishes agreement on that outcome alone.
