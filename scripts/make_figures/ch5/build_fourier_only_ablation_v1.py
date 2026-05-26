from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.make_figures._run_research_script import run_research_script


if __name__ == "__main__":
    run_research_script(
        "research_validation/ch5_fourier_only_ablation/build_fourier_only_ablation_v1.py"
    )
