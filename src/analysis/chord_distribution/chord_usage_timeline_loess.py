import numpy as np
from pydantic import BaseModel, ConfigDict
from tqdm import tqdm

from src.analysis.util import create_or_get_aria_chord_lookup


def weighted_loess(x, y, weights, eval_x, frac=0.3):
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
        time_weights = (1 - u**3) ** 3

        # combine time distance tricube weights with aria size weights
        W = time_weights * neighbor_weights

        """ 
        Solve the equation: 
        beta = (X.T * W * X)^-1 * X.T * W * y
        => (X.T * W * X) * beta = X.T * W * y
        """

        # build x for the neighborhood, with (1, year)
        X_matrix[:, 1] = neighbor_x

        # apply weights to X and y
        XW = X_matrix * W[:, np.newaxis]

        # solve system
        try:
            ATA = XW.T @ X_matrix  # reduce to 2x2 fields (X.T * W * X)
            ATy = (
                XW.T @ neighbor_y
            )  # where does it want to go, in 2x2 fields (X.T * W * y)
            beta = np.linalg.solve(ATA, ATy)  # solve lin equation ATA * beta = ATy

            # get smoothened / predicted value
            smoothed_y[i] = beta[0] + beta[1] * x_val
        except np.linalg.LinAlgError:
            # fallback to simple weighted mean if the matrix is singular
            smoothed_y[i] = np.average(neighbor_y, weights=W + 1e-10)
    return smoothed_y


class ChordGroupLoessGraphModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )  # needed to allow np.ndarray

    x: np.ndarray  # years
    y: np.ndarray  # percentages of chord group in arias
    w: np.ndarray  # total number of chords in arias
    eval_years: np.ndarray  # grid
    smoothed_y: np.ndarray


def get_chord_group_loess_series(
    chord_group: list[str],
    timeline_resolution: int = 300,
    frac: float = 0.3,
    is_major: bool | None = None,
    min_year: int = 1720,
    max_year: int = 1800,
) -> ChordGroupLoessGraphModel:
    if len(chord_group) < 1:
        raise ValueError("Chord group cannot be empty.")
    if frac <= 0 or frac > 1:
        raise ValueError("Frac has to be between 0 and 1.")

    raw_years = []
    raw_percentages = []
    raw_weights = []

    for _, aria_data in create_or_get_aria_chord_lookup(
        min_year=min_year,
        max_year=max_year,
    ).items():
        # aria chord lookup should have right years, but still needs mode filtering
        assert min_year <= aria_data.year <= max_year
        if is_major is True and aria_data.mode != "major":
            continue
        elif is_major is False and aria_data.mode != "minor":
            continue

        # calculate chord percentage
        chord_counts = aria_data.counts
        total_chords = sum(chord_counts.values())
        if total_chords == 0:
            continue

        group_count = sum(chord_counts.get(chord, 0) for chord in chord_group)
        chord_pct = (group_count / total_chords) * 100

        raw_years.append(aria_data.year)
        raw_percentages.append(chord_pct)
        raw_weights.append(total_chords)

    if not raw_years:
        raise ValueError("No data matched the filtering criteria.")

    # convert to np array
    x = np.array(raw_years)
    y = np.array(raw_percentages)
    w = np.array(raw_weights)

    # sort by year
    sort_idx = np.argsort(x)
    x, y, w = x[sort_idx], y[sort_idx], w[sort_idx]

    # calculate loess cuve
    eval_years = np.linspace(min_year, max_year, timeline_resolution)
    smoothed_y = weighted_loess(x, y, w, eval_years, frac=frac)

    return ChordGroupLoessGraphModel(
        x=x, y=y, w=w, eval_years=eval_years, smoothed_y=smoothed_y
    )


def get_chord_group_loess_bootstrap_bounds(
    series_data: ChordGroupLoessGraphModel,
    frac: float = 0.3,
    n_bootstrap: int = 200,
    bootstrap_cutoff_percentile: float = 2.5,
) -> dict[str, np.ndarray]:
    x = series_data.x
    y = series_data.y
    w = series_data.w
    eval_years = series_data.eval_years

    if bootstrap_cutoff_percentile > 100 or bootstrap_cutoff_percentile < 0:
        raise ValueError("Bootstrap cutoff percentile has to be between 0 and 100.")
    if frac <= 0 or frac > 1:
        raise ValueError("Frac has to be between 0 and 1.")
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be at least 1.")

    bootstrap_matrix = []
    np.random.seed(42)

    # do the actual bootstrapping
    for _ in tqdm(
        range(n_bootstrap),
        desc="Bootstrapping using weighted random selections and weighted loess",
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

    # clean the results using cutoffs
    bootstrap_array = np.array(bootstrap_matrix)

    lower_bound = np.nanpercentile(
        bootstrap_array,
        bootstrap_cutoff_percentile,
        axis=0,
    )
    upper_bound = np.nanpercentile(
        bootstrap_array,
        100 - bootstrap_cutoff_percentile,
        axis=0,
    )

    return {
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
    }
