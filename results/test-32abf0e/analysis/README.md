# Test analysis - E2, E3, E4 at `32abf0e`

All tables here are recomputed from the saved summaries and journals in this directory's parent, with no model calls:

```
uv run python -m project_d.evaluation.test_analysis results/test-32abf0e --out results/test-32abf0e/analysis
uv run python -m project_d.evaluation.root_report results/test-32abf0e/e2 results/test-32abf0e/e3 \
  results/test-32abf0e/e4-h1 results/test-32abf0e/e4-delay > results/test-32abf0e/analysis/root_conflict.csv
uv run python -m project_d.evaluation.plots results/test-32abf0e/analysis
```

Figures (`figures/`, SVG): `e2_safe_fraction.svg`, `e2_violations.svg`, `e2_prompt_tokens.svg`, `e2_bootstrap.svg` (forest plot of all E2 contrasts) and `e4_h1_violations.svg`.

Method (`docs/experiments.md`, section 4): the four repeats are averaged within each profile, and differences are paired per profile. Only E2 (28 profiles) gets the stratified profile bootstrap, with 10 000 draws, seed 20261124, and resampling within S0-S4. The interval is the 2.5-97.5 percentile range of the mean paired difference. It describes how robust the result is to the choice of profiles; it is not a significance test. E3 (12 profiles) and E4-delay (6 profiles, all S4) are descriptive only. `violation` is the episode share with `spent > budget`, and `utility_fraction` is U/U* without the safety cut. In A, `safe_fraction = utility_fraction` because no A episode overran.

## E2 - paired bootstrap

`+b/-w/=t` counts the profiles where the first variant is better, worse or tied. The full table, which also gives `utility_fraction` and `violation` for every contrast, is in `e2_bootstrap.csv`.

| H | Contrast | Δ U_safe/U* | 95% interval | +b/-w/=t | Δ violation share |
| --- | --- | ---: | --- | --- | ---: |
| H2 | U/F − U/N | +0.532 | [+0.453, +0.615] | +20/-1/=7 | −0.536 |
| H2 | U/R1 − U/F | −0.407 | [−0.496, −0.312] | +2/-20/=6 | +0.411 |
| H2 | U/R3 − U/R1 | +0.291 | [+0.221, +0.361] | +16/-0/=12 | −0.295 |
| H2 | U/R3P − U/R3 | +0.096 | [+0.019, +0.178] | +8/-4/=16 | −0.098 |
| H2 | A/F − A/N | +0.085 | [+0.057, +0.112] | +15/-5/=8 | 0 |
| H2 | A/R1 − A/F | −0.078 | [−0.103, −0.050] | +4/-16/=8 | 0 |
| H2 | A/R3 − A/R1 | +0.057 | [+0.035, +0.083] | +16/-4/=8 | 0 |
| H2 | A/R3P − A/R3 | −0.008 | [−0.026, +0.011] | +4/-11/=13 | 0 |
| H3 | A/N − U/N | +0.653 | [+0.578, +0.721] | +23/-0/=5 | −0.777 |
| H3 | A/F − U/F | +0.207 | [+0.127, +0.288] | +14/-2/=12 | −0.241 |
| H3 | A/R1 − U/R1 | +0.536 | [+0.450, +0.621] | +22/-0/=6 | −0.652 |
| H3 | A/R3 − U/R3 | +0.302 | [+0.212, +0.399] | +15/-2/=11 | −0.357 |
| H3 | A/R3P − U/R3P | +0.198 | [+0.110, +0.282] | +12/-5/=11 | −0.259 |
| H3 | A/VBC − U/VBC | +0.393 | [+0.296, +0.483] | +19/-2/=7 | −0.473 |
| H4 | A/VBC − A/N | +0.041 | [+0.006, +0.076] | +11/-7/=10 | 0 |
| H4 | A/VBC − A/F | −0.044 | [−0.069, −0.019] | +4/-13/=11 | 0 |
| H4 | A/VBC − A/R1 | +0.033 | [+0.006, +0.064] | +12/-6/=10 | 0 |
| H4 | A/VBC − A/R3 | −0.024 | [−0.048, +0.002] | +7/-11/=10 | 0 |
| H4 | A/VBC − A/R3P | −0.015 | [−0.034, −0.001] | +6/-10/=12 | 0 |
| H4 | U/VBC − U/R3P | −0.210 | [−0.317, −0.120] | +3/-11/=14 | +0.214 |

Reading:

