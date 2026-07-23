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
  CLI args, not commented lines). Finalized against Modal's current docs: the
  `add_local_python_source` packaging guard, Hugging Face + vLLM weight-cache
  Volumes (so targets are not re-downloaded each run), and the `modal run -m`
  module form (required for the package's relative imports). The Function returns
  only primitives (never inspect `EvalLog` objects), so remote results are never
  deserialized against a mismatched local inspect version. inspect is left
  unpinned in the image on purpose: the version matching the local `.venv`
  (0.3.211) could not start `vllm serve` for the target, whereas the unpinned/
  newer inspect serves targets correctly. Image also installs `procps` (for
  `pkill`) so inspect can tear down the vLLM subprocess cleanly.
- Fixed Olmo 3 target serving on Modal (diagnosed empirically via a `diagnose_vllm`
  function that runs `vllm serve` variants and prints the real stderr). Two issues,
  both resolved:
  1. vLLM's **native** Olmo2 loader crashes on Olmo 3 with `KeyError: 'rope_theta'`
     (transformers 5.x restructured RoPE config per-layer-type). Fix: serve Olmo 3
     via vLLM's **Transformers backend** — `model_impl=transformers` is now in
     `olmo_target_model_args` and applied to every target (Berg and PETRI).
  2. vLLM's flashinfer JIT-compiles CUDA kernels at startup and needs `nvcc`, which
     `debian_slim` lacks (`Could not find nvcc ... cuda_home='/usr/local/cuda'`).
     Fix: build the image on `nvidia/cuda:12.9.0-devel` (has the toolkit) with
     `vllm==0.21.0` (torch cu12x matches the toolkit), mirroring Modal's vLLM example.
  `diagnose_vllm` confirmed `transformers_backend` and `transformers_backend_with_tools`
  both start OK, while native still fails. SFT then produced a real PETRI transcript
  (target generated 745 tokens; a genuine 1.0/10, not vacuous). NB: sharing vLLM /
  flashinfer compile caches across stages made DPO/Instruct fail at `vllm serve`
  (the Olmo 3 stages have identical configs, so they collide on one compile-cache
  key), so those caches are intentionally not shared — each stage recompiles.
- Multi-stage isolation: set `single_use_containers=True` on `run_stage` so each
  stage runs in a fresh container. The DPO/Instruct failures had the hallmarks of
  GPU state carried over from the SFT stage (identical model configs, and a
  ~1-minute `vllm serve` failure far too fast for a real cold start) — a warm
  container reused across stages can leave the previous stage's vLLM server holding
  the GPU. A single-use container guarantees a clean GPU per stage.
- Added `diagnose_vllm` to `modal_app.py`: runs the exact `vllm serve` command
  with `VLLM_LOGGING_LEVEL=DEBUG` (base vs. `olmo3` tool-parser variants) to
  surface the real vLLM failure reason.
- Note: earlier "mean 1.0/10" runs on the unpinned image were vacuous — the
  target never served, the auditor exhausted its turns, and the judge floored the
  score. The May-25 log, by contrast, has a full target/tool transcript, so the
  README's PETRI result is real.
- Add a "Running the evals (refactored pipeline)" section to the README with the
  `modal run` commands and dashboard-regeneration steps.
- Add `tests/test_starters.py` and `tests/test_methods.py`.

The ~12 prototyping eval scripts are superseded by this package and can be retired
once a live Modal re-run confirms parity.

Still behavior-preserving: no eval is re-run and the README charts are untouched.

### Task #15 — Retire superseded prototype scripts; wire the dashboard to `refactor_runs/`

- Deleted the seven superseded one-off eval-generation scripts from
  `prototyping_scripts/` (`BergPaperStyleMay25AcrossTrainingStack.py`,
  `BergPaperStyleSelfMonitoringMay25.py`,
  `ModalExperimentsBergPaperStyleSelfMonitoring.py`,
  `OverlyComplicatedBergPaperStyleSelfMonitoringMay25.py`,
  `PETRIevalsApril22.py`, `PETRIevalsMay25.py`,
  `PETRIevalsMay25AcrossTrainingStack.py`). Their logic now lives in the package
  (`methods.py`, `run.py`, `modal_app.py`, `starters.py`, `scoring.py`); the files
  are preserved in git history. The genuinely-exploratory notebooks (`.ipynb`) and
  their logs are kept.
- Parameterised the three `production_scripts/plot_*.py` dashboard scripts so they
  can consume the new `refactor_runs/` logs: each reader now takes an optional
  `log_dir` (the dashboard takes `berg`/`petri` dirs), and each `main()` grew
  `--log-dir` (`--berg-log-dir`/`--petri-log-dir`), `--output`, and `--subtitle`
  flags. `evals_df` reads recursively, so the per-stage `refactor_runs/<method>/
  <stack>/<stage>/` layout is picked up without flattening.
- The defaults are unchanged — the historical May-25 log paths — so a no-argument
  run still regenerates the published charts and
  `tests/test_readme_regression.py` (which calls the readers with no arguments)
  stays green. `--output` lets a `refactor_runs` regeneration write new PNGs
  without clobbering the committed historical charts.
- Updated the README "Running the evals" section with the pull-and-regenerate
  commands and repointed the retired-script provenance notes at the kept notebook /
  git history.

Still behavior-preserving: no eval is re-run and the committed README charts are
untouched. A live Berg re-run (`refactor_runs/berg/...`) is still needed before the
new 20-prompt baseline can replace the historical 1/18 figures.
