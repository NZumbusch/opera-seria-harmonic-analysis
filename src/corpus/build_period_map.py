import json
import math
from collections import defaultdict

from src.corpus.build_aria_index import create_or_load_aria_index
from src.corpus.models import AriaHeaderModel
from src.paths import ARIA_PERIOD_MAP_PATH
from src.visualization.util import PERIOD_NUMBER


def chunk_list(seq, n_chunks):
    chunk_size = math.ceil(len(seq) / n_chunks)
    return [seq[i : i + chunk_size] for i in range(0, len(seq), chunk_size)]


def get_arias_by_year_period(n_periods: int = 8) -> dict[str, list[AriaHeaderModel]]:
    aria_index = create_or_load_aria_index()

    valid_arias = [
        aria
        for aria in aria_index
        if aria.year is not None
        and aria.file_name is not None
        and 1500 <= aria.year <= 1850
    ]
    if not valid_arias:
        return {}

    valid_arias = sorted(
        valid_arias, key=lambda aria: aria.year if aria.year is not None else -1
    )
    aria_chunks = chunk_list(valid_arias, n_periods)

    out: dict[str, list[AriaHeaderModel]] = {}
    for chunk in aria_chunks:
        if not chunk:
            continue

        start_year = chunk[0].year
        end_year = chunk[-1].year
        label = f"{start_year}-{end_year}"
        out[label] = chunk

    return out


def save_aria_period_map() -> None:
    groups = get_arias_by_year_period(PERIOD_NUMBER)

    with ARIA_PERIOD_MAP_PATH.open("w", encoding="utf8") as f:
        for label, arias in groups.items():
            for aria in arias:
                row = {
                    "id": aria.id,
                    "file_name": aria.file_name,
                    "year": aria.year,
                    "period": label,
                    "n": len(arias),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        f"Wrote aria period map at {ARIA_PERIOD_MAP_PATH} "
        f"with {sum(len(v) for v in groups.values())} assignments."
    )


def create_or_get_period_map() -> dict[str, list[AriaHeaderModel]]:
    if not ARIA_PERIOD_MAP_PATH.exists():
        ARIA_PERIOD_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_aria_period_map()

    aria_index = create_or_load_aria_index()
    aria_by_id = {aria.id: aria for aria in aria_index}

    out: defaultdict[str, list[AriaHeaderModel]] = defaultdict(list)

    with ARIA_PERIOD_MAP_PATH.open("r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            row = json.loads(line)
            aria_id = row["id"]
            period = row["period"]

            aria = aria_by_id.get(aria_id)
            if aria is None:
                continue

            out[period].append(aria)

    return dict(out)


if __name__ == "__main__":
    print(create_or_get_period_map())
