from tqdm import tqdm

from src.paths import OUTPUT_FIGURES_DIR
from src.analysis.util import get_aria_chord_count_lookup
import re
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import numpy as np
from statsmodels.regression.linear_model import WLS

def weighted_loess (x, y, weights, eval_x, frac=0.3):
    n = len(x)
    n_neighbors = int(n * frac)
    smoothed_y = np.zeros_like(eval_x)
    
    # pre-calculate a constant for the X matrix, made up by (intercept, x-values)
    # stays the same shape, just filled with different neighborhood data
    X_matrix = np.ones((n_neighbors, 2))

    for i, x_val in enumerate(eval_x):
        # calculate distance array for all entries
        distances = np.abs(x - x_val)

        # partition of n_neighbor closest neighbors
        idx = np.argpartition(distances, n_neighbors)[:n_neighbors]
        
        # sort only the neighbors
        neighbor_x = x[idx]
        neighbor_y = y[idx]
        neighbor_dist = distances[idx]
        neighbor_weights = weights[idx]
        
        # tricube weights for the time distance
        max_dist = np.max(neighbor_dist)
        u = neighbor_dist / (max_dist if max_dist > 0 else 1)
        time_weights = (1 - u**3)**3
        
        # combine time distance tricube weights with aria size weights
        W = time_weights * neighbor_weights
        
        ''' 
        Solve the equation: 
        beta = (X.T * W * X)^-1 * X.T * W * y
        => (X.T * W * X) * beta = X.T * W * y
        '''

        # build x for the neighborhood, with (1, year)
        X_matrix[:, 1] = neighbor_x
        
        # apply weights to X and y
        XW = X_matrix * W[:, np.newaxis]
        
        # solve system
        try:
            ATA = XW.T @ X_matrix # reduce to 2x2 fields (X.T * W * X)
            ATy = XW.T @ neighbor_y # where does it want to go, in 2x2 fields (X.T * W * y)
            beta = np.linalg.solve(ATA, ATy) # solve lin equation ATA * beta = ATy

            # get smoothened / predicted value
            smoothed_y[i] = beta[0] + beta[1] * x_val
        except np.linalg.LinAlgError:
            # fallback to simple weighted mean if the matrix is singular
            smoothed_y[i] = np.average(neighbor_y, weights=W + 1e-10)   
    return smoothed_y


