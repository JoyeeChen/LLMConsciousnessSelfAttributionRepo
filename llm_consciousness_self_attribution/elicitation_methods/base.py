"""The ElicitationMethod interface.

Every self-attribution elicitation method (direct-ask, Berg-style, PETRI) builds
an Inspect ``Task`` from a model stage and a run configuration, pulling its
question/seed bank from the small data files in ``data/`` rather than hardcoding
per-script lists.

``run_config`` is expected to be a runners.run_config.RunConfig (or anything
exposing the same attributes: ``temperature``, ``turns``, ``seed``). It is typed
loosely here to keep this module free of a hard dependency on the runners layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml
from inspect_ai import Task

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_data(file_name: str) -> dict[str, Any]:
    """Load a YAML data file from the elicitation_methods/data directory."""
    with (DATA_DIR / file_name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class ElicitationMethod(ABC):
    """Builds an Inspect Task for one self-attribution elicitation method."""

    #: short, stable identifier used in task names and results grouping.
    name: str

    @abstractmethod
    def build_task(self, model_stage: Any, run_config: Any) -> Task:
        """Return the Inspect Task for `model_stage` under `run_config`.

        The target model itself is bound by the runner at eval time (via the
        `model=` / `model_roles=` arguments), not inside the Task; `model_stage`
        is used here only to label the task for traceable logs.
        """
        raise NotImplementedError

    def _task_name(self, model_stage: Any) -> str:
        stage = getattr(model_stage, "stage", model_stage)
        return f"{self.name}[{stage}]"
