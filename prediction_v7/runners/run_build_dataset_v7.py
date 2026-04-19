from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    script = ROOT / 'prediction_v7' / 'dataset' / 'build_pure_prediction_dataset_v7.py'
    for freq_cap in (250.0, 300.0):
        cmd = [sys.executable, str(script), '--dataset-tag', 'v1', '--freq-cap', str(freq_cap)]
        print(f'[RUN] {" ".join(cmd)}')
        subprocess.run(cmd, check=True, cwd=ROOT)


if __name__ == '__main__':
    main()
