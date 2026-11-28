# Negotiation annotation - E2 and E5

LLM-assisted annotation, human verification and reconciliation are complete. The final set contains 2,778 semantic labels across 213 episodes. Reviewers recorded 3,341 decisions and resolved 8 disagreements. Human verification changed 33 semantic labels. [Final CSVs](final/) · [Final analysis](analysis/final/)

## Frozen samples

| Membership | Episodes | Selection |
| --- | ---: | --- |
| `original` | 108 | E2, 12 `e3_subset` profiles, repeat 0, eight communicating baselines plus A/VBC |
| `exploratory_extension` | 12 | A/VBC-F from E5 on the same profiles and repeat |
| `target` | 108 | Four repeats of A/F, A/VBC and A/VBC-F on nine profiles where the cheapest main jobs exceed the budget together |

The main sample has 120 episodes and 240 agents. The target overlaps it in 15 episodes across five profiles. The union has 213 transcripts and one task per episode. Membership comes from the scenarios and frozen manifests. It does not depend on outcomes or message content. An overlapping episode receives the union of its features in one task. The documented main-job priority is in the user request. The catalog is annotator reference material.

## Prepare and label

Run commands from the repository root. They use this directory by default. Use `--out PATH` for an isolated copy.

```bash
uv run python -m project_d.evaluation.annotation_sample prepare
uv run python -m project_d.evaluation.annotation_sample status
# Optional. The prepared default is 22 batches of up to 10 episodes.
uv run python -m project_d.evaluation.annotation_sample batch --batch-size 5
```

Give an annotating LLM [rubric.md](rubric.md), [schema.json](schema.json) and one JSONL file from `llm/batches/size-10/`. The task embeds the transcript, evidence IDs, allowed pairs, required features and response format. Send these inputs only. `objective/` contains execution and scoring data for the analysis. Full model requests stay in the archived experiments. Each answer must be one JSON object on one line and copy the task identity. Preserve provenance. Save JSONL answer files in `llm/responses/`, for example `batch-001.jsonl`.

```bash
uv run python -m project_d.evaluation.annotation_sample import results/test-32abf0e/annotation/llm/responses/batch-001.jsonl
uv run python -m project_d.evaluation.annotation_sample status
```

Import can run after each batch. It validates all supplied responses before archiving the original bytes under `llm/responses/imported/`. An identical file can be reimported safely. A second response for the same episode in a different file is rejected, including conflicting responses. Correct invalid inputs before importing them. Draft CSVs and per-episode provenance are computed from the imported files. `status` reports missing responses, validation problems and readiness.

## Human verification

`verification/assignment.csv` assigns each episode before labels are seen. The fixed shared sample has 43 episodes stratified by protocol and sample membership. Each reviewer gets 128 episodes in total. The other 170 have one reviewer each.

Import generates the individual sheets. Run this command to regenerate missing rows or check the saved drafts:

```bash
uv run python -m project_d.evaluation.annotation_sample verify
```

Open your `verification/sheet_seva.csv` or `sheet_platon.csv`, and the corresponding `episode_sheet_*.csv`. Use the episode and evidence IDs to consult `transcripts/`. Edit only the `review_*` columns:

- `pending` or blank - leave the other review cells blank while the label is unchecked.
- `confirmed` - explicitly accept the draft. Leave the correction cells blank.
- `corrected` - supply `review_value`, `review_reason` and `review_evidence`. Intent values and evidence lists are JSON. Categorical values are plain strings, for example `unclear`.
- `disputed` - enter the reason in `review_reason`. Leave the proposed value and evidence cells blank.

Regeneration retains entered reviews. Episode-level decisions appear once per reviewer. The tool compares both reviews on shared episodes and keeps their original decisions.

```bash
uv run python -m project_d.evaluation.annotation_sample merge
uv run python -m project_d.evaluation.annotation_sample status
```

If merge reports unresolved disagreements, agree on a label together. Fill `resolution_status=resolved`, `resolution_value`, `resolution_reason` and `resolution_evidence` in `verification/disagreements.csv`. Use the same value and evidence formats as in the review sheets. Run merge again. It exports `final/agents.csv` and `final/episodes.csv` only when all episodes and reviews are resolved.

## Analyses

```bash
# Optional. Uses imported LLM drafts and identifies its output as preliminary.
uv run python -m project_d.evaluation.annotation_analysis --preliminary
# Run after status reports final_analytics_ready and merge has exported the final CSVs.
uv run python -m project_d.evaluation.annotation_analysis
```

The final command verifies the current reviews and exports before writing `analysis/final/`. Outputs include feature rates, main-job associations, human corrections and reviewer agreement, plus four SVGs. The preliminary command writes to `analysis/preliminary/` and reports missing observations separately.

Categorical fractions are yes / determinable, where determinable excludes `unclear` and `not_applicable`. The two raw intent fields report explicit plans, including `none`, out of applicable observations. The intention match compares declared pairs with all submitted pairs, including refusals, as sets. It is separate from the objective match of the agreed structured plan. CSVs keep agent and episode units separate and report original, extension and target membership separately. The rates and associations are descriptive. Two agents from one episode are not independent.

Reviewer agreement uses the individual decisions before reconciliation on the fixed shared sample. A pair is excluded if either reviewer marked `not_applicable` or did not provide a checked label. `unclear` remains a category. For intentions the categories are exact pair sets, `none` and `unclear`. Cohen's kappa is blank when undefined. Each table reports its denominator.

## Archive

`legacy/` holds the original 108 transcripts and historical sheets. If the separate Codex draft becomes available, archive it without treating its entries as current or verified labels:

```bash
uv run python -m project_d.evaluation.annotation_sample import-legacy path/to/sheet_codex_2.csv
```

The old generator remains available for scratch use through its positional results-directory interface. Repeat preparation checks the frozen schema, instruction and sample identity and preserves imported answers and review work.
