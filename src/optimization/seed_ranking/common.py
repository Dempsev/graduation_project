from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.io.python_runner import ROOT, run_python_script
from shared.optimization.legacy_seed_only import STAGE3_TRAINING

__all__ = ['ROOT', 'STAGE3_TRAINING', 'run_python_script']
