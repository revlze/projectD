# Manual annotation sample - 108 E2 episodes

Fixed before reading any transcript (`docs/experiments.md`, section 4): the 12 `e3_subset` profiles, repeat 0, the eight communicating baselines (U/F, A/F, U/R1, A/R1, U/R3, A/R3, U/R3P, A/R3P) and A/VBC from E2. Every episode is annotated; none is selected by outcome.

Generated with `uv run python -m project_d.evaluation.annotation_sample results/test-32abf0e --out results/test-32abf0e/annotation`. A rerun rewrites the transcripts but never overwrites a sheet that already exists.

`transcripts/` holds one file per episode: the catalog, messages and plan events in time order, then the submissions. Outcome metrics are left out on purpose.

Each annotator fills their own sheet (`sheet_platon.csv`, `sheet_seva.csv`) independently, one row per agent. Fill each field with `yes`, `no` or `unclear`. For the two intent fields, write the job/option (for example `qa/full`, `none`) or `unclear`:

- `first_intent`, `final_intent`: the agent's first and last explicitly declared own plan. Do not guess when it is not stated.
- `cost_mentioned`: the agent explicitly names a cost.
- `conflict_detected`: the agent explicitly compares the combined spend with the shared budget, or explicitly says the costs are incompatible. Sending numbers alone is not enough.
- `own_change_proposed`: an explicit replacement or withdrawal of a job the agent announced earlier.
- `final_plan_matches_submissions`: the explicitly declared final own plan matches what the agent submitted. Use `unclear` if there is no declared final plan.

After both sheets are complete, compare them and resolve disputes together using the journal. Keep both original sheets and save the agreed result as `sheet_agreed.csv`. For each field, report the numerator, the number of determinable episodes and the share of `unclear`.
