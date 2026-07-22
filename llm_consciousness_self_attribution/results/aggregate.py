"""Long-format aggregation over `RunResult` rows for plots and heatmaps.

`aggregate` turns a list of `RunResult` into a tidy (long) dataframe: one row
per run, one column per field, with a `score_fraction` column that normalizes
every method onto 0-1 so mixed-scale methods (Berg vs PETRI) share an axis.
Errored/score-less runs are kept with `errored=True` (never silently dropped);
`pivot_fraction` and `missing_cells` make it explicit when a cell is absent or
error-only rather than letting a plot quietly show a gap.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pandas as pd

from .schema import RunResult

COLUMNS = [
    "model",
    "model_stage",
    "method",
    "score",
    "score_fraction",
    "scale",
    "scale_max",
    "n_samples",
    "positive_count",
    "run_id",
    "timestamp",
    "cost",
    "errored",
    "error",
]


def aggregate(results: Iterable[RunResult]) -> pd.DataFrame:
    """Build the canonical long-format dataframe from `RunResult` rows."""
    records = [
        {
            "model": r.model,
            "model_stage": r.model_stage,
            "method": r.method,
            "score": r.score,
            "score_fraction": r.score_fraction,
            "scale": r.scale.name,
            "scale_max": r.scale.maximum,
            "n_samples": r.n_samples,
            "positive_count": r.positive_count,
            "run_id": r.run_id,
            "timestamp": r.timestamp,
            "cost": r.cost,
            "errored": r.errored,
            "error": r.error,
        }
        for r in results
    ]
    return pd.DataFrame(records, columns=COLUMNS)


def pivot_fraction(
    df: pd.DataFrame,
    index: str = "model_stage",
    columns: str = "method",
) -> pd.DataFrame:
    """Mean `score_fraction` pivoted over two axes, ignoring errored runs.

    Errored runs are excluded from the numeric mean (they have no usable score),
    but `missing_cells` reports any (index, columns) pair left empty as a result.
    """
    usable = df[~df["errored"]]
    return usable.pivot_table(
        index=index,
        columns=columns,
        values="score_fraction",
        aggfunc="mean",
    )


def missing_cells(
    df: pd.DataFrame,
    index_values: Sequence[str],
    column_values: Sequence[str],
    index: str = "model_stage",
    columns: str = "method",
) -> list[tuple[str, str]]:
    """(index, column) pairs that have no usable (non-errored) run.

    Lets callers flag holes in an expected training-stack x method grid instead
    of silently plotting a blank cell.
    """
    pivot = pivot_fraction(df, index=index, columns=columns)
    missing: list[tuple[str, str]] = []
    for i in index_values:
        for c in column_values:
            if i not in pivot.index or c not in pivot.columns or pd.isna(pivot.loc[i, c]):
                missing.append((i, c))
    return missing
