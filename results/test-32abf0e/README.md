# Test - E2, E3, E4-H1, E4-delay, DeepSeek, frozen configuration

1824 episodes on `deepseek-v4-1-flash-1017` on the frozen `test` split, one commit, one configuration: E2 1344, E3 240, E4-H1 144, E4-delay 96 (`docs/experiments.md`, section 3). E1 of record: `results/e1-7a475c0` (baselines) and `results/e1s-9ad7d2e` (structured variants, `vbc-5`).

Setup (`*/deepseek-v4-1-flash-1017/run_manifest.json`): code `32abf0e` on `master`, clean tree, prompt `phases-6-vbc`, protocol `vbc-5` for structured variants; Mistral API, `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, `llm_seed` sent as `random_seed`, request attribution metadata on (not part of the model input), history not truncated; 30 parallel episodes. Run on 2026-11-26 from 10:03 to 10:37 UTC on a VPS (1 vCPU, 1 GB RAM, system Python 3.12.3 with `PYTHONPATH=src`; the code has no dependencies). E1 ran locally on Python 3.14; requests are built by the same standard-library code. `progress.log` is the series log of the run script; the series ran one after another and each started only after the previous one ended with 0 failures and 0 audit issues.

Command per series (`<S>` = E2, E3, E4-H1, E4-delay):

```
python3 -m project_d.experiments.matrix <S> --allow-test --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --output-dir outputs/<s>-32abf0e/deepseek-v4-1-flash-1017
```

Outcome: 0 failed episodes, 0 audit issues, 0 context warnings in every series; 13 parse errors (E2 12, E3 1) and 5 length finishes (E2 4, E3 1), each a lost turn in a completed episode. All 1824 episodes were re-verified locally through their receipts (journal audit, shown history, manifest), and all 9132 files match the VPS copy byte for byte.

## E2 (28 profiles x 4 repeats per variant)

U_safe/U* is the mean over episodes.

| Protocol | U: U_safe/U* | U: violations | A: U_safe/U* | A: violations |
| --- | ---: | ---: | ---: | ---: |
| N | 0.222 | 87 | 0.875 | 0 |
| F | 0.754 | 27 | 0.961 | 0 |
| R1 | 0.347 | 73 | 0.883 | 0 |
| R3 | 0.638 | 40 | 0.940 | 0 |
| R3P | 0.734 | 29 | 0.932 | 0 |
| VBC | 0.524 | 53 | 0.916 | 0 |

Agreements in VBC: U/VBC 45 within budget, 28 over budget; A/VBC 46 within, 30 over.

## E3 (12 profiles of `e3_subset` x 4 repeats)

| Variant | U_safe/U* | Agreed within budget | Agreed over budget |
| --- | ---: | ---: | ---: |
| A/S | 0.888 | 12 | 26 |
| A/S+V | 0.905 | 15 | 5 |
| A/S+G | 0.900 | 14 | 33 |
| A/VBC-r0 | 0.875 | 8 | 12 |
| A/VBC-r2 | 0.916 | 26 | 17 |

`A/VBC` (one round) for the V x G and round comparisons is taken from E2 on the same keys.

## E4-H1 (`test_s1_01`, `test_s1_02` x 4 repeats, 8 episodes per cell)

Episodes with a budget violation:

| Variant | commit_delay | gap 0 | gap 2 | gap 4 |
| --- | ---: | ---: | ---: | ---: |
| U/N | 0 | 0 | 0 | 0 |
| U/N | 1 | 8 | 0 | 0 |
| U/N | 3 | 8 | 8 | 0 |
| U/R3P | 0 | 0 | 0 | 0 |
| U/R3P | 1 | 7 | 0 | 0 |
| U/R3P | 3 | 8 | 7 | 0 |

## E4-delay (six S4 profiles x 4 repeats, 24 episodes per cell)

| Variant | message_delay 4 | message_delay 8 |
| --- | ---: | ---: |
| A/R3P | 0.964 | 0.967 |
| A/VBC | 0.966 | 0.963 |

Delay 1 is taken from E2 on the same keys.

These are descriptive numbers; hypothesis tests (paired bootstrap by profile) are done in the analysis, not here.

Files: per series, `deepseek-v4-1-flash-1017/` runner output (`*.summary.json`, `*.log.jsonl`, `*.llm.jsonl`, `*.prompts.json`, `*.receipt.json`, `run_manifest.json`, `summary.csv`) and the console log. Hosted weights cannot be pinned; the date identifies the run.