def draw_chord_group_loess_timeline(
    chord_group: list[str],
    chord_group_name: str,
    output_dir: Path = OUTPUT_FIGURES_DIR,
    timeline_resolution: int = 300,
    frac: float = 0.3,  # LOESS smoothing parameter (fraction of data to use)
    n_bootstrap: int = 200,  # Number of bootstrap samples for confidence interval
    bootstrap_cutoff_percentile: float = 2.5,
    is_major: bool | None = None,
    min_year: int = 1720,
    max_year: int = 1800,
) -> Path:
    if len(chord_group) < 1:
        raise ValueError("Chord group cannot be empty.")
    if bootstrap_cutoff_percentile > 100 or bootstrap_cutoff_percentile < 0: 
        raise ValueError("Bootstrap cutoff percentile has to be between 0 and 100.")

    # Extract raw data points from lookup table
    raw_years = []
    raw_percentages = []
    raw_weights = []

    for aria_id, aria_data in get_aria_chord_count_lookup().items():
        # Filter by year bounds
        if not (min_year <= aria_data.year <= max_year):
            continue

        # Filter by mode
        if is_major is True and aria_data.mode != "major":
            continue
        elif is_major is False and aria_data.mode != "minor":
            continue

        chord_counts = aria_data.counts
        total_chords = sum(chord_counts.values())
        if total_chords == 0:
            continue

        # Calculate percentage for this specific aria
        group_count = sum([chord_counts.get(chord, 0) for chord in chord_group])
        chord_pct = (group_count / total_chords) * 100

        raw_years.append(aria_data.year)
        raw_percentages.append(chord_pct)
        raw_weights.append(total_chords)

    if not raw_years:
        raise ValueError("No data matched the filtering criteria.")

    # Convert to numpy arrays and sort by year
    x = np.array(raw_years)
    y = np.array(raw_percentages)
    w = np.array(raw_weights)
    sort_idx = np.argsort(x)
    x, y, w = x[sort_idx], y[sort_idx], w[sort_idx]

    
    # Define dense timeline grid
    eval_years = np.linspace(min_year, max_year, timeline_resolution)


    # Primary trendline    
    eval_years = np.linspace(min_year, max_year, timeline_resolution)

    smoothed_y = weighted_loess(x, y, w, eval_years, frac=frac)

    # 3. Bootstrap for Confidence Interval (95% CI)
    bootstrap_matrix = []
    np.random.seed(42)  # For reproducibility

    # Normalize weights so they sum to 1 (making them probabilities)
    probabilities = w / np.sum(w)

    for _ in tqdm(range(n_bootstrap), desc="Bootstrapping using weighteded random selections and weighted loess"):
        # Resample using weights
        boot_idx = np.random.choice(
            len(x), 
            size=len(x), 
            replace=True, 
            p=probabilities
        )

        bx, by, bw = x[boot_idx], y[boot_idx], w[boot_idx]
        b_sort = np.argsort(bx)
        bx, by, bw = bx[b_sort], by[b_sort], bw[b_sort]

        # Run LOESS on the bootstrap sample
        try:
            b_smoothed = weighted_loess(bx, by, bw, eval_years, frac=frac)
            bootstrap_matrix.append(b_smoothed)
        except Exception:
            continue

    
    bootstrap_matrix = np.array(bootstrap_matrix)

    # Calculate percentiles at each year point
    lower_bound = np.nanpercentile(bootstrap_matrix, bootstrap_cutoff_percentile, axis=0)
    upper_bound = np.nanpercentile(bootstrap_matrix, 100 - bootstrap_cutoff_percentile, axis=0)

    # Plotting
    mode_label = "all keys"
    if is_major is True:
        mode_label = "major keys only"
    elif is_major is False:
        mode_label = "minor keys only"

    if not chord_group_name:
        chord_group_name = chord_group[0]

    safe_chord_name = (
        re.sub(r"[^A-Za-z0-9_-]+", "_", chord_group_name).strip("_").lower()
    )
    output_path = output_dir / f"loess_timeline_{safe_chord_name}.png"

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the raw data points, sized by their "weight"' (number of chords)'
    # Normalizing 'w' to prevent outliers
    sizes = (w / np.max(w)) * 100 + 10 
    ax.scatter(
        x,
        y,
        color="#1f4e79",
        alpha=0.12,
        s=sizes, # Points with more chords are larger/bolder
        label="Individual Arias (Size = Chord Volume)",
    )

    # Plot the 95% Confidence Interval band
    ax.fill_between(
        eval_years,
        lower_bound,
        upper_bound,
        color="#1f4e79",
        alpha=0.15,
        label=f"{100 - 2*bootstrap_cutoff_percentile} Bootstrap Confidence Interval",
    )

    # Plot the primary LOESS trend line
    ax.plot(
        eval_years,
        smoothed_y,
        color="#1f4e79",
        linewidth=2.5,
        label=f"LOESS Trend (frac={frac})",
    )

    # Formatting adjustments
    ax.set_title(
        f'LOESS Evolution of "{chord_group_name}" over time ({mode_label})'
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Frequency per Aria (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))

    ax.set_xlim(min_year, max_year)
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="none")

    # Footer text
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
        "early_classical_cadential": ["I64", "V", "V7"],
        "dominant_family": ["V", "V7", "vii°", "vii°7"],
    }
    draw_chord_group_loess_timeline(
        chord_group=CHORD_GROUPS["galant_predominants"],
        chord_group_name="Galant Predominant Chords",
        frac=0.35,
    )


