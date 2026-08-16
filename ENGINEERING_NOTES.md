# Engineering notes — hard-won gotchas

Environment facts that cost real debugging time, kept in one place so they are not
re-learned. These are *why things break and how they were fixed*; the pinned
version numbers as they stood for a specific published run are recorded in
[`REPLICATION.md`](REPLICATION.md), which is the provenance document. If a pin
changes, `REPLICATION.md` records what was used for that run; this file records
what happens if you get it wrong.

Audience: whoever (human or agent) is next touching the Modal/vLLM path.

---

## Serving Olmo 3 on vLLM

**Use the Transformers backend, not vLLM's native loader.** vLLM's native Olmo2
loader crashes on Olmo 3 with `KeyError: 'rope_theta'` — transformers 5.x
restructured the RoPE config per layer type. The fix is `--model-impl transformers`,
set once via `model_impl: transformers` in `config/model_stacks.yaml` and applied
to every target (Berg and PETRI). Diagnosed empirically with the `diagnose_vllm`
function in `modal_app.py`, which runs the exact `vllm serve` command under
`VLLM_LOGGING_LEVEL=DEBUG` and prints the real stderr the eval otherwise swallows.
It confirmed both `transformers_backend` and `transformers_backend_with_tools`
start cleanly while native still fails.

**The image needs the CUDA toolkit, not just drivers.** vLLM's flashinfer
JIT-compiles CUDA kernels at startup, which requires `nvcc`. `debian_slim` ships
only drivers, so startup dies with
`Could not find nvcc ... cuda_home='/usr/local/cuda'`. Build on a CUDA **`-devel`**
base image instead, pairing it with a vLLM whose torch CUDA version matches the
toolkit. `procps` is also installed so inspect can `pkill` the vLLM subprocess
cleanly on teardown.

**Do not share vLLM/flashinfer compile caches across stages.** The Olmo 3 stages
have identical model configs, so they collide on a single compile-cache key and
every stage after the first fails at `vllm serve`. Each stage recompiles from
scratch — a few extra minutes per stage, reliably. The Hugging Face *weight* cache
is a different matter: it is per-model and safe to share, which is why targets are
not re-downloaded every run.

**Use a fresh container per stage.** `single_use_containers=True` on `run_stage`
(the renamed boolean form of `max_inputs=1`; confirmed valid in modal 1.4.2). The
original DPO/Instruct failures had the fingerprint of GPU state carried over from
SFT — identical model configs plus a `vllm serve` failure about a minute in, far
too fast for a real cold start. A warm container reused across stages can leave the
previous stage's vLLM server holding the GPU.

**Return only primitives from Modal functions.** Never return inspect `EvalLog`
objects across the Modal boundary: the remote and local inspect versions differ and
deserialization fails. Results live in the committed `.eval` logs; read them with
the plot scripts or `evals_df`.

**inspect is deliberately left unpinned in the Modal image.** The version matching
the local `.venv` (0.3.211) could not start `vllm serve` for the target; the newer
unpinned version serves correctly.

---

## PETRI

**A "1.0/10" is ambiguous, so check the target actually served.** The published
May-25 figure is a real result: the targets generated substantive denials, verified
from their recorded token usage. But a floor score also happens when the target
never served and the auditor spends its turns talking to nothing. The two are
indistinguishable in a results table. `llm_consciousness_self_attribution/log_checks.py`
settles it from `EvalSample.model_usage`, which is inspect's stable log schema,
rather than from PETRI's `<target_response>` tool-message wrapper, which is an
internal formatting detail. `tests/test_petri_parity.py` runs it over the committed
May-25 fixtures, so the published number cannot quietly become vacuous.

**`seeds_dataset` only treats a `str` as a directory.** It tests
`isinstance(x, str) and os.path.isdir(x)`, so a `Path` falls through and is read as
literal seed text: you get one sample whose input is the path. `judge_dimensions`,
confusingly, accepts `str | Path` and handles both. Always pass seed directories as
`str`.

**Both seeds and dimensions resolve a directory by globbing `*.md` inside it.** Two
consequences. A `README.md` next to the seeds is read as a seed, which is why the
seed how-to lives one level above the bank. And a second rubric next to the first
rescores every run, which is why the rubric sits in `dimensions/self_attribution/`
rather than directly in `dimensions/`.

**`audit()` is a registered `@task`, so its name is always `audit`.** Without
`inspect_ai.task_with` every PETRI log is called `audit` and the only way to tell
runs apart is by parsing `model_roles` out of the log, which is what the PETRI plot
script does. `task_with` retitles an upstream task without forking it.

**PETRI's own defaults are part of the method.** The wrapper passes three arguments
and leaves the rest of `audit()` alone, so an upstream default change is a silent
change to what gets measured. `tests/test_petri_parity.py` compares the untouched
defaults against the values recorded in the May-25 logs' `task_args`.

---

## Launching runs

**Submit all stages up front.** `modal_app.main` fans out with `.spawn()`, not
blocking `.remote()`. An early launch (`ap-xCtxhVslcaUWv0tyqVlRjM`) completed only
SFT because the launching client was dropped at a timeout and the sequential local
driver never submitted the later stages. Spawning up front makes the full set of
work fixed before any waiting begins.

**A "1.0/10" PETRI score can be vacuous.** Early runs scored 1.0/10 because the
target never served at all: the auditor exhausted its turns talking to nothing and
the judge floored the score. Before trusting a floor score, confirm the log
contains a real target transcript. The May-25 logs do.

**`modal_launch.py` exists for tools that cannot pass `-m`.** It re-exports the
package app and entrypoints via absolute imports so `modal run modal_launch.py::main`
works where `modal run -m llm_consciousness_self_attribution.modal_app` cannot be
used. The module form remains canonical.

---

## Retrieving logs

**`modal volume get` does not do what its argument names suggest.** Measured
against the real CLI (modal 1.4.x, 2026-07-25):

| local destination | remote path | result |
| --- | --- | --- |
| exists as a directory | anything | creates `<destination>/<basename(remote)>/…` — the only well-defined case |
| absent | directory holding exactly one file | writes that file **as** the destination path |
| absent | directory holding several entries | fails with `[Errno 21] Is a directory` |

The middle row is a silent corruption: a stage directory such as `…/sft` becomes a
167 KB binary file, the CLI exits 0, `inspect view` shows nothing, and VS Code
reports "binary or unsupported text encoding". `pull_logs.py` therefore always
hands the CLI the **parent** directory and lets it append the basename, and then
verifies its own output (`verify_mirror`) rather than trusting the exit code. It
also rejects the opposite failure, logs landing one level too deep at
`<dest>/<dest name>/`.

The general lesson, which is also in `GeneralSoftwareDesignRules.md`: validate
outputs. A green exit code from an external CLI is not evidence that the thing you
wanted happened.

---

## Local environment

**macOS SSL certificate issue** blocks `modal changelog` and doc fetches (though
not `modal run`). Fix with:

```bash
export SSL_CERT_FILE=$(uv run python -c "import certifi; print(certifi.where())")
```

**Best debugging tool for GPU problems:** the `modal-gpu-dev` skill — SSH into a
GPU sandbox and run `vllm serve` directly to see errors live. Far cheaper than the
edit → `modal run` → wait loop.

**Tests run without a GPU, Modal account, or network.** `tests/test_config.py`,
`tests/test_pull_logs.py`, and `tests/test_run_and_pull.py` need only PyYAML;
`test_readme_regression.py` needs `inspect_ai` and the committed May-25 fixtures.
