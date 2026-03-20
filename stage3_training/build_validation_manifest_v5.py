from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v5' / 'cascade_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v5' / 'validation_manifest_v5'

MANIFEST_FIELDS = [
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source', 'rank_cascade', 'rank_surrogate',
    'sample_id',
    'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'step_num', 'step_offset', 'step_distance', 'step_window', 'is_seed_shape',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'class_score', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build v5 COMSOL validation manifest for targeted step-neighborhood exploitation.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--gated-top-k', type=int, default=0, help='0 means keep all gated rows')
    parser.add_argument('--probe-top-k', type=int, default=0, help='0 means keep all nongated rows')
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


def sort_for_cascade(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['cascade_gate', 'seed_tier_priority', 'step_distance', 'cascade_score', 'surrogate_pred_gap34_gain_Hz'],
        ascending=[False, True, True, False, False],
    ).copy()


def sort_for_surrogate(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['surrogate_pred_gap34_gain_Hz', 'seed_tier_priority', 'step_distance', 'class_score'],
        ascending=[False, True, True, False],
    ).copy()


def limit_rows(df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    if top_k <= 0:
        return df.copy()
    return df.head(min(top_k, len(df))).copy()


def attach_rank_maps(df: pd.DataFrame) -> pd.DataFrame:
    cascade_sorted = sort_for_cascade(df)
    surrogate_sorted = sort_for_surrogate(df)
    cascade_rank = {str(sample_id): idx for idx, sample_id in enumerate(cascade_sorted['sample_id'].astype(str), start=1)}
    surrogate_rank = {str(sample_id): idx for idx, sample_id in enumerate(surrogate_sorted['sample_id'].astype(str), start=1)}
    ranked = df.copy()
    ranked['rank_cascade'] = ranked['sample_id'].astype(str).map(cascade_rank)
    ranked['rank_surrogate'] = ranked['sample_id'].astype(str).map(surrogate_rank)
    return ranked


def build_selection_rows(df: pd.DataFrame, selection_source: str, selection_label: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        rows.append({
            'selection_source': selection_source,
            'selection_label': selection_label,
            'rank_within_source': idx,
            **row.to_dict(),
        })
    return rows


def main() -> None:
    args = parse_args()
    if not args.scored_csv.exists():
        raise FileNotFoundError(args.scored_csv)
    ensure_dir(args.out_dir)

    df = pd.read_csv(args.scored_csv)
    if df.empty:
        raise RuntimeError('Scored candidate pool is empty.')

    for col in ['cascade_score', 'class_score', 'surrogate_pred_gap34_gain_Hz', 'step_distance']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['seed_tier_priority'] = pd.to_numeric(df.get('seed_tier_priority', 1), errors='coerce').fillna(1)
    df = attach_rank_maps(df)

    cascade_sorted = sort_for_cascade(df)
    gated_rows = limit_rows(cascade_sorted[cascade_sorted['cascade_gate'] == 1].copy(), args.gated_top_k)
    probe_rows = limit_rows(cascade_sorted[cascade_sorted['cascade_gate'] != 1].copy(), args.probe_top_k)

    gated_label = 'cascade_targeted_all' if args.gated_top_k <= 0 else f'cascade_targeted_top_{args.gated_top_k}'
    probe_label = 'targeted_probe_all' if args.probe_top_k <= 0 else f'targeted_probe_top_{args.probe_top_k}'
    gated_selection = build_selection_rows(gated_rows, 'cascade_targeted', gated_label)
    probe_selection = build_selection_rows(probe_rows, 'targeted_probe', probe_label)
    manifest_rows = gated_selection + probe_selection

    for idx, row in enumerate(manifest_rows, start=1):
        row['validation_id'] = f'val{idx:03d}'

    gated_csv = args.out_dir / 'cascade_targeted_candidates_for_validation.csv'
    probe_csv = args.out_dir / 'targeted_probe_candidates_for_validation.csv'
    manifest_csv = args.out_dir / 'comsol_validation_manifest_v5.csv'
    summary_json = args.out_dir / 'validation_manifest_summary.json'

    extra_fields = [field for field in MANIFEST_FIELDS if field not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}]
    write_csv(gated_csv, gated_selection, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(probe_csv, probe_selection, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(manifest_csv, manifest_rows, MANIFEST_FIELDS)

    summary = {
        'scored_csv': str(args.scored_csv),
        'gated_top_k': args.gated_top_k,
        'probe_top_k': args.probe_top_k,
        'gated_rows': len(gated_selection),
        'probe_rows': len(probe_selection),
        'manifest_rows': len(manifest_rows),
        'core_rows': int((df['seed_tier'].astype(str) == 'core').sum()),
        'optional_rows': int((df['seed_tier'].astype(str) == 'optional').sum()),
        'seed_rows': int((pd.to_numeric(df['is_seed_shape'], errors='coerce').fillna(0) == 1).sum()),
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] validation manifest v5 built')
    print(f'[OUT] {manifest_csv}')
    print(f"[SUMMARY] gated={len(gated_selection)} probe={len(probe_selection)} total={len(manifest_rows)}")


if __name__ == '__main__':
    main()
