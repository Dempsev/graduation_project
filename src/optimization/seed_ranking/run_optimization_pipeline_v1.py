from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import run_python_script


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the standalone optimization pipeline.')
    parser.add_argument('--with-ga', action='store_true', help='Include the optional local GA refinement branch.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    steps = [
        ROOT / 'build_optimization_candidate_pool_v1.py',
        ROOT / 'score_optimization_candidates_v1.py',
        ROOT / 'build_optimization_manifest_v1.py',
    ]
    if args.with_ga:
        steps.extend([
            ROOT / 'run_optimization_local_ga_v1.py',
            ROOT / 'build_optimization_ga_manifest_v1.py',
        ])

    for step in steps:
        print(f'[RUNNING] {step.name}')
        run_python_script(step)

    print('[DONE] optimization pipeline v1 complete')
    print(f'[WITH_GA] {int(args.with_ga)}')
