from __future__ import annotations

import argparse
from pathlib import Path

from common import run_python_script
from shared.optimization.legacy_seed_only import (
    DEFAULT_SCORING_DATASET as DEFAULT_DATASET,
    DEFAULT_SCORING_POLICY as DEFAULT_POLICY,
    DEFAULT_SCORING_RUN_NAME as DEFAULT_RUN_NAME,
    SCORING_SCRIPT as SCRIPT,
)


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

