"""Generic bar-chart dashboards over the canonical aggregate dataframe.

Replaces the three bespoke scripts in `production_scripts/` (the Berg-only bar,
the PETRI-only chart, and the combined grouped bar) with one parameterized
function. Every method is plotted on the shared 0-100% `score_fraction` axis, so
a single-method call reproduces the old per-method plots and a multi-method call
reproduces the combined dashboard.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from .style import DEFAULT_COLORS, apply_style

DEFAULT_METHOD_LABELS = {
    "berg": "Berg-style self-monitoring",
    "petri": "PETRI adaptive elicitation",
    "direct_ask": "Direct ask",
}


def elicitation_bar(
    df: pd.DataFrame,
    stage_order: list[str] | None = None,
    method_order: list[str] | None = None,
    stage_labels: dict[str, str] | None = None,
    method_labels: dict[str, str] | None = None,
    title: str = "Consciousness Self-Attribution Elicitation",
    subtitle: str | None = None,
    output_path: str | Path | None = None,
) -> Figure:
    """Grouped bar chart of self-attribution % by training stage and method.

    Bars show `score_fraction` * 100 (Berg's rate as-is, PETRI's 1-10 score as a
    percentage of 10). Errored runs are excluded from the plotted means. Pass a
    single method to reproduce a per-method bar chart.
    """
    apply_style()
    usable = df[~df["errored"]]

    stages = stage_order or sorted(usable["model_stage"].unique())
    methods = method_order or sorted(usable["method"].unique())
    labels = {**DEFAULT_METHOD_LABELS, **(method_labels or {})}
    stage_label = stage_labels or {s: s for s in stages}

    means = usable.groupby(["model_stage", "method"])["score_fraction"].mean()

    fig = Figure(figsize=(11, 6.4))
    ax = fig.subplots()
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.14)

    n_methods = len(methods)
    group_width = 0.8
    bar_width = group_width / max(n_methods, 1)

    for m_index, method in enumerate(methods):
        heights = [
            100 * means.get((stage, method), float("nan")) for stage in stages
        ]
        positions = [
            i - group_width / 2 + bar_width * (m_index + 0.5)
            for i in range(len(stages))
        ]
        color = DEFAULT_COLORS[m_index % len(DEFAULT_COLORS)]
        bars = ax.bar(
            positions,
            heights,
            width=bar_width,
            color=color,
            label=labels.get(method, method),
        )
        for bar, height in zip(bars, heights, strict=True):
            if height == height:  # not NaN
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + 1.5,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=10.5,
                    weight="bold",
                )

    fig.suptitle(title, fontsize=17, weight="bold", y=0.97)
    if subtitle:
        fig.text(0.5, 0.9, subtitle, ha="center", va="top", fontsize=11, color="#555555")

    ax.set_ylabel("Self-attribution score (%)")
    ax.set_xlabel("Training stage")
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 10))
    ax.set_xticks(range(len(stages)), [stage_label.get(s, s) for s in stages])
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)
    if n_methods > 1:
        ax.legend(loc="upper left", frameon=False, ncols=n_methods)

    if output_path is not None:
        fig.savefig(output_path, dpi=180)
    return fig