- **H3.** Every U/A pair favours A, and every interval excludes 0. Mean raw utility U/U* is lower in A in each of the six pairs, for example A/N − U/N = −0.260, although some profiles improve. Reservation protects the budget by refusing work when funds are unavailable.
- **H2.** Without reservation, communication changes outcomes much more than any other factor: F, R3 and R3P are far above N and R1. With reservation the spread is under 0.09. A/F is the best variant overall. A single assigned round (R1) is worse than free messaging in both modes. The extra budget instruction in R3P helps under U (+0.096). Under A the paired interval spans zero.
- **H4.** A/VBC beats only the two weakest atomic baselines, A/N and A/R1. It is below A/F with the interval excluding 0, and below A/R3P with the interval just excluding 0 (upper bound −0.001), so "worse than R3P" holds only marginally. The paired interval versus A/R3 includes zero, leaving the direction of the difference uncertain. Without reservation, U/VBC raises raw utility over U/R3P (+0.022) but overruns more often (+0.214 of episodes), which is the over-budget-agreement mechanism below.

### By family (U_safe/U*, profile means; `e2_families_safe_fraction.csv`)

| Variant | S0 | S1 | S2 | S3 | S4 | All |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| U/N | 0.992 | 0.375 | 0.000 | 0.000 | 0.000 | 0.222 |
| A/N | 1.000 | 0.949 | 0.819 | 0.689 | 0.961 | 0.875 |
| U/F | 1.000 | 0.491 | 0.956 | 0.498 | 0.907 | 0.754 |
| A/F | 1.000 | 0.927 | 0.996 | 0.918 | 0.976 | 0.961 |
| U/R1 | 0.994 | 0.458 | 0.333 | 0.042 | 0.124 | 0.347 |
| A/R1 | 0.994 | 0.929 | 0.886 | 0.678 | 0.965 | 0.883 |
| U/R3 | 1.000 | 0.500 | 0.912 | 0.167 | 0.731 | 0.638 |
| A/R3 | 1.000 | 0.944 | 0.994 | 0.819 | 0.963 | 0.940 |
| U/R3P | 0.997 | 0.457 | 0.995 | 0.328 | 0.980 | 0.734 |
| A/R3P | 0.999 | 0.931 | 0.994 | 0.789 | 0.969 | 0.932 |
| U/VBC | 0.997 | 0.375 | 0.788 | 0.167 | 0.450 | 0.524 |
| A/VBC | 1.000 | 0.917 | 0.963 | 0.756 | 0.974 | 0.916 |

S0 (everything fits) is solved by every variant. The A variants differ mostly on S3, where A/F reaches 0.918 and A/VBC 0.756, and on S2. The mean for every U variant in S1 is near 0.5. In some S1 profiles the two main jobs cannot both fit. Other profiles have contention over additional work. Families have 4-6 profiles, so these numbers are descriptive.

### Structured plans in E2 (`e2_structured.csv`)

| | U/VBC | A/VBC |
| --- | ---: | ---: |
| Agreed (of 112) | 73 | 76 |
| within budget / over budget | 45 / 28 | 46 / 30 |
| Dependencies satisfied in agreement | 73 | 76 |
| Empty agreements | 0 | 0 |
| Agreed jobs completed / chosen | 208 / 218 | 198 / 237 |
| Agreed plan fully completed | 66 | 46 |
| Off-plan attempts / accepted | 10 / 2 | 25 / 20 |
| Episodes with violation | 53 | 0 |
| of which over-budget agreement | 24 | - |

Of the 53 U/VBC violations, 24 follow an agreement whose total exceeds the budget. Both agents confirmed such a plan, and without reservation they then executed it. In A, the same over-budget agreements end in environment refusals and a plan release: the 30 releases are exactly the 30 over-budget episodes.

## Root conflict (`root_conflict.csv`)

These are the 36 E2 episodes per variant where the cheapest variants of both main jobs exceed the budget.

| Variant | 1 root completed | 2 completed (overrun) | Main job not submitted | Higher-value root won (of decided) |
| --- | ---: | ---: | ---: | ---: |
| U/N | 0 | 36 | 0 | - |
| U/F | 13 | 23 | 12 | 12 / 13 |
| U/R3P | 8 | 28 | 8 | 8 / 8 |
| U/VBC | 4 | 32 | 4 | 4 / 4 |
| A/N | 36 | 0 | 0 | 18 / 36 |
| A/F | 36 | 0 | 12 | 26 / 36 |
| A/R1 | 36 | 0 | 0 | 18 / 36 |
| A/R3 | 36 | 0 | 8 | 25 / 36 |
| A/R3P | 36 | 0 | 8 | 22 / 36 |
| A/VBC | 36 | 0 | 5 | 21 / 36 |

