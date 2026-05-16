from typing import TypedDict

from tqdm import tqdm
from src.analysis.types import ChordStat
from src.paths import get_aria_analysis_path
from src.corpus.load_emotion_table import get_arias_by_basic_passion
from collections import Counter, defaultdict
import pandas as pd
from pathlib import Path


def count_chords(tsv_path: str | Path) -> dict[str, int]:
    df = pd.read_csv(tsv_path, sep="\t")
    return dict(Counter(df["chord"].dropna()))



def get_chord_distribution_by_emotion () -> dict[str, dict[str, int]]:
    arias_by_emotion = get_arias_by_basic_passion()

    skipped_files = []
    chord_distributions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for emotion, arias in tqdm(arias_by_emotion.items(), desc="Emotions"):
        tsv_file_paths = [ get_aria_analysis_path(aria.file_name, "expanded") for aria in arias if aria.file_name is not None]
        
        # count chords
        total = Counter()
        for path in tqdm(tsv_file_paths, desc=f"Reading {emotion} files", leave=False):
            if not path.is_file():
                skipped_files.append(path)
                continue

            df = pd.read_csv(path, sep="\t")
            total.update(df["chord"].dropna())
        
        # set chord distribution
        for chord, count in total.items():
            chord_distributions[emotion][chord] = count
        
    if len(skipped_files) > 0:
        print(f"Skipped the following { len(skipped_files) } files:")

        for file in skipped_files:
            print(f"\t{file}")

    return chord_distributions
        

def global_top_n_chords(
    chord_distributions: dict[str, dict[str, int]], n: int = 15
) -> list[str]:
    total_counts = Counter()
    for counts in chord_distributions.values():
        total_counts.update(counts)
    return [chord for chord, _ in total_counts.most_common(n)]    


    


