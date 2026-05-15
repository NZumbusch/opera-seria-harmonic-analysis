from collections import Counter
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel
from tqdm import tqdm

from src.corpus.build_aria_index import create_or_load_aria_index
import pandas as pd

from src.paths import get_aria_analysis_path


def get_aria_mode_from_tsv(aria_file_name: str) -> str | None:
    path = get_aria_analysis_path(aria_file_name, "expanded")
    if not path.is_file():
        return None

    df = pd.read_csv(path, sep="\t")
    if "globalkey_is_minor" not in df.columns:
        return None

    values = df["globalkey_is_minor"].dropna()
    if values.empty:
        return None

    first_value = int(values.iloc[0])
    if first_value == 0:
        return "major"
    if first_value == 1:
        return "minor"
    return None







class CachedAriaChordData(BaseModel):
    year: int
    mode: str | None
    counts: Counter[str]

def get_aria_chord_count_lookup(
    min_year: int = 1700,
    max_year: int = 1850,
) -> dict[int, CachedAriaChordData]:
    aria_index = create_or_load_aria_index()

    lookup: dict[int, CachedAriaChordData] = {}
    skipped_files: list[Path] = []

    valid_arias = [
        aria for aria in aria_index
        if aria.year is not None
        and aria.id is not None
        and aria.file_name is not None
        and min_year <= aria.year <= max_year
    ]

    for aria in tqdm(valid_arias, desc="Building aria chord lookup"):
        assert aria.year is not None
        assert aria.id is not None
        assert aria.file_name is not None

        path = get_aria_analysis_path(aria.file_name, "expanded")
        if not path.is_file():
            skipped_files.append(path)
            continue

        mode = get_aria_mode_from_tsv(aria.file_name)

        df = pd.read_csv(path, sep="\t", usecols=["chord"])
        counts: Counter[str] = Counter(df["chord"].dropna())

        lookup[aria.id] = CachedAriaChordData(
            year=aria.year, 
            mode=mode,
            counts=counts
        )

    if skipped_files:
        print(f"Skipped the following {len(skipped_files)} files:")
        for file in skipped_files:
            print(f"\t{file}")

    return lookup