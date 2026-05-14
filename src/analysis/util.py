import pandas as pd

from src.paths import get_aria_analysis_path


def get_aria_mode_from_tsv(aria_file_name: str) -> str | None:
    path = get_aria_analysis_path(aria_file_name, "expanded")
    if not path.is_file():
        return None

    df = pd.read_csv(path, sep="\t")
    if "globalkey_is_minor" not in df.columns:
        return None

    values = df["globalkey_is_minor"].dropna()
    if values.empty:
        return None

    first_value = int(values.iloc[0])
    if first_value == 0:
        return "major"
    if first_value == 1:
        return "minor"
    return None