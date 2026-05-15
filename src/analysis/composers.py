from collections import defaultdict

from src.corpus.models import AriaHeaderModel
from src.corpus.build_aria_index import create_or_load_aria_index






def get_arias_grouped_by_composer ():
    aria_index = create_or_load_aria_index()

    composer_grouping: dict[str, list[AriaHeaderModel]] = defaultdict(list)
    for aria in aria_index:
        if aria.composer:
            composer_grouping[aria.composer.lower().strip()].append(aria)

    return composer_grouping

def get_composer_aria_number ():
    composer_numbers: dict[str, int] = defaultdict(lambda: 0)

    for composer, arias in get_arias_grouped_by_composer().items():
        for aria in arias: composer_numbers[composer] += 1

    return composer_numbers






if __name__ == "__main__":
    print(get_composer_aria_number())