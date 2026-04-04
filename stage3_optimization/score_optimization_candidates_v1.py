from __future__ import annotations

import argparse
from pathlib import Path

from common import ROOT, STAGE3_TRAINING, run_python_script

SCRIPT = STAGE3_TRAINING / 'run_seed_discovery_scoring_v7.py'
DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v10' / 'candidate_pool_v10_seed_only_refined' / 'candidate_pool_v10.csv'
DEFAULT_POLICY = STAGE3_TRAINING / 'policies' / 'seed_discovery_v10.json'
DEFAULT_RUN_NAME = 'candidate_pool_seed_discovery_v10'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Score optimization candidates for the refined seed-only mainline.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--policy-json', type=Path, default=DEFAULT_POLICY)
    parser.add_argument('--run-name', default=DEFAULT_RUN_NAME)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_python_script(SCRIPT, [
        '--dataset', str(args.dataset),
        '--policy-json', str(args.policy_json),
        '--run-name', str(args.run_name),
    ])
    print('[DONE] optimization candidate scoring v1 complete')
    print(f'[SCRIPT] {SCRIPT}')
