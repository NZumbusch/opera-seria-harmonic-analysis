from src.analysis.chord_distribution.chord_usage_timeline_loess import get_chord_group_loess_bootstrap_bounds, get_chord_group_loess_series
from src.paths import OUTPUT_FIGURES_DIR
import re
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

def draw_chord_group_loess_timeline(
    chord_group: list[str],
    chord_group_name: str,
    output_dir: Path = OUTPUT_FIGURES_DIR,
    timeline_resolution: int = 300,
    frac: float = 0.3,
    n_bootstrap: int = 200,
    bootstrap_cutoff_percentile: float = 2.5,
    is_major: bool | None = None,
    min_year: int = 1720,
    max_year: int = 1800,
) -> Path:
    series_data = get_chord_group_loess_series(
        chord_group=chord_group,
        timeline_resolution=timeline_resolution,
        frac=frac,
        is_major=is_major,
        min_year=min_year,
        max_year=max_year,
    )

    bootstrap_data = get_chord_group_loess_bootstrap_bounds(
        series_data,
        n_bootstrap=n_bootstrap,
        bootstrap_cutoff_percentile=bootstrap_cutoff_percentile,
    )

    lower_bound = bootstrap_data["lower_bound"]
    upper_bound = bootstrap_data["upper_bound"]

    mode_label = "all keys"
    if is_major is True:
        mode_label = "major keys only"
    elif is_major is False:
        mode_label = "minor keys only"

    if not chord_group_name:
        chord_group_name = chord_group[0]

    safe_chord_name = re.sub(r"[^A-Za-z0-9_-]+", "_", chord_group_name).strip("_").lower()
    output_path = output_dir / f"loess_timeline_{safe_chord_name}.png"

    fig, ax = plt.subplots(figsize=(12, 6))

    sizes = (series_data.w / np.max(series_data.w)) * 100 + 10
    ax.scatter(
        series_data.x,
        series_data.y,
        color="#1f4e79",
        alpha=0.12,
        s=sizes,
        label="Individual Arias (Size = Chord Volume)",
    )

    ax.fill_between(
        series_data.eval_years,
        lower_bound,
        upper_bound,
        color="#1f4e79",
        alpha=0.15,
        label=f"{100 - 2 * bootstrap_cutoff_percentile} Bootstrap Confidence Interval",
    )

    ax.plot(
        series_data.eval_years,
        series_data.smoothed_y,
        color="#1f4e79",
        linewidth=2.5,
        label=f"LOESS Trend (frac={frac})",
    )

    ax.set_title(f'LOESS Evolution of "{chord_group_name}" over time ({mode_label})')
    ax.set_xlabel("Year")
    ax.set_ylabel("Frequency per Aria (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))

    ax.set_xlim(min_year, max_year)
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="none")

    fig.text(
        0.5,
        0.01,
        f"LOESS Smoothing parameter (frac): {frac} | Bootstrap Iterations: {n_bootstrap}",
        ha="center",
        fontsize=9,
        style="italic",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path



if __name__ == "__main__":
    CHORD_GROUPS: dict[str, list[str]] = {
        "galant_predominants": ["ii6", "ii65", "IV", "IV6", "V/V", "vii°/V"],
        "early_classical_cadential": ["I64"],
        "dominant_family": ["V", "V7", "vii°", "vii°7"],
    }
    draw_chord_group_loess_timeline(
        chord_group=CHORD_GROUPS["early_classical_cadential"],
        chord_group_name="Early classical cadential chords",
        frac=0.35,
        is_major=True
    )


