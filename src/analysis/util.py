from collections import Counter
import json
from pathlib import Path
from typing import TypedDict
import numpy as np
import numpy.typing as npt
from pydantic import BaseModel
from tqdm import tqdm

from src.corpus.build_aria_index import create_or_load_aria_index
import pandas as pd

from src.paths import ARIA_CHORD_LOOKUP_DIR, get_aria_analysis_path


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
    total: int
    counts: Counter[str]

def create_aria_chord_count_lookup(
    min_year: int = 1700,
    max_year: int = 1850,
    hide_lookup_info: bool = True
) -> dict[int, CachedAriaChordData]:
    aria_index = create_or_load_aria_index(hide_lookup_info=True)

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
            counts=counts,
            total=sum(counts.values())
        )

    if skipped_files:
        print(f"Skipped the following {len(skipped_files)} files:")
        for file in skipped_files:
            print(f"\t{file}")

    return lookup



def create_or_get_aria_chord_lookup (min_year: int, max_year: int, hide_lookup_info: bool = True) -> dict[int, CachedAriaChordData]:
    path = ARIA_CHORD_LOOKUP_DIR / f"aria_chord_lookup_{min_year}_{max_year}.json"

    if path.is_file():
        if not hide_lookup_info: print(f"Using saved aria chord lookup file at {path}")
        with open(path, "r") as f:
            return {
                aria_id: CachedAriaChordData(**aria_data)
                for aria_id, aria_data in json.load(f).items()
            }
    else:
        if not hide_lookup_info: print(f"No saved aria chord lookup dir found. Creating new one and saving at {path}")
        lookup = create_aria_chord_count_lookup(min_year=min_year, max_year=max_year, hide_lookup_info=hide_lookup_info)
        
        serializable_lookup = {
            file_name: data.model_dump(mode="json")
            for file_name, data in lookup.items()
        }


        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable_lookup, f, ensure_ascii=False, indent=2)
        
        return lookup
    


def z_score_normalization (y: npt.NDArray, epsilon: float=0) -> npt.NDArray:
    mean = np.mean(y)
    std_dv = np.std(y) + epsilon
    return (y - mean) / (std_dv if std_dv > 0 else 1.0)
    
def percentage_signal_change_normalization (y: npt.NDArray) -> npt.NDArray:
    mean = np.mean(y)
    return (y - mean) / (mean if mean > 0 else 1.0)


def log_scaling (y: npt.NDArray) -> npt.NDArray:
    return np.log(np.clip(y, a_min=0.0, a_max=None))