import csv
from collections import Counter

def midi_to_intervals(chord_str: str) -> tuple:
    """Converts a comma-separated midi string '60,64,67' to a relative interval tuple (0,4,7)."""
    midis = sorted([int(m) for m in chord_str.split(',')])
    root = midis[0]
    return tuple(m - root for m in midis), root

def schemata_to_halftones(schema_raw: str) -> str:
    """
    Translates raw schemata into the transposition-invariant format:
    Bass interval progression + Relative chord intervals.
    Example output: "Bass:[0, -5, 2] Chords:[(0, 4, 7), (0, 3, 7), (0, 4, 7)]"
    """
    chords = [c.strip() for c in schema_raw.split('|')]
    
    chord_intervals = []
    roots = []
    
    for chord in chords:
        intervals, root = midi_to_intervals(chord)
        chord_intervals.append(intervals)
        roots.append(root)
        
    # Calculate bass progression relative to the first chord's bass note
    base_root = roots[0]
    bass_progression = tuple(r - base_root for r in roots)
    
    # Format the abstract schema
    return f"Bass:{list(bass_progression)} Chords:{chord_intervals}"

def process_and_count(input_file: str, top_n: int = 20):
    schema_counts = Counter()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            raw_seq = row['chord_sequence']
            abstract_schema = schemata_to_halftones(raw_seq)
            schema_counts[abstract_schema] += 1
            
    # Output the top results
    print(f"\n--- Top {top_n} Most Common Schemata ---")
    for schema, count in schema_counts.most_common(top_n):
        print(f"Count: {count:4d} | {schema}")

if __name__ == "__main__":
    process_and_count('raw_schemata.tsv', top_n=20)