"""Local (non-Modal) eval runner.

Used for runs that don't need a Modal GPU box (e.g. base-model or CPU-only
experiments). It also holds the provider-agnostic eval-invocation helper that the
Modal runner reuses, so the "model= vs model_roles=" dispatch lives in one place.
"""

from __future__ import annotations

from inspect_ai import eval

from ..config import auditor_model, judge_model
from .run_config import RunConfig


def run_eval_task(run_config: RunConfig):
    """Build the task for `run_config`, run inspect eval, and return the logs.

    PETRI-style methods bind auditor/target/judge via `model_roles`; the static
    methods (Berg, direct-ask) bind a single target via `model`.
    """
    task = run_config.build_task()
    if run_config.method.uses_model_roles:
        return eval(
            task,
            model_roles=dict(
                auditor=auditor_model(),
                target=run_config.target_model(),
                judge=judge_model(),
            ),
            log_dir=run_config.log_dir,
            log_format="eval",
        )
    return eval(
        task,
        model=run_config.target_model(),
        log_dir=run_config.log_dir,
    )


def run_local(run_config: RunConfig):
    """Run `run_config` locally."""
    return run_eval_task(run_config)
