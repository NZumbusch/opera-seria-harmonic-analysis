from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors


def make_sequential_colors(
    groups: Sequence[str], cmap_name: str = "cividis"
) -> dict[str, str]:
    cmap = plt.get_cmap(cmap_name)
    n = len(groups)

    if n == 1:
        values = [0.5]
    else:
        values = np.linspace(0.12, 0.88, n)

    return {group: mcolors.to_hex(cmap(v)) for group, v in zip(groups, values)}


def get_colors_for_groups(
    groups: Sequence[str], ordered: bool = False
) -> dict[str, str]:
    if ordered:
        return make_sequential_colors(groups, cmap_name="cividis")
    return make_project_colors(groups)


def make_project_colors(groups: Sequence[str]) -> dict[str, str]:
    n = len(groups)

    if n <= len(BASE_PROJECT_COLORS):
        palette = BASE_PROJECT_COLORS[:n]
    else:
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "project_palette", BASE_PROJECT_COLORS
        )
        palette = [mcolors.to_hex(cmap(x)) for x in np.linspace(0, 1, n)]

    return dict(zip(groups, palette))


BASE_PROJECT_COLORS = [
    "#264653",  # deep blue-green
    "#457b9d",  # muted blue
    "#2a9d8f",  # teal
    "#8ab17d",  # soft green
    "#e9c46a",  # muted yellow
    "#f4a261",  # soft orange
    "#d9822b",  # earthy orange
    "#d1495b",  # muted red
]
PERIOD_NUMBER = 8
