import csv

from src.corpus.build_aria_index import create_or_load_aria_index

bad = [
    aria
    for aria in create_or_load_aria_index()
    if aria.year is not None and (aria.year < 1500 or aria.year > 1850)
]

with open("suspicious_years.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "year", "composer", "opera", "aria", "file_name"])
    for aria in bad:
        writer.writerow(
            [aria.id, aria.year, aria.composer, aria.opera, aria.aria, aria.file_name]
        )
