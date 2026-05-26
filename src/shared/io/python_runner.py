from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parents[2]


def run_python_script(script_path: Path, args: Iterable[str] | None = None) -> None:
    args = list(args or [])
    if not script_path.exists():
        raise FileNotFoundError(script_path)
    cmd: List[str] = [sys.executable, str(script_path), *args]
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f'Command failed with exit code {result.returncode}: {cmd}')

