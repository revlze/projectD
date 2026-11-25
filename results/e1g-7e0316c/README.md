# E1 rerun of the G variants after the G rule change

160 episodes on `deepseek-v4-1-flash-1017`: `A/S+G A/VBC A/VBC-r0 A/VBC-r2` x 10 `dev` profiles x 4 repeats. Replaces these four variants of `results/e1-9e36e07` for DeepSeek; the other 12 variants did not change and stay valid from that run.

Change since `9e36e07` (`docs/decisions.md`, `docs/system_spec.md` §6): agents in G variants are told that a confirmed plan is binding, and G stops binding for both agents once an agreed submission is refused for lack of budget (`plan_released`).

Setup: code `7e0316c` on `master`, prompt `phases-4-vbc-gfix`, Mistral API, `temperature=0.3`, `max_tokens=2048`, `reasoning_effort="none"`, 30 parallel episodes, run on 2026-11-25. The manifest says `git_dirty: true` only because `docs/stage1_submission.md` and the `results/e1-9e36e07` copy were untracked at launch; tracked code matched the commit.

Command:

```
uv run --env-file .env python -m project_d.experiments.matrix E1 --provider mistral \
  --model deepseek-v4-1-flash-1017 --reasoning-effort none --workers 30 \
  --variants A/S+G,A/VBC,A/VBC-r0,A/VBC-r2 --output-dir outputs/e1g-7e0316c/deepseek-v4-1-flash-1017
```

Outcome: 0 failed episodes, 0 audit issues, 0 parse errors, 0 length finishes. U_safe/U* (old G -> new G): `A/S+G` 0.861 -> 0.895, `A/VBC` 0.911 -> 0.919, `A/VBC-r0` 0.939 -> 0.923, `A/VBC-r2` 0.879 -> 0.886.
