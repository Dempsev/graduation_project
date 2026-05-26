from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts._run_refactored_script import run_refactored_script


if __name__ == "__main__":
    run_refactored_script(
        "src/prediction/targetband_param/runners/run_build_curated_application_bundle_v1.py"
    )
