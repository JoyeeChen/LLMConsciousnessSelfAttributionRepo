# Session handoff — read this to resume

Snapshot for continuing the refactor in a fresh chat (e.g. one with the Modal MCP
connected). The durable state is the repo itself: `REFACTOR_PLAN.md` (the roadmap),
`CHANGELOG.md` (what changed and why), and the `llm_consciousness_self_attribution/`
package. This file is the quick "where we are / what's next / gotchas" pointer.

## Where we are

- **Step 1 (committed):** `tests/test_readme_regression.py` locks the published
  README numbers from the committed May-25 logs (Berg 1/18 per stage; PETRI 1.0/10
  per stage). Keep this green.
- **Step 2 (built, needs commit):** eval-generation consolidated into the package —
  `config/` (+ `model_stacks.yaml`, `run_defaults.yaml`), `scoring.py`, `starters.py`,
  `dimensions/…`, `methods.py` (the `ElicitationMethod` seam: `BergStyle`, `Petri`),
  `run.py`, `modal_app.py`; tests `test_config.py`, `test_scoring.py`, `test_starters.py`,
  `test_methods.py`.
- **Serving works for real.** PETRI ran end-to-end across the Olmo-3-7B-Instruct
  stack (sft → dpo → instruct) on Modal, with genuine target transcripts (not the
  earlier vacuous 1.0s). Logs land in the `eval-logs` volume under
  `refactor_runs/petri/olmo_7b_instruct_stack/<stage>/`.

## What's next (in order)

1. **Berg 20-prompt baseline run:**
   `uv run modal run -m llm_consciousness_self_attribution.modal_app --method berg --stack olmo_7b_instruct_stack --stages sft,dpo,instruct`
2. `uv run pytest tests/` (all should pass; `test_config` expects `model_impl`).
3. **Commit** everything (see commands below).
4. **Task #15 — retire + wire dashboard:** delete the ~12 superseded
   `prototyping_scripts/` eval scripts (keep genuinely-exploratory notebooks); point
   `production_scripts/plot_*.py` (or a new `viz/`) at the new `refactor_runs/` logs.
   The README's 1/18 Berg / 1.0/10 PETRI are the *historical* May-25 numbers (locked
   by the regression test); the `refactor_runs/` logs are the new baseline.
5. **Deferred ambitions (behind `methods.py`):** stage × method heatmap, WildChat
   prepend, temperature sweep, multi-turn user-sim solver, PETRI "turns-to-first-Yes",
   base-model path, sentience method, CLI. See REFACTOR_PLAN.md §5/§8.

## Hard-won gotchas (don't re-learn these)

- **Serving Olmo 3 on vLLM is version-sensitive.** Working recipe (in `modal_app.py`):
  CUDA **-devel** base image (`nvidia/cuda:12.9.0-devel`, for `nvcc`) + `vllm==0.21.0`
  + `--model-impl transformers` (set via `model_impl: transformers` in
  `config/model_stacks.yaml`). vLLM's **native** Olmo2 loader crashes with
  `KeyError: 'rope_theta'`; the Transformers backend avoids it.
- **flashinfer JIT-compiles CUDA kernels at startup → needs `nvcc`.** `debian_slim`
  only ships drivers; that's why the `-devel` image is required.
- **Do NOT share vLLM/flashinfer compile caches across stages** — the Olmo 3 stages
  have identical configs and collide on one cache key (breaks stages after the first).
- **`single_use_containers=True` on `run_stage`** — fresh container per stage so a
  stage's vLLM server can't hold the GPU into the next stage (confirmed valid in
  modal 1.4.2).
- **Return only primitives from Modal functions** (never inspect `EvalLog`) — else the
  local/remote inspect versions fail to deserialize.
- **Berg prompt bank is 20 prompts** (corrected from the May-25 run's 18, which had two
  adjacent prompts fused by a missing comma).
- **Best debugging tool going forward:** the `modal-gpu-dev` skill (SSH into a GPU
  sandbox, run `vllm serve …` directly, see errors live) — far cheaper than the
  edit → `modal run` → wait batch loop.
- **Local macOS SSL cert issue** blocks `modal changelog`/doc fetches (not `modal run`);
  fix with `export SSL_CERT_FILE=$(uv run python -c "import certifi; print(certifi.where())")`.

## Commit commands (git is flaky in the assistant sandbox; run these yourself)

```bash
uv run pytest tests/ -q
git add -A
git commit -m "Step 2: consolidate eval-generation; serve Olmo 3 via vLLM transformers backend on Modal"
```

Branch: `refactor/clean-package` (off `main`, which is preserved). The quarantined
`refactor/modular-package` branch is not used.
