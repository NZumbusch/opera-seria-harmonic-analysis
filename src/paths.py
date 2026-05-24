from __future__ import annotations
import os
from pathlib import Path
from typing import Literal

_MARKERS = ("pyproject.toml", ".git")

def find_project_root(start: Path | None = None) -> Path:
    env_root = os.environ.get("PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if any((candidate / marker).exists() for marker in _MARKERS):
            return candidate

    raise RuntimeError("Could not find project root.")

PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "output"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
SRC_DIR = PROJECT_ROOT / "src"

MS3_ANALYSIS_DIR = INTERIM_DIR / "ms3-analysis"
MS3_LABELS_DIR = MS3_ANALYSIS_DIR / "labels"
MS3_EXPANDED_DIR = MS3_ANALYSIS_DIR / "expanded"
MS3_MEASURES_DIR = MS3_ANALYSIS_DIR / "measures"
MS3_NOTES_DIR = MS3_ANALYSIS_DIR / "notes"

NOTES_GROUPED_DIR = INTERIM_DIR / "notes-grouped"
def get_aria_analysis_path ( aria_file_name: str, type: Literal["labels", "expanded", "measures", "notes", "notes-grouped"] = "labels" ):
    cleaned = Path(aria_file_name).name.replace(".mscx", "")
    match type:
        case "labels":
            return MS3_LABELS_DIR / (cleaned + ".labels.tsv")
        case "expanded":
            return MS3_EXPANDED_DIR / (cleaned + ".harmonies.tsv")
        case "measures":
            return MS3_MEASURES_DIR / (cleaned + ".measures.tsv")
        case "notes":
            return MS3_NOTES_DIR / (cleaned + ".notes.tsv")
        case "notes-grouped":
            return NOTES_GROUPED_DIR / (cleaned + ".tsv")




# raw
MSCX_FOLDER_DIR = RAW_DIR / "musescore" / "didone"
EMOTION_TABLE_PATH = RAW_DIR / "Passions.xlsx"

# intermediate
ANALYSIS_OUT_DIR = INTERIM_DIR / "ms3-analysis"
ARIA_INDEX_PATH = INTERIM_DIR / "aria_index.jsonl"
ARIA_PERIOD_MAP_PATH = INTERIM_DIR / "aria_period_map.jsonl"
BASIC_PASSION_OF_ARIA_MAP_PATH = INTERIM_DIR / "basic_passion_of_aria_map.json"
ARIA_CHORD_LOOKUP_DIR = INTERIM_DIR / "aria-chord-lookup"

# Visualizations
OUTPUT_FIGURES_DIR = OUTPUT_DIR / "figures"
OUTPUT_FIGURES_INTERACTIVE_DIR = OUTPUT_FIGURES_DIR / "interactive"
OUTPUT_TABLES_DIR = OUTPUT_DIR / "tables"
