# E1 - dev, U/VBC, DeepSeek, supplement to e1-7a475c0

40 episodes on `deepseek-v4-1-flash-1017`: `U/VBC` x 10 `dev` profiles x 4 repeats. `U/VBC` is full VBC (V, G, one negotiation round) with unreserved execution; it was added on 2026-11-26 as the U/A pair of `A/VBC` for H3 (see `docs/decisions.md`). Superseded as E1 of record by `results/e1s-9ad7d2e` (protocol `vbc-5`); kept as the first `U/VBC` run. The other 16 variants are not rerun; commit `09135ca` changes only the variant registry and the matrix, and the `U/VBC` prompts are byte-identical to `A/VBC`.

Setup (`deepseek-v4-1-flash-1017/run_manifest.json`): code `09135ca` on `feat/u-vbc`, clean tree, prompt `phases-6-vbc`, protocol `vbc-2`; Mistral API, `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, `llm_seed` sent as `random_seed`, history not truncated; 30 parallel episodes; run on 2026-11-26. A one-episode preflight (`dev_s3_01`, repeat 0) passed before the run. Difference from `7a475c0`: requests carry Mistral attribution metadata (`dba59eb`, `request_metadata: true`); it is not part of the model input.

Command:

```
uv run --env-file .env python -m project_d.experiments.matrix E1 --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --variants U/VBC --output-dir outputs/e1-uvbc-09135ca/deepseek-v4-1-flash-1017
```

Outcome: 0 failed episodes, 0 audit issues, 0 length finishes, 0 parse errors.

U_safe/U* (mean over episodes, as in `e1-7a475c0`): U/VBC 0.472; for reference U/F 0.713, U/R3P 0.592, A/VBC 0.914. Budget violated in 21 of 40 episodes (U/F 11, U/R3P 16, A/VBC 0). By agreement outcome: plan confirmed within budget 15 episodes, 0 violations; confirmed over budget 12, 10 violations; no agreement 13, 11 violations.

Files: `deepseek-v4-1-flash-1017/` runner output (`*.summary.json`, `*.log.jsonl`, `*.llm.jsonl`, `*.prompts.json`, `*.receipt.json`, `run_manifest.json`, `summary.csv`) and the console log. Hosted weights cannot be pinned; the date identifies the run. An earlier run of the same 40 episodes on an uncommitted tree is not of record.
