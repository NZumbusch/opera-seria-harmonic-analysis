import csv
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

from src.analysis.schemata.pre_process import (
    ContrapuntalPair,
    get_aria_outer_voice_pairs_fuzzy,
)
from src.analysis.schemata.schemata import SCHEMA_LIBRARY, SchemaMatch, match_schema_to_skipgram
from src.analysis.schemata.skipgrams import PathNode, Skipgram, skipgram
from src.analysis.util import INT_TO_NOTE
from src.corpus.build_aria_index import create_or_load_aria_index
from src.paths import get_aria_analysis_path


def to_scale_degree_vector(pair: ContrapuntalPair, key_tonic: int) -> dict:
    """
    Maps absolute MIDI to scale degrees relative to a tonic.
    """
    bass_sd = (pair.bass.midi - key_tonic) % 12
    sop_sd = (pair.soprano.midi - key_tonic) % 12

    return {"bass_sd": bass_sd, "sop_sd": sop_sd, "harm_int": (sop_sd - bass_sd) % 12}


# Parameter functions
def cost_function_relative(
    g1: ContrapuntalPair, g2: ContrapuntalPair, k: float
) -> float:
    # filter out non sequential pairs
    if (g1.soprano.onset > g2.bass.onset or g1.bass.onset > g2.soprano.onset):
        return k + 1
    
    distance = abs(g2.center_time - g1.center_time)
        
    return 0 if distance <= k else k + 1


def predicate_schemata(node: PathNode[ContrapuntalPair]) -> bool:
    path = node.to_list()

    max_len = max(len(s.sections) for s in SCHEMA_LIBRARY.values())
    if len(path) > max_len:
        return False

    # check if the path so far is a valid prefix for ANY schema
    for schema in SCHEMA_LIBRARY.values():
        if len(path) > len(schema.sections):
            continue

        is_match = True
        for i, pair in enumerate(path):
            target_bass = (
                schema.sections[i].bass_minor
                if pair.is_minor
                else schema.sections[i].bass_major
            )
            target_sop = (
                schema.sections[i].soprano_minor
                if pair.is_minor
                else schema.sections[i].soprano_major
            )

            if pair.bass_sd != target_bass or pair.soprano_sd != target_sop:
                is_match = False
                break

        # found at least one correct schema
        if is_match:
            return True

    return False


def stream_deduplicate_pairs(
    pair_stream: Iterator[ContrapuntalPair],
) -> Iterator[ContrapuntalPair]:
    """Filters out duplicate pairs at the same exact time slice footprint."""
    seen = set()
    current_onset = None

    for pair in pair_stream:
        # Clear cache when the bass timeline moves forward
        if pair.bass.onset != current_onset:
            current_onset = pair.bass.onset
            seen.clear()

        # Unique signature of the structural connection
        key = (pair.bass.midi, pair.soprano.onset, pair.soprano.midi)
        if key not in seen:
            seen.add(key)
            yield pair

def stream_deduplicate_matches(
    match_stream: Iterator[SchemaMatch], time_tolerance: float = 2.0, max_skip: float = 4.0
) -> Iterator[SchemaMatch]:
    """
    Deduplicates schema micro-variations by dropping incoming matches if they
    share the SAME name AND either a similar start_time OR a similar end_time.
    """
    active_buffer: list[SchemaMatch] = []
    recently_emitted: list[SchemaMatch] = []

    for new_match in match_stream:
        current_time = new_match.end_time

        flush_threshold = current_time - max_skip - time_tolerance
        active_buffer.sort(key=lambda x: x.start_time)

        flushed = [item for item in active_buffer if item.end_time < flush_threshold]
        active_buffer = [
            item for item in active_buffer if item.end_time >= flush_threshold
        ]

        for item in flushed:
            yield item
            recently_emitted.append(item)

        history_threshold = current_time - (max_skip * 2) - time_tolerance
        recently_emitted = [
            item for item in recently_emitted if item.end_time >= history_threshold
        ]

        # Duplicate Evaluation
        is_duplicate = False
        for item in active_buffer + recently_emitted:
            if item.name == new_match.name:
                start_close = (
                    abs(item.start_time - new_match.start_time) <= time_tolerance
                )
                end_close = (
                    abs(item.end_time - new_match.end_time) <= time_tolerance
                )

                if start_close or end_close:
                    is_duplicate = True
                    break

        if not is_duplicate:
            active_buffer.append(new_match)

    active_buffer.sort(key=lambda x: x.start_time)
    for item in active_buffer:
        yield item



