import csv
import re
from collections import Counter
from pathlib import Path

from visualization.util import BASE_PROJECT_COLORS

from src.analysis.util import get_aria_total_duration
from src.analysis.chord_distribution.chord_usage_timeline_loess import weighted_loess
from pydantic import BaseModel, ConfigDict
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from src.corpus.build_aria_index import create_or_load_aria_index
from src.paths import get_aria_analysis_path, OUTPUT_FIGURES_DIR


class SchemaLoessGraphModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    x: np.ndarray # years
    y: np.ndarray # percentages of schema in arias
    w: np.ndarray # total number of schemata in aria (weight)
    eval_years: np.ndarray # grid
    smoothed_y: np.ndarray 


def get_schema_loess_bootstrap_bounds(
    series_data: SchemaLoessGraphModel,
    frac: float = 0.3,
    n_bootstrap: int = 200,
    bootstrap_cutoff_percentile: float = 2.5,
) -> dict[str, np.ndarray]:
    x = series_data.x
    y = series_data.y
    w = series_data.w
    eval_years = series_data.eval_years

    bootstrap_matrix = []
    np.random.seed(42)

    for _ in tqdm(
        range(n_bootstrap),
        desc="Bootstrapping schema LOESS bounds",
    ):
        boot_idx = np.random.choice(len(x), size=len(x), replace=True)
        bx, by, bw = x[boot_idx], y[boot_idx], w[boot_idx]
        b_sort = np.argsort(bx)
        bx, by, bw = bx[b_sort], by[b_sort], bw[b_sort]

        try:
            b_smoothed = weighted_loess(bx, by, bw, eval_years, frac=frac)
            bootstrap_matrix.append(b_smoothed)
        except Exception:
            continue

    if not bootstrap_matrix:
        raise ValueError("Bootstrapping failed for all samples.")

    bootstrap_array = np.array(bootstrap_matrix)

    return {
        "lower_bound": np.nanpercentile(bootstrap_array, bootstrap_cutoff_percentile, axis=0),
        "upper_bound": np.nanpercentile(bootstrap_array, 100 - bootstrap_cutoff_percentile, axis=0),
    }

