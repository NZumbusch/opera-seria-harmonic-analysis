from pydantic import BaseModel
from typing import Optional


class AriaMetaDataModel (BaseModel):
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

class AriaHeaderModel (AriaMetaDataModel):
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