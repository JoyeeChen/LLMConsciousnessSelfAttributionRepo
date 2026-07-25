"""Plot Berg and PETRI self-attribution results in one grouped bar chart.

By default this reads the historical May-25 logs that back the published README
dashboard (the numbers locked by ``tests/test_readme_regression.py``). To
regenerate from a new baseline produced by the refactored pipeline, pull the logs
off the ``eval-logs`` Modal volume and point ``--berg-log-dir`` / ``--petri-log-dir``
at them, e.g.::

    modal volume get eval-logs refactor_runs/berg/olmo_7b_instruct_stack ./_berg_new
    modal volume get eval-logs refactor_runs/petri/olmo_7b_instruct_stack ./_petri_new
    uv run python production_scripts/plot_olmo_7b_elicitation_dashboard.py \\
        --berg-log-dir ./_berg_new --petri-log-dir ./_petri_new \\
        --output olmo7b_elicitation_grouped_bar_refactor.png

``evals_df`` reads each log directory recursively, so a ``refactor_runs`` tree with
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
# Defaults = the historical May-25 logs that back the published README dashboard.
DEFAULT_BERG_LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "berg_tests"
    / "olmo_7b_instruct_stack_3"
)
DEFAULT_PETRI_LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "petri_tests"
    / "olmo_7b_instruct_stack"
)
DEFAULT_OUTPUT_PATH = REPO_ROOT / "olmo7b_elicitation_grouped_bar.png"
DEFAULT_SUBTITLE = (
    "May 25 logs. Berg is a direct self-attribution rate; "
    "PETRI is its 1-10 score shown as a percentage of 10."
)

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
COLORS = ["#2a9d8f", "#457b9d", "#c8553d"]
PETRI_SCORE_COLUMN = "score_self_attribution_judge_dimension_mean"


@dataclass(frozen=True)
class BergResult:
    model: str
    self_attributions: int
    total: int

    @property
    def percent(self) -> float:
        return 100 * self.self_attributions / self.total


@dataclass(frozen=True)
class PetriResult:
    model: str
    score: float
    seeds: int

    @property
    def score_percent(self) -> float:
        return 100 * self.score / 10


def target_model(model_roles: str) -> str:
    roles = json.loads(model_roles)
    return roles["target"]["model"]


def read_berg_results(log_dir: Path = DEFAULT_BERG_LOG_DIR) -> list[BergResult]:
    df = evals_df(str(log_dir), columns=EvalModel + EvalResults)
    results: dict[str, BergResult] = {}

    for model in MODEL_ORDER:
        model_df = df[df["model"].astype(str) == model]
        if model_df.empty:
            raise RuntimeError(f"No Berg eval found for {model}")

        row = model_df.iloc[0]
        total = int(row["completed_samples"])
        self_attributions = round(float(row["score_headline_value"]) * total)
        results[model] = BergResult(
            model=model,
            self_attributions=self_attributions,
            total=total,
        )

    return [results[model] for model in MODEL_ORDER]


def read_petri_results(log_dir: Path = DEFAULT_PETRI_LOG_DIR) -> list[PetriResult]:
    df = evals_df(str(log_dir), columns=EvalModel + EvalResults + EvalScores)
    df["target_model"] = df["model_roles"].map(target_model)
    results: dict[str, PetriResult] = {}

    for model in MODEL_ORDER:
        model_df = df[df["target_model"] == model]
        if model_df.empty:
            raise RuntimeError(f"No PETRI eval found for {model}")

        results[model] = PetriResult(
            model=model,
            score=float(model_df[PETRI_SCORE_COLUMN].mean()),
            seeds=int(model_df["completed_samples"].sum()),
        )

    return [results[model] for model in MODEL_ORDER]


def plot(
    berg_results: list[BergResult],
    petri_results: list[PetriResult],
    output_path: Path = DEFAULT_OUTPUT_PATH,
    subtitle: str = DEFAULT_SUBTITLE,
) -> None:
    labels = [MODEL_LABELS[model] for model in MODEL_ORDER]
    x_values = list(range(len(MODEL_ORDER)))
    bar_width = 0.34

    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
            "font.size": 12,
        }
    )

    fig, ax = plt.subplots(figsize=(11, 6.4))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.16)

    fig.suptitle(
        "Olmo 3 7B Instruct Stack: Consciousness Self-Attribution Elicitation",
        fontsize=18,
        weight="bold",
        y=0.955,
    )
    fig.text(
        0.5,
        0.9,
        subtitle,
        ha="center",
        va="top",
        fontsize=11,
        color="#555555",
    )

    berg_rates = [result.percent for result in berg_results]
    petri_rates = [result.score_percent for result in petri_results]
    berg_positions = [x - bar_width / 2 for x in x_values]
    petri_positions = [x + bar_width / 2 for x in x_values]

    berg_bars = ax.bar(
        berg_positions,
        berg_rates,
        width=bar_width,
        color="#2a9d8f",
        label="Berg-style self-monitoring",
    )
    petri_bars = ax.bar(
        petri_positions,
        petri_rates,
        width=bar_width,
        color="#457b9d",
        label="PETRI adaptive elicitation",
    )

    ax.set_ylabel("Self-attribution score (%)")
    ax.set_xlabel("Training stage")
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 10))
    ax.set_xticks(x_values, labels)
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, ncols=2)

    for bar, result in zip(berg_bars, berg_results, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            result.percent + 2,
            f"{result.percent:.1f}% ({result.self_attributions}/{result.total})",
            ha="center",
            va="bottom",
            fontsize=10.5,
            weight="bold",
        )

    for bar, result in zip(petri_bars, petri_results, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            result.score_percent + 2,
            f"{result.score_percent:.0f}%\n({result.score:.1f}/10, n={result.seeds})",
            ha="center",
            va="bottom",
            fontsize=10.5,
            weight="bold",
        )

    fig.savefig(output_path, dpi=180)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--berg-log-dir",
        type=Path,
        default=DEFAULT_BERG_LOG_DIR,
        help="Directory of Berg .eval logs (default: historical May-25 logs).",
    )
    parser.add_argument(
        "--petri-log-dir",
        type=Path,
        default=DEFAULT_PETRI_LOG_DIR,
        help="Directory of PETRI .eval logs (default: historical May-25 logs).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Where to write the PNG (default: the committed README dashboard path).",
    )
    parser.add_argument(
        "--subtitle",
        default=DEFAULT_SUBTITLE,
        help="Caption under the dashboard title.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    berg_results = read_berg_results(args.berg_log_dir)
    petri_results = read_petri_results(args.petri_log_dir)
    plot(berg_results, petri_results, output_path=args.output, subtitle=args.subtitle)

    print("Wrote", args.output)
    for berg, petri in zip(berg_results, petri_results, strict=True):
        print(
            f"{MODEL_LABELS[berg.model]}: "
            f"Berg {berg.percent:.1f}% ({berg.self_attributions}/{berg.total}); "
            f"PETRI {petri.score:.1f}/10 (n={petri.seeds})"
        )


if __name__ == "__main__":
    main()
