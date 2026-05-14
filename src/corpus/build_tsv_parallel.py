import multiprocessing as mp
from pathlib import Path
import re, warnings, ms3, signal

from src.paths import ANALYSIS_OUT_DIR, MS3_EXPANDED_DIR, MS3_LABELS_DIR, MS3_MEASURES_DIR, MSCX_FOLDER_DIR
from src.corpus.build_aria_index import create_or_load_aria_index, load_aria_index
from tqdm import tqdm
from functools import partial


def process_aria(file_name: str) -> tuple[str, str, str]:
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


    
    #notes_dir_name = "notes"

    mscx_path = Path(MSCX_FOLDER_DIR) / file_name

    expected_files = [
        MS3_LABELS_DIR / f"{mscx_path.stem}.labels.tsv",
        MS3_EXPANDED_DIR / f"{mscx_path.stem}.harmonies.tsv",
        MS3_MEASURES_DIR / f"{mscx_path.stem}.measures.tsv",
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
            root_dir=str(ANALYSIS_OUT_DIR),
            labels_folder=str(MS3_LABELS_DIR),
            expanded_folder=str(MS3_EXPANDED_DIR),
            measures_folder=str(MS3_MEASURES_DIR),
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

    # actually parse arias
    arias = create_or_load_aria_index()
    done_arias = []
    missing_files = []
    failed_files = []
    skipped_files = []
    file_names = [aria.file_name for aria in arias if aria.file_name]
    with mp.Pool(processes=6, initializer=init_worker, maxtasksperchild=10, initargs=(stop_event,)) as pool:
        try:
            worker_fn = partial(process_aria)
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