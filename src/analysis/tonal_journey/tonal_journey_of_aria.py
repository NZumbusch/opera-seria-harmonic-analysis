import pandas as pd
from src.paths import get_aria_analysis_path


def get_tonal_spaces(aria_file_name: str):
    path = get_aria_analysis_path(aria_file_name, "expanded")
    if not path.is_file():
        return None

    # df = pd.read_csv(path, sep="\t")
    return None

