from typing import Mapping

import matplotlib.pyplot as plt
import scienceplots  # needed for plt.style

from paths import OUTPUT_FIGURES_DIR
from src.visualization.util import get_colors_for_groups
from src.analysis.major_minor_distribution_periods import get_mode_percentages_by_period


def prepare_mode_percentage_series(
    mode_percentages: dict[str, dict[str, float]],
) -> tuple[list[str], dict[str, list[float]]]:
    periods = list(mode_percentages.keys())

    series = {
        "major": [mode_percentages[p].get("major", 0.0) for p in periods],
        "minor": [mode_percentages[p].get("minor", 0.0) for p in periods],
    }

    return periods, series


def draw_mode_percentage_distribution(
    mode_percentages: dict[str, dict[str, float]],
    *,
    title: str = "Major and minor arias by period",
    x_label: str = "Period",
    y_label: str = "Percentage of arias",
    colors: Mapping[str, str] | None = None,
    output_path = OUTPUT_FIGURES_DIR / "mode_distribution_periods.png",
) -> None:
    x_values, series = prepare_mode_percentage_series(mode_percentages)

    plt.style.use(["science", "no-latex"])
    fig, ax = plt.subplots(figsize=(12, 6))

    for group in ["major", "minor"]:
        y_values = series[group]
        line, = ax.plot(
            x_values,
            y_values,
            linewidth=1.8,
            label=group.capitalize(),
            color=colors.get(group) if colors else None,
        )
        line.set_solid_capstyle("round")
        line.set_solid_joinstyle("round")

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False)
    ax.grid(True, which="major", linestyle="-", alpha=0.18)
    ax.grid(False, which="minor")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def draw_mode_percentage_periods() -> None:
    mode_percentages = get_mode_percentages_by_period()

    draw_mode_percentage_distribution(
        mode_percentages,
        title="Major and minor arias by period",
        colors={
            "major": "#4c72b0",
            "minor": "#c44e52",
        },
        output_path=OUTPUT_FIGURES_DIR / "mode_distribution_periods.png",
    )


if __name__ == "__main__":
    draw_mode_percentage_periods()