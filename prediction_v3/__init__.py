"""Compatibility package for archived prediction v3 feature-engineering code."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

for path in [ROOT / "stage3_dataset", ROOT / "stage3_training"]:
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

__path__ = [str(ROOT / "archive" / "legacy_prediction" / "prediction_v3")]
