from __future__ import annotations

import argparse
from pathlib import Path

from common import STAGE3_TRAINING, run_python_script

SCRIPT = STAGE3_TRAINING / 'run_parametric_ga_seed_search_v1.py'
DEFAULT_POLICY = STAGE3_TRAINING / 'policies' / 'ga_v1.json'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the optional local GA refinement branch for optimization.')
    parser.add_argument('--policy-json', type=Path, default=DEFAULT_POLICY)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_python_script(SCRIPT, ['--policy-json', str(args.policy_json)])
    print('[DONE] optimization local GA refinement v1 complete')
    print(f'[SCRIPT] {SCRIPT}')
