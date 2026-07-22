"""Headless smoke tests for the viz layer over the golden aggregate dataframe.

No display or network: figures are built with the Agg-backed Figure API and
saved to a tmp path. These assert the plots render from real fixture data and
that the heatmap surfaces missing cells rather than crashing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from llm_consciousness_self_attribution.results import load_results
from llm_consciousness_self_attribution.results.aggregate import aggregate
from llm_consciousness_self_attribution.viz import (
    attribution_heatmap,
    elicitation_bar,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MAY_25 = REPO_ROOT / "eval-logs" / "may_25_logs"
BERG_STACK_3 = MAY_25 / "berg_tests" / "olmo_7b_instruct_stack_3"
PETRI_STACK = MAY_25 / "petri_tests" / "olmo_7b_instruct_stack"

STAGE_ORDER = ["sft", "dpo", "instruct"]


def _golden_df() -> pd.DataFrame:
    return aggregate(load_results(BERG_STACK_3) + load_results(PETRI_STACK))


def test_elicitation_bar_renders(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.png"
    fig = elicitation_bar(
        _golden_df(),
        stage_order=STAGE_ORDER,
        method_order=["berg", "petri"],
        output_path=out,
    )
    assert out.exists() and out.stat().st_size > 0
    assert len(fig.axes) >= 1


def test_heatmap_renders(tmp_path: Path) -> None:
    out = tmp_path / "heatmap.png"
    fig = attribution_heatmap(
        _golden_df(),
        index_order=STAGE_ORDER,
        column_order=["berg", "petri"],
        output_path=out,
    )
    assert out.exists() and out.stat().st_size > 0
    assert len(fig.axes) >= 1


def test_heatmap_handles_missing_cell(tmp_path: Path) -> None:
    """A method with no run for a stage still renders (blank 'n/a' cell)."""
    df = _golden_df()
    # Drop PETRI's 'instruct' row so that cell is missing.
    df = df[~((df["method"] == "petri") & (df["model_stage"] == "instruct"))]
    fig = attribution_heatmap(
        df,
        index_order=STAGE_ORDER,
        column_order=["berg", "petri"],
        output_path=tmp_path / "sparse.png",
    )
    assert len(fig.axes) >= 1
