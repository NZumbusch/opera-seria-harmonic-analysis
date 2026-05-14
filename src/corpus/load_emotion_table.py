from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
import pandas as pd
from src.paths import EMOTION_TABLE_PATH
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

    # Convert to list of models & validate each row
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
        
        


        



if __name__ == "__main__":
    print(get_arias_by_basic_passion())