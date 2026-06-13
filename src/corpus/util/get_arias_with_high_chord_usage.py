from corpus.util.util import parse_roman_chord
import pandas as pd
from src.analysis.util import create_or_get_aria_chord_lookup
from src.corpus.build_aria_index import create_or_load_aria_index
from src.paths import get_aria_analysis_path


def get_arias_with_high_chord_usage(
    chord_group: list[str],
    group_by_parts: list[str] | None = None,
    top_n: int = 10,
    is_major: bool | None = None,
    min_year: int = 1700,
    max_year: int = 1820,
):
    """
    Find arias with the highest usage of a specific chord group.
    
    Parameters:
    - chord_group: List of target chords (e.g., ["iii7"]).
    - group_by_parts: If None, matches exact strings. If a list (e.g., ["numeral", "form"]), 
      matches any chord sharing those specific parsed parts with the targets.
    """
    aria_index = create_or_load_aria_index(hide_lookup_info=True)
    aria_map = {aria.id: aria for aria in aria_index if aria.id is not None}

    lookup = create_or_get_aria_chord_lookup(
        min_year=min_year, max_year=max_year, hide_lookup_info=True
    )

    parsed_targets = []
    if group_by_parts:
        for t in chord_group:
            parsed = parse_roman_chord(t)
            parsed_targets.append({k: parsed[k] for k in group_by_parts})

    results = []
    for aria_id, aria_data in lookup.items():
        if is_major is True and aria_data.mode != "major":
            continue
        elif is_major is False and aria_data.mode != "minor":
            continue

        total_chords = aria_data.total
        if total_chords == 0:
            continue

        matched_chords_in_aria = set()
        group_count = 0
        if not group_by_parts:
            matched_chords_in_aria = set(chord_group) & set(aria_data.counts.keys())
            group_count = sum(aria_data.counts[c] for c in matched_chords_in_aria)
        else:
            for chord_str, count in aria_data.counts.items():
                parsed_chord = parse_roman_chord(chord_str)
                
                for pt in parsed_targets:
                    if all(parsed_chord[k] == pt[k] for k in group_by_parts):
                        matched_chords_in_aria.add(chord_str)
                        group_count += count
                        break
        percentage = (group_count / total_chords) * 100

        if percentage > 0:
            results.append(
                {
                    "aria_id": aria_id,
                    "percentage": percentage,
                    "total_chords": total_chords,
                    "group_count": group_count,
                    "year": aria_data.year,
                    "matched_chords": matched_chords_in_aria,
                }
            )

    # Sort and take top n
    results.sort(key=lambda x: x["percentage"], reverse=True)
    top_results = results[:top_n]

    match_mode_str = f"parts {group_by_parts}" if group_by_parts else "exact strings"
    print(f"\nTop {len(top_results)} arias with highest usage of {chord_group} (matching by {match_mode_str}):")
    print("-" * 80)

    for res in top_results:
        aria = aria_map.get(res["aria_id"])
        if not aria:
            continue

        print(f"Aria: {aria.aria} ({aria.incipit})")
        print(f"Composer: {aria.composer} | Year: {aria.year} | Opera: {aria.opera}")
        print(f"Usage: {res['percentage']:.2f}% ({res['group_count']}/{res['total_chords']} chords)")

        # Find occurrences
        if aria.file_name is None: 
            continue
        path = get_aria_analysis_path(aria.file_name, "expanded")
        if path.is_file():
            df = pd.read_csv(path, sep="\t")
            
            matches = df[df["chord"].isin(res["matched_chords"])]
            unique_pairs = matches[['mc', 'chord']].drop_duplicates().sort_values(by='mc')
            formatted_measures = [f"{row['mc']} ({row['chord']})" for _, row in unique_pairs.iterrows()]
            
            if len(formatted_measures) > 20:
                measures_str = ", ".join(formatted_measures[:20]) + "..."
            else:
                measures_str = ", ".join(formatted_measures)
            
            print(f"Occurs in measures (mc): {measures_str}")
        else:
            print("Could not find harmony TSV to extract measures.")
        
        print("-" * 80)

if __name__ == "__main__":
    # Example usage
    get_arias_with_high_chord_usage(
        chord_group=["viio7"], 
        group_by_parts=["numeral", "form"], 
        top_n=5
    )