def get_schema_loess_series(
    schema_names: list[str],
    timeline_resolution: int = 300,
    frac: float = 0.3,
    is_major: bool | None = None,
    min_year: int = 1720,
    max_year: int = 1800,
    normalization: str = "density" #"density", "raw", or "percentage"
) -> SchemaLoessGraphModel:
    if frac <= 0 or frac > 1:
        raise ValueError("Frac has to be between 0 and 1.")

    raw_years = []
    raw_values = []
    raw_weights = []

    aria_index = create_or_load_aria_index()

    for aria in aria_index:
        if not aria.file_name or not aria.year:
            continue
        if aria.year < min_year or aria.year > max_year:
            continue
        if is_major is True and getattr(aria, 'mode', None) != "major":
            continue
        elif is_major is False and getattr(aria, 'mode', None) != "minor":
            continue

        tsv_path = get_aria_analysis_path(aria.file_name, "schemata")
        if not tsv_path.exists():
            continue

        total_duration = get_aria_total_duration(aria.file_name)

        schema_counts = Counter()
        total_schemata = 0
        max_end_time = 0.0
        
        with open(tsv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                schema_counts[row["schema_name"]] += 1
                total_schemata += 1
                
                try:
                    end_t = float(row.get("end_time", 0))
                    if end_t > max_end_time:
                        max_end_time = end_t
                except ValueError:
                    pass

        if total_schemata == 0:
            continue

        group_count = 0
        if len(schema_names) == 0:
            group_count = sum(schema_counts.values())
        else:
            group_count = sum(schema_counts.get(s, 0) for s in schema_names)

        
        if normalization == "density":
            # Occurrences per 100 quarter beats
            y_val = (group_count / total_duration) * 100 
        elif normalization == "raw":
            y_val = float(group_count)
        else: # "percentage"
            y_val = (group_count / total_schemata) * 100

        raw_years.append(aria.year)
        raw_values.append(y_val)
        raw_weights.append(total_schemata)

    if not raw_years:
        raise ValueError("No data matched the filtering criteria.")

    x = np.array(raw_years)
    y = np.array(raw_values)
    w = np.array(raw_weights)

    sort_idx = np.argsort(x)
    x, y, w = x[sort_idx], y[sort_idx], w[sort_idx]

    eval_years = np.linspace(min_year, max_year, timeline_resolution)
    smoothed_y = weighted_loess(x, y, w, eval_years, frac=frac)

    return SchemaLoessGraphModel(x=x, y=y, w=w, eval_years=eval_years, smoothed_y=smoothed_y)

def draw_schema_loess_timeline(
    schema_names: list[str],
    display_name: str = "",
    output_dir: Path = OUTPUT_FIGURES_DIR,
    timeline_resolution: int = 300,
    frac: float = 0.3,
    n_bootstrap: int = 200,
    bootstrap_cutoff_percentile: float = 2.5,
    is_major: bool | None = None,
    min_year: int = 1720,
    max_year: int = 1800,
    normalization: str = "density"
) -> Path:
    
    series_data = get_schema_loess_series(
        schema_names=schema_names,
        timeline_resolution=timeline_resolution,
        frac=frac,
        is_major=is_major,
        min_year=min_year,
        max_year=max_year,
        normalization=normalization
    )

    bootstrap_data = get_schema_loess_bootstrap_bounds(
        series_data,
        frac=frac,
        n_bootstrap=n_bootstrap,
        bootstrap_cutoff_percentile=bootstrap_cutoff_percentile,
    )

    mode_label = "all keys"
    if is_major is True:
        mode_label = "major keys only"
    elif is_major is False:
        mode_label = "minor keys only"

    if not display_name:
        display_name = schema_names[0]

    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", display_name).strip("_").lower()
    output_path = output_dir / f"loess_timeline_schema_{safe_name}.png"

    fig, ax = plt.subplots(figsize=(12, 6))

   
    sizes = (series_data.w / np.max(series_data.w)) * 100 + 10
    
    color = BASE_PROJECT_COLORS[-1]
    ax.scatter(
        series_data.x,
        series_data.y,
        color=color,
        alpha=0.15,
        s=sizes,
        label="Individual Arias (Size = Schema Volume)",
    )

    ax.fill_between(
        series_data.eval_years,
        bootstrap_data["lower_bound"],
        bootstrap_data["upper_bound"],
        color=color,
        alpha=0.15,
        label=f"{100 - 2 * bootstrap_cutoff_percentile}% Confidence Interval",
    )

    ax.plot(
        series_data.eval_years,
        series_data.smoothed_y,
        color=color,
        linewidth=2.5,
        label=f"LOESS Trend (frac={frac})",
    )

    ax.set_title(f'Evolution of "{display_name}" ({mode_label})')
    ax.set_xlabel("Year")

    if normalization == "density":
        ax.set_ylabel("Density (Occurrences per 100 quarter beats)")
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
    elif normalization == "raw":
        ax.set_ylabel("Absolute Count per Aria")
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
    else:
        ax.set_ylabel("Frequency per Aria (% of all schemata)")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))

    ax.set_xlim(min_year, max_year)
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="none")

    fig.text(
        0.5, 0.01,
        f"LOESS frac: {frac} | Bootstraps: {n_bootstrap}",
        ha="center", fontsize=9, style="italic",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    print(f"Saved graph to {output_path}")
    return output_path

if __name__ == "__main__":
    draw_schema_loess_timeline(
        schema_names=[],
        display_name="All Schemata",
        frac=0.35,
        is_major=None, 
        min_year=1720,
        max_year=1800,
        normalization="density"
    )