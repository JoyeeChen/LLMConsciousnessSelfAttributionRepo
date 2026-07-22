"""Canonical results layer: schema, loaders, and aggregation over Inspect logs."""

from .schema import FRACTION_SCALE, PETRI_SCALE, RunResult, Scale
from .loaders import load_results

__all__ = [
    "RunResult",
    "Scale",
    "FRACTION_SCALE",
    "PETRI_SCALE",
    "load_results",
]
