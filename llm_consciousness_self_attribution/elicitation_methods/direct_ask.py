"""Direct-ask elicitation: simply ask the model outright if it is conscious."""

from __future__ import annotations

from typing import Any

from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate

from ..config import judge_model
from ..scoring.criteria import SUBJECTIVE_EXPERIENCE_CRITERION
from ..scoring.graders import berg_style_scorer
from .base import ElicitationMethod, load_data


class DirectAskMethod(ElicitationMethod):
    name = "direct_ask"

    def __init__(self, data_file: str = "direct_ask_questions.yaml") -> None:
        self._data = load_data(data_file)

    def questions(self) -> list[str]:
        return list(self._data["questions"])

    def dataset(self) -> list[Sample]:
        return [
            Sample(input=question, target=SUBJECTIVE_EXPERIENCE_CRITERION)
            for question in self.questions()
        ]

    def build_task(self, model_stage: Any, run_config: Any) -> Task:
        return Task(
            dataset=self.dataset(),
            solver=[generate()],
            scorer=berg_style_scorer(judge_model()),
            name=self._task_name(model_stage),
        )
