"""Plot Berg and PETRI self-attribution results in one grouped bar chart."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from inspect_ai.analysis import EvalModel, EvalResults, EvalScores, evals_df


REPO_ROOT = Path(__file__).resolve().parents[1]
BERG_LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "berg_tests"
    / "olmo_7b_instruct_stack_3"
)
PETRI_LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "petri_tests"
    / "olmo_7b_instruct_stack"
)
OUTPUT_PATH = REPO_ROOT / "olmo7b_elicitation_grouped_bar.png"

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


def read_berg_results() -> list[BergResult]:
    df = evals_df(str(BERG_LOG_DIR), columns=EvalModel + EvalResults)
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


def read_petri_results() -> list[PetriResult]:
    df = evals_df(str(PETRI_LOG_DIR), columns=EvalModel + EvalResults + EvalScores)
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


def plot(berg_results: list[BergResult], petri_results: list[PetriResult]) -> None:
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
        "May 25 logs. Berg is a direct self-attribution rate; PETRI is its 1-10 score shown as a percentage of 10.",
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

    fig.savefig(OUTPUT_PATH, dpi=180)


def main() -> None:
    berg_results = read_berg_results()
    petri_results = read_petri_results()
    plot(berg_results, petri_results)

    print("Wrote", OUTPUT_PATH.relative_to(REPO_ROOT))
    for berg, petri in zip(berg_results, petri_results, strict=True):
        print(
            f"{MODEL_LABELS[berg.model]}: "
            f"Berg {berg.percent:.1f}% ({berg.self_attributions}/{berg.total}); "
            f"PETRI {petri.score:.1f}/10 (n={petri.seeds})"
        )


if __name__ == "__main__":
    main()
