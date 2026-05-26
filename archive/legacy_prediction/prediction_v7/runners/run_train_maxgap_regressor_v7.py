from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    script = ROOT / 'prediction_v7' / 'models' / 'train_maxgap_regressor_v7.py'
    runs = [
        ('cap250_family', ROOT / 'data' / 'pure_prediction_v7' / 'v1' / 'cap250' / 'pure_maxgap_regression_v7.csv', 'stratified_group_kfold'),
        ('cap250_stage', ROOT / 'data' / 'pure_prediction_v7' / 'v1' / 'cap250' / 'pure_maxgap_regression_v7.csv', 'leave_one_stage_out'),
        ('cap300_family', ROOT / 'data' / 'pure_prediction_v7' / 'v1' / 'cap300' / 'pure_maxgap_regression_v7.csv', 'stratified_group_kfold'),
        ('cap300_stage', ROOT / 'data' / 'pure_prediction_v7' / 'v1' / 'cap300' / 'pure_maxgap_regression_v7.csv', 'leave_one_stage_out'),
    ]
    for run_name, dataset, eval_mode in runs:
        cmd = [
            sys.executable,
            str(script),
            '--dataset',
            str(dataset),
            '--target',
            'max_gap_below_cap_width_Hz',
            '--eval-mode',
            eval_mode,
            '--run-name',
            run_name,
        ]
        print(f'[RUN] {" ".join(cmd)}')
        subprocess.run(cmd, check=True, cwd=ROOT)


if __name__ == '__main__':
    main()
