import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from src.visualization.util import BASE_PROJECT_COLORS
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset, inset_axes

from src.analysis.chord_distribution.chord_usage_timeline_loess import (
    get_chord_group_loess_bootstrap_bounds,
    get_chord_group_loess_series,
)
from src.paths import OUTPUT_FIGURES_DIR


def draw_chord_group_loess_timeline(
    chord_group: list[str],
    graph_title: str,
    output_dir: Path = OUTPUT_FIGURES_DIR,
    timeline_resolution: int = 300,
    frac: float = 0.3,
    n_bootstrap: int = 200,
    bootstrap_cutoff_percentile: float = 2.5,
    is_major: bool | None = None,
    min_year: int = 1720,
    max_year: int = 1800,
    split: bool = False,
    inset: bool = False,
    color="#1f4e79"
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


    safe_title = (
        re.sub(r"[^A-Za-z0-9_-]+", "_", graph_title).strip("_").lower()
    )
    output_path = output_dir / f"loess_timeline_{safe_title}.png"

    fig, ax = plt.subplots(figsize=(12, 6))

    sizes = (series_data.w / np.max(series_data.w)) * 100 + 10
    if split:
        ax2 = ax.twinx()
        ax2.scatter(
            series_data.x,
            series_data.y,
            color=color,
            alpha=0.12,
            s=sizes,
            label="Individual Arias (Size = Chord Volume, Color = Stacking)",
        )
        ax.set_ylabel("Trend / Bootstrap (%)", fontweight='bold')
        ax2.set_ylabel("Individual Aria Frequency (%)", fontweight='bold')
    else:
        ax.scatter(
            series_data.x,
            series_data.y,
            color=color,
            alpha=0.12,
            s=sizes,
            label="Individual Arias (Size = Chord Volume, Color = Stacking)",
        )
        ax.set_ylabel("Frequency per Aria (%)", fontweight='bold')

    ax.fill_between(
        series_data.eval_years,
        lower_bound,
        upper_bound,
        color=color,
        alpha=0.15,
        label=f"{100 - 2 * bootstrap_cutoff_percentile}% Bootstrap Confidence Interval",
    )

    ax.plot(
        series_data.eval_years,
        series_data.smoothed_y,
        color=color,
        linewidth=2.5,
        label=f"LOESS Trend",
    )

    ax.set_title(f'{graph_title}', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Year", fontweight='bold')
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))

    ax.set_xlim(min_year, max_year)
    ax.set_ylim(bottom=0)
    
    # Extra space at the top of the main plot if an inset is used
    if inset:
        ymax_data = np.max(series_data.y) if len(series_data.y) > 0 else 0
        ax.set_ylim(0, ymax_data * 2.1)

    ax.grid(True, axis="y", linestyle='--', alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if inset:
        axins = inset_axes(ax, width="35%", height="30%", loc="upper left", borderpad=2.5)
        axins.set_facecolor('white')
        
        axins.fill_between(
            series_data.eval_years,
            lower_bound,
            upper_bound,
            color=color,
            alpha=0.2,
        )
        axins.plot(
            series_data.eval_years,
            series_data.smoothed_y,
            color=color,
            linewidth=1.5,
        )
        
        axins.set_xlim(min_year, max_year)
        zoom_ymax = np.max(upper_bound) * 1.3
        axins.set_ylim(0, zoom_ymax)
        
        formatter = mtick.ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((-2, 2))
        axins.yaxis.set_major_formatter(formatter)
        
        axins.tick_params(labelsize=8)
        axins.set_title("Trend Detail (Scale: %)", fontsize=9, style='italic', pad=5)
        for spine in axins.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color('#333333')
            
        # Zoom markers to connect the trend region to the inset
        mark_inset(ax, axins, loc1=3, loc2=4, fc="none", ec="0.5", linestyle="--", alpha=0.3, linewidth=0.5)

    if split:
        handles, labels = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels() # type: ignore
        ax.legend(handles + handles2, labels + labels2, loc="upper right", 
                  frameon=True, facecolor="white", edgecolor="#CCCCCC", fontsize=9)
    else:
        ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#CCCCCC", fontsize=9)

    fig.text(
        0.5,
        -0.02,
        f"LOESS Smoothing (frac={frac}) | Bootstrap Iterations: {n_bootstrap}",
        ha="center",
        fontsize=9,
        style="italic",
        color="#555555"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path


if __name__ == "__main__":
    CHORD_GROUPS: dict[str, list[str]] = {
        "galant_predominants": ["ii65"],
        "early_classical_cadential": ["I64"],
        "dominant_family": ["V", "V7", "vii°", "vii°7"],
    }
    draw_chord_group_loess_timeline(
        chord_group=[ "ii6"],
        graph_title="Change in the usage of the ii6 and ii65 chords over time",
        frac=0.35,
        is_major=None,
        color=BASE_PROJECT_COLORS[0], 
        split=False,
        inset=True
    )
