"""Visualization layer: generic dashboards and heatmaps over aggregate results."""

from .dashboard import elicitation_bar
from .heatmap import attribution_heatmap

__all__ = ["elicitation_bar", "attribution_heatmap"]
