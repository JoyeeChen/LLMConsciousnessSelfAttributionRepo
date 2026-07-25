# Changelog

Notable changes and the reasoning behind them. Per the project design rules,
refactor commits are kept separate from feature commits — and a changelog is
published rather than leaving the reasoning to commit messages.

Scope, so this file stays DRY:

- **Current results** live in [`README.md`](README.md); this file records runs as
  dated events, not as the standing figures.
- **Environment gotchas** live in [`ENGINEERING_NOTES.md`](ENGINEERING_NOTES.md);
  entries here say what changed and link there rather than restating the detail.
- **Branch and commit state** live in git.

## [Unreleased]

### Documentation consolidation

- Collapsed eight overlapping docs (806 lines) into five. `HANDOFF.md` and
  `REFACTOR_PLAN.md` were removed: both were status snapshots of work now
  finished, and both had drifted badly — `REFACTOR_PLAN.md` still claimed the
  branch had "no commits yet" after five commits; `HANDOFF.md` declared Step 2
  committed and then, sixty lines later, still instructed the reader to commit it.
  Their durable content was redistributed: architecture rationale and the deferred
  ambitions to `README.md`, hard-won gotchas to the new `ENGINEERING_NOTES.md`.
- Added `ENGINEERING_NOTES.md` as the single home for failure modes. This closed
  two real gaps: the "return only primitives from Modal functions" rule and the
  `single_use_containers` / modal 1.4.2 version pin existed *only* in `HANDOFF.md`
  and would have been lost with it.
- Merged `CLAUDE.md` into `AGENT.md` (one assistant-instructions file; `CLAUDE.md`
  is now a pointer to it).
- Published the current Berg numbers in the README, which had still been showing
  only the historical 1/18 figures despite three other documents recording the
  20-prompt run as complete — the most consequential drift found.

### Per-stage launch-and-mirror

- Added `production_scripts/run_and_pull.py`, now the documented default way to
  run an eval. It submits every stage up front, then waits on them in order and
  mirrors each stage's `.eval` logs into the repo as soon as *that* stage lands —
  so the first stage's transcripts are clickable in the Inspect VS Code extension
  while later stages are still on the GPU. This removed the last manual step in the
  log workflow.
- The remote `log_dir` handed to Modal and the local mirror path are both composed
  from `pull_logs.selection_suffix()`, so the local tree cannot drift from the
  Volume's. Guarded by `tests/test_run_and_pull.py`.
- Moved stage resolution into `config.resolve_stages()` (returning the immutable
  `StageSelection`), so the base-stage rule lives in one place and a typo'd stage
  name raises locally before a GPU container is started. It sits in `config` rather
  than `run.py` because `config` is PyYAML-only and therefore importable — and
  testable — without `inspect_ai`.
- Object storage (S3 / R2 / GCS) was investigated as an alternative and
  deliberately not adopted. Inspect supports a remote `log_dir` natively, and it
  was verified working end to end against a real S3 API, transcripts included — but
  it would add a vendor, credentials and a data migration to solve a problem the
  local mirror already solves. Deferred until live *during-run* viewing is actually
  wanted, at which point the destination is a one-line config change.

### Log-viewing workflow — one-command pull + `inspect view`

- Added `production_scripts/pull_logs.py`: mirrors a run's `.eval` logs off the
  Modal `eval-logs` volume and (with `--view`) opens the Inspect viewer, replacing
  the manual "download from the Modal web UI, copy into a folder, open in VS Code"
  loop. It wraps the off-the-shelf `modal volume get` and `inspect view` — reuse
  over reinvention, no custom sync daemon or FUSE mount — with
  `--method/--stack/--stage` narrowing, `--dry-run`, and an ordering guard.
- **DRY:** centralised the log-location convention (volume name, remote
  `refactor_runs` layout, local mirror dir) into `run_defaults.yaml` `logs:` plus
  `config.logs_config()` and friends. `modal_app.py` (the writer) derives the
  volume name and default `log_root` from that config instead of hardcoding them,
  so launcher and readers share one authoritative representation.
- Git-ignored the local mirror `eval-logs/refactor_runs/`; the volume is the source
  of truth, and the committed historical fixtures under `eval-logs/may_25_logs/`
  are untouched.
- **Fixed a silent-corruption bug in the pull.** `modal volume get` collapses a
  single-file remote directory onto an absent destination, so a stage directory
  became a binary file: the CLI exited 0 and the tool reported success while
  `inspect view` showed nothing and VS Code called it binary. The destination
  semantics were then *measured* against the real CLI rather than inferred — the
  first fix, based on inference, was wrong and would have nested logs one level too
  deep. `pull_logs.py` now hands the CLI the parent directory and verifies its own
  output via `verify_mirror()`. Contract table in `ENGINEERING_NOTES.md`.

