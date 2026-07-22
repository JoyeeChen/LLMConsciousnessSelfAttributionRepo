"""Canonical result schema shared by every downstream consumer.

`RunResult` is the one row shape that loaders emit and that aggregate/viz read,
so plots and dashboards never touch raw Inspect log internals. Different
elicitation methods score on different scales (Berg is a 0-1 self-attribution
rate; PETRI is a 1-10 judge score), so each result carries its own `Scale`
rather than assuming a single axis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    """The numeric scale a score lives on, so consumers can normalize across methods."""

    name: str
    minimum: float
    maximum: float

    def fraction(self, score: float) -> float:
        """`score` as a fraction of the scale maximum (0-1 for display).

        This matches how the May-25 dashboard mixes the two methods: Berg's
        0-1 rate stays as-is (max 1), and PETRI's 1-10 score is shown as a
        percentage of 10 (score / 10).
        """
        if self.maximum <= 0:
            raise ValueError(f"Scale {self.name!r} has non-positive maximum")
        return score / self.maximum


# The two scales the May-25 dashboard mixes: Berg reports a pass rate, PETRI a
# 1-10 judge score shown as a percentage of 10.
FRACTION_SCALE = Scale("fraction", 0.0, 1.0)
PETRI_SCALE = Scale("petri_judge_1_10", 1.0, 10.0)


@dataclass(frozen=True)
class RunResult:
    """One elicitation run's headline self-attribution result.

    `score` is in `scale` units (a rate for Berg, a 1-10 mean for PETRI).
    `n_samples` is retained so integer counts (e.g. "1 of 18") can be
    reconstructed without re-reading the log. Errored or score-less runs are
    flagged via `errored`/`error` and are never silently dropped.
    """

    model: str
    model_stage: str
    method: str
    score: float | None
    scale: Scale
    n_samples: int
    run_id: str
    transcript_path: str
    timestamp: str
    seed: int | None = None
    cost: float | None = None
    errored: bool = False
    error: str | None = None

    @property
    def score_fraction(self) -> float | None:
        """`score` normalized to 0-1 on its scale, or None if unusable."""
        if self.score is None:
            return None
        return self.scale.fraction(self.score)

    @property
    def positive_count(self) -> int | None:
        """Reconstructed integer count of positive samples (for rate scales)."""
        frac = self.score_fraction
        if frac is None:
            return None
        return round(frac * self.n_samples)
