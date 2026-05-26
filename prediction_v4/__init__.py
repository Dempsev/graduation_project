"""Compatibility package for archived prediction v4 code."""

from __future__ import annotations

from pathlib import Path

__path__ = [
    str(Path(__file__).resolve().parents[1] / "archive" / "legacy_prediction" / "prediction_v4")
]
