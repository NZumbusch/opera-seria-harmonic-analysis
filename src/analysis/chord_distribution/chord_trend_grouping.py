from collections import defaultdict
from collections.abc import Callable

import numpy as np
import numpy.typing as npt
import skfda
from skfda.preprocessing.dim_reduction import FPCA
from sklearn.cluster import KMeans as SklearnKMeans
from tqdm import tqdm

from src.analysis.chord_distribution.chord_usage_timeline_loess import (
    get_chord_group_loess_series,
)
from src.analysis.util import create_or_get_aria_chord_lookup, z_score_normalization


def get_chord_development_matrix(
    min_year: int = 1700,
    max_year: int = 1820,
    timeline_resolution: int = 300,
    min_percentage_of_arias_with_chord: float = 0.2,
    is_major: None | bool = None,
    frac: float = 0.35,
    hide_lookup_info: bool = True,
    normalization_function: Callable[[npt.NDArray], npt.NDArray]
    | None = z_score_normalization,
) -> tuple[list[str], npt.NDArray, npt.NDArray]:
    if min_percentage_of_arias_with_chord < 0 or min_percentage_of_arias_with_chord > 1:
        raise ValueError(
            "min percentage of arias with chords has to be between 0 and 1"
        )

    # look up chords
    chord_lookup = create_or_get_aria_chord_lookup(
        min_year, max_year, hide_lookup_info=hide_lookup_info
    )
    if is_major is True:
        chord_lookup = {
            aria_id: data
            for aria_id, data in chord_lookup.items()
            if data.mode == "major"
        }
    elif is_major is False:
        chord_lookup = {
            aria_id: data
            for aria_id, data in chord_lookup.items()
            if data.mode == "minor"
        }
    if not chord_lookup:
        raise ValueError("No arias matched the filtering criteria.")

    chord_dict: dict[str, int] = defaultdict(int)
    for _, data in chord_lookup.items():
        for chord in data.counts:
            chord_dict[chord] += 1

    # filter out uncommon chords
    min_bar = min_percentage_of_arias_with_chord * len(chord_lookup)
    chords = [chord for chord, freq in chord_dict.items() if freq >= min_bar]

    if not chords:
        raise ValueError("No chords passed the frequency threshold.")

    # build series
    rows: list[npt.NDArray[np.float64]] = []
    eval_years = np.linspace(min_year, max_year, timeline_resolution)

    for chord in tqdm(chords, desc="Generating loess series for all graphs"):
        y = get_chord_group_loess_series(
            [chord],
            timeline_resolution=timeline_resolution,
            is_major=is_major,
            min_year=min_year,
            max_year=max_year,
            frac=frac,
        ).smoothed_y

        # normalization
        if normalization_function:
            y = normalization_function(y)

        rows.append(y)

    matrix = np.vstack(rows)
    return chords, eval_years, matrix


def find_trend_groupings_fpca(
    min_year: int = 1700,
    max_year: int = 1820,
    timeline_resolution: int = 300,
    min_percentage_of_arias_with_chord: float = 0.2,
    is_major: None | bool = None,
    frac: float = 0.35,
    n_components: int = 2,
    n_clusters: int = 4,
    outlier_percentile: float = 85.0,
    normalization_function: Callable[[npt.NDArray], npt.NDArray]
    | None = z_score_normalization,
    outlier_grouping: bool = False,
):
    chords, eval_years, development_matrix = get_chord_development_matrix(
        min_year=min_year,
        max_year=max_year,
        timeline_resolution=timeline_resolution,
        min_percentage_of_arias_with_chord=min_percentage_of_arias_with_chord,
        is_major=is_major,
        frac=frac,
        normalization_function=normalization_function,
    )

    fd = skfda.FDataGrid(data_matrix=development_matrix, grid_points=eval_years)
    fpca = FPCA(n_components=n_components)
    fpca.fit(fd)

    # (n_chords, n_components)
    scores_matrix = fpca.transform(fd)

    chord_groups = {i: [] for i in range(n_clusters)}
    if outlier_grouping:
        # pass 1, initial rough clustering
        initial_kmeans = SklearnKMeans(
            n_clusters=n_clusters - 1, random_state=42, n_init="auto"
        )
        initial_labels = initial_kmeans.fit_predict(scores_matrix)

        # calculate distances to find outlier
        initial_centers = initial_kmeans.cluster_centers_
        distances = np.sqrt(
            np.sum((scores_matrix - initial_centers[initial_labels]) ** 2, axis=1)
        )
        cutoff_distance = np.percentile(distances, outlier_percentile)

        # split outliers out of dataset
        clean_mask = distances <= cutoff_distance
        clean_scores = scores_matrix[clean_mask]
        clean_chords = [c for idx, c in enumerate(chords) if clean_mask[idx]]
        misfit_chords = [c for idx, c in enumerate(chords) if not clean_mask[idx]]

        # rerun k means on dataset without outliers
        final_kmeans = SklearnKMeans(
            n_clusters=n_clusters - 1, random_state=42, n_init="auto"
        )
        final_labels = final_kmeans.fit_predict(clean_scores)

        for name, label in zip(clean_chords, final_labels):
            chord_groups[label].append(name)
        chord_groups[n_clusters - 1] = misfit_chords
    else:
        kmeans = SklearnKMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(scores_matrix)

        for name, label in zip(chords, labels):
            chord_groups[label].append(name)

    print(f"Explained variance ratio by component: {fpca.explained_variance_ratio_}")

    return chord_groups, eval_years, development_matrix, chords


if __name__ == "__main__":
    print(get_chord_development_matrix()[0])
