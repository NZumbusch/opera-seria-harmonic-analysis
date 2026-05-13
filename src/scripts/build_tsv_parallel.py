import multiprocessing as mp
from pathlib import Path
import re, warnings, ms3, signal
from paths import DATA_DIR, OUTPUT_DIR
from src.types.models import AriaHeaderModel
from src.scripts.build_index import build_index
from tqdm import tqdm
from functools import partial

# variables
mscx_folder_path = DATA_DIR / "musescore" / "didone"
analysis_out_dir = OUTPUT_DIR / "ms3-analysis"
aria_index_path = OUTPUT_DIR / "aria_index.jsonl"



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




def process_aria(file_name: str, mscx_folder_path: Path, analysis_out_dir: Path) -> tuple[str, str, str]:
    global worker_stop_event

    if worker_stop_event is not None and worker_stop_event.is_set():
        return ("stopped", file_name, "stop requested before start")
    
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


    labels_dir_name = "labels"
    expanded_dir_name = "expanded"
    measures_dir_name = "measures"
    #notes_dir_name = "notes"

    mscx_path = Path(mscx_folder_path) / file_name

    expected_files = [
        analysis_out_dir / labels_dir_name / f"{mscx_path.stem}.labels.tsv",
        analysis_out_dir / expanded_dir_name / f"{mscx_path.stem}.harmonies.tsv",
        analysis_out_dir / measures_dir_name / f"{mscx_path.stem}.measures.tsv",
        #analysis_out_dir / notes_dir_name / f"{mscx_path.stem}.notes.tsv",
    ]

    if all(path.is_file() for path in expected_files):
        return ("skipped", file_name, "already done")

    if not mscx_path.is_file():
        return ("missing", file_name, str(mscx_path))

    try:
        p = ms3.Parse(
            str(mscx_path.parent),
            recursive=False,
            file_re=rf"^{re.escape(mscx_path.name)}$",
        )

        p.parse_scores()

        if worker_stop_event is not None and worker_stop_event.is_set():
            return ("stopped", file_name, "stop requested before start")

        p.store_extracted_facets(
            root_dir=str(analysis_out_dir),
            labels_folder=labels_dir_name,
            expanded_folder=expanded_dir_name,
            measures_folder=measures_dir_name,
            #notes_folder=notes_dir_name,
            simulate=False,
            frictionless=False,
        )

        if all(path.is_file() for path in expected_files):
            return ("done", file_name, "")
        return ("failed", file_name, "Not all expected TSVs were written")

    except Exception as e:
        return ("failed", file_name, repr(e))

worker_stop_event = None
def main_shutdown(sig, frame):
    print("Shutting down...")
    global stop_event
    stop_event.set()

def init_worker(stop_evt):
    global worker_stop_event
    worker_stop_event = stop_evt
    signal.signal(signal.SIGINT, signal.SIG_IGN)

if __name__ == "__main__":
    stop_event = mp.Event()
    signal.signal(signal.SIGINT, main_shutdown)

    # generate aria_index if not already existing
    if not aria_index_path.is_file():
        print(f'No aria index found. Generating new aria index at { aria_index_path }.')
        build_index(aria_index_path)
    else:
        print(f'Using existing aria index at {aria_index_path}.')

    # actually parse arias
    arias = load_aria_index(aria_index_path)
    done_arias = []
    missing_files = []
    failed_files = []
    skipped_files = []
    file_names = [aria.file_name for aria in arias if aria.file_name]
    with mp.Pool(processes=6, initializer=init_worker, maxtasksperchild=10, initargs=(stop_event,)) as pool:
        try:
            worker_fn = partial(
                process_aria,
                mscx_folder_path=mscx_folder_path,
                analysis_out_dir=analysis_out_dir,
            )
            for status, file_name, msg in tqdm(pool.imap_unordered(worker_fn, file_names, chunksize=1),total=len(file_names),desc="Parsing and storing arias"):
                if status == "done":
                    done_arias.append(file_name)
                elif status == "skipped":
                    skipped_files.append(file_name)
                elif status == "missing":
                    missing_files.append(msg)
                else:
                    failed_files.append((file_name, msg))
                
        except KeyboardInterrupt:
            print("Interrupted, terminating workers...")
            stop_event.set()
            pool.terminate()
            pool.join()
            raise

    print(f"Done. Done {len(done_arias)} of {len(arias)}")
    attempted = len(done_arias) + len(failed_files) + len(missing_files)
    print(f"Attempted this run: {attempted}")
    print(f"Succeeded this run: {len(done_arias)}")
    print(f"Skipped already done: {len(skipped_files)}")
    print(f"Missing files: {len(missing_files)}")
    print(f"Failed files: {len(failed_files)}")