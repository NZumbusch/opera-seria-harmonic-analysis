import csv
import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Hashable

import numpy as np
import numpy.typing as npt
import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm

from src.corpus.build_aria_index import create_or_load_aria_index
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
    min_year: int = 1700, max_year: int = 1850, hide_lookup_info: bool = True
) -> dict[int, CachedAriaChordData]:
    aria_index = create_or_load_aria_index(hide_lookup_info=True)

    lookup: dict[int, CachedAriaChordData] = {}
    skipped_files: list[Path] = []

    valid_arias = [
        aria
        for aria in aria_index
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
            year=aria.year, mode=mode, counts=counts, total=sum(counts.values())
        )

    if skipped_files:
        print(f"Skipped the following {len(skipped_files)} files:")
        for file in skipped_files:
            print(f"\t{file}")

    return lookup


def parse_to_float(value: str) -> float:
    """Converts a string (e.g., '356/2' or '0.5') to a float."""
    if "/" in value:
        numerator, denominator = value.split("/")
        return float(numerator) / float(denominator)
    return float(value)


def get_chord_id_at_quarter_beat(
    file_name: str | Path, quarter_beat: float
) -> Hashable:
    path = get_aria_analysis_path(str(file_name), "expanded")
    if not path.is_file():
        raise ValueError(f"No aria exists at {file_name}")

    df = pd.read_csv(path, sep="\t", usecols=["quarterbeats_all_endings"])
    for idx, row in df.iterrows():
        if parse_to_float(row["quarterbeats_all_endings"]) >= quarter_beat:
            return idx

    return df.index[-1]


def create_or_get_aria_chord_lookup(
    min_year: int, max_year: int, hide_lookup_info: bool = True
) -> dict[int, CachedAriaChordData]:
    path = ARIA_CHORD_LOOKUP_DIR / f"aria_chord_lookup_{min_year}_{max_year}.json"

    if path.is_file():
        if not hide_lookup_info:
            print(f"Using saved aria chord lookup file at {path}")
        with open(path, "r") as f:
            return {
                aria_id: CachedAriaChordData(**aria_data)
                for aria_id, aria_data in json.load(f).items()
            }
    else:
        if not hide_lookup_info:
            print(
                f"No saved aria chord lookup dir found. Creating new one and saving at {path}"
            )
        lookup = create_aria_chord_count_lookup(
            min_year=min_year, max_year=max_year, hide_lookup_info=hide_lookup_info
        )

        serializable_lookup = {
            file_name: data.model_dump(mode="json")
            for file_name, data in lookup.items()
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable_lookup, f, ensure_ascii=False, indent=2)

        return lookup


def z_score_normalization(y: npt.NDArray, epsilon: float = 0) -> npt.NDArray:
    mean = np.mean(y)
    std_dv = np.std(y) + epsilon
    return (y - mean) / (std_dv if std_dv > 0 else 1.0)


def percentage_signal_change_normalization(y: npt.NDArray) -> npt.NDArray:
    mean = np.mean(y)
    return (y - mean) / (mean if mean > 0 else 1.0)


def log_scaling(y: npt.NDArray) -> npt.NDArray:
    return np.log(np.clip(y, a_min=0.0, a_max=None))


PITCH_CLASSES = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}
INT_TO_NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

LOCAL_KEY_MAJOR_OFFSETS = {
    "I": 0,
    "II": 2,
    "III": 4,
    "IV": 5,
    "V": 7,
    "VI": 9,
    "VII": 11,
}
LOCAL_KEY_MINOR_OFFSETS = {
    "I": 0,
    "II": 2,
    "III": 3,
    "IV": 5,
    "V": 7,
    "VI": 8,
    "VII": 10,
}


def get_localkey_midi(global_key: str, is_minor: bool, local_key_numeral: str) -> int:
    """
    Calculates the MIDI pitch class (0-11) of the local key.
    """
    if not local_key_numeral or local_key_numeral.upper() == "I":
        return PITCH_CLASSES.get(global_key.upper(), 0)

    # Parse the optional accidental (b or #) and the Roman numeral
    match = re.match(r"(b|#)?([ivIV]+)", local_key_numeral)
    if not match:
        return PITCH_CLASSES.get(global_key.upper(), 0)

    accidental, numeral = match.groups()
    numeral_upper = numeral.upper()

    # Get the base diatonic offset based on global mode
    offsets = LOCAL_KEY_MINOR_OFFSETS if is_minor else LOCAL_KEY_MAJOR_OFFSETS
    interval = offsets.get(numeral_upper, 0)

    if accidental == "b":
        interval -= 1
    elif accidental == "#":
        interval += 1

    global_midi = PITCH_CLASSES.get(global_key.upper(), 0)
    return (global_midi + interval) % 12


def get_aria_total_duration(file_name: str) -> float:
    measures_path = get_aria_analysis_path(file_name, "measures")
    if not measures_path.exists():
        return 0.0

    with open(measures_path, mode="r", encoding="utf-8") as f:
        # Use DictReader to locate the 'quarterbeats' column
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        if not rows:
            return 0.0

        last_row = rows[-1]
        raw_qb = last_row.get("quarterbeats", "0")

        # Handle fractions like "169/2" or simple floats
        try:
            return float(Fraction(raw_qb)) + float(last_row.get("duration_qb", 0))
        except (ValueError, ZeroDivisionError):
            return 0.0
