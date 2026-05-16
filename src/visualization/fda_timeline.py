from pathlib import Path
from src.analysis.chord_distribution.chord_trend_grouping import find_trend_groupings_fpca, get_chord_development_matrix
import matplotlib.pyplot as plt
import numpy as np
from src.paths import OUTPUT_FIGURES_DIR


def draw_fpca_clusters_timeline(
    min_year: int = 1700, 
    max_year: int = 1820, 
    timeline_resolution: int = 300,
    min_percentage_of_arias_with_chord: float = 0.2,
    is_major: None | bool = None,
    frac: float = 0.35,
    n_components: int = 2,
    n_clusters: int = 4,
    output_dir: Path = OUTPUT_FIGURES_DIR,
    outlier_percentile: float = 85.0
) -> Path:    
    chord_groups, eval_years, development_matrix, chords = find_trend_groupings_fpca(
        min_year=min_year, max_year=max_year, 
        timeline_resolution=timeline_resolution, 
        min_percentage_of_arias_with_chord=min_percentage_of_arias_with_chord, 
        is_major=is_major, frac=frac, 
        n_components=n_components, n_clusters=n_clusters,
        outlier_percentile=outlier_percentile
    )

    # dynamic grid (e.g. 2x2 for 4 clusters)
    nrows = int(np.ceil(n_clusters / 2))
    ncols = 2 if n_clusters > 1 else 1
    
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(14, 4 * nrows), sharex=True, sharey=True)
    axes = np.array(axes).flatten() # flatten to handle 1D or 2D

    # color palette
    colors = ["#e7298a", "#d95f02", "#7570b3", "#1f4e79"]

    # map chord names to their row index in the development matrix
    chord_to_row_idx = {name: idx for idx, name in enumerate(chords)}

    mode_label = "all keys" if is_major is None else ("major keys only" if is_major else "minor keys only")

    for iter, (cluster_id, cluster_chords) in enumerate(chord_groups.items()):
        ax = axes[cluster_id]
        color = colors[cluster_id % len(colors)]
        
        if not cluster_chords:
            ax.set_title(f"Cluster {cluster_id + 1}: Empty")
            continue
            
        # get the normalized rows for just the chords in this cluster
        cluster_row_indices = [chord_to_row_idx[name] for name in cluster_chords]
        cluster_curves = development_matrix[cluster_row_indices]
        
        # plot individual faint lines for each chord in the cluster
        for i, chord_name in enumerate(cluster_chords):
            ax.plot(
                eval_years, 
                cluster_curves[i], 
                color=color, 
                alpha=0.25, 
                linewidth=1,
                label="Individual Chord Trend" if i == 0 else ""
            )
            
        # calculate and plot the average master trend for all clusters except the last one (outliers)
        if iter < len(chord_groups) - 1:
            cluster_mean_profile = np.mean(cluster_curves, axis=0)
            ax.plot(
                eval_years, 
                cluster_mean_profile, 
                color=color, 
                linewidth=3.5, 
                label="Cluster Center Trend"
            )
        
        # subplot details
        ax.set_title(f"Cluster {cluster_id + 1} ({len(cluster_chords)} Chords)", fontsize=11, fontweight='bold')
        ax.grid(True, axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlim(min_year, max_year)
        
        # display sample chords
        sample_size = min(5, len(cluster_chords))
        sample_string = ", ".join(cluster_chords[:sample_size]) + ("..." if len(cluster_chords) > sample_size else "")
        ax.legend(title=f"Sample: {sample_string}", loc="upper right", fontsize=8, frameon=True, facecolor="white", edgecolor="none")

    # label shared structural axes
    for col in range(ncols):
        axes[-(col+1)].set_xlabel("Year")
    for row in range(nrows):
        axes[row * ncols].set_ylabel("Standardized Frequency (Z-Score)")

    fig.suptitle(f"FPCA Historical Trend Groupings ({mode_label})", fontsize=14, fontweight="bold", y=0.98)
    
    fig.text(
        0.5,
        0.01,
        f"LOESS frac: {frac} | Normalization: Z-Score (Shape Matching Only) | Min Presence: {min_percentage_of_arias_with_chord*100}%",
        ha="center",
        fontsize=9,
        style="italic",
    )

    # clean up unused panels if n_clusters is an odd number
    for j in range(n_clusters, len(axes)):
        fig.delaxes(axes[j])

    # save fig
    output_path = output_dir / f"fpca_clusters_{mode_label.replace(' ', '_')}.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path

if __name__ == "__main__":
    draw_fpca_clusters_timeline(
        min_year=1700,
        max_year=1820,
        min_percentage_of_arias_with_chord=0.1,
        n_clusters=4,
        frac=0.35,
        is_major=True,
        outlier_percentile=75.0
    )