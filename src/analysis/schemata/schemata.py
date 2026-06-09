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
