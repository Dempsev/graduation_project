"""Compatibility package for the refactored seed-ranking modules.

The public source tree now keeps these modules under
`src/optimization/seed_ranking`. This shim preserves imports such as
`optimization.seed_ranking.run_targetband_seed_scoring_v1`.
"""

from __future__ import annotations

from pathlib import Path

__path__ = [
    str(Path(__file__).resolve().parents[2] / "src" / "optimization" / "seed_ranking")
]
