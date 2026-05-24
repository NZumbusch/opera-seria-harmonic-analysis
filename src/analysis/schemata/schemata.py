

from pydantic import BaseModel



class SchemaSection (BaseModel):
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
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=4)
        ]
    ),
    "FONTE": SchemaDefinition(
        name="Fonte", 
        sections=[
            SchemaSection(bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
            SchemaSection(bass_major=11, bass_minor=11, soprano_major=5, soprano_minor=5),
            SchemaSection(bass_major=0, bass_minor=0, soprano_major=4, soprano_minor=3),
        ]
    )
}



