from __future__ import annotations

import argparse
from pathlib import Path

from common import run_python_script


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'src' / 'optimization' / 'seed_ranking' / 'run_targetband_seed_scoring_v1.py'
DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_optimization_v1' / 'candidate_pool_optimization_v1.csv'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Score optimization candidates with a target-band conditional objective.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--band-low', type=float, default=180.0)
    parser.add_argument('--band-high', type=float, default=220.0)
    parser.add_argument('--run-name', default='targetband_seed_scoring_v1')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_python_script(
        SCRIPT,
        [
            '--dataset',
            str(args.dataset),
            '--band-low',
            str(args.band_low),
            '--band-high',
            str(args.band_high),
            '--run-name',
            str(args.run_name),
        ],
    )
    print('[DONE] target-band optimization candidate scoring v1 complete')
    print(f'[SCRIPT] {SCRIPT}')
