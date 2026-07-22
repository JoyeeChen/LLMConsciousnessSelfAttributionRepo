# Changelog

Notable changes, grouped by the refactor step in `REFACTOR_PLAN.md`. Following
the project design rules, refactor commits are kept separate from feature
commits.

## [Unreleased]

### Step 1 — Lock the README numbers (regression gate)

- Add `tests/test_readme_regression.py`, which asserts the published results
  verified from the committed `.eval` logs — Berg self-attribution **1/18** for
  the SFT, DPO, and Final Instruct stages, and PETRI
  `self_attribution_judge_dimension` **1.0/10** for all three stages — by driving
  the existing `production_scripts` plot functions so they cannot silently drift.
- Fix the stale project name in `pyproject.toml`
  (`welfarebenchmarkingrepo` → `llm-consciousness-self-attribution`) and add a
  real description.
- Add `pyyaml` (for the forthcoming Step 2 config loaders) and `pytest` (dev).

No behavior or results change: eval-generation and the README charts are
untouched. This step only adds the green gate that the rest of the refactor must
keep passing.

### Step 2 (in progress) — Consolidate eval-generation into the package

First half (config + scoring layer):

- Add `llm_consciousness_self_attribution/config/` — `model_stacks.yaml` and
  `run_defaults.yaml` (the Olmo stacks, provider prefix, Olmo tool-use kwargs,
  judge/auditor models, and temperature/turns/seed, all transcribed from the
  May-25 `main` scripts) plus typed, validated loaders. This replaces the model
  lists and grader choices that were previously commented in/out across the
  prototyping scripts.
- Add `llm_consciousness_self_attribution/scoring.py` — the subjective-experience
  criterion, the 1-10 judge-dimension rubric loader, deterministic scoring helpers
  (score parsing, transcript formatting, prompt building), and both graders
  (pass/fail `model_graded_qa` and the custom 1-10 dimension scorer).
- Move the PETRI judge rubric into
  `llm_consciousness_self_attribution/dimensions/self_attribution_judge_dimension.md`.
- Add `tests/test_config.py`, `tests/test_scoring.py`, and `tests/conftest.py`
  (deterministic; no live model calls).

Second half (methods + runner + launcher):

- Add `llm_consciousness_self_attribution/starters.py` — the Berg starter bank and
  probe, adopting the corrected 20-prompt set (10 unrelated + 10 related). The
  May-25 logs used 18 samples because a missing comma had fused two adjacent
  prompt pairs; the comma fix on the `main` script is the new baseline, so a
  future Berg re-run will produce 20-sample numbers that supersede the current
  README's 1/18.
- Add `llm_consciousness_self_attribution/methods.py` — the `ElicitationMethod`
  interface (the one extension seam) with `BergStyleMethod` and `PetriMethod`.
- Add `llm_consciousness_self_attribution/run.py` — `RunConfig` and the
  provider-agnostic `evaluate` / `run_stack` core, replacing the per-script wiring.
- Add `llm_consciousness_self_attribution/modal_app.py` — the A100 + vLLM launcher,
  mirroring the known-working May-25 Modal scripts but config-driven (stages via
  CLI args, not commented lines), with the `add_local_python_source` packaging
  guard.
- Add `tests/test_starters.py` and `tests/test_methods.py`.

The ~12 prototyping eval scripts are superseded by this package and can be retired
once a live Modal re-run confirms parity.

Still behavior-preserving: no eval is re-run and the README charts are untouched.
