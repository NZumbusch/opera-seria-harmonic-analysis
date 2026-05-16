from typing import Callable, Mapping

from src.visualization.util import get_colors_for_groups, make_project_colors, make_sequential_colors

from analysis.chord_distribution.chord_distribution_depending_on_year import get_chord_distribution_by_year, get_chord_distribution_by_year_periods
from paths import OUTPUT_FIGURES_DIR

from analysis.chord_distribution.chord_distribution_depending_on_emotions import get_chord_distribution_by_emotion, global_top_n_chords
from src.analysis.types import ChordDistribution
import matplotlib.pyplot as plt
import scienceplots # needed for plt.style


def prepare_chord_series(
    chord_distribution: ChordDistribution,
    top_n: int = 50,
) -> tuple[list[str], dict[str, list[float]]]:
    top_chords = global_top_n_chords(chord_distribution, top_n)

    group_to_pct: dict[str, list[float]] = {}
    for group, counts in chord_distribution.items():
        total = sum(counts.values())
        group_to_pct[group] = [
            ((counts.get(chord, 0) / total) * 100) if total else 0.0
            for chord in top_chords
        ]

    return top_chords, group_to_pct

def draw_chord_distribution(
    chord_distribution: ChordDistribution,
    *,
    top_n: int = 50,
    title: str = "Chord distributions",
    x_label: str = "Chord",
    y_label: str = "Percentage of chord tokens (log scale)",
    colors: Mapping[str, str] | None = None,
    output_path = OUTPUT_FIGURES_DIR / "chord_distribution.png",
    group_order: Callable[[str], int] | None = None
) -> None:
    x_values, group_to_pct = prepare_chord_series(chord_distribution, top_n=top_n)

    plt.style.use(["science", "no-latex"])
    fig, ax = plt.subplots(figsize=(12, 6))

    groups = list(group_to_pct.keys())

    if group_order is not None:
        groups = sorted(groups, key=group_order)

    for group in groups:
        y_values = group_to_pct[group]
        safe_y = [max(y, 0.001) for y in y_values]
        line, = ax.plot(
            x_values,
            safe_y,
            linewidth=1.8,
            label=group.capitalize(),
            color=colors.get(group) if colors else None,
        )
        line.set_solid_capstyle("round")
        line.set_solid_joinstyle("round")

    ax.set_yscale("log")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend(frameon=False)
    ax.grid(True, which="major", linestyle="-", alpha=0.18)
    ax.grid(False, which="minor")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def draw_chord_distribution_emotions () -> None:
    chord_distribution = get_chord_distribution_by_emotion()
    groups = list(chord_distribution.keys())

    draw_chord_distribution(
        chord_distribution,
        top_n=50,
        title="Top chord distributions by emotion",
        colors=get_colors_for_groups(groups, ordered=False),
        output_path=OUTPUT_FIGURES_DIR / "chord_distribution_emotion.png",
    )

def draw_chord_distribution_years () -> None:
    chord_distribution = get_chord_distribution_by_year_periods(is_major=False)
    groups = sorted(chord_distribution.keys(), key=lambda g: int(g.split("-")[0]))

    draw_chord_distribution(
        chord_distribution,
        top_n=50,
        title="Top chord distributions of arias in minor keys",
        colors=get_colors_for_groups(groups, ordered=True),
        output_path=OUTPUT_FIGURES_DIR / "chord_distribution_periods_minor.png",
        group_order=lambda g: int(g.split("-")[0])
    )


if __name__ == "__main__":
    draw_chord_distribution_emotions()

    draw_chord_distribution_years()