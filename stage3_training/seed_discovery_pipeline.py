from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from objective_registry import (
    GENERIC_OBJECTIVE_NAME_COLUMN,
    GENERIC_OBJECTIVE_PREDICTION_COLUMN,
    GENERIC_PREDICTION_COLUMN,
)

POOL_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'shape_step', 'has_seed_context', 'step_num', 'step_offset', 'step_distance', 'step_direction_sign',
    'step_window', 'is_seed_shape', 'preferred_direction_sign', 'matches_preferred_direction', 'within_directional_window',
    'selection_priority', 'target_rule', 'preferred_direction', 'directional_offset', 'allowed_offsets',
    'v5_reference_validation_id', 'v5_reference_gain_Hz',
    'stage1_reference_sample_id', 'stage1_reference_fourier_id', 'stage1_reference_gap_Hz', 'stage1_reference_gap_gain_Hz',
    'stage1_reference_contact_length', 'stage1_reference_candidate_tier',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height', 'shape_bbox_aspect_ratio',
    'shape_centroid_x', 'shape_centroid_y', 'shape_point_count',
    'contact_length', 'n_domains',
    'gap34_Hz', 'gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive',
]

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
    GENERIC_OBJECTIVE_NAME_COLUMN, GENERIC_OBJECTIVE_PREDICTION_COLUMN, GENERIC_PREDICTION_COLUMN,
]

POINT_MANIFEST_FIELDS = [
    'candidate_point_id', 'pool_arm', 'pool_role', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
]

SEED_MANIFEST_FIELDS = [
    'seed_index', 'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'stage1_reference_sample_id', 'stage1_reference_fourier_id', 'stage1_reference_gap_Hz', 'stage1_reference_gap_gain_Hz',
    'stage1_reference_contact_length', 'stage1_reference_candidate_tier',
]

PRIMARY_TIERS = {'strong_positive', 'weak_positive'}
PROBE_TIERS = {'neutral_or_baseline_like'}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def parse_shape_id(shape_id: str) -> Tuple[str, int]:
    text = str(shape_id)
    family = text.split('_')[0] if text else ''
    match = re.search(r'_step(\d+)', text)
    step_num = int(match.group(1)) if match else -1
    return family, step_num


def collect_excluded_families(stage4_result_files: List[Path]) -> Set[str]:
    families: Set[str] = set()
    for path in stage4_result_files:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if 'shape_family' not in df.columns:
            continue
        families.update(df['shape_family'].astype(str).str.strip().tolist())
    return {item for item in families if item}


def build_seed_manifest(shape_df: pd.DataFrame, stage1_df: pd.DataFrame, excluded_families: Set[str]) -> List[Dict[str, object]]:
    shape_lookup = shape_df.set_index('shape_id', drop=False)

    stage1 = stage1_df.copy()
    stage1['shape_family'] = stage1['shape_id'].astype(str).map(lambda item: parse_shape_id(item)[0])
    stage1['seed_step'] = stage1['shape_id'].astype(str).map(lambda item: parse_shape_id(item)[1])
    for col in ['gap_gain_Hz', 'gap_target_Hz', 'contact_length']:
        stage1[col] = pd.to_numeric(stage1[col], errors='coerce')

    if excluded_families:
        stage1 = stage1[~stage1['shape_family'].isin(excluded_families)].copy()
    stage1 = stage1[stage1['shape_id'].astype(str).isin(shape_lookup.index.astype(str))].copy()
    if stage1.empty:
        raise RuntimeError('No stage1 positive seeds remain after applying family filters.')

    reps = stage1.sort_values(
        ['shape_family', 'gap_gain_Hz', 'contact_length', 'shape_id'],
        ascending=[True, False, False, True],
    ).groupby('shape_family', as_index=False).head(1).copy()
    reps = reps.sort_values(['gap_gain_Hz', 'contact_length', 'shape_family'], ascending=[False, False, True]).copy()

    rows: List[Dict[str, object]] = []
    for index, (_, row) in enumerate(reps.iterrows(), start=1):
        shape_id = str(row['shape_id'])
        seed_family, seed_step = parse_shape_id(shape_id)
        rows.append({
            'seed_index': index,
            'seed_shape_id': shape_id,
            'seed_family': seed_family,
            'seed_step': seed_step,
            'seed_tier': 'stage1_seed_only_candidate',
            'seed_source': 'stage1_positive_family_best_seed',
            'stage1_reference_sample_id': str(row.get('sample_id', '')),
            'stage1_reference_fourier_id': str(row.get('fourier_id', '')),
            'stage1_reference_gap_Hz': float(row['gap_target_Hz']) if pd.notna(row['gap_target_Hz']) else '',
            'stage1_reference_gap_gain_Hz': float(row['gap_gain_Hz']) if pd.notna(row['gap_gain_Hz']) else '',
            'stage1_reference_contact_length': float(row['contact_length']) if pd.notna(row['contact_length']) else '',
            'stage1_reference_candidate_tier': str(row.get('candidate_tier', '')),
        })
    return rows


