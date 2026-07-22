"""Launch self-attribution eval runs on Modal (A100 + vLLM).

Mirrors the known-working May-25 Modal scripts, but DRY: the models, graders,
methods, seeds, and scorers all come from the package instead of being pasted
(and commented in/out) per file. Run stages are chosen by CLI args, not by
editing commented lines.

CRITICAL packaging guard: the image MUST include this package via
``add_local_python_source("llm_consciousness_self_attribution")`` (below), or the
remote container raises ``ModuleNotFoundError`` -- the failure mode to avoid.

Usage (from the repo root, on a machine with Modal configured)::

    modal run -m llm_consciousness_self_attribution.modal_app -- \
        --method berg --stack olmo_7b_instruct_stack --stages sft,dpo,instruct
"""

from __future__ import annotations

from pathlib import Path

import modal

from . import config
from .run import RunConfig, evaluate, methods_registry

APP_NAME = "llm-consciousness-self-attribution"
SECRET_NAME = "llm_consciousness_self_attribution_secrets"

app = modal.App(APP_NAME)
volume = modal.Volume.from_name("eval-logs", create_if_missing=True)

image = (
    modal.Image.debian_slim()
    .uv_pip_install(["inspect-ai", "vllm", "inspect-petri", "openai", "pyyaml"])
    # The packaging guard: ship this package into the container.
    .add_local_python_source("llm_consciousness_self_attribution")
)


@app.function(
    gpu="A100",
    image=image,
    volumes={"/eval-logs": volume},
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=3600,
)
def run_stage(method_key: str, stack_name: str, stage_name: str, log_dir: str):
    method = methods_registry()[method_key]
    stage = next(s for s in config.load_stack(stack_name) if s.stage == stage_name)
    run_config = RunConfig.from_defaults(stage, method, log_dir=log_dir)
    print(f"Running {method_key} on {stack_name}:{stage_name} -> {log_dir}")
    try:
        return evaluate(run_config)
    finally:
        log_path = Path(log_dir)
        if log_path.exists():
            print("Inspect log files:", sorted(p.name for p in log_path.iterdir()))
        volume.commit()
        print("Committed Modal volume: eval-logs")


@app.local_entrypoint()
def main(
    method: str = "berg",
    stack: str = "olmo_7b_instruct_stack",
    stages: str = "sft,dpo,instruct",
    log_root: str = "/eval-logs/refactor_runs",
):
    stage_names = [s.strip() for s in stages.split(",") if s.strip()]
    for stage_name in stage_names:
        log_dir = f"{log_root}/{method}/{stack}/{stage_name}"
        run_stage.remote(method, stack, stage_name, log_dir)
