import bisect
import csv
import re
from pathlib import Path
from typing import Iterator, Tuple

from pydantic import BaseModel

from src.analysis.util import get_localkey_midi, parse_to_float
from src.paths import get_aria_analysis_path


class NoteInfo(BaseModel):
    onset: float
    duration: float
    midi: int


class ActiveNote(NoteInfo):
    end: float
    staff: int


class ContrapuntalPair(BaseModel):
    soprano: NoteInfo
    bass: NoteInfo
    tonic: int
    is_minor: bool

    @property
    def center_time(self) -> float:
        return (self.bass.onset + self.soprano.onset) / 2.0

    @property
    def onset_time(self) -> float:
        return min(self.bass.onset, self.soprano.onset)

    @property
    def distance(self) -> float:
        return abs(self.soprano.onset - self.bass.onset)

    @property
    def bass_sd(self) -> int:
        return (self.bass.midi - self.tonic) % 12

    @property
    def soprano_sd(self) -> int:
        return (self.soprano.midi - self.tonic) % 12


def load_harmony_map(harmony_tsv_path: str | Path) -> list[tuple[float, int, bool]]:
    """Loads harmony data into a sorted list for binary search."""
    harmony_map = []

    with open(harmony_tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            onset = float(parse_to_float(row["quarterbeats_all_endings"]))

            harmony_map.append(
                (
                    onset,
                    get_localkey_midi(
                        row["globalkey"],
                        True if row["globalkey_is_minor"] == "1" else False,
                        row["localkey"],
                    ),
                    True if row["globalkey_is_minor"] == "1" else False,
                )
            )

    # Ensure it is sorted by time just in case
    harmony_map.sort(key=lambda x: x[0])
    return harmony_map


def get_tonic_at_time(
    onset: float, harmony_map: list[tuple[float, int, bool]], harmony_times: list
) -> Tuple[int, bool]:
    if not harmony_map:
        return (0, False)

    idx = bisect.bisect_right(harmony_times, onset)

    if idx == 0:
        return (harmony_map[0][1], harmony_map[0][2])

    return (harmony_map[idx - 1][1], harmony_map[idx - 1][2])


def generate_fuzzy_pairs(
    bass_notes: list[NoteInfo],
    soprano_notes: list[NoteInfo],
    harmony_file: str | Path,
    max_sync_distance: float = 2.0,
    grid_size: float | None = 0.5,
    min_duration: float = 0.5,
) -> Iterator[ContrapuntalPair]:
    """
    Pairs bass and soprano notes using a sliding window.
    Assumes lists are sorted by onset time.
    """
    soprano_idx = 0
    num_sopranos = len(soprano_notes)
    harmony_map = load_harmony_map(harmony_file)
    harmony_times = [h[0] for h in harmony_map]

    for bass in bass_notes:
        if bass.duration < min_duration:
            continue
        if grid_size and (bass.onset % grid_size != 0):
            continue

        # Move index forward
        while soprano_idx < num_sopranos and soprano_notes[soprano_idx].onset < (
            bass.onset - max_sync_distance
        ):
            soprano_idx += 1

        # Check potential matches in the window
        for i in range(soprano_idx, num_sopranos):
            soprano = soprano_notes[i]

            if soprano.onset > (bass.onset + max_sync_distance):
                break

            if soprano.duration < min_duration:
                continue

            if grid_size and (soprano.onset % grid_size != 0):
                continue

            current_tonic, is_minor = get_tonic_at_time(
                bass.onset, harmony_map, harmony_times
            )

            yield ContrapuntalPair(
                bass=bass, soprano=soprano, tonic=current_tonic, is_minor=is_minor
            )


def strip_octave(note_name: str) -> str:
    """Strips numerical octaves from note names (e.g., 'Eb4' -> 'Eb')"""
    return re.sub(r"\d+", "", note_name)


def extract_outer_voices(
    notes_file_path: str | Path,
) -> Tuple[list[NoteInfo], list[NoteInfo]]:
    """Yields the true active outer voices at every distinct onset time."""

    active_notes: list[ActiveNote] = []
    soprano_notes: list[NoteInfo] = []
    bass_notes: list[NoteInfo] = []
    current_time = -1.0

    with open(notes_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        current_bass = None
        current_soprano = None
        for row in reader:
            if row.get("gracenote"):
                continue

            onset = parse_to_float(row["quarterbeats_all_endings"])
            duration = float(row["duration_qb"])
            midi = int(row["midi"])
            staff = int(row["staff"])

            if onset > current_time and current_time != -1.0:
                if active_notes:
                    bass = min(active_notes, key=lambda n: n.midi)
                    soprano = max(active_notes, key=lambda n: n.midi)

                    if current_bass != bass or current_soprano != soprano:
                        soprano_notes.append(soprano)
                        bass_notes.append(bass)

                        current_bass, current_soprano = bass, soprano

                active_notes = [n for n in active_notes if n.end > onset]

            current_time = onset
            active_notes.append(
                ActiveNote(
                    midi=midi,
                    onset=onset,
                    duration=duration,
                    end=onset + duration,
                    staff=staff,
                )
            )

        # evaluate last notes
        if active_notes:
            bass = min(active_notes, key=lambda n: n.midi)
            soprano = max(active_notes, key=lambda n: n.midi)

            soprano_notes.append(soprano)
            bass_notes.append(bass)

    return (soprano_notes, bass_notes)


def get_aria_outer_voice_pairs_fuzzy(
    file_name: str, max_sync_distance: int = 2
) -> Iterator[ContrapuntalPair]:
    clean_stem = Path(file_name).name.replace(".mscx", "")
    notes_file_path = get_aria_analysis_path(clean_stem, "notes")
    harmony_file_path = get_aria_analysis_path(clean_stem, "expanded")

    soprano_notes, bass_notes = extract_outer_voices(notes_file_path)

    return generate_fuzzy_pairs(
        bass_notes,
        soprano_notes,
        max_sync_distance=max_sync_distance,
        harmony_file=harmony_file_path,
    )


if __name__ == "__main__":
    pass
