from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v8' / 'cascade_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v8' / 'validation_manifest_v8'

MANIFEST_FIELDS = [
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source', 'rank_cascade', 'rank_surrogate',
    'sample_id',
    'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'shape_step', 'has_seed_context', 'step_num', 'step_offset', 'step_distance', 'step_direction_sign',
    'step_window', 'is_seed_shape', 'preferred_direction_sign', 'matches_preferred_direction', 'within_directional_window',
    'selection_priority', 'target_rule', 'preferred_direction', 'directional_offset', 'allowed_offsets',
    'v5_reference_validation_id', 'v5_reference_gain_Hz',
    'stage1_reference_sample_id', 'stage1_reference_fourier_id', 'stage1_reference_gap_Hz', 'stage1_reference_gap_gain_Hz',
    'stage1_reference_contact_length', 'stage1_reference_candidate_tier',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'class_score', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build v8 COMSOL validation manifest for seed-only family discovery.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--top-k', type=int, default=12)
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
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    work = df.copy()
    work['stage1_candidate_tier_rank'] = work['stage1_reference_candidate_tier'].astype(str).map(tier_map).fillna(-1).astype(int)
    work['contact_prob_bucket'] = pd.to_numeric(work['contact_prob'], errors='coerce').round(4)
    work['positive_prob_bucket'] = pd.to_numeric(work['positive_prob'], errors='coerce').round(4)
    return work.sort_values(
        ['cascade_gate', 'contact_prob_bucket', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', 'positive_prob_bucket', 'surrogate_pred_gap34_gain_Hz', 'stage1_reference_contact_length', 'contact_prob'],
        ascending=[False, False, False, False, False, False, False, False],
    ).copy()


def sort_for_cascade(df: pd.DataFrame) -> pd.DataFrame:
    return sort_selection(df)


def sort_for_surrogate(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work['stage1_candidate_tier_rank'] = work['stage1_reference_candidate_tier'].astype(str).map({'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}).fillna(-1).astype(int)
    work['contact_prob_bucket'] = pd.to_numeric(work['contact_prob'], errors='coerce').round(4)
    return work.sort_values(['surrogate_pred_gap34_gain_Hz', 'contact_prob_bucket', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', 'contact_prob'], ascending=[False, False, False, False, False]).copy()


def main() -> None:
    args = parse_args()
    if not args.scored_csv.exists():
        raise FileNotFoundError(args.scored_csv)
    ensure_dir(args.out_dir)

    df = pd.read_csv(args.scored_csv)
    if df.empty:
        raise RuntimeError('Scored candidate pool is empty.')

    for col in ['contact_prob', 'positive_prob', 'cascade_score', 'class_score', 'surrogate_pred_gap34_gain_Hz', 'stage1_reference_gap_gain_Hz', 'stage1_reference_contact_length']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    sorted_df = sort_selection(df).head(min(args.top_k, len(df))).copy()
    cascade_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(sort_for_cascade(df)['sample_id'].astype(str), start=1)}
    surrogate_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(sort_for_surrogate(df)['sample_id'].astype(str), start=1)}

    manifest_rows: List[Dict[str, object]] = []
    label = f'seed_only_discovery_top_{len(sorted_df)}'
    for idx, (_, row) in enumerate(sorted_df.iterrows(), start=1):
        item = row.to_dict()
        item['validation_id'] = f'val{idx:03d}'
        item['selection_source'] = 'seed_only_discovery'
        item['selection_label'] = label
        item['rank_within_source'] = idx
        item['rank_cascade'] = cascade_rank_map.get(str(row['sample_id']), '')
        item['rank_surrogate'] = surrogate_rank_map.get(str(row['sample_id']), '')
        manifest_rows.append(item)

    manifest_csv = args.out_dir / 'comsol_validation_manifest_v8.csv'
    ordered_csv = args.out_dir / 'seed_only_candidates_for_validation.csv'
    summary_json = args.out_dir / 'validation_manifest_summary.json'

    extra_fields = [field for field in MANIFEST_FIELDS if field not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}]
    write_csv(ordered_csv, manifest_rows, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(manifest_csv, manifest_rows, MANIFEST_FIELDS)

    summary = {
        'scored_csv': str(args.scored_csv),
        'top_k': args.top_k,
        'manifest_rows': len(manifest_rows),
        'cascade_gate_count': int(pd.to_numeric(sorted_df['cascade_gate'], errors='coerce').fillna(0).astype(int).sum()),
        'strong_positive_count': int((sorted_df['stage1_reference_candidate_tier'].astype(str) == 'strong_positive').sum()),
        'weak_positive_count': int((sorted_df['stage1_reference_candidate_tier'].astype(str) == 'weak_positive').sum()),
        'neutral_count': int((sorted_df['stage1_reference_candidate_tier'].astype(str) == 'neutral_or_baseline_like').sum()),
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] validation manifest v8 built')
    print(f'[OUT] {manifest_csv}')
    print(f'[SUMMARY] total={len(manifest_rows)}')


if __name__ == '__main__':
    main()
