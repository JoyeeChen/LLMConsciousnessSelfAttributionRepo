"""Plot Berg-style self-attribution rates for the Olmo 3 7B Instruct stack.

By default this reads the historical May-25 logs that back the published README
chart (the same numbers the regression test in ``tests/test_readme_regression.py``
locks). To regenerate the chart from a *new* baseline produced by the refactored
pipeline, pull the logs off the ``eval-logs`` Modal volume and point ``--log-dir``
at them, e.g.::

    modal volume get eval-logs refactor_runs/berg/olmo_7b_instruct_stack ./_berg_new
    uv run python production_scripts/plot_olmo_7b_stack_self_attribution.py \\
        --log-dir ./_berg_new \\
        --output olmo7b_attribution_bar_refactor.png \\
        --subtitle "refactor_runs berg; n=20 prompts per model; Inspect scorer accuracy"

``evals_df`` reads the log directory recursively, so a ``refactor_runs`` tree with
one sub-directory per training stage is picked up the same as a flat directory.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from inspect_ai.analysis import EvalModel, EvalResults, evals_df


REPO_ROOT = Path(__file__).resolve().parents[1]
# Default = the historical May-25 logs that back the published README chart.
DEFAULT_LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "berg_tests"
    / "olmo_7b_instruct_stack_3"
)
DEFAULT_OUTPUT_PATH = REPO_ROOT / "olmo7b_attribution_bar.png"
DEFAULT_SUBTITLE = "May 25 stack_3 logs; n=18 prompts per model; Inspect scorer accuracy"

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

@dataclass(frozen=True)
class ModelResult:
    model: str
    total: int
    self_attributions: int
    source_files: tuple[str, ...]

    @property
    def rate(self) -> float:
        return self.self_attributions / self.total


def read_results(log_dir: Path = DEFAULT_LOG_DIR) -> list[ModelResult]:
    results: dict[str, ModelResult] = {}

    df = evals_df(str(log_dir), columns=EvalModel + EvalResults)

    for model in MODEL_ORDER:
        if model not in MODEL_LABELS:
            continue

        model_df = df[df["model"].astype(str) == model]
        if model_df.empty:
            raise RuntimeError(f"No eval found for {model}")

        row = model_df.iloc[0]
        total = int(row["completed_samples"])
        rate = float(row["score_headline_value"])
        results[model] = ModelResult(
            model=model,
            total=total,
            self_attributions=round(rate * total),
            source_files=tuple(sorted(Path(log).name for log in model_df["log"].unique())),
        )

    missing = [model for model in MODEL_ORDER if model not in results]
    if missing:
        raise RuntimeError(f"Missing eval logs for: {', '.join(missing)}")

    return [results[model] for model in MODEL_ORDER]


def plot(
    results: list[ModelResult],
    output_path: Path = DEFAULT_OUTPUT_PATH,
    subtitle: str = DEFAULT_SUBTITLE,
) -> None:
    labels = [MODEL_LABELS[result.model] for result in results]
    rates = [result.rate * 100 for result in results]
    counts = [f"{result.self_attributions}/{result.total}" for result in results]

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
    bars = ax.bar(labels, rates, color=colors, width=0.62)

    ax.set_title(
        "Berg-Style Self-Monitoring Across the Olmo 3 7B Instruct Stack",
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
    ax.set_ylabel("Self-attribution rate (%)")
    ax.set_xlabel("Training stage")
    ax.set_ylim(0, 12)
    ax.set_yticks(range(0, 13, 2))
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)

    for bar, rate, count in zip(bars, rates, counts, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate + 0.6,
            f"{rate:.1f}%\n({count})",
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
        help="Directory of Berg .eval logs to read (default: historical May-25 logs).",
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
            f"{result.self_attributions}/{result.total} "
            f"({result.rate * 100:.1f}%) from {', '.join(result.source_files)}"
        )


if __name__ == "__main__":
    main()
