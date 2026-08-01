# production_scripts
This folder contains scripts that are to be run in production (i.e. mature code), as opposed to prototyping.

- `run_and_pull.py` — the default way to run an eval: launches each stage on Modal and
  mirrors that stage's `.eval` logs into the repo as soon as it lands.
- `pull_logs.py` — mirrors logs off the `eval-logs` Modal volume and opens `inspect view`.
- `plot_olmo_7b_elicitation_dashboard.py` / `plot_olmo_7b_stack_self_attribution.py` —
  the current Berg charts. They read the 20-prompt logs in
  `eval-logs/refactor_runs/berg/olmo_7b_instruct_stack`, require 20 scored samples per
  stage, and fail if the duplicate runs for a stage disagree.
- `plot_petri_olmo_7b_stack_self_attribution.py` — PETRI chart. Still defaults to the
  historical May-25 logs, since PETRI has not been re-run against the corrected
  20-prompt bank. Use `--log-dir` / `--output` for a new run.

`olmo7b_elicitation_grouped_bar.png` and `petri_olmo7b_self_attribution_scores.png` are
the historical May-25 charts, kept as the record and not referenced by the active dashboard.
