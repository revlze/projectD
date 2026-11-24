# E1 baseline - dev, 10 configurations, two API models

400 episodes per model: variants `U/N U/F A/N A/F U/R1 A/R1 U/R3 A/R3 U/R3P A/R3P` x 10 `dev` profiles x 4 repeats (first agent A/B x role swap). VBC (`S`, `V`, `G`) is not implemented yet and is not part of this run; full E1 adds the 240 structured episodes later.

Setup (see `<model>/run_manifest.json`):

- code `bc00219` on `master`, clean tree, prompt `baseline-phases-2`;
- Mistral API (`https://api.mistral.ai/v1`), models `mistral-small-2603` and `deepseek-v4-1-flash-1017`;
- `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, `llm_seed` sent as `random_seed`, history not truncated;
- 12 episodes in parallel per model; run on 2026-11-24.

Command, run once per model:

```
uv run --env-file .env python -m project_d.experiments.matrix E1 --baseline-only \
  --provider mistral --model <model> --reasoning-effort none --workers 12 \
  --output-dir outputs/e1-baseline-bc00219/<model>
```

Outcome: 0 failed episodes and 0 audit issues for both models; 0 length finishes; parse errors 0 (Small) and 5 (DeepSeek).

Files:

- `summary_all.csv` - one row per episode for both models, with a `model` column. Use this table.
- `<model>/` - runner output: `*.summary.json`, environment journal `*.log.jsonl`, LLM turns with full requests `*.llm.jsonl`, prompt hashes `*.prompts.json`, completion receipts `*.receipt.json`, `run_manifest.json`, `summary.csv`.
- `<model>.console.log` - runner console output.

Hosted weights cannot be pinned: the provider may change a model under the same id, and equal seeds do not guarantee equal answers. The dates above identify the run.
