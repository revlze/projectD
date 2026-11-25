# E1 - dev, all 16 variants, two API models

640 episodes per model: 10 baselines (`U|A` x `N F R1 R3 R3P`) and 6 structured variants (`A/S A/S+V A/S+G A/VBC A/VBC-r0 A/VBC-r2`) x 10 `dev` profiles x 4 repeats (first agent A/B x role swap).

Setup (see `<model>/run_manifest.json`):

- code `9e36e07` on `master`, clean tree, prompt `phases-4-vbc`;
- Mistral API, models `mistral-small-2603` and `deepseek-v4-1-flash-1017`;
- `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, `llm_seed` sent as `random_seed`, history not truncated;
- 12 parallel episodes for Small, 30 for DeepSeek; run on 2026-11-25.

Command, run once per model:

```
uv run --env-file .env python -m project_d.experiments.matrix E1 \
  --provider mistral --model <model> --reasoning-effort none --workers <12|30> \
  --output-dir outputs/e1-9e36e07/<model>
```

Outcome: 0 failed episodes and 0 audit issues for both models. Small: 0 parse errors, 0 length finishes. DeepSeek: 2 parse errors and 2 length finishes (`E1__dev_s1_02__A-F__r2`, `E1__dev_s4_02__A-R1__r0`), both episodes completed normally. The trailing `ValueError: I/O operation on closed file` lines in `mistral-small-2603.console.log` are Python warnings when HTTP connections are finalized at exit; all 640 episodes are present.

Files: `summary_all.csv` (one row per episode, both models, `model` column), `<model>/` runner output (`*.summary.json`, `*.log.jsonl`, `*.llm.jsonl`, `*.prompts.json`, `*.receipt.json`, `run_manifest.json`, `summary.csv`), `<model>.console.log`.

Hosted weights cannot be pinned; the date above identifies the run.
