# E1 - dev, 10 configurations

400 episodes: variants `U/N U/F A/N A/F U/R1 A/R1 U/R3 A/R3 U/R3P A/R3P` x 10 `dev` profiles x 4 repeats (first agent A/B x role swap). VBC components (`S`, `V`, `G`) are not part of this run.

All episodes share one setup (see `g*/run_manifest.json`, identical in all four groups):

- code `fcca9f7`, clean tree, prompt `protocol-v2.2`;
- Ollama 0.40.17, model `qwen3-4b-t8:latest` = weights `sha256-85e4a5b7...` of `qwen3:4b-instruct-2507-q4_K_M` plus `num_thread 8`;
- context 16384, flash attention, KV cache `q8_0`, `OLLAMA_NUM_PARALLEL=8`, temperature 0.3, llm seed = repeat;
- one RTX 3090 (vast.ai), four runner processes in parallel.

Files:

- `summary_all.csv` - one row per episode, built from all `*.summary.json`. Use this table.
- `g0`-`g3/` - runner output per process: `*.summary.json`, environment journal `*.log.jsonl`, LLM turns `*.llm.jsonl`, prompt hashes `*.prompts.json`, `run_manifest.json`, `run.log` (`run_part1.log` before the restart that dropped the VBC variants).
- `g*/summary.csv` are partial (written by a filtered resume) - do not use them.

Known caveat: on every turn the runner shows the agent its own jobs with status and option costs (`runner.py:155`), while the spec says costs come from `list_jobs()`. The block is identical in all variants. Open question with Seva, 2026-11-24.

The earlier `results/e1_baselines` run (prompt v2.1, Apple M5) is not comparable with this one and is not used.
