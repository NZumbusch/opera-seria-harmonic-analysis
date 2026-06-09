from src.analysis.util import get_aria_mode_from_tsv
from src.corpus.build_period_map import create_or_get_period_map


def get_mode_percentages_by_period() -> dict[str, dict[str, float]]:
    period_map = create_or_get_period_map()
    out = {}

    for period, arias in period_map.items():
        major = 0
        minor = 0

        for aria in arias:
            if not aria.file_name:
                continue

            mode = get_aria_mode_from_tsv(aria.file_name)
            if mode == "major":
                major += 1
            elif mode == "minor":
                minor += 1

        total = major + minor
        out[period] = {
            "major": (major / total * 100) if total else 0.0,
            "minor": (minor / total * 100) if total else 0.0,
        }

    return out
