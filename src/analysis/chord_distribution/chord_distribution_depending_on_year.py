from collections import Counter, defaultdict
import math

from src.analysis.util import get_aria_mode_from_tsv

from src.corpus.build_period_map import create_or_get_period_map
from src.corpus.build_aria_index import create_or_load_aria_index
from paths import get_aria_analysis_path
from tqdm import tqdm
import pandas as pd


def chunk_list(seq, n_chunks):
    chunk_size = math.ceil(len(seq) / n_chunks)
    return [seq[i:i + chunk_size] for i in range(0, len(seq), chunk_size)]


def get_chord_distribution_by_year (bin_size: int = 10) -> dict[str, dict[str, int]]:
    aria_index = create_or_load_aria_index()

    years = [aria.year for aria in aria_index if aria.year is not None]
    if not years:
        return {}
    min_year = min(years)

    skipped_files = []
    chord_distributions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for aria in tqdm(aria_index, desc="Arias by year bin"):
        if not aria.file_name or not aria.year: continue

        year = aria.year
        bin_start = min_year + ((year - min_year) // bin_size) * bin_size
        bin_end = bin_start + bin_size - 1
        year_bin = f"{bin_start}-{bin_end}"
        
        path = get_aria_analysis_path(aria.file_name, "expanded")
        if not path.is_file():
            skipped_files.append(path)
            continue

        df = pd.read_csv(path, sep="\t")
        counts = Counter(df["chord"].dropna())

        for chord, count in counts.items():
            chord_distributions[year_bin][chord] += count

    if skipped_files:
        print(f"Skipped the following {len(skipped_files)} files:")
        for file in skipped_files:
            print(f"\t{file}")

    return chord_distributions



def get_chord_distribution_by_year_periods(is_major: bool | None = None) -> dict[str, dict[str, int]]:
    period_map = create_or_get_period_map()
    if not period_map:
        return {}

    skipped_files = []
    chord_distributions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for label, arias in tqdm(period_map.items(), desc="Year periods"):
        total = Counter()

        for aria in arias:
            if not aria.file_name: continue

            if is_major is not None:
                mode = get_aria_mode_from_tsv(aria.file_name)
                if mode is None:
                    continue
                if is_major and mode != "major":
                    continue
                if not is_major and mode != "minor":
                    continue

            path = get_aria_analysis_path(aria.file_name, "expanded")
            if not path.is_file():
                skipped_files.append(path)
                continue

            df = pd.read_csv(path, sep="\t")
            total.update(df["chord"].dropna())

        for chord, count in total.items():
            chord_distributions[label][chord] = count

    if skipped_files:
        print(f"Skipped the following {len(skipped_files)} files:")
        for file in skipped_files:
            print(f"\t{file}")

    return chord_distributions




if __name__ == "__main__":
    print(get_chord_distribution_by_year(10))