def build_candidate_pool_rows(
    shape_df: pd.DataFrame,
    seed_manifest: List[Dict[str, object]],
    point_specs: List[Dict[str, object]],
    profile: Dict[str, Any],
    excluded_families_count: int,
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    shape_lookup = shape_df.set_index('shape_id', drop=False)
    rows: List[Dict[str, object]] = []
    tier_counts: Dict[str, int] = {}
    point_counts: Dict[str, int] = {}

    for seed in seed_manifest:
        shape_id = str(seed['seed_shape_id'])
        if shape_id not in shape_lookup.index:
            raise RuntimeError(f'Missing shape features for {shape_id}')
        shape = shape_lookup.loc[shape_id]
        tier = str(seed['stage1_reference_candidate_tier'])
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        for point in point_specs:
            point_id = str(point['point_id'])
            point_counts[point_id] = point_counts.get(point_id, 0) + 1
            rows.append({
                'sample_id': f"{profile['sample_prefix']}_{point['candidate_point_id']}_{shape_id}",
                'source_stage': profile['source_stage'],
                'source_role': point['pool_role'],
                'pool_arm': point['pool_arm'],
                'point_strategy': point['point_strategy'],
                'family_prior_source': point['family_prior_source'],
                'seed_prior_source': point['seed_prior_source'],
                'seed_shape_id': seed['seed_shape_id'],
                'seed_family': seed['seed_family'],
                'seed_step': seed['seed_step'],
                'seed_tier': seed['seed_tier'],
                'seed_source': seed['seed_source'],
                'shape_step': seed['seed_step'],
                'has_seed_context': 1,
                'step_num': seed['seed_step'],
                'step_offset': 0,
                'step_distance': 0,
                'step_direction_sign': 0,
                'step_window': 'seed',
                'is_seed_shape': 1,
                'preferred_direction_sign': 0,
                'matches_preferred_direction': 0,
                'within_directional_window': 1,
                'selection_priority': 0,
                'target_rule': str(profile.get('target_rule', 'seed_only_family_discovery')), 
                'preferred_direction': '',
                'directional_offset': '',
                'allowed_offsets': '0',
                'v5_reference_validation_id': '',
                'v5_reference_gain_Hz': '',
                'stage1_reference_sample_id': seed['stage1_reference_sample_id'],
                'stage1_reference_fourier_id': seed['stage1_reference_fourier_id'],
                'stage1_reference_gap_Hz': seed['stage1_reference_gap_Hz'],
                'stage1_reference_gap_gain_Hz': seed['stage1_reference_gap_gain_Hz'],
                'stage1_reference_contact_length': seed['stage1_reference_contact_length'],
                'stage1_reference_candidate_tier': seed['stage1_reference_candidate_tier'],
                'shape_id': shape_id,
                'shape_family': str(shape.get('shape_family', seed['seed_family'])),
                'shape_role': str(shape.get('shape_role', 'screening')),
                'candidate_id': point['candidate_point_id'],
                'main_id': point['main_id'],
                'point_id': point['point_id'],
                'a1': point['a1'],
                'a2': point['a2'],
                'b1': point['b1'],
                'b2': point['b2'],
                'a3': point['a3'],
                'b3': point['b3'],
                'a4': point['a4'],
                'b4': point['b4'],
                'a5': point['a5'],
                'b5': point['b5'],
                'r0': point['r0'],
                'shift': point['shift'],
                'neigs': point['neigs'],
                'shape_area': shape['shape_area'],
                'shape_perimeter': shape['shape_perimeter'],
                'shape_bbox_width': shape['shape_bbox_width'],
                'shape_bbox_height': shape['shape_bbox_height'],
                'shape_bbox_aspect_ratio': shape['shape_bbox_aspect_ratio'],
                'shape_centroid_x': shape['shape_centroid_x'],
                'shape_centroid_y': shape['shape_centroid_y'],
                'shape_point_count': shape['shape_point_count'],
                'contact_length': '',
                'n_domains': '',
                'gap34_Hz': '',
                'gap34_rel': '',
                'gap34_gain_Hz': '',
                'gap34_gain_rel': '',
                'max_gap_Hz': '',
                'max_gap_rel': '',
                'max_gap_lower_band': '',
                'max_gap_upper_band': '',
                'max_gap_center_freq': '',
                'is_gap34_positive': '',
                'is_gap34_gain_positive': '',
            })

    rows.sort(
        key=lambda item: (
            -float(item['stage1_reference_gap_gain_Hz'] or 0.0),
            -float(item['stage1_reference_contact_length'] or 0.0),
            str(item['shape_id']),
            str(item['candidate_id']),
        )
    )
    info = {
        'profile_name': profile['name'],
        'shape_dataset': str(profile['shape_dataset']),
        'stage1_positive_csv': str(profile['stage1_positive_csv']),
        'excluded_families_count': excluded_families_count,
        'point_count': len(point_specs),
        'point_ids': [str(point['point_id']) for point in point_specs],
        'anchor_point_id': str(point_specs[0]['point_id']) if point_specs else '',
        'candidate_rows': len(rows),
        'family_count': len(seed_manifest),
        'candidate_rows_per_family': len(point_specs),
        'counts_by_stage1_tier': tier_counts,
        'counts_by_point': point_counts,
        'strategy': profile['strategy_summary'],
    }
    return rows, info


def build_candidate_pool_for_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    out_dir = Path(profile['out_dir'])
    ensure_dir(out_dir)
    shape_df = read_csv(Path(profile['shape_dataset']))
    stage1_df = read_csv(Path(profile['stage1_positive_csv']))
    exclude_validated = bool(profile.get('exclude_stage4_validated_families', True))
    excluded_families = collect_excluded_families(list(profile['stage4_result_files'])) if exclude_validated else set()
    seed_manifest = build_seed_manifest(shape_df, stage1_df, excluded_families)
    pool_rows, info = build_candidate_pool_rows(shape_df, seed_manifest, list(profile['point_specs']), profile, len(excluded_families))
    info['excluded_families'] = sorted(excluded_families)

    point_manifest_path = out_dir / str(profile['point_manifest_name'])
    seed_manifest_path = out_dir / str(profile['seed_manifest_name'])
    pool_csv_path = out_dir / str(profile['pool_csv_name'])
    info_json_path = out_dir / str(profile['info_json_name'])

    write_csv(point_manifest_path, list(profile['point_specs']), POINT_MANIFEST_FIELDS)
    write_csv(seed_manifest_path, seed_manifest, SEED_MANIFEST_FIELDS)
    write_csv(pool_csv_path, pool_rows, POOL_FIELDS)
    info_json_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')

    return {
        'excluded_families': sorted(excluded_families),
        'seed_manifest': seed_manifest,
        'pool_rows': pool_rows,
        'info': info,
        'point_manifest_path': point_manifest_path,
        'seed_manifest_path': seed_manifest_path,
        'pool_csv_path': pool_csv_path,
        'info_json_path': info_json_path,
    }


def resolve_prediction_column(df: pd.DataFrame) -> str:
    if GENERIC_OBJECTIVE_PREDICTION_COLUMN in df.columns and len(df):
        col = str(df[GENERIC_OBJECTIVE_PREDICTION_COLUMN].iloc[0])
        if col and col in df.columns:
            return col
    if GENERIC_PREDICTION_COLUMN in df.columns:
        return GENERIC_PREDICTION_COLUMN
    if 'surrogate_pred_gap34_gain_Hz' in df.columns:
        return 'surrogate_pred_gap34_gain_Hz'
    raise KeyError('Unable to resolve surrogate prediction column from scored csv.')


def prepare_manifest_frame(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    work = df.copy()
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    numeric_cols = ['contact_prob', 'positive_prob', 'cascade_score', 'class_score', pred_col, 'stage1_reference_gap_gain_Hz', 'stage1_reference_contact_length']
    if GENERIC_PREDICTION_COLUMN in work.columns and GENERIC_PREDICTION_COLUMN not in numeric_cols:
        numeric_cols.append(GENERIC_PREDICTION_COLUMN)
    for col in numeric_cols:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors='coerce')
    for col in ['cascade_gate', 'contact_gate', 'positive_gate', 'reg_positive_gate']:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors='coerce').fillna(0).astype(int)
        else:
            work[col] = 0
    if GENERIC_OBJECTIVE_NAME_COLUMN not in work.columns:
        work[GENERIC_OBJECTIVE_NAME_COLUMN] = 'gap34_gain_Hz'
    if GENERIC_OBJECTIVE_PREDICTION_COLUMN not in work.columns:
        work[GENERIC_OBJECTIVE_PREDICTION_COLUMN] = pred_col
    if GENERIC_PREDICTION_COLUMN not in work.columns:
        work[GENERIC_PREDICTION_COLUMN] = work[pred_col]
    work['stage1_candidate_tier_rank'] = work['stage1_reference_candidate_tier'].astype(str).map(tier_map).fillna(-1).astype(int)
    work['selection_bucket'] = work['stage1_reference_candidate_tier'].astype(str).map(lambda x: 'primary' if x in PRIMARY_TIERS else ('probe' if x in PROBE_TIERS else 'other'))
    return work


