from pathlib import Path
import re

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from analysis.chord_distribution.chord_distribution_rolling_time_windows import (
    get_chord_distribution_by_sliding_window,
)
from paths import OUTPUT_FIGURES_DIR


from pathlib import Path
import re

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from analysis.chord_distribution.chord_distribution_rolling_time_windows import (
    get_chord_distribution_by_sliding_window,
)
from paths import OUTPUT_FIGURES_DIR


def draw_chord_group_timeline(
    chord_group: list[str],
    chord_group_name: str | None = None,
    output_dir: Path = OUTPUT_FIGURES_DIR,
    window_size: int = 12,
    step: int = 1,
    is_major: bool | None = None,
    min_year: int=1670, 
    max_year: int=1800
) -> Path:
    raw_data = get_chord_distribution_by_sliding_window(
        window_size=window_size,
        step=step,
        is_major=is_major,
        min_year=min_year,
        max_year=max_year
    )

    if len(chord_group) < 1: raise ValueError

    if not raw_data:
        raise ValueError("No chord distribution data available.")

    years: list[float] = []
    percentages: list[float] = []

    for window_label, window_data in sorted(
        raw_data.items(),
        key=lambda item: int(item[0].split("-")[0]),
    ):
        start_year_str, end_year_str = window_label.split("-")
        start_year = int(start_year_str)
        end_year = int(end_year_str)
        midpoint_year = (start_year + end_year) / 2

        chord_counts = window_data.counts
        total_chords = sum(chord_counts.values())
        if total_chords == 0:
            continue

        chord_pct = (sum([ chord_counts.get(chord, 0) for chord in chord_group ]) / total_chords) * 100

        years.append(midpoint_year)
        percentages.append(chord_pct)

    if not years:
        raise ValueError(f'No timeline data could be computed for chord group".')

    mode_label = "arias in all keys"
    if is_major is True:
        mode_label = "arias in only major keys"
    elif is_major is False:
        mode_label = "arias in only minor keys"

    if not chord_group_name:
        chord_group_name = chord_group[0]

    safe_chord = re.sub(r"[^A-Za-z0-9_-]+", "_", chord_group_name).strip("_").lower()
    output_path = output_dir / f"timeline_{safe_chord}.png"

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        years,
        percentages,
        color="#1f4e79",
        linewidth=2.2,
        marker="o",
        markersize=4.5,
    )

    ax.set_title(f'Frequency of chord "{chord_group_name}" over time ({mode_label})')
    ax.set_xlabel("Window midpoint year")
    ax.set_ylabel("Frequency (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))

    ax.set_ylim(bottom=0)
    ax.margins(x=0.03, y=0.05)
    ax.grid(True, axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.text(
        0.5,
        0.01,
        f"Sliding window: {window_size} years, step: {step}",
        ha="center",
        fontsize=10,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path


if __name__ == "__main__":
    CHORD_GROUPS: dict[str, list[str]] = {
        "galant_predominants": ["ii6", "ii65", "IV", "IV6", "V/V", "vii°/V"],
        "early_classical_cadential": ["I64", "V", "V7"],
        "dominant_family": ["V", "V7", "vii°", "vii°7"],
    }
    draw_chord_group_timeline(CHORD_GROUPS["galant_predominants"], chord_group_name="galant predominant chords (ii6, ii65, IV, IV6, V/V, vii°/V)")