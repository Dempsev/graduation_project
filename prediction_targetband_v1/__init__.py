"""Compatibility package for archived early target-band prediction code."""

from __future__ import annotations

from pathlib import Path

__path__ = [
    str(
        Path(__file__).resolve().parents[1]
        / "archive"
        / "legacy_prediction"
        / "prediction_targetband_v1"
    )
]
