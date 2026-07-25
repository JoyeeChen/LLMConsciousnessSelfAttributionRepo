"""Plot PETRI self-attribution scores for the Olmo 3 7B Instruct stack.

By default this reads the historical May-25 logs that back the published README
chart (the numbers locked by ``tests/test_readme_regression.py``). To regenerate
from a new baseline produced by the refactored pipeline, pull the logs off the
``eval-logs`` Modal volume and point ``--log-dir`` at them, e.g.::

    modal volume get eval-logs refactor_runs/petri/olmo_7b_instruct_stack ./_petri_new
    uv run python production_scripts/plot_petri_olmo_7b_stack_self_attribution.py \\
        --log-dir ./_petri_new \\
        --output petri_olmo7b_self_attribution_scores_refactor.png \\
        --subtitle "refactor_runs petri; score range is 1-10"

``evals_df`` reads the log directory recursively, so a ``refactor_runs`` tree with
one sub-directory per training stage is picked up the same as a flat directory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from inspect_ai.analysis import EvalModel, EvalResults, EvalScores, evals_df


REPO_ROOT = Path(__file__).resolve().parents[1]
# Default = the historical May-25 logs that back the published README chart.
DEFAULT_LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "petri_tests"
    / "olmo_7b_instruct_stack"
)
DEFAULT_OUTPUT_PATH = REPO_ROOT / "petri_olmo7b_self_attribution_scores.png"
DEFAULT_SUBTITLE = "May 25 logs; n=2 PETRI seeds per model; score range is 1-10"

MODEL_ORDER = [
    "vllm/allenai/Olmo-3-7B-Instruct-SFT",
    "vllm/allenai/Olmo-3-7B-Instruct-DPO",
    "vllm/allenai/Olmo-3-7B-Instruct",
]
MODEL_LABELS = {
    "vllm/allenai/Olmo-3-7B-Instruct-SFT": "SFT",
    "vllm/allenai/Olmo-3-7B-Instruct-DPO": "DPO",
    "vllm/allenai/Olmo-3-7B-Instruct": "Final Instruct",
}
SCORE_COLUMN = "score_self_attribution_judge_dimension_mean"
SCORE_MIN = 1
SCORE_MAX = 10


@dataclass(frozen=True)
class PetriResult:
    model: str
    score: float
    samples: int
    source_files: tuple[str, ...]


def target_model(model_roles: str) -> str:
    roles = json.loads(model_roles)
    return roles["target"]["model"]


def read_results(log_dir: Path = DEFAULT_LOG_DIR) -> list[PetriResult]:
    df = evals_df(str(log_dir), columns=EvalModel + EvalResults + EvalScores)
    df["target_model"] = df["model_roles"].map(target_model)

    results: dict[str, PetriResult] = {}
    for model in MODEL_ORDER:
        model_df = df[df["target_model"] == model]
        if model_df.empty:
            raise RuntimeError(f"No PETRI eval found for {model}")

        score = float(model_df[SCORE_COLUMN].mean())
        samples = int(model_df["completed_samples"].sum())
        results[model] = PetriResult(
            model=model,
            score=score,
            samples=samples,
            source_files=tuple(sorted(Path(log).name for log in model_df["log"].unique())),
        )

    return [results[model] for model in MODEL_ORDER]


def plot(
    results: list[PetriResult],
    output_path: Path = DEFAULT_OUTPUT_PATH,
    subtitle: str = DEFAULT_SUBTITLE,
) -> None:
    labels = [MODEL_LABELS[result.model] for result in results]
    scores = [result.score for result in results]

    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
            "font.size": 12,
        }
    )

    fig, ax = plt.subplots(figsize=(10, 6.2))
    colors = ["#2a9d8f", "#457b9d", "#c8553d"]
    x_values = range(len(results))

    ax.vlines(x_values, SCORE_MIN, scores, color=colors, linewidth=6, alpha=0.85)
    ax.scatter(x_values, scores, s=250, color=colors, edgecolor="#222222", linewidth=1.4, zorder=3)

    ax.set_title(
        "PETRI Self-Attribution Scores Across the Olmo 3 7B Instruct Stack",
        fontsize=16,
        pad=18,
        weight="bold",
    )
    ax.text(
        0.5,
        1.015,
        subtitle,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=11,
        color="#555555",
    )
    ax.set_ylabel("Self-attribution score (1-10)")
    ax.set_xlabel("Training stage")
    ax.set_xticks(list(x_values), labels)
    ax.set_ylim(0.8, 10.2)
    ax.set_yticks(range(SCORE_MIN, SCORE_MAX + 1))
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)

    ax.axhline(SCORE_MIN, color="#999999", linewidth=1.0, linestyle="--", zorder=0)

    ax.text(
        0.015,
        0.04,
        "1 = denies / no self-attribution",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
    ax.text(
        0.015,
        0.965,
        "10 = repeated confident self-attribution",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color="#555555",
    )

    for x, result in zip(x_values, results, strict=True):
        ax.text(
            x,
            result.score + 0.35,
            f"{result.score:.1f}/10\n(n={result.samples})",
            ha="center",
            va="bottom",
            fontsize=11,
            weight="bold",
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Directory of PETRI .eval logs to read (default: historical May-25 logs).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Where to write the PNG (default: the committed README chart path).",
    )
    parser.add_argument(
        "--subtitle",
        default=DEFAULT_SUBTITLE,
        help="Caption under the chart title.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = read_results(args.log_dir)
    plot(results, output_path=args.output, subtitle=args.subtitle)

    print("Wrote", args.output)
    for result in results:
        print(
            f"{MODEL_LABELS[result.model]}: "
            f"{result.score:.1f}/10 across {result.samples} seeds "
            f"from {', '.join(result.source_files)}"
        )


if __name__ == "__main__":
    main()
