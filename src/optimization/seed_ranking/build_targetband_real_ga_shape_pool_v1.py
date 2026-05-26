from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CANDIDATE_POOL = (
    ROOT
    / 'data'
    / 'ml_dataset'
    / 'v12'
    / 'candidate_pool_optimization_v1'
    / 'candidate_pool_optimization_v1.csv'
)
DEFAULT_OUT = ROOT / 'data' / 'ml_runs' / 'targetband_baseline_abc_v1' / 'real_ga_shape_pool_v1.csv'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build the shape pool used by the target-band real-GA baseline.')
    parser.add_argument('--candidate-pool', type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = parse_args()
    candidate_pool = resolve_path(args.candidate_pool)
    out_path = resolve_path(args.out)
    if not candidate_pool.exists():
        raise FileNotFoundError(candidate_pool)

    df = pd.read_csv(candidate_pool)
    required = ['shape_id', 'stage1_reference_gap_gain_Hz', 'stage1_reference_candidate_tier']
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f'{candidate_pool} is missing required columns: {missing}')

    pool = (
        df.sort_values(['stage1_reference_gap_gain_Hz', 'shape_id'], ascending=[False, True])
        .drop_duplicates('shape_id', keep='first')
        .copy()
    )
    out = pd.DataFrame(
        {
            'shape_id': pool['shape_id'].astype(str),
            'gap_gain_Hz': pd.to_numeric(pool['stage1_reference_gap_gain_Hz'], errors='coerce').fillna(0.0),
            'candidate_tier': pool['stage1_reference_candidate_tier'].astype(str),
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding='utf-8')
    print(f'[DONE] wrote real-GA shape pool: {out_path}')
    print(f'[ROWS] {len(out)} unique shapes')


if __name__ == '__main__':
    main()
