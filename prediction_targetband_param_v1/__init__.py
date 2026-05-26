"""Compatibility package for the refactored target-band prediction modules.

The public source tree now keeps these modules under
`src/prediction/targetband_param`. This shim preserves existing imports such as
`prediction_targetband_param_v1.models.inference` while scripts are migrated to
the new layout.
"""

from __future__ import annotations

from pathlib import Path

__path__ = [
    str(Path(__file__).resolve().parents[1] / "src" / "prediction" / "targetband_param")
]
