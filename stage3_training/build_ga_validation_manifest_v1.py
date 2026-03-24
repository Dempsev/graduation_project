from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT, save_csv_rows, save_json

DEFAULT_GA_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1' / 'ga_candidate_manifest_v1.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1' / 'validation_manifest_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a compact COMSOL-ready manifest from GA candidates.')
    parser.add_argument('--ga-csv', type=Path, default=DEFAULT_GA_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--total-k', type=int, default=6)
    parser.add_argument('--per-seed-k', type=int, default=2)
    return parser.parse_args()


def rank_candidates(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['fitness', 'cascade_score', 'contact_prob', 'surrogate_pred_gap34_gain_Hz', 'distance_from_base'],
        ascending=[False, False, False, False, True],
    ).copy()


def main() -> None:
    args = parse_args()
    if not args.ga_csv.exists():
        raise FileNotFoundError(args.ga_csv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.ga_csv)
    if df.empty:
        raise RuntimeError('GA candidate manifest is empty.')

    ranked = rank_candidates(df)
    selected_rows: List[Dict[str, object]] = []
    for _, subset in ranked.groupby('ga_seed_shape_id', sort=False):
        selected_rows.extend(subset.head(max(1, args.per_seed_k)).to_dict(orient='records'))

    selected = rank_candidates(pd.DataFrame(selected_rows)).head(max(1, args.total_k)).copy()
    if selected.empty:
        raise RuntimeError('No GA validation rows selected.')

    selected['validation_id'] = [f'ga_val{i:03d}' for i in range(1, len(selected) + 1)]
    selected['selection_source'] = 'parametric_ga_v1'
    selected['selection_label'] = f'ga_top_{len(selected)}_per_seed_{int(args.per_seed_k)}'
    selected['rank_within_source'] = range(1, len(selected) + 1)

    manifest_path = args.out_dir / 'ga_validation_manifest_v1.csv'
    summary_path = args.out_dir / 'ga_validation_manifest_summary.json'
    selected.to_csv(manifest_path, index=False, encoding='utf-8-sig')
    save_json(summary_path, {
        'ga_csv': str(args.ga_csv),
        'manifest_rows': int(len(selected)),
        'total_k': int(args.total_k),
        'per_seed_k': int(args.per_seed_k),
        'unique_seed_shapes': int(selected['ga_seed_shape_id'].astype(str).nunique()),
        'unique_points': int(selected['point_id'].astype(str).nunique()),
        'mean_fitness': float(selected['fitness'].mean()),
        'mean_distance_from_base': float(selected['distance_from_base'].mean()),
    })

    print('[DONE] GA validation manifest built')
    print(f'[OUT] {manifest_path}')
    print(f'[SUMMARY] total={len(selected)} unique_seed_shapes={selected["ga_seed_shape_id"].astype(str).nunique()}')


if __name__ == '__main__':
    main()
