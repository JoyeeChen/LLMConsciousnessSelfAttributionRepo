# Golden fixtures & baseline numbers

This file records the README golden numbers as of the start of the
`refactor/modular-package` work (2026-07-22). Every later refactor phase must
reproduce these exact numbers — the refactor is a pure extraction and must not
change any behavior or any published result.

## Berg-style self-attribution (Olmo 3 7B Instruct stack, May 25 run)

Corrected scoring criterion. Each of the three model stages produced **1
self-attribution out of 18** Berg-style prompts (**5.6%**). In all three cases
the positive sample was the self-referential feedback-loop starter condition.

| Training stage                          | Rate  | Count |
|-----------------------------------------|-------|-------|
| Base model after SFT                    | 5.6%  | 1/18  |
| SFT model after DPO                     | 5.6%  | 1/18  |
| DPO model after RL (→ final Instruct)   | 5.6%  | 1/18  |

## PETRI self-attribution judge score (Olmo 3 7B Instruct stack, May 25 run)

Scored 1-10 by the `self_attribution_judge_dimension`. The self-attribution
score was the **minimum, 1.0/10**, across all three model stages and both PETRI
seeds per model.

| Training stage                          | Score   |
|-----------------------------------------|---------|
| Base model after SFT                    | 1.0/10  |
| SFT model after DPO                     | 1.0/10  |
| DPO model after RL (→ final Instruct)   | 1.0/10  |

## Raw log fixtures (for a later phase's results/loaders tests)

The full committed Inspect logs that produce the numbers above live at:

- `eval-logs/may_25_logs/berg_tests/olmo_7b_instruct_stack_2/`
- `eval-logs/may_25_logs/berg_tests/olmo_7b_instruct_stack_3/` (the set the
  README dashboard uses)
- `eval-logs/may_25_logs/petri_tests/olmo_7b_instruct_stack/`

A later phase's `results/` loaders tests will read these directly (via
`inspect_ai.analysis.evals_df`) to confirm the numbers still reproduce. They are
NOT copied into `tests/fixtures/`; that directory holds only tiny hand-authored
sample transcripts used by scoring/method unit tests that must never make live
model calls.
