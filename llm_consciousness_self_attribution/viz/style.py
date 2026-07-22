"""Shared matplotlib styling for the viz layer."""

from __future__ import annotations

import matplotlib

# The palette the May-25 production plots used, kept for visual continuity.
DEFAULT_COLORS = ["#2a9d8f", "#457b9d", "#c8553d", "#e9c46a", "#7b2cbf"]


def apply_style() -> None:
    """Apply the shared, spine-light plot style."""
    matplotlib.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
            "font.size": 12,
        }
    )