def sort_primary(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    return df.sort_values(
        ['cascade_gate', 'contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', pred_col, 'stage1_reference_contact_length'],
        ascending=[False, False, False, False, False, False],
    ).copy()


def sort_probe(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    return df.sort_values(
        ['cascade_gate', 'contact_prob', 'stage1_reference_gap_gain_Hz', pred_col, 'stage1_reference_contact_length'],
        ascending=[False, False, False, False, False],
    ).copy()


def can_take(row: pd.Series, shape_counts: Dict[str, int], family_counts: Dict[str, int], max_per_shape: int, max_per_family: int) -> bool:
    shape_id = str(row.get('shape_id', ''))
    family_id = str(row.get('shape_family', ''))
    if max_per_shape > 0 and shape_counts.get(shape_id, 0) >= max_per_shape:
        return False
    if max_per_family > 0 and family_counts.get(family_id, 0) >= max_per_family:
        return False
    return True


def register_selection(row: pd.Series, bucket: str, sample_ids: Set[str], shape_counts: Dict[str, int], family_counts: Dict[str, int], point_counts: Dict[str, int]) -> Dict[str, object]:
    item = row.to_dict()
    item['selection_bucket'] = bucket
    sample_id = str(row['sample_id'])
    shape_id = str(row.get('shape_id', ''))
    family_id = str(row.get('shape_family', ''))
    point_id = str(row.get('point_id', ''))
    sample_ids.add(sample_id)
    shape_counts[shape_id] = shape_counts.get(shape_id, 0) + 1
    family_counts[family_id] = family_counts.get(family_id, 0) + 1
    point_counts[point_id] = point_counts.get(point_id, 0) + 1
    return item


def take_rows(sorted_df: pd.DataFrame, limit: int, bucket: str, sample_ids: Set[str], shape_counts: Dict[str, int], family_counts: Dict[str, int], point_counts: Dict[str, int], max_per_shape: int, max_per_family: int) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    if limit <= 0:
        return rows
    for _, row in sorted_df.iterrows():
        sample_id = str(row['sample_id'])
        if sample_id in sample_ids:
            continue
        if not can_take(row, shape_counts, family_counts, max_per_shape, max_per_family):
            continue
        rows.append(register_selection(row, bucket, sample_ids, shape_counts, family_counts, point_counts))
        if len(rows) >= limit:
            break
    return rows


def sort_diversity(df: pd.DataFrame, point_counts: Dict[str, int], family_counts: Dict[str, int], pred_col: str) -> pd.DataFrame:
    work = df.copy()
    work['diversity_new_point'] = work['point_id'].astype(str).map(lambda x: 1 if point_counts.get(x, 0) == 0 else 0)
    work['diversity_new_family'] = work['shape_family'].astype(str).map(lambda x: 1 if family_counts.get(x, 0) == 0 else 0)
    return work.sort_values(
        ['diversity_new_point', 'diversity_new_family', 'cascade_gate', 'contact_prob', 'stage1_candidate_tier_rank', pred_col, 'stage1_reference_gap_gain_Hz'],
        ascending=[False, False, False, False, False, False, False],
    ).copy()


def take_diversity_rows(df: pd.DataFrame, limit: int, sample_ids: Set[str], shape_counts: Dict[str, int], family_counts: Dict[str, int], point_counts: Dict[str, int], max_per_shape: int, max_per_family: int, pred_col: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    if limit <= 0:
        return rows
    while len(rows) < limit:
        remaining = df[~df['sample_id'].astype(str).isin(sample_ids)].copy()
        if remaining.empty:
            break
        sorted_df = sort_diversity(remaining, point_counts, family_counts, pred_col)
        picked = False
        for _, row in sorted_df.iterrows():
            if not can_take(row, shape_counts, family_counts, max_per_shape, max_per_family):
                continue
            rows.append(register_selection(row, 'diversity', sample_ids, shape_counts, family_counts, point_counts))
            picked = True
            break
        if not picked:
            break
    return rows


def build_selection(df: pd.DataFrame, pred_col: str, policy: Dict[str, Any]) -> pd.DataFrame:
    sample_ids: Set[str] = set()
    shape_counts: Dict[str, int] = {}
    family_counts: Dict[str, int] = {}
    point_counts: Dict[str, int] = {}
    primary_k = int(policy.get('primary_k', 0))
    probe_k = int(policy.get('probe_k', 0))
    diversity_k = int(policy.get('diversity_k', 0))
    max_per_shape = int(policy.get('max_per_shape', 0))
    max_per_family = int(policy.get('max_per_family', 0))

    selected_rows: List[Dict[str, object]] = []
    selected_rows.extend(take_rows(sort_primary(df[df['selection_bucket'] == 'primary'], pred_col), primary_k, 'primary', sample_ids, shape_counts, family_counts, point_counts, max_per_shape, max_per_family))
    selected_rows.extend(take_rows(sort_probe(df[df['selection_bucket'] == 'probe'], pred_col), probe_k, 'probe', sample_ids, shape_counts, family_counts, point_counts, max_per_shape, max_per_family))
    selected_rows.extend(take_diversity_rows(df, diversity_k, sample_ids, shape_counts, family_counts, point_counts, max_per_shape, max_per_family, pred_col))

    combined = pd.DataFrame(selected_rows)
    if combined.empty:
        return combined
    combined['bucket_priority'] = combined['selection_bucket'].map({'primary': 0, 'probe': 1, 'diversity': 2}).fillna(9)
    combined = combined.sort_values(
        ['bucket_priority', 'cascade_gate', 'contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', pred_col],
        ascending=[True, False, False, False, False, False],
    ).copy()
    return combined


def sort_for_surrogate(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    return df.sort_values([pred_col, 'contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz'], ascending=[False, False, False, False]).copy()


def build_validation_manifest_for_profile(profile: Dict[str, Any], policy: Dict[str, Any], scored_csv: Path | None = None, out_dir: Path | None = None) -> Dict[str, Any]:
    manifest_cfg = dict(profile['manifest'])
    scored_csv = scored_csv or Path(manifest_cfg['scored_csv'])
    out_dir = out_dir or Path(manifest_cfg['out_dir'])
    if not scored_csv.exists():
        raise FileNotFoundError(scored_csv)
    ensure_dir(out_dir)

    df = pd.read_csv(scored_csv)
    if df.empty:
        raise RuntimeError('Scored candidate pool is empty.')

    pred_col = resolve_prediction_column(df)
    work = prepare_manifest_frame(df, pred_col)
    selected = build_selection(work, pred_col, policy)
    if selected.empty:
        raise RuntimeError('No validation rows selected.')

    cascade_order = work.sort_values(
        ['cascade_gate', 'contact_prob', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', pred_col],
        ascending=[False, False, False, False, False],
    ).copy()
    cascade_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(cascade_order['sample_id'].astype(str), start=1)}
    surrogate_rank_map = {str(sample_id): idx for idx, sample_id in enumerate(sort_for_surrogate(work, pred_col)['sample_id'].astype(str), start=1)}

    manifest_rows: List[Dict[str, object]] = []
    label = f"{manifest_cfg['selection_label_prefix']}_primary_{int((selected['selection_bucket'] == 'primary').sum())}_probe_{int((selected['selection_bucket'] == 'probe').sum())}_diversity_{int((selected['selection_bucket'] == 'diversity').sum())}"
    for idx, (_, row) in enumerate(selected.iterrows(), start=1):
        item = row.to_dict()
        item['validation_id'] = f'val{idx:03d}'
        item['selection_source'] = manifest_cfg['selection_source']
        item['selection_label'] = label
        item['rank_within_source'] = idx
        item['rank_cascade'] = cascade_rank_map.get(str(row['sample_id']), '')
        item['rank_surrogate'] = surrogate_rank_map.get(str(row['sample_id']), '')
        if pred_col == 'surrogate_pred_gap34_gain_Hz' and GENERIC_PREDICTION_COLUMN in item:
            item['surrogate_pred_gap34_gain_Hz'] = item[GENERIC_PREDICTION_COLUMN]
        manifest_rows.append(item)

    manifest_csv = out_dir / str(manifest_cfg['manifest_csv_name'])
    ordered_csv = out_dir / str(manifest_cfg['ordered_csv_name'])
    summary_json = out_dir / 'validation_manifest_summary.json'

    extra_fields = [field for field in MANIFEST_FIELDS if field not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}]
    write_csv(ordered_csv, manifest_rows, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(manifest_csv, manifest_rows, MANIFEST_FIELDS)

    summary = {
        'profile_name': profile['name'],
        'scored_csv': str(scored_csv),
        'prediction_column': pred_col,
        'primary_k': int(policy.get('primary_k', 0)),
        'probe_k': int(policy.get('probe_k', 0)),
        'diversity_k': int(policy.get('diversity_k', 0)),
        'max_per_shape': int(policy.get('max_per_shape', 0)),
        'max_per_family': int(policy.get('max_per_family', 0)),
        'manifest_rows': len(manifest_rows),
        'primary_rows': int((selected['selection_bucket'] == 'primary').sum()),
        'probe_rows': int((selected['selection_bucket'] == 'probe').sum()),
        'diversity_rows': int((selected['selection_bucket'] == 'diversity').sum()),
        'strong_positive_count': int((selected['stage1_reference_candidate_tier'].astype(str) == 'strong_positive').sum()),
        'weak_positive_count': int((selected['stage1_reference_candidate_tier'].astype(str) == 'weak_positive').sum()),
        'neutral_count': int((selected['stage1_reference_candidate_tier'].astype(str) == 'neutral_or_baseline_like').sum()),
        'unique_shape_count': int(selected['shape_id'].astype(str).nunique()),
        'unique_family_count': int(selected['shape_family'].astype(str).nunique()),
        'unique_point_count': int(selected['point_id'].astype(str).nunique()),
        'selection_source': manifest_cfg['selection_source'],
        'selection_label': label,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    return {
        'manifest_rows': manifest_rows,
        'summary': summary,
        'manifest_csv': manifest_csv,
        'ordered_csv': ordered_csv,
        'summary_json': summary_json,
        'prediction_column': pred_col,
    }
