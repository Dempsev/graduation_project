from __future__ import annotations

from common import run_python_script
from shared.optimization.legacy_seed_only import CANDIDATE_POOL_SCRIPT as SCRIPT


if __name__ == '__main__':
    run_python_script(SCRIPT)
    print('[DONE] optimization candidate pool v1 built')
    print(f'[SCRIPT] {SCRIPT}')

