from pathlib import Path
import re
import warnings, ms3, traceback
from paths import DATA_DIR, OUTPUT_DIR
from src.types.models import AriaHeaderModel
from src.scripts.build_index import build_index
from tqdm import tqdm

# filter futurewarnings from pandas / ms3
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=r".*DataFrameGroupBy.apply operated on the grouping columns.*",
)

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=r".*Downcasting object dtype arrays on \.fillna, \.ffill, \.bfill is deprecated.*",
)



# variables
mscx_folder_path = DATA_DIR / "musescore" / "didone"
analysis_out_dir = OUTPUT_DIR / "ms3-analysis"
aria_index_path = OUTPUT_DIR / "aria_index.jsonl"
labels_dir_name = "labels"
expanded_dir_name = "expanded"
measures_dir_name = "measures"
notes_dir_name = "notes"


# generate aria_index if not already existing
if not aria_index_path.is_file():
    print(f'No aria index found. Generating new aria index at { aria_index_path }.')
    build_index(aria_index_path)
else:
    print(f'Using existing aria index at {aria_index_path}.')

def load_aria_index(path: Path) -> list[AriaHeaderModel]:
    arias: list[AriaHeaderModel] = []
    with path.open("r", encoding="utf8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                arias.append(AriaHeaderModel.model_validate_json(line))
            except Exception as e:
                print(f"Skipping invalid JSONL line {line_no}: {e}")
    return arias

def is_done(file_name: str) -> bool:
    stem = Path(file_name).stem
    expected_files = [
        analysis_out_dir / labels_dir_name / f"{stem}.labels.tsv",
        analysis_out_dir / expanded_dir_name / f"{stem}.harmonies.tsv",
        analysis_out_dir / measures_dir_name / f"{stem}.measures.tsv",
        analysis_out_dir / notes_dir_name / f"{stem}.notes.tsv",
    ]
    return all(path.is_file() for path in expected_files)


arias = load_aria_index(aria_index_path)
done_arias: list[str] = []
missing_files: list[str] = []
failed_files: list[tuple[str, str]] = []
skipped_files: list[str] = []
for aria in tqdm(arias, desc="Parsing and storing arias", unit="file"):
    if not aria.file_name:
        failed_files.append(("<missing file_name>", f"id={aria.id}"))
        continue

    if is_done(aria.file_name):
        skipped_files.append(aria.file_name)
        continue

    mscx_path = mscx_folder_path / aria.file_name

    if not mscx_path.is_file():
        missing_files.append(str(mscx_path))
        continue
    

    try:
        p = ms3.Parse(
            str(mscx_path.parent),
            recursive=False,
            file_re=rf"^{re.escape(mscx_path.name)}$",
        )

        p.parse_scores()

        p.store_extracted_facets(
            root_dir=str(analysis_out_dir),
            labels_folder=labels_dir_name,
            expanded_folder=expanded_dir_name,
            measures_folder=measures_dir_name,
            notes_folder=notes_dir_name,
            simulate=False,
            frictionless=False
        )

        if is_done(aria.file_name):
            done_arias.append(mscx_path.name)
        else:
            print(f"Not all expected TSVs were written for aria {aria.file_name}")
            failed_files.append((str(mscx_path), "Not all expected TSVs were written"))

    except KeyboardInterrupt:
        print("\nInterrupted by user. Stopping cleanly.")
        break
    except Exception as e:
        print(f"\nFAILED: {mscx_path}")
        traceback.print_exc()
        failed_files.append((str(mscx_path), repr(e)))


print(f"Done. Done {len(done_arias)} of {len(arias)}")
attempted = len(done_arias) + len(failed_files) + len(skipped_files) + len(missing_files)
print(f"Attempted this run: {attempted}")
print(f"Succeeded this run: {len(done_arias)}")
print(f"Skipped already done: {len(skipped_files)}")
print(f"Missing files: {len(missing_files)}")
print(f"Failed files: {len(failed_files)}")