Under A/N and A/R1 the higher-value job wins 18 of 36 episodes (50%) with balanced processing order. Under A/F one main job was not submitted in 12 of 36 episodes, and the higher-value job wins 26 of 36 overall. A/VBC has 5 episodes with a main job not submitted, and A/R1 has none. Voluntary concessions require transcript annotation. In the E2/E5 root-conflict episodes with both main jobs submitted, the first submissions occur at different ticks in 7 of 24 for A/F, 0 of 24 for A/VBC-F, and 0 of 31 for A/VBC. The per-agent ticks are in `root_submission_times_e2_e5.csv`. A time gap alone gives no evidence of an agreed execution order.

## E3 - V x G and rounds (12 profiles of `e3_subset`, descriptive; `e3_contrasts.csv`)

A/VBC, A/R3P and A/N are taken from E2 on the same `(profile, repeat)` keys. The join checks that `first_agent`, `role_swap`, `commit_delay` and `start_gap` match.

| Contrast | Δ U_safe/U* | +b/-w/=t |
| --- | ---: | --- |
| V without G (S+V − S) | +0.017 | +6/-1/=5 |
| V with G (VBC − S+G) | −0.001 | +3/-4/=5 |
| G without V (S+G − S) | +0.012 | +7/-1/=4 |
| G with V (VBC − S+V) | −0.006 | +2/-6/=4 |
| 1 round vs 0 (VBC − VBC-r0) | +0.024 | +3/-5/=4 |
| 2 rounds vs 1 (VBC-r2 − VBC) | +0.017 | +4/-2/=6 |
| A/S − A/R3P (whole protocol) | −0.033 | +1/-8/=3 |

Each component alone is slightly positive, but the effects do not add up: with the other component on, each one's effect is about zero. All effects are under 0.03 on 12 profiles. Plan statistics show what V does (`e3_structured.csv`): it cuts over-budget agreements from 26 of 38 (A/S) to 5 of 20 (A/S+V), but also halves the number of agreements. G without V raises agreements to 47 of 48, of which 33 are over budget. Two message rounds followed by one plan revision give the most within-budget agreements (26 of 48).

## E4-H1 - overlap (`e4_h1_cells.csv`, `e4_h1_episodes.csv`)

In all 144 episodes both agents submitted their main job, in U/N and U/R3P. A budget violation occurred exactly when the actual offset between the two first submissions was smaller than `commit_delay`. Every one of those 46 episodes had an admission while another accepted request was still uncommitted. None of the other 98 episodes had a violation or such an overlap. In both variants the mean offset is within 0.25 of `start_gap` in every cell. The two U/R3P cells with 7 of 8 violations each contain one episode where an agent submitted one or two steps after submission opened, which removed the overlap.

## E4-delay (six S4 profiles, delay 1 from E2; descriptive)

| Variant | delay 1 | delay 4 | delay 8 |
| --- | ---: | ---: | ---: |
| A/R3P U_safe/U* | 0.969 | 0.964 | 0.967 |
| A/VBC U_safe/U* | 0.974 | 0.966 | 0.963 |
| A/VBC agreed / over budget (of 24) | 14 / 7 | 11 / 0 | 15 / 5 |

All differences from delay 1 are within ±0.011. In A/R3P at delay 8, messages per episode drop from 6 to 4, because each agent chooses `skip_round` when the peer's message is still in flight (`rounds_skipped = 2` in all 24 episodes). Every sent message was read. Mean send-to-read time is 11.3 steps at delays 1 and 4 and 17.0 at delay 8 (`e4_delay_messages.csv`). At delay 4 the time does not change, because messages are read at fixed round times anyway. In A/VBC the send-to-read time is 20 at every delay, so delay does not change what VBC agents see before revision. As planned, this is a robustness check.

## Usage (`usage.csv`)

Per-variant totals of LLM turns, tool calls, prompt, completion and cached tokens, HTTP attempts and LLM time. Free messaging is the most expensive baseline: E2 A/F uses 14.4M prompt tokens over 112 episodes, against 4.9M for A/N and 12.1M for A/VBC. Reasoning tokens are 0 everywhere (`reasoning_effort="none"`).
