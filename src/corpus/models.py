import math
import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class AriaMetaDataModel(BaseModel):
    id: Optional[int] = None
    ismn: Optional[str] = None
    act_scene: Optional[str] = None
    aria: Optional[str] = None
    incipit: Optional[str] = None
    aria_label: Optional[str] = None
    character: Optional[str] = None
    composer: Optional[str] = None
    movement_number: Optional[int] = None
    movement_title: Optional[str] = None
    opera: Optional[str] = None
    original_format: Optional[str] = None
    lyricist: Optional[str] = None
    platform: Optional[str] = None
    source: Optional[str] = None
    source_year: Optional[str] = None
    year: Optional[int] = None
    creation_date: Optional[str] = None
    file_name: Optional[str] = None


class AriaHeaderModel(AriaMetaDataModel):
    id: Optional[int] = None
    ismn: Optional[str] = None
    act_scene: Optional[str] = None
    aria: Optional[str] = None
    aria_label: Optional[str] = None
    character: Optional[str] = None
    composer: Optional[str] = None
    movement_number: Optional[int] = None
    movement_title: Optional[str] = None
    opera: Optional[str] = None
    original_format: Optional[str] = None
    lyricist: Optional[str] = None
    platform: Optional[str] = None
    source: Optional[str] = None
    source_year: Optional[str] = None
    year: Optional[int] = None
    creation_date: Optional[str] = None


class EmotionLabelModel(BaseModel):
    opera: str
    label: str
    aria: str
    basic_passion: str
    passion_a: list[str] = Field(default_factory=list)
    passion_b: list[str] = Field(default_factory=list)
    valence: list[str] = Field(default_factory=list)
    valence_2: list[str] = Field(default_factory=list)
    time: Optional[str] = None
    bonora_a: list[str] = Field(default_factory=list)
    bonora_b: list[str] = Field(default_factory=list)
    zhang_a: list[str] = Field(default_factory=list)
    zhang_b: list[str] = Field(default_factory=list)
    jmd_a: list[str] = Field(default_factory=list)
    jmd_b: list[str] = Field(default_factory=list)

    # convert comma or semicolon seperated strings into lists
    @field_validator(
        "passion_a",
        "passion_b",
        "valence",
        "valence_2",
        "bonora_a",
        "bonora_b",
        "zhang_a",
        "zhang_b",
        "jmd_a",
        "jmd_b",
        mode="before",
    )
    @classmethod
    def parse_emotion_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, float) and math.isnan(v):
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            parts = re.split(r"[;,]", v)
            return [part.strip() for part in parts if part.strip()]
        return [str(v).strip()] if str(v).strip() else []


# Maps Emotion.xlsx columns to model fields
emotion_table_model_map = {
    "Opera": "opera",
    "Label": "label",
    "Aria": "aria",
    "Basic_passion": "basic_passion",
    "PassionA": "passion_a",
    "PassionB": "passion_b",
    "Valence": "valence",
    "Valence2": "valence_2",
    "Bonora A": "bonora_a",
    "Bonora B": "bonora_b",
    "Zhang A": "zhang_a",
    "Zhang B": "zhang_b",
    "JMD A": "jmd_a",
    "JMD B": "jmd_b",
}
