"""Shared Modal App / image / volume factory for eval runs.

This replaces the ~6 near-identical Modal boilerplate blocks that were copied
across the prototyping and production eval scripts. There is now one image
(inspect-ai + vllm + inspect-petri, with the judge-dimensions directory mounted),
one persistent volume, one secret, and one GPU function that runs any RunConfig.
"""

from __future__ import annotations

from pathlib import Path

import modal

from ..scoring.criteria import SELF_ATTRIBUTION_DIMENSION_PATH
from .local_app import run_eval_task
from .run_config import RunConfig

VOLUME_NAME = "eval-logs"
SECRET_NAME = "llm_consciousness_self_attribution_secrets"
GPU = "A100"
TIMEOUT = 3600
PIP_PACKAGES = ["inspect-ai", "vllm", "inspect-petri"]

DIMENSIONS_DIR = SELF_ATTRIBUTION_DIMENSION_PATH.parent
REMOTE_DIMENSIONS_DIR = "/root/prototyping_scripts/dimensions"


def build_app(name: str = "self-attribution-evals") -> modal.App:
    return modal.App(name)


def build_volume() -> modal.Volume:
    return modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


def build_image() -> modal.Image:
    return (
        modal.Image.debian_slim()
        .uv_pip_install(PIP_PACKAGES)
        .add_local_dir(str(DIMENSIONS_DIR), remote_path=REMOTE_DIMENSIONS_DIR)
    )


app = build_app()
volume = build_volume()
image = build_image()


@app.function(
    gpu=GPU,
    image=image,
    volumes={f"/{VOLUME_NAME}": volume},
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=TIMEOUT,
)
def run_eval_remote(run_config: RunConfig):
    """Run a RunConfig on a Modal GPU box, committing logs to the volume."""
    try:
        return run_eval_task(run_config)
    finally:
        log_dir = Path(run_config.log_dir)
        if log_dir.exists():
            print(f"Inspect log directory: {log_dir}")
            print("Inspect log files:", sorted(p.name for p in log_dir.iterdir()))
        volume.commit()
        print(f"Committed Modal volume: {VOLUME_NAME}")


@app.local_entrypoint()
def main() -> None:
    raise SystemExit(
        "Import build_app/run_eval_remote and pass a RunConfig; this module has "
        "no default run so it can serve every elicitation method."
    )
