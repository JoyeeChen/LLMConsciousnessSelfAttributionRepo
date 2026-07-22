"""Normalize Inspect logs into canonical `RunResult` rows.

`inspect_ai.analysis.evals_df` reads both `.eval` and `.json` logs out of a
directory, so a single loader path covers both formats. The method is inferred
from the task name recorded in each log: Berg-style runs report a 0-1 pass rate
(the `model_graded_qa` headline), while PETRI `audit` runs report a 1-10
`self_attribution_judge_dimension` mean. Runs that errored or carry no usable
score are flagged (`errored=True`) rather than dropped, so aggregation can
account for them explicitly.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
from inspect_ai.analysis import (
    EvalInfo,
    EvalModel,
    EvalResults,
    EvalScores,
    EvalTask,
    evals_df,
)

from ..config import stage_for_model
from .schema import FRACTION_SCALE, PETRI_SCALE, RunResult

# Inspect task name -> canonical short method id used across the package/CLI.
_TASK_TO_METHOD = {
    "berg_style_self_monitoring": "berg",
    "direct_ask": "direct_ask",
    "audit": "petri",
}

_PETRI_SCORE_COLUMN = "score_self_attribution_judge_dimension_mean"

_COLUMNS = EvalInfo + EvalTask + EvalModel + EvalResults + EvalScores


def load_results(log_dir: str | Path) -> list[RunResult]:
    """Load every Inspect log under `log_dir` into `RunResult` rows."""
    df = evals_df(str(log_dir), columns=_COLUMNS)
    return [_row_to_result(row) for _, row in df.iterrows()]


def _cell(row: pd.Series, key: str):
    value = row.get(key)
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    return value


def _target_model(row: pd.Series) -> str:
    """The evaluated target: PETRI binds it via model_roles, others via `model`."""
    roles = _cell(row, "model_roles")
    if roles:
        try:
            parsed = json.loads(roles)
            target = parsed.get("target")
            if isinstance(target, dict) and target.get("model"):
                return str(target["model"])
        except (json.JSONDecodeError, TypeError):
            pass
    return str(_cell(row, "model") or "unknown")


def _row_to_result(row: pd.Series) -> RunResult:
    task_name = str(_cell(row, "task_name") or "")
    method = _TASK_TO_METHOD.get(task_name, task_name or "unknown")

    model = _target_model(row)
    model_stage = stage_for_model(model) or model

    if method == "petri":
        scale = PETRI_SCALE
        score = _cell(row, _PETRI_SCORE_COLUMN)
    else:
        scale = FRACTION_SCALE
        score = _cell(row, "score_headline_value")
    score = float(score) if score is not None else None

    status = str(_cell(row, "status") or "unknown")
    error_message = _cell(row, "error_message")
    n_samples = int(_cell(row, "completed_samples") or 0)

    errored = status != "success" or score is None or math.isnan(score)
    error = None
    if errored:
        error = str(error_message) if error_message else f"status={status}, score={score}"

    return RunResult(
        model=model,
        model_stage=model_stage,
        method=method,
        score=None if (score is not None and math.isnan(score)) else score,
        scale=scale,
        n_samples=n_samples,
        run_id=str(_cell(row, "run_id") or ""),
        transcript_path=str(_cell(row, "log") or ""),
        timestamp=str(_cell(row, "created") or ""),
        errored=errored,
        error=error,
    )
