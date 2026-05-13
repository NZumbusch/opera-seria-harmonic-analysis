from __future__ import annotations
import os
from pathlib import Path

_MARKERS = ("pyproject.toml", ".git")

def find_project_root(start: Path | None = None) -> Path:
    env_root = os.environ.get("PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if any((candidate / marker).exists() for marker in _MARKERS):
            return candidate

    raise RuntimeError("Could not find project root.")

PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SRC_DIR = PROJECT_ROOT / "src"