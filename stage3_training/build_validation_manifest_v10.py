from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'seed_discovery_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'validation_manifest_v10'

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

PRIMARY_TIERS = {'strong_positive', 'weak_positive'}
PROBE_TIERS = {'neutral_or_baseline_like'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build v10 COMSOL validation manifest for refined seed-only discovery.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--primary-k', type=int, default=6)
    parser.add_argument('--probe-k', type=int, default=2)
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


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    for col in ['contact_prob', 'positive_prob', 'cascade_score', 'class_score', 'surrogate_pred_gap34_gain_Hz', 'stage1_reference_gap_gain_Hz', 'stage1_reference_contact_length']:
        work[col] = pd.to_numeric(work[col], errors='coerce')
    work['stage1_candidate_tier_rank'] = work['stage1_reference_candidate_tier'].astype(str).map(tier_map).fillna(-1).astype(int)
    work['selection_bucket'] = work['stage1_reference_candidate_tier'].astype(str).map(lambda x: 'primary' if x in PRIMARY_TIERS else ('probe' if x in PROBE_TIERS else 'other'))
    return work


def sort_primary(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', 'surrogate_pred_gap34_gain_Hz', 'stage1_reference_contact_length'],
        ascending=[False, False, False, False, False],
    ).copy()


def sort_probe(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['contact_prob', 'stage1_reference_gap_gain_Hz', 'surrogate_pred_gap34_gain_Hz', 'stage1_reference_contact_length'],
        ascending=[False, False, False, False],
    ).copy()


def build_selection(df: pd.DataFrame, primary_k: int, probe_k: int) -> pd.DataFrame:
    primary = sort_primary(df[df['selection_bucket'] == 'primary']).head(max(primary_k, 0)).copy()
    probe = sort_probe(df[df['selection_bucket'] == 'probe']).head(max(probe_k, 0)).copy()
    combined = pd.concat([primary, probe], ignore_index=True)
    combined['bucket_priority'] = combined['selection_bucket'].map({'primary': 0, 'probe': 1}).fillna(9)
    combined = combined.sort_values(
        ['bucket_priority', 'contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', 'surrogate_pred_gap34_gain_Hz'],
        ascending=[True, False, False, False, False],
    ).copy()
    return combined


def sort_for_surrogate(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(['surrogate_pred_gap34_gain_Hz', 'contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz'], ascending=[False, False, False, False]).copy()


def main() -> None:
    args = parse_args()
    if not args.scored_csv.exists():
        raise FileNotFoundError(args.scored_csv)
    ensure_dir(args.out_dir)

    df = pd.read_csv(args.scored_csv)
    if df.empty:
        raise RuntimeError('Scored candidate pool is empty.')

    work = prepare_frame(df)
    selected = build_selection(work, args.primary_k, args.probe_k)
    cascade_order = pd.concat([sort_primary(work), sort_probe(work)], ignore_index=True)
    cascade_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(cascade_order['sample_id'].astype(str), start=1)}
    surrogate_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(sort_for_surrogate(work)['sample_id'].astype(str), start=1)}

    manifest_rows: List[Dict[str, object]] = []
    label = f'seed_only_refined_primary_{len(selected[selected["selection_bucket"]=="primary"])}_probe_{len(selected[selected["selection_bucket"]=="probe"])}'
    for idx, (_, row) in enumerate(selected.iterrows(), start=1):
        item = row.to_dict()
        item['validation_id'] = f'val{idx:03d}'
        item['selection_source'] = 'seed_only_refined'
        item['selection_label'] = label
        item['rank_within_source'] = idx
        item['rank_cascade'] = cascade_rank_map.get(str(row['sample_id']), '')
        item['rank_surrogate'] = surrogate_rank_map.get(str(row['sample_id']), '')
        manifest_rows.append(item)

    manifest_csv = args.out_dir / 'comsol_validation_manifest_v10.csv'
    ordered_csv = args.out_dir / 'seed_only_refined_candidates_for_validation_v10.csv'
    summary_json = args.out_dir / 'validation_manifest_summary.json'

    extra_fields = [field for field in MANIFEST_FIELDS if field not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}]
    write_csv(ordered_csv, manifest_rows, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(manifest_csv, manifest_rows, MANIFEST_FIELDS)

    summary = {
        'scored_csv': str(args.scored_csv),
        'primary_k': args.primary_k,
        'probe_k': args.probe_k,
        'manifest_rows': len(manifest_rows),
        'primary_rows': int((selected['selection_bucket'] == 'primary').sum()),
        'probe_rows': int((selected['selection_bucket'] == 'probe').sum()),
        'strong_positive_count': int((selected['stage1_reference_candidate_tier'].astype(str) == 'strong_positive').sum()),
        'weak_positive_count': int((selected['stage1_reference_candidate_tier'].astype(str) == 'weak_positive').sum()),
        'neutral_count': int((selected['stage1_reference_candidate_tier'].astype(str) == 'neutral_or_baseline_like').sum()),
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] validation manifest v10 built')
    print(f'[OUT] {manifest_csv}')
    print(f'[SUMMARY] total={len(manifest_rows)} primary={summary["primary_rows"]} probe={summary["probe_rows"]}')


if __name__ == '__main__':
    main()
