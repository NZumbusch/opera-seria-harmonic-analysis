from collections import Counter
import csv
from pathlib import Path
from typing import Iterator

from src.corpus.build_aria_index import create_or_load_aria_index

from src.analysis.schemata.schemata import SCHEMA_LIBRARY
from paths import NOTES_GROUPED_DIR

from src.analysis.schemata.pre_process import ContrapuntalPair, get_aria_outer_voice_pairs_fuzzy
from tqdm import tqdm

from src.analysis.schemata.skipgrams import PathNode, Skipgram, skipgram



PRINNER_MAJOR_TEMPLATE = [
    {"bass_sd": 5, "sop_sd": 9},
    {"bass_sd": 4, "sop_sd": 7},
    {"bass_sd": 2, "sop_sd": 5},
    {"bass_sd": 0, "sop_sd": 4}
]

PRINNER_MINOR_TEMPLATE = [
    {"bass_sd": 5, "sop_sd": 8},
    {"bass_sd": 3, "sop_sd": 7},
    {"bass_sd": 2, "sop_sd": 5},
    {"bass_sd": 0, "sop_sd": 3}
]



def to_scale_degree_vector(pair: ContrapuntalPair, key_tonic: int) -> dict:
    """
    Maps absolute MIDI to scale degrees relative to a tonic.
    """
    bass_sd = (pair.bass.midi - key_tonic) % 12
    sop_sd = (pair.soprano.midi - key_tonic) % 12
    
    return {"bass_sd": bass_sd, "sop_sd": sop_sd, "harm_int": (sop_sd - bass_sd) % 12}

# Parameter functions
def cost_function (g1: ContrapuntalPair, g2: ContrapuntalPair) -> float:
    return max(0.0, g2.center_time - g1.center_time)

def cost_function_relative (g1: ContrapuntalPair, g2: ContrapuntalPair, k: float) -> float:
    distance = abs(g2.center_time - g1.center_time)
    return 0 if distance <= k else k + 1

def predicate_schemata(node: PathNode[ContrapuntalPair]) -> bool:
    path = node.to_list()
    # prune if longer than longest schema
    max_len = max(len(s.sections) for s in SCHEMA_LIBRARY.values())
    if len(path) > max_len:
        return False
    
    # check if the path so far is a valid prefix for ANY schema
    for schema in SCHEMA_LIBRARY.values():
        is_match = True
        for i, pair in enumerate(path):
            # select correct degrees based on major/minor
            target_bass = schema.sections[i].bass_minor if pair.is_minor else schema.sections[i].bass_major
            target_sop = schema.sections[i].soprano_minor if pair.is_minor else schema.sections[i].soprano_major
            
            if pair.bass_sd != target_bass or pair.sop_sd != target_sop:
                is_match = False
                break

        # found at least one correct schema
        if is_match:
            return True
            
    return False


def find_schemata (file_name: str, max_sync_distance:int=2, combinations_per_schema: int = 4, max_schema_time_skip: float = 12.0):
    output_path = NOTES_GROUPED_DIR / (str(Path(file_name).stem) + ".tsv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pair_stream = get_aria_outer_voice_pairs_fuzzy(file_name, max_sync_distance=max_sync_distance)

    schemata: Iterator[Skipgram[ContrapuntalPair]] = skipgram(
        input=pair_stream,
        k=max_schema_time_skip,
        n=combinations_per_schema,
        c=lambda a, b: cost_function_relative(a, b, k=max_schema_time_skip),
        p=predicate_schemata
    )

    for schema in tqdm(schemata, desc="Extracting Schemata"):     
        # find schemata
        for name, defn in SCHEMA_LIBRARY.items():
            if len(schema.contents) != len(defn.sections):
                continue
            
            is_match = True
            for i, pair in enumerate(schema.contents):
                t_bass = defn.sections[i].bass_minor if pair.is_minor else defn.sections[i].bass_major
                t_sop = defn.sections[i].soprano_minor if pair.is_minor else defn.sections[i].soprano_major
                if pair.bass_sd != t_bass or pair.sop_sd != t_sop:
                    is_match = False
                    break
            
            if is_match:
                print(f"Found schema {defn.name} between quarter beat number { schema.contents[0].onset_time } to quarter beat number { schema.contents[-1].onset_time + schema.contents[-1].center_time }")
                break

    



if __name__ == "__main__":
    aria_index = create_or_load_aria_index()

    for aria in tqdm(aria_index):
        if not aria.file_name: continue
        find_schemata(aria.file_name)