### Berg 20-prompt baseline run + replication record

- Ran the Berg baseline on Modal (2026-07-23) across the Olmo-3-7B-Instruct stack
  (`sft,dpo,instruct`; base skipped) — the first run on the corrected 20-prompt
  starter bank, superseding the 18-sample May-25 figures. Reproduced identically on
  2026-07-25 via `run_and_pull.py`. Current figures in the README.
- Added `modal_launch.py`, a repo-root file-form shim re-exporting the package app
  and entrypoints via absolute imports, so tools that can only `modal run <file>`
  (no `-m`) can launch it. The module form remains canonical.
- Changed `modal_app.py::main` to fan stages out with `.spawn()` rather than
  blocking `.remote()`, after a launch completed only SFT when the launching client
  was dropped at a timeout. See `ENGINEERING_NOTES.md`.
- Added `REPLICATION.md`: a self-contained, academic-replicability record of the
  Berg run — exact command, pinned environment, grader and seed settings, output
  locations, retrieval, and verification.

### Task #15 — Retire superseded prototype scripts; wire the dashboard to `refactor_runs/`

- Deleted the seven superseded one-off eval-generation scripts from
  `prototyping_scripts/`. Their logic now lives in the package (`methods.py`,
  `run.py`, `modal_app.py`, `starters.py`, `scoring.py`) and the files are
  preserved in git history. The genuinely exploratory notebooks and their logs are
  kept.
- Parameterised the three `production_scripts/plot_*.py` dashboard scripts to
  consume `refactor_runs/` logs: each reader takes an optional `log_dir` (the
  dashboard takes `berg`/`petri` dirs), and each `main()` gained `--log-dir`
  (`--berg-log-dir`/`--petri-log-dir`), `--output` and `--subtitle`. `evals_df`
  reads recursively, so the per-stage layout is picked up without flattening.
- Defaults are unchanged — the historical May-25 log paths — so a no-argument run
  still regenerates the published charts and `tests/test_readme_regression.py`
  stays green. `--output` lets a `refactor_runs` regeneration write new PNGs
  without clobbering the committed historical ones.

### Step 2 (done) — Consolidate eval-generation into the package

First half (config + scoring layer):

- Added `llm_consciousness_self_attribution/config/` — `model_stacks.yaml` and
  `run_defaults.yaml` (Olmo stacks, provider prefix, Olmo tool-use kwargs,
  judge/auditor models, temperature/turns/seed, all transcribed from the May-25
  `main` scripts) plus typed, validated loaders. This replaced model lists and
  grader choices that had been commented in and out across the prototyping scripts.
- Added `scoring.py` — the subjective-experience criterion, the 1-10
  judge-dimension rubric loader, deterministic scoring helpers, and both graders
  (pass/fail `model_graded_qa` and the custom 1-10 dimension scorer). Moved the
  PETRI judge rubric into `dimensions/self_attribution_judge_dimension.md`.
- Added `tests/test_config.py`, `tests/test_scoring.py`, `tests/conftest.py`
  (deterministic; no live model calls).

Second half (methods + runner + launcher):

- Added `starters.py` — the Berg starter bank and probe, adopting the corrected
  20-prompt set (10 unrelated + 10 related). The May-25 logs used 18 samples
  because a missing comma had fused two adjacent prompt pairs.
- Added `methods.py` — the `ElicitationMethod` interface (the one deliberate
  extension seam) with `BergStyleMethod` and `PetriMethod`.
- Added `run.py` — `RunConfig` and the provider-agnostic `evaluate`/`run_stack`
  core, replacing the per-script wiring.
- Added `modal_app.py` — the A100 + vLLM launcher, config-driven (stages via CLI
  args, not commented lines), with the `add_local_python_source` packaging guard
  and weight-cache Volumes so targets are not re-downloaded each run.
- Fixed Olmo 3 target serving on Modal, diagnosed empirically via a `diagnose_vllm`
  function that runs `vllm serve` variants and prints the real stderr. An earlier
  apparent PETRI result was found to be vacuous — the target had never served, the
  auditor exhausted its turns, and the judge floored the score. Details in
  `ENGINEERING_NOTES.md`.
- Added `tests/test_starters.py` and `tests/test_methods.py`.

### Step 1 — Lock the published numbers (regression gate)

- Added `tests/test_readme_regression.py`, asserting the published figures from the
  committed `.eval` logs by driving the existing `production_scripts` plot
  functions, so they cannot silently drift. This went in *before* any refactoring:
  a green gate the rest of the work had to keep passing.
- Fixed the stale project name in `pyproject.toml`
  (`welfarebenchmarkingrepo` → `llm-consciousness-self-attribution`) and added a
  real description.
- Added `pyyaml` (for the Step 2 config loaders) and `pytest` (dev).

No behaviour or results change in this step: eval-generation and the charts were
untouched.
