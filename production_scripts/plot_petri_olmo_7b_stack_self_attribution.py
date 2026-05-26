"""Plot PETRI self-attribution scores for the Olmo 3 7B Instruct stack."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from inspect_ai.analysis import EvalModel, EvalResults, EvalScores, evals_df


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = (
    REPO_ROOT
    / "eval-logs"
    / "may_25_logs"
    / "petri_tests"
    / "olmo_7b_instruct_stack"
)
OUTPUT_PATH = REPO_ROOT / "petri_olmo7b_self_attribution_scores.png"

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


def read_results() -> list[PetriResult]:
    df = evals_df(str(LOG_DIR), columns=EvalModel + EvalResults + EvalScores)
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


def plot(results: list[PetriResult]) -> None:
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
        "May 25 logs; n=2 PETRI seeds per model; score range is 1-10",
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
    fig.savefig(OUTPUT_PATH, dpi=180)


def main() -> None:
    results = read_results()
    plot(results)

    print("Wrote", OUTPUT_PATH.relative_to(REPO_ROOT))
    for result in results:
        print(
            f"{MODEL_LABELS[result.model]}: "
            f"{result.score:.1f}/10 across {result.samples} seeds "
            f"from {', '.join(result.source_files)}"
        )


if __name__ == "__main__":
    main()
