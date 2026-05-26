from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'prediction' / 'models' / 'train_pure_bandgap_regressor_v1.py'


def main() -> None:
    sys.argv = [str(TARGET), *sys.argv[1:]]
    runpy.run_path(str(TARGET), run_name='__main__')


if __name__ == '__main__':
    main()
