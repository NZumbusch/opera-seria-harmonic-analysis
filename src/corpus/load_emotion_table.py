import json
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
import pandas as pd
from src.paths import BASIC_PASSION_OF_ARIA_MAP_PATH, EMOTION_TABLE_PATH
from pydantic import ValidationError
from corpus.build_aria_index import create_or_load_aria_index
from src.corpus.models import AriaHeaderModel, EmotionLabelModel, emotion_table_model_map


def load_emotion_table () -> list[EmotionLabelModel]:
    df = pd.read_excel(EMOTION_TABLE_PATH)

    # rename columns to match model
    df_subset = df[list(emotion_table_model_map.keys())].rename(columns=emotion_table_model_map)
 
    # convert pandas NaN to None
    df_subset = df_subset.where(pd.notna(df_subset), None)

    # drop rows with missing required fields
    df_subset = df_subset.dropna(subset=["opera", "label", "aria"])

    # convert to list of models & validate each row
    models: list[EmotionLabelModel] = []
    for row in df_subset.to_dict('records'):
        try:
            models.append(EmotionLabelModel.model_validate(row))
        except ValidationError as e:
            print(f"Row validation failed: {e}")
    
    return models


def get_emotions_of_aria (aria_label: str) -> Optional[EmotionLabelModel]:
    """ Finds emotion data for aria """

    for aria in load_emotion_table():
        if aria.label.lower() == aria_label.lower():
            return aria
    
    return None


def get_all_base_emotions () -> dict[str, list[str]]:
    emotion_table = load_emotion_table()
    emotions = defaultdict(list)

    # gets all
    for aria_emotion in emotion_table:
        emotions[aria_emotion.basic_passion].append(aria_emotion.label)

    return emotions


def get_arias_by_basic_passion () -> dict[str, list[AriaHeaderModel]]:
    """Groups all arias by basic passion according to Passions.xlsx"""

    arias = create_or_load_aria_index()
    emotions = get_all_base_emotions()

    aria_index: dict[str, list[AriaHeaderModel]] = defaultdict(list)
    for aria in arias:
        if aria.aria is not None:
            aria_index[aria.aria].append(aria)

    return {
        emotion: [
            aria
            for label in labels
            for aria in aria_index.get(label, [])
        ]
        for emotion, labels in emotions.items()
    }



def create_basic_passion_by_aria_id_map () -> dict[int, str]:
    out: dict[int, str] = {}
    for emotion, arias in get_arias_by_basic_passion().items():
        for aria in arias:
            if aria.id:
                out[aria.id] = emotion

    with open(BASIC_PASSION_OF_ARIA_MAP_PATH, "w") as f:
        json.dump(out, f)

    return out


def create_or_get_basic_passion_by_aria_id_map ():
    # generate basic_passion_map if not already existing
    if not BASIC_PASSION_OF_ARIA_MAP_PATH.is_file():
        print(f'No aria index found. Generating new basic passion of aria map at { BASIC_PASSION_OF_ARIA_MAP_PATH }.')
        return create_basic_passion_by_aria_id_map()
    else:
        print(f'Using existing aria index at {BASIC_PASSION_OF_ARIA_MAP_PATH}.')

        with open(BASIC_PASSION_OF_ARIA_MAP_PATH, "r") as f:
            return json.load(f)
    
    raise LookupError



        
def get_basic_passion_by_aria_id (aria_id: int, aria_emotion_grouping: dict[str, list[AriaHeaderModel]] | None = None):
    if not aria_emotion_grouping:
        aria_emotion_grouping = get_arias_by_basic_passion()

    for emotion, arias in aria_emotion_grouping.items():
        for aria in arias:
            if aria.id == aria_id:
                return emotion

        



if __name__ == "__main__":
    print(create_or_get_basic_passion_by_aria_id_map())