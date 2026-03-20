from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v6' / 'cascade_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v6' / 'validation_manifest_v6'

MANIFEST_FIELDS = [
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source', 'rank_cascade', 'rank_surrogate',
    'sample_id',
    'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'step_num', 'step_offset', 'step_distance', 'step_window', 'is_seed_shape',
    'selection_priority', 'target_rule', 'preferred_direction', 'directional_offset', 'allowed_offsets',
    'v5_reference_validation_id', 'v5_reference_gain_Hz',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'class_score', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build v6 COMSOL validation manifest for directional step-targeted exploitation.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--top-k', type=int, default=0, help='0 means keep all rows')
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def sort_selection(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['selection_priority', 'v5_reference_gain_Hz', 'cascade_gate', 'cascade_score', 'surrogate_pred_gap34_gain_Hz'],
        ascending=[True, False, False, False, False],
    ).copy()


def sort_for_cascade(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(['cascade_score', 'surrogate_pred_gap34_gain_Hz'], ascending=[False, False]).copy()


def sort_for_surrogate(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(['surrogate_pred_gap34_gain_Hz', 'cascade_score'], ascending=[False, False]).copy()


def main() -> None:
    args = parse_args()
    if not args.scored_csv.exists():
        raise FileNotFoundError(args.scored_csv)
    ensure_dir(args.out_dir)

    df = pd.read_csv(args.scored_csv)
    if df.empty:
        raise RuntimeError('Scored candidate pool is empty.')

    for col in ['selection_priority', 'v5_reference_gain_Hz', 'cascade_score', 'class_score', 'surrogate_pred_gap34_gain_Hz']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    sorted_df = sort_selection(df)
    if args.top_k > 0:
        sorted_df = sorted_df.head(min(args.top_k, len(sorted_df))).copy()

    cascade_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(sort_for_cascade(df)['sample_id'].astype(str), start=1)}
    surrogate_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(sort_for_surrogate(df)['sample_id'].astype(str), start=1)}

    manifest_rows: List[Dict[str, object]] = []
    label = 'directional_targeted_all' if args.top_k <= 0 else f'directional_targeted_top_{args.top_k}'
    for idx, (_, row) in enumerate(sorted_df.iterrows(), start=1):
        item = row.to_dict()
        item['validation_id'] = f'val{idx:03d}'
        item['selection_source'] = 'directional_targeted'
        item['selection_label'] = label
        item['rank_within_source'] = idx
        item['rank_cascade'] = cascade_rank_map.get(str(row['sample_id']), '')
        item['rank_surrogate'] = surrogate_rank_map.get(str(row['sample_id']), '')
        manifest_rows.append(item)

    manifest_csv = args.out_dir / 'comsol_validation_manifest_v6.csv'
    ordered_csv = args.out_dir / 'directional_targeted_candidates_for_validation.csv'
    summary_json = args.out_dir / 'validation_manifest_summary.json'

    extra_fields = [field for field in MANIFEST_FIELDS if field not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}]
    write_csv(ordered_csv, manifest_rows, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(manifest_csv, manifest_rows, MANIFEST_FIELDS)

    summary = {
        'scored_csv': str(args.scored_csv),
        'top_k': args.top_k,
        'manifest_rows': len(manifest_rows),
        'seed_rows': int((sorted_df['is_seed_shape'].astype(str).isin(['1', '1.0', 'True', 'true'])).sum()) if 'is_seed_shape' in sorted_df.columns else None,
        'directional_rows': int((sorted_df['target_rule'].astype(str) == 'directional_pm3_hit').sum()) if 'target_rule' in sorted_df.columns else None,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] validation manifest v6 built')
    print(f'[OUT] {manifest_csv}')
    print(f'[SUMMARY] total={len(manifest_rows)}')


if __name__ == '__main__':
    main()
