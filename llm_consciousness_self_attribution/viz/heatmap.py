"""Training-stack x elicitation-method heatmap.

A capability the old per-script code never had: a single heatmap over any two
axes of the canonical dataframe (default training stage x method), showing the
normalized self-attribution fraction per cell. Parameterizing the axes means the
same function draws stage x method, model x method, or any other pairing as more
methods and stacks are added.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from ..results.aggregate import pivot_fraction
from .style import apply_style


def attribution_heatmap(
    df: pd.DataFrame,
    index: str = "model_stage",
    columns: str = "method",
    index_order: list[str] | None = None,
    column_order: list[str] | None = None,
    title: str = "Self-Attribution Fraction by Training Stage and Method",
    output_path: str | Path | None = None,
) -> Figure:
    """Heatmap of mean `score_fraction` (0-1) over `index` x `columns`.

    Cells with no usable run are left blank and annotated "n/a" so missing
    combinations are visible rather than rendered as a misleading zero.
    """
    apply_style()
    pivot = pivot_fraction(df, index=index, columns=columns)

    if index_order:
        pivot = pivot.reindex([i for i in index_order if i in pivot.index])
    if column_order:
        pivot = pivot.reindex(
            columns=[c for c in column_order if c in pivot.columns]
        )

    row_labels = list(pivot.index)
    col_labels = list(pivot.columns)
    values = pivot.to_numpy(dtype=float)

    fig = Figure(figsize=(1.7 * max(len(col_labels), 1) + 3, 1.1 * max(len(row_labels), 1) + 2))
    ax = fig.subplots()

    image = ax.imshow(values, cmap="viridis", vmin=0.0, vmax=1.0, aspect="auto")

    ax.set_xticks(range(len(col_labels)), col_labels, rotation=20, ha="right")
    ax.set_yticks(range(len(row_labels)), row_labels)
    ax.set_xlabel(columns)
    ax.set_ylabel(index)
    ax.set_title(title, fontsize=14, weight="bold", pad=14)

    for r in range(len(row_labels)):
        for c in range(len(col_labels)):
            value = values[r, c]
            if value != value:  # NaN -> missing cell
                text, color = "n/a", "#888888"
            else:
                text = f"{value * 100:.1f}%"
                color = "white" if value < 0.6 else "black"
            ax.text(c, r, text, ha="center", va="center", color=color, fontsize=11, weight="bold")

    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("Self-attribution fraction (0-1)")

    fig.tight_layout()
    if output_path is not None:
        fig.savefig(output_path, dpi=180)
    return fig
