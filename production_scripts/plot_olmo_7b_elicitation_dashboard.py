"""Plot the trusted refactor-era self-attribution dashboard."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from production_scripts.plot_olmo_7b_stack_self_attribution import (
    MODEL_LABELS,
    ModelResult,
    read_results,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "olmo7b_elicitation_dashboard.png"


def plot(results: list[ModelResult]) -> None:
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

    fig, ax = plt.subplots(figsize=(11, 6.4))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.79, bottom=0.24)
    colors = ["#2a9d8f", "#457b9d", "#c8553d"]
    bars = ax.bar(labels, rates, color=colors, width=0.62)

    fig.suptitle(
        "Olmo 3 7B Instruct Stack: Trusted Self-Attribution Results",
        fontsize=18,
        weight="bold",
        y=0.95,
    )
    fig.text(
        0.5,
        0.895,
        "Latest refactor-era Berg-style logs; the pre-refactor PETRI results are excluded.",
        ha="center",
        va="top",
        fontsize=11,
        color="#555555",
    )

    ax.set_ylabel("Berg-style self-attribution rate (%)")
    ax.set_xlabel("Training stage")
    ax.set_ylim(0, 10)
    ax.set_yticks(range(0, 11, 2))
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)

    for bar, rate, count in zip(bars, rates, counts, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate + 0.35,
            f"{rate:.1f}%\n({count})",
            ha="center",
            va="bottom",
            fontsize=11,
            weight="bold",
        )

    fig.text(
        0.5,
        0.075,
        "Direct ask: 0% observed personally; no trusted refactor-era scored log is claimed.\n"
        "PETRI: no trusted refactor-era logs are present, so it is omitted from this figure.",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )

    fig.savefig(OUTPUT_PATH, dpi=180)


def main() -> None:
    results = read_results()
    plot(results)

    print("Wrote", OUTPUT_PATH.relative_to(REPO_ROOT))
    for result in results:
        print(
            f"{MODEL_LABELS[result.model]}: "
            f"{result.self_attributions}/{result.total} "
            f"({result.rate * 100:.1f}%) from {result.source_file}"
        )


if __name__ == "__main__":
    main()
