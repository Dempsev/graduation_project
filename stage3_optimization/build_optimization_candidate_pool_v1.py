from __future__ import annotations

from pathlib import Path

from common import STAGE3_TRAINING, run_python_script

SCRIPT = STAGE3_TRAINING / 'build_candidate_pool_v10.py'


if __name__ == '__main__':
    run_python_script(SCRIPT)
    print('[DONE] optimization candidate pool v1 built')
    print(f'[SCRIPT] {SCRIPT}')
