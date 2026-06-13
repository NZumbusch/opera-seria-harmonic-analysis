from src.analysis.schemata.skipgrams import Skipgram
from src.analysis.schemata.pre_process import ContrapuntalPair
from pydantic import BaseModel


class SchemaSection(BaseModel):
    soprano_major: int
    soprano_minor: int
    bass_major: int
    bass_minor: int


class SchemaDefinition(BaseModel):
    name: str
    sections: list[SchemaSection]


SCHEMA_LIBRARY = {
    "PRINNER": SchemaDefinition(
        name="Prinner",
        sections=[
            SchemaSection(bass_major=5, bass_minor=5, soprano_major=9, soprano_minor=8),
            SchemaSection(bass_major=4, bass_minor=3, soprano_major=7, soprano_minor=7),
            SchemaSection(bass_major=2, bass_minor=2, soprano_major=5, soprano_minor=5),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=4),
        ],
    ),
    "FONTE": SchemaDefinition(
        name="Fonte",
        sections=[
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
        ],
    ),
    "ROMENESCA": SchemaDefinition(
        name="Romenesca",
        sections=[
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=0, soprano_minor=0),
            SchemaSection(
                bass_major=11, bass_minor=10, soprano_major=7, soprano_minor=7
            ),
            SchemaSection(bass_major=9, bass_minor=8, soprano_major=0, soprano_minor=0),
            SchemaSection(bass_major=4, bass_minor=3, soprano_major=0, soprano_minor=0),
        ],
    ),
    "DOREMI": SchemaDefinition(
        name="Do-Re-Mi",
        sections=[
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=0, soprano_minor=0),
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=2, soprano_minor=2
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
        ],
    ),
    "MONTE": SchemaDefinition(
        name="Monte",
        sections=[
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(
                bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3
            ),  # should it go to major or minor?
        ],
    ),
    "MEYER": SchemaDefinition(
        name="Meyer",
        sections=[
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=0, soprano_minor=0),
            SchemaSection(
                bass_major=2, bass_minor=2, soprano_major=11, soprano_minor=11
            ),
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
        ],
    ),
    "QUIESCENZA": SchemaDefinition(
        name="Quiescenza",
        sections=[
            SchemaSection(
                bass_major=0, bass_minor=0, soprano_major=10, soprano_minor=10
            ),  # what is this in minor?
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=9, soprano_minor=9),
            SchemaSection(
                bass_major=0, bass_minor=0, soprano_major=11, soprano_minor=11
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=0, soprano_minor=0),
        ],
    ),
    "FENAROLI": SchemaDefinition(
        name="Fenaroli",
        sections=[
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
            SchemaSection(
                bass_major=2, bass_minor=2, soprano_major=11, soprano_minor=11
            ),
            SchemaSection(bass_major=4, bass_minor=3, soprano_major=0, soprano_minor=0),
        ],
    ),
    "SOLFAMI": SchemaDefinition(
        name="Sol-Fa-Mi",
        sections=[
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=7, soprano_minor=7),
            SchemaSection(bass_major=2, bass_minor=2, soprano_major=5, soprano_minor=5),
            SchemaSection(
                bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5
            ),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
        ],
    ),
}




class SchemaMatch(BaseModel):
    name: str
    start_time: float
    end_time: float
    schema_definition: list[ContrapuntalPair]

def match_schema_to_skipgram (skipgram: list[ContrapuntalPair]) -> SchemaMatch | None:
    for _, schema in SCHEMA_LIBRARY.items():
            if len(skipgram) != len(schema.sections):
                continue

            is_match = True
            for i, pair in enumerate(skipgram):
                t_bass = (
                    schema.sections[i].bass_minor
                    if pair.is_minor
                    else schema.sections[i].bass_major
                )
                t_sop = (
                    schema.sections[i].soprano_minor
                    if pair.is_minor
                    else schema.sections[i].soprano_major
                )
                if pair.bass_sd != t_bass or pair.soprano_sd != t_sop:
                    is_match = False
                    break

            if is_match:
                # context dependant matching
                if schema.name in ["Monte", "Fonte"] and len(skipgram) >= 3:
                    bass_start_midi = skipgram[0].bass.midi
                    bass_sequence_midi = skipgram[2].bass.midi
                    midi_delta = bass_sequence_midi - bass_start_midi

                    if schema.name == "Monte" and midi_delta <= 0:
                        continue
                    if schema.name == "Fonte" and midi_delta >= 0:
                        continue

                return SchemaMatch(name=schema.name, start_time=skipgram[0].onset_time, end_time=skipgram[-1].center_time, schema_definition=skipgram )
    return None