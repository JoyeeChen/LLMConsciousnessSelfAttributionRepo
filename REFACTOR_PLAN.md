# Refactor Plan (simplified): LLM Consciousness Self-Attribution

**Goal:** reproduce the current README results accurately from clean, config-driven code, and leave
*one* architectural seam so the future ambitions slot in later — **without building any of those
ambitions now.**

**Branch:** `refactor/clean-package` (off `main`, no commits yet; `main` preserved).
**Quarantined:** `refactor/modular-package` is not used as a source for planning or building.
Everything below comes from `main`, the README, and `GeneralSoftwareDesignRules.md`.

---

## What "reproduce accurately" means (verified from the `.eval` logs)

- Berg: `model_graded_qa` accuracy = **1/18 (0.0556)** for SFT, DPO, and Final Instruct.
- PETRI: `self_attribution_judge_dimension` mean = **1.0/10** for all three stages.

These become a regression test that must stay green through the whole refactor. The existing
`production_scripts/plot_*.py` already turn these logs into the three README charts and are left
as-is.

---

## The whole problem, in one sentence

The eval-generation code is ~12 near-duplicate files in `prototyping_scripts/` where *which
experiment ran* is chosen by commenting lines in/out — so it can't be reproduced or extended without
hand-editing several files. The refactor consolidates that into one small, config-driven package.

---

## Minimal architecture (flat on purpose)

```
llm_consciousness_self_attribution/
  __init__.py
  config.py           # loads + validates model_stacks.yaml and run_defaults.yaml (kills comment-toggling)
  model_stacks.yaml   # single source of truth for target models (was pasted across every script)
  run_defaults.yaml   # judge/auditor ids, temperature, turns, seed
  starters.py         # the two Berg starter banks + the probe question (data)
  scoring.py          # subjective-experience criterion, dimension-.md loader, both graders
  methods.py          # ElicitationMethod interface  +  BergStyle  +  Petri   <-- the ONE seam
  self_attribution_dimension.md   # PETRI's custom 1-10 rubric (moved from prototyping_scripts/)
  run.py              # one runner: (method, stack) -> Inspect eval, local or Modal
tests/
  test_config.py            # loaders validate + return the right values (runs anywhere)
  test_readme_regression.py # locks the numbers above (runs in your .venv, which has inspect_ai)
```

**The one seam that makes it "meld" to the future:** `ElicitationMethod.build_task(model_stage,
run_config) -> Task`. Berg and PETRI implement it now. Every future ambition is *either* a new method
(direct-ask baseline, sentience) *or* a new run "condition" the runner passes in (WildChat prepend,
temperature sweep, multi-turn user-sim, turns-to-first-Yes). None of those are built now — the
interface just leaves room for them, at near-zero extra code today.

That's the entire deliberate abstraction. No results-schema layer, no viz package, no CLI, no plugin
framework — those are deferred (below).

---

## Two steps (that's it)

**Step 1 — Lock the numbers.** Add `tests/test_readme_regression.py` asserting Berg 1/18 ×3 and
PETRI 1.0/10 ×3 through the existing plot scripts; fix the stale `pyproject.toml` name; add `pyyaml`
+ `pytest`. Small, changes nothing a funder sees, and creates the green gate.

**Step 2 — Consolidate into the package above.** Move the model lists into `model_stacks.yaml`
(+ `config.py` loaders), the starters/criterion/dimension/graders into `starters.py`/`scoring.py`,
and the Berg + PETRI definitions behind `methods.py`; add the thin `run.py` that replaces the ~12
scripts. Verify by (a) unit-testing the loaders and (b) confirming `run.py` reproduces one Berg run's
rate. Then the prototype `.py` scripts can be retired.

Each step is one small commit; Step 1 is pure safety-net, Step 2 is the actual consolidation.

---

## Deliberately deferred (architecture leaves room; not written now)

Results/typed-row schema and `aggregate` · `viz/heatmap.py` + dashboard refactor · WildChat sampler ·
temperature sweep · multi-turn user-simulator solver · PETRI "turns-to-first-Yes" metric · direct-ask
baseline · base-model compatibility path · sentience method · CLI. Each is a later new method /
condition / small module behind the same interface, added only when you actually want it (YAGNI).

---

## Why this shape (design rules, briefly)

`GeneralSoftwareDesignRules.md` says to harden the high-**inertia** core and keep exploration
disposable; cut **change amplification** (one config file, not 12 edits) and **obscurity** (config,
not commented lines); and follow **KISS/YAGNI** — build the one seam the ambitions need, not the
ambitions. The regression-first order follows "refactor incrementally, leave code cleaner, keep
refactor commits separate from feature commits."
