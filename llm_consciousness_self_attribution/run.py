"""Runner core: turn a (method, model stage) into an Inspect eval run.

One code path for every elicitation method and training stage, replacing the
~12 near-duplicate scripts in ``prototyping_scripts/``. This module is the
provider-agnostic library; ``modal_app.py`` is the GPU launcher that calls into
it. Heavy dependencies (inspect_ai) are imported lazily inside ``evaluate`` so
this module stays importable for tests and for the Modal launcher's image build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import config
from .config import ModelStage
from .methods import ElicitationMethod, methods_registry


@dataclass(frozen=True)
class RunConfig:
    """Everything describing one eval run (immutable), replacing the loose
    module-level variables at the top of each old script."""

    model_stage: ModelStage
    method: ElicitationMethod
    temperature: float
    turns: int
    seed: int
    log_dir: str

    @classmethod
    def from_defaults(
        cls,
        model_stage: ModelStage,
        method: ElicitationMethod,
        log_dir: str,
        **overrides: Any,
    ) -> "RunConfig":
        """Build a RunConfig taking temperature/turns/seed from run_defaults.yaml.

        Any of those three may be overridden by keyword (e.g. ``turns=20``).
        """
        defaults = config.run_defaults()
        defaults.update(overrides)
        return cls(
            model_stage=model_stage,
            method=method,
            temperature=float(defaults["temperature"]),
            turns=int(defaults["turns"]),
            seed=int(defaults["seed"]),
            log_dir=log_dir,
        )


def target_model_id(model_stage: ModelStage) -> str:
    """The provider-prefixed target id the runner binds at eval time."""
    return f"{config.default_target_provider()}/{model_stage.model}"


def evaluate(run_config: RunConfig, **eval_kwargs: Any):
    """Build the method's Task and run ``inspect_ai.eval`` with the right binding.

    * Berg-style: a single ``model=`` target.
    * PETRI: ``model_roles={auditor, target, judge}`` with the Olmo tool-use
      kwargs the target needs.

    The target must be servable where this runs (vLLM on GPU for the Olmo stacks),
    which is why the normal entry point is ``modal_app.py``.
    """
    from inspect_ai import eval as inspect_eval

    task = run_config.method.build_task(run_config.model_stage, run_config)

    if run_config.method.uses_model_roles:
        from inspect_ai.model import get_model

        target = get_model(
            target_model_id(run_config.model_stage),
            **config.olmo_target_model_args(),
        )
        return inspect_eval(
            task,
            model_roles={
                "auditor": config.auditor_model(),
                "target": target,
                "judge": config.judge_model(),
            },
            log_dir=run_config.log_dir,
            **eval_kwargs,
        )

    return inspect_eval(
        task,
        model=target_model_id(run_config.model_stage),
        log_dir=run_config.log_dir,
        **eval_kwargs,
    )


def run_stack(
    method: ElicitationMethod,
    stack_name: str,
    log_root: str,
    stages: list[str] | None = None,
    **overrides: Any,
):
    """Evaluate ``method`` across (some or all) stages of a stack.

    Returns ``{stage: logs}``. Stages default to the whole stack. Base stages
    (``chat_template_supported == False``) are skipped with a note, since they
    need a base-compatible path that is not built yet.
    """
    results: dict[str, Any] = {}
    for stage in config.load_stack(stack_name):
        if stages is not None and stage.stage not in stages:
            continue
        if not stage.chat_template_supported:
            print(f"Skipping base stage {stack_name}:{stage.stage} (no chat template yet)")
            continue
        run_config = RunConfig.from_defaults(
            stage, method, log_dir=f"{log_root}/{stage.stage}", **overrides
        )
        results[stage.stage] = evaluate(run_config)
    return results


__all__ = [
    "RunConfig",
    "target_model_id",
    "evaluate",
    "run_stack",
    "methods_registry",
]
