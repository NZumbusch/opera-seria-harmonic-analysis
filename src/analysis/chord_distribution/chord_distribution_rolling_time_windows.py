from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import TypedDict
import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm

from src.analysis.util import CachedAriaChordData, create_aria_chord_count_lookup, get_aria_mode_from_tsv
from src.corpus.build_aria_index import create_or_load_aria_index
from src.paths import get_aria_analysis_path




class TimeframeChordData(BaseModel):
    n_works: int
    counts: dict[str, int]



def get_chord_distribution_of_year (
        year: int, 
        is_major: bool | None = None
) -> TimeframeChordData:
    lookup: dict[int, CachedAriaChordData] = create_aria_chord_count_lookup(min_year=year, max_year=year)

    chord_counts: dict[str, int] = defaultdict(lambda: 0)
    number = 0

    for aria, data in lookup.items():
        if int(data.year) == year:
            for chord, number in data.counts.items():
                chord_counts[chord] += number
                number += 1
    
    return TimeframeChordData(n_works=number, counts=chord_counts)

            




def get_chord_distribution_by_sliding_window(
    window_size: int = 12,
    step: int = 1,
    is_major: bool | None = None,
    min_year: int = 1700,
    max_year: int = 1850,
) -> dict[str, TimeframeChordData]:
    lookup = create_aria_chord_count_lookup(
        min_year=min_year,
        max_year=max_year,
    )

    if not lookup:
        return {}

    valid_arias = sorted(
        lookup.items(),
        key=lambda item: item[1].year,
    )

    years = [aria_data.year for _, aria_data in valid_arias]
    min_window_year = min(years)
    max_window_year = max(years)

    chord_distributions: dict[str, TimeframeChordData] = {}

    for start_year in tqdm(
        range(min_window_year, max_window_year - window_size + 2, step),
        desc="Sliding windows",
    ):
        end_year = start_year + window_size - 1

        total: Counter[str] = Counter()
        used_arias = 0

        for _, aria_data in valid_arias:
            year = aria_data.year
            mode = aria_data.mode

            if not (start_year <= year <= end_year):
                continue

            if is_major is not None:
                if mode is None:
                    continue
                if is_major and mode != "major":
                    continue
                if not is_major and mode != "minor":
                    continue

            total.update(aria_data.counts)
            used_arias += 1

        if not total:
            continue

        label = f"{start_year}-{end_year}"
        chord_distributions[label] = TimeframeChordData(n_works=used_arias, counts=dict(total))

    return chord_distributions



# NDA konform
def export_public_chord_distribution_windows(
    output_path: Path | None = None,
    window_size: int = 12,
    step: int = 1,
    is_major: bool | None = None,
    top_n: int = 20,
    min_works: int = 12,
    decimals: int = 1,
) -> dict[str, dict[str, float]]:
    raw = get_chord_distribution_by_sliding_window(
        window_size=window_size,
        step=step,
        is_major=is_major,
    )

    global_counts = Counter()
    for window_data in raw.values():
        global_counts.update(window_data.counts)

    top_chords = [chord for chord, _ in global_counts.most_common(top_n)]

    public_data: dict[str, dict[str, float]] = {}

    for window_label, window_data in raw.items():
        n_works = int(window_data.n_works)
        counts = window_data.counts

        if n_works < min_works:
            continue

        total = sum(counts.values())
        if total == 0:
            continue

        row: dict[str, float] = {"n_works": n_works}

        covered = 0
        for chord in top_chords:
            pct = (counts.get(chord, 0) / total) * 100
            row[chord] = round(pct, decimals)
            covered += counts.get(chord, 0)

        other_pct = ((total - covered) / total) * 100
        row["other"] = round(other_pct, decimals)

        public_data[window_label] = row

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "meta": {
                        "window_size": window_size,
                        "step": step,
                        "is_major": is_major,
                        "top_n": top_n,
                        "min_works": min_works,
                        "decimals": decimals,
                    },
                    "windows": public_data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    return public_data



if __name__ == "__main__":
    print(export_public_chord_distribution_windows())