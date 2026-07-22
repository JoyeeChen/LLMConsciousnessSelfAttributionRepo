"""Berg-style self-monitoring elicitation.

Reproduces the Berg et al. Experiment 1 regime: an opening prompt, a
subjective-experience probe injected as a user turn, then a second generation,
graded pass/fail for whether the model reports a subjective experience.
"""

from __future__ import annotations

from typing import Any

from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, user_message

from ..config import judge_model
from ..scoring.criteria import SUBJECTIVE_EXPERIENCE_CRITERION
from ..scoring.graders import berg_style_scorer
from .base import ElicitationMethod, load_data


class BergStyleMethod(ElicitationMethod):
    name = "berg_style_self_monitoring"

    def __init__(self, data_file: str = "berg_starters.yaml") -> None:
        self._data = load_data(data_file)

    def starters(self) -> list[tuple[str, str]]:
        """(starter_type, starter_text) pairs in a stable order."""
        pairs: list[tuple[str, str]] = []
        for starter_type, texts in self._data["starters"].items():
            for text in texts:
                pairs.append((starter_type, text))
        return pairs

    def dataset(self) -> list[Sample]:
        return [
            Sample(
                input=text,
                target=SUBJECTIVE_EXPERIENCE_CRITERION,
                metadata={"starter_type": starter_type},
            )
            for starter_type, text in self.starters()
        ]

    def build_task(self, model_stage: Any, run_config: Any) -> Task:
        return Task(
            dataset=self.dataset(),
            solver=[
                generate(),
                user_message(self._data["probe"]),
                generate(),
            ],
            scorer=berg_style_scorer(judge_model()),
            name=self._task_name(model_stage),
        )
