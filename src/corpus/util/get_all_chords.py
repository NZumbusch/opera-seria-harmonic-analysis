import pandas as pd
from src.analysis.util import create_or_get_aria_chord_lookup
from src.corpus.build_aria_index import create_or_load_aria_index
from collections import Counter

def find_all_chords(
    top_n: int = 10,
    is_major: bool | None = None,
    min_year: int = 1700,
    max_year: int = 1820,
):
    """
    Find all used chords and their individual counts.
    """

    lookup = create_or_get_aria_chord_lookup(
        min_year=min_year, max_year=max_year, hide_lookup_info=True
    )

    chord_counts: Counter = Counter()

    for _, aria_data in lookup.items():
        if is_major is True and aria_data.mode != "major":
            continue
        elif is_major is False and aria_data.mode != "minor":
            continue

        chord_counts += aria_data.counts;

    print(f"\nTop {len(chord_counts)} chords found.:")
    print("-" * 80)
    for chord, count in chord_counts.most_common(top_n):
        print(f"Chord: {chord}, occurred {count} times.")



if __name__ == "__main__":
    # Example usage
    find_all_chords(top_n=200)
