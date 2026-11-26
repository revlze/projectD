# E1 - dev, structured variants, DeepSeek, protocol vbc-5

280 episodes on `deepseek-v4-1-flash-1017`: the seven structured variants (`A/S A/S+V A/S+G A/VBC A/VBC-r0 A/VBC-r2 U/VBC`) x 10 `dev` profiles x 4 repeats, all on one commit. Together with the 400 baseline episodes of `results/e1-7a475c0` this is the E1 of record for DeepSeek (17 variants, 680 episodes; see `docs/decisions.md`). Baselines are not rerun: with `start_gap = 0` their requests on `9ad7d2e` are byte-identical to `7a475c0` for a scripted client.

Setup (`deepseek-v4-1-flash-1017/run_manifest.json`): code `9ad7d2e` on `fix/plan-refusal-reason`, clean tree, prompt `phases-6-vbc`, protocol `vbc-5`; Mistral API, `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, `llm_seed` sent as `random_seed`, request attribution metadata on (not part of the model input), history not truncated; 30 parallel episodes; run on 2026-11-26.

Command:

```
uv run --env-file .env python -m project_d.experiments.matrix E1 --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --variants "A/S,A/S+V,A/S+G,A/VBC,A/VBC-r0,A/VBC-r2,U/VBC" \
  --output-dir outputs/e1s-9ad7d2e/deepseek-v4-1-flash-1017
```

Outcome: 0 failed episodes, 0 audit issues, 0 length finishes, 0 context warnings, 2 parse errors (each a lost turn in a completed episode). No proposal was refused; 27 proposals had a chosen option removed from their alternatives. Agents confirmed 50% of `OVER_BUDGET` final versions (49% at `vbc-3`, 90% at `vbc-4`).

| Variant | U_safe/U* | Violations | Agreed within budget | Agreed over budget |
| --- | ---: | ---: | ---: | ---: |
| A/S | 0.910 | 0 | 18 | 16 |
| A/S+V | 0.889 | 0 | 17 | 10 |
| A/S+G | 0.907 | 0 | 18 | 16 |
| A/VBC | 0.912 | 0 | 19 | 8 |
| A/VBC-r0 | 0.895 | 0 | 13 | 6 |
| A/VBC-r2 | 0.914 | 0 | 25 | 10 |
| U/VBC | 0.573 | 17 | 23 | 4 |

U_safe/U* is the mean over episodes, as in `e1-7a475c0` (baselines there: U/R3P 0.592, U/F 0.713, A/R3P 0.913, A/F 0.955).

Earlier S runs (`vbc-2` in `e1-7a475c0`, `U/VBC` in `e1-uvbc-09135ca`, `vbc-3` at `5c289af`, `vbc-4` at `278df59`) document the protocol changes and are not used in the final comparisons.

Files: `deepseek-v4-1-flash-1017/` runner output (`*.summary.json`, `*.log.jsonl`, `*.llm.jsonl`, `*.prompts.json`, `*.receipt.json`, `run_manifest.json`, `summary.csv`) and the console log. Hosted weights cannot be pinned; the date identifies the run.
