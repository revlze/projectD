# E5 - A/VBC-F on test, post-hoc exploratory

112 episodes of `A/VBC-F` on `deepseek-v4-1-flash-1017` on the 28 `test` profiles x 4 repeats. Code `6a5b6f70` on `master`, clean tree, prompt `phases-6-vbc`, protocol `vbc-5-f`. Same settings as the frozen test run (`results/test-32abf0e`): Mistral API, `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, 30 parallel episodes. Run on 2026-11-27 from 05:29 to 05:32 UTC on the same VPS.

**Status.** The variant was designed after the test results were seen. It explores outcomes with a free negotiation window in VBC. The existing variants were not rerun. Comparisons use E2 on the same `(profile, repeat)` keys and are exploratory.

**Variant.** A/VBC-F is A/VBC (A execution, V and G on, proposals at t=6, first plan version and feedback at t=7, revision at t=33, confirmation at t=37) with the single message round at t=13 replaced by a free-negotiation window, t=8..32. In the window agents get ordinary turns as in F (send_message, read_messages, wait_until, status tools). Outside it, `send_message` returns `messaging_closed`. Delivered messages are shown in the observation, as in VBC rounds, whereas in F the agent has to call `read_messages`. Texts: `docs/system_spec.md`, `docs/experiments.md`.

**Comparability.** `python -m project_d.experiments.replay_check` rebuilds every recorded test episode (E2, E3, E4) through the code at `6a5b6f70` with the recorded model responses. All 1824 episodes give identical requests and identical environment journals, so adding the variant changed nothing for the existing variants. E5 itself also replays identically (112 of 112). Hosted weights cannot be pinned, and E2 ran one day earlier (2026-11-26), so a date effect cannot be excluded.

Command:

```
python3 -m project_d.experiments.matrix E5 --allow-test --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --output-dir outputs/e5-6a5b6f70/deepseek-v4-1-flash-1017
```

Outcome: 0 failed episodes, 0 audit issues, 0 parse errors, 0 length finishes, 0 context warnings. All 766 files (with `results/e5-dev-6a5b6f70`) match the VPS copy byte for byte.

## Paired comparison with E2 (U_safe/U*; `analysis/e5_paired.csv`)

Recompute with `uv run python -m project_d.evaluation.e5_analysis results/e5-6a5b6f70/deepseek-v4-1-flash-1017/summary.csv results/test-32abf0e/e2/deepseek-v4-1-flash-1017/summary.csv --out results/e5-6a5b6f70/analysis`.

The interval is a 10 000-draw stratified profile bootstrap with seed 20261124, as in E2. It is descriptive.

| A/VBC-F vs | A/VBC-F | Reference | Δ | 95% interval | +b/-w/=t |
| --- | ---: | ---: | ---: | --- | --- |
| A/VBC | 0.937 | 0.916 | +0.021 | [−0.005, +0.049] | +13/-3/=12 |
| A/F | 0.937 | 0.961 | −0.023 | [−0.049, +0.003] | +8/-10/=10 |
| A/R3P | 0.937 | 0.932 | +0.006 | [−0.015, +0.030] | +10/-7/=11 |
| A/R3 | 0.937 | 0.940 | −0.003 | [−0.020, +0.012] | +9/-7/=12 |
| A/N | 0.937 | 0.875 | +0.062 | [+0.032, +0.093] | +12/-3/=13 |

By family (`analysis/e5_families_safe_fraction.csv`):

| Variant | S0 | S1 | S2 | S3 | S4 | All |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A/VBC-F | 1.000 | 0.931 | 0.995 | 0.801 | 0.980 | 0.937 |
| A/VBC | 1.000 | 0.917 | 0.963 | 0.755 | 0.974 | 0.916 |
| A/F | 1.000 | 0.927 | 0.996 | 0.918 | 0.975 | 0.961 |

Plans (`analysis/e5_structured.csv`):

| | A/VBC (E2) | A/VBC-F |
| --- | ---: | ---: |
| Agreed (of 112) | 76 | 110 |
| within / over budget | 46 / 30 | 85 / 25 |
| Over-budget share of agreements | 39% | 23% |
| Off-plan attempts / accepted | 25 / 20 | 16 / 16 |
| Violations | 0 | 0 |

Cost (`analysis/e5_usage.csv`): the mean prompt tokens per episode are 155k for A/VBC-F, 129k for A/F and 108k for A/VBC.

Reading: A/VBC-F has a point estimate close to R3 and R3P. It reaches agreement in almost every episode and stays within the agreement budget more often than A/VBC. The utility interval against A/VBC includes zero. In these runs A/VBC-F had lower mean utility than A/F and used more tokens. The utility gap sits almost entirely in S3 (−0.117). The other families are within ±0.005. The comparison covers the full protocols, including differences in available negotiation turns and message display. It does not isolate the effect of plan structure.

`results/e5-dev-6a5b6f70` holds the 40-episode `E5-dev` debugging run on dev, made before E5. It is not a result.
