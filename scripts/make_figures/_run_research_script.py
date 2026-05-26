from __future__ import annotations

import runpy
import sys
from pathlib import Path


def run_research_script(relative_target: str) -> None:
    root = Path(__file__).resolve().parents[2]
    target = root / relative_target
    if not target.is_file():
        raise FileNotFoundError(target)
    sys.argv = [str(target), *sys.argv[1:]]
    runpy.run_path(str(target), run_name="__main__")
