from __future__ import annotations

import argparse
from pathlib import Path

from common import run_python_script
from shared.optimization.legacy_seed_only import DEFAULT_LOCAL_GA_POLICY as DEFAULT_POLICY
from shared.optimization.legacy_seed_only import LOCAL_GA_SCRIPT as SCRIPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the optional local GA refinement branch for optimization.')
    parser.add_argument('--policy-json', type=Path, default=DEFAULT_POLICY)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_python_script(SCRIPT, ['--policy-json', str(args.policy_json)])
    print('[DONE] optimization local GA refinement v1 complete')
    print(f'[SCRIPT] {SCRIPT}')
