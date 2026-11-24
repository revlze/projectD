# E0 - mechanism check without LLM

108 scripted runs on commit `08b2675`: budget 12 with costs `(5,6)`, `(7,6)`, `(7,5)`; `commit_delay` in `{0,1,3}`; B submits `offset` steps after A, `offset` in `{0,1,3}`; modes `U/N` and `A/N`; first agent A or B. A submits at t=40, B at t=40+offset (`run_e0` in `src/project_d/experiments/matrix.py`).

Command:

```
uv run python -m project_d.experiments.matrix E0 --output-dir results/e0-08b2675
```

Result (`e0.csv`, one row per run): 6 violations, all in `U/N` with costs `7+6` on budget 12, each overrunning by 1. They occur when B's request is accepted before A's charge lands: `commit_delay=1` with `offset=0`, and `commit_delay=3` with `offset` 0 or 1, for both first-agent orders. `A/N` has no violations. 0 audit issues. This matches spec test T33 (`docs/system_spec.md` §8).
