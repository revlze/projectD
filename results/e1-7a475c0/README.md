# E1 - dev, all 16 variants, DeepSeek, final configuration

640 episodes on `deepseek-v4-1-flash-1017`: 10 baselines (`U|A` x `N F R1 R3 R3P`) and 6 structured variants (`A/S A/S+V A/S+G A/VBC A/VBC-r0 A/VBC-r2`) x 10 `dev` profiles x 4 repeats, all on one commit. This is the E1 of record for DeepSeek; `results/e1-9e36e07` and `results/e1g-7e0316c` are earlier configurations (see `docs/decisions.md`).

Setup (`deepseek-v4-1-flash-1017/run_manifest.json`): code `7a475c0` on `master`, clean tree, prompt `phases-6-vbc`, protocol `vbc-2`; Mistral API, `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, `llm_seed` sent as `random_seed`, history not truncated; 30 parallel episodes; run on 2026-11-25. A 16-episode preflight (all variants on `dev_s3_01`, repeat 0) passed before the run.

Command:

```
uv run --env-file .env python -m project_d.experiments.matrix E1 --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --output-dir outputs/e1-7a475c0/deepseek-v4-1-flash-1017
```

Outcome: 0 failed episodes, 0 audit issues, 0 length finishes, 3 parse errors (each a lost turn in a completed episode). HTTP telemetry is stored per LLM turn in `*.llm.jsonl`.

U_safe/U* by variant: U/N 0.299, U/F 0.713, A/N 0.865, A/F 0.955, U/R1 0.369, A/R1 0.886, U/R3 0.593, A/R3 0.938, U/R3P 0.592, A/R3P 0.913, A/S 0.927, A/S+V 0.904, A/S+G 0.899, A/VBC 0.914, A/VBC-r0 0.918, A/VBC-r2 0.911.

Files: `deepseek-v4-1-flash-1017/` runner output (`*.summary.json`, `*.log.jsonl`, `*.llm.jsonl`, `*.prompts.json`, `*.receipt.json`, `run_manifest.json`, `summary.csv`) and the console log. Hosted weights cannot be pinned; the date identifies the run.
