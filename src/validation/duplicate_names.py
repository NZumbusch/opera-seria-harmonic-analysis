import re
import unicodedata
from collections import defaultdict

from src.corpus.build_aria_index import create_or_load_aria_index


def normalize_composer_name(name: str) -> str:
    name = name.lower().strip()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def get_composer_clusters():
    aria_index = create_or_load_aria_index()
    clusters = defaultdict(list)

    for aria in aria_index:
        if aria.composer:
            raw = aria.composer.lower().strip()
            norm = normalize_composer_name(aria.composer)
            clusters[norm].append(raw)

    return clusters


def print_duplicate_clusters():
    clusters = get_composer_clusters()
    for norm, names in sorted(clusters.items(), key=lambda x: (-len(set(x[1])), x[0])):
        unique_names = sorted(set(names))
        if len(unique_names) > 1:
            print(f"\n{norm} -> {len(unique_names)} variants")
            for name in unique_names:
                print(f"  - {name}")


if __name__ == "__main__":
    print_duplicate_clusters()
