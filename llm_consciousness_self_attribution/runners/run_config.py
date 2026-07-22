"""RunConfig: the single value object describing one eval run.

It bundles what previously lived as loose module-level variables at the top of
each script (which model stage, which elicitation method, temperature/turns/seed,
and where logs go) so the local and Modal runners can share one code path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from inspect_ai import Task

from ..config import (
    ModelStage,
    default_target_provider,
    olmo_target_model_args,
    run_defaults,
)
from ..elicitation_methods import ElicitationMethod


@dataclass(frozen=True)
class RunConfig:
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
        """Build a RunConfig, taking temperature/turns/seed from run_defaults.yaml.

        Any of those three may be overridden by keyword (e.g. ``turns=20``).
        """
        defaults = run_defaults()
        defaults.update(overrides)
        return cls(
            model_stage=model_stage,
            method=method,
            temperature=defaults["temperature"],
            turns=defaults["turns"],
            seed=defaults["seed"],
            log_dir=log_dir,
        )

    def build_task(self) -> Task:
        return self.method.build_task(self.model_stage, self)

    def target_model(self) -> Any:
        """The target the runner binds at eval time.

        For PETRI (model-roles) runs the Olmo target needs the tool-use kwargs, so
        a constructed model is returned; otherwise the provider-prefixed id string
        is enough for inspect to resolve.
        """
        model_id = f"{default_target_provider()}/{self.model_stage.model}"
        if self.method.uses_model_roles:
            from inspect_ai.model import get_model

            return get_model(model_id, **olmo_target_model_args())
        return model_id