def match_schemata_lazy(
    skipgram_stream: Iterator[Skipgram[ContrapuntalPair]],
) -> Iterator[SchemaMatch]:
    """Identifies musical schemata from raw skipgrams lazily."""
    for skipgram in skipgram_stream:
        r = match_schema_to_skipgram(skipgram.contents)

        if (r): yield r
        else: continue # no schemata found


def find_schemata(
    file_name: str,
    max_sync_distance: int = 2,
    max_schema_time_skip: float = 4.0,
    print_schemata=False,
):
    output_path = get_aria_analysis_path(file_name, "schemata")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pair_stream: Iterator[ContrapuntalPair] = get_aria_outer_voice_pairs_fuzzy(
        file_name, max_sync_distance=max_sync_distance
    )
    clean_pair_stream = stream_deduplicate_pairs(pair_stream)

    raw_skipgrams: Iterator[Skipgram[ContrapuntalPair]] = skipgram(
        input=clean_pair_stream,
        k=max_schema_time_skip,
        n=max([len(schema.sections) for schema in SCHEMA_LIBRARY.values()]),
        er=lambda s: match_schema_to_skipgram(s) is not None,
        c=lambda a, b: cost_function_relative(a, b, k=max_schema_time_skip),
        p=predicate_schemata,
    )

    raw_matches = match_schemata_lazy(raw_skipgrams)

    final_schemata_stream = stream_deduplicate_matches(
        raw_matches, time_tolerance=2.0, max_skip=max_schema_time_skip
    )

    max_slots = max([len(schema[1].sections) for schema in SCHEMA_LIBRARY.items()])
    with open(output_path, mode="w", newline="", encoding="utf-8") as tsv_file:
        writer = csv.writer(tsv_file, delimiter="\t")

        header = ["schema_name"]
        for i in range(1, max_slots + 1):
            header.extend(
                [
                    f"stage_{i}_bass_onset",
                    f"stage_{i}_bass_sd",
                    f"stage_{i}_bass_name",
                    f"stage_{i}_soprano_onset",
                    f"stage_{i}_sop_sd",
                    f"stage_{i}_sop_name",
                ]
            )
        writer.writerow(header)

        for match in final_schemata_stream:
            schema: list[ContrapuntalPair] = match.schema_definition
            row = [match.name]

            for i in range(max_slots):
                if i < len(schema):
                    stage = schema[i]

                    bass_note_name = INT_TO_NOTE[stage.bass.midi % 12]
                    sop_note_name = INT_TO_NOTE[stage.soprano.midi % 12]

                    row.extend(
                        [
                            str(stage.bass.onset),
                            str(stage.bass_sd),
                            bass_note_name,
                            str(stage.soprano.onset),
                            str(stage.soprano_sd),
                            sop_note_name,
                        ]
                    )
                else:
                    row.extend(["", "", "", "", "", ""])

            writer.writerow(row)

            if print_schemata:
                schema_string = " -> ".join(
                    [
                        f"{stage.bass_sd} ({stage.bass.onset})-{stage.soprano_sd}({stage.soprano.onset})"
                        for stage in schema
                    ]
                )
                print(
                    f"[{Path(file_name).stem}] Found {match.name} ({match.start_time} to {match.end_time}): {schema_string}"
                )


if __name__ == "__main__":
    aria_index = create_or_load_aria_index()

    for aria in tqdm(aria_index):
        if not aria.file_name:
            continue

        try:
            if not get_aria_analysis_path(aria.file_name, "schemata").is_file():
                find_schemata(aria.file_name)
        except FileNotFoundError:
            print(f"Found no file for aria {aria.file_name}. Skipping it.")
