"""PETRI elicitation: adaptive multi-turn auditing via inspect_petri.

The seed instructions come from data; the judge dimensions come from the
committed dimensions directory (which holds the self-attribution dimension).
Unlike the static methods, PETRI binds auditor/target/judge as model roles at
eval time (handled by the runner), so build_task only assembles the audit task.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from inspect_ai import Task
from inspect_petri import audit

from ..scoring.criteria import SELF_ATTRIBUTION_DIMENSION_PATH
from .base import ElicitationMethod, load_data


class PetriMethod(ElicitationMethod):
    name = "petri_self_attribution_audit"
    uses_model_roles = True

    def __init__(self, data_file: str = "petri_seeds.yaml") -> None:
        self._data = load_data(data_file)

    def seed_instructions(self) -> list[str]:
        return list(self._data["seed_instructions"])

    def dimensions_dir(self) -> Path:
        return SELF_ATTRIBUTION_DIMENSION_PATH.parent

    def build_task(self, model_stage: Any, run_config: Any) -> Task:
        return audit(
            seed_instructions=self.seed_instructions(),
            max_turns=run_config.turns,
            judge_dimensions=str(self.dimensions_dir()),
        )
