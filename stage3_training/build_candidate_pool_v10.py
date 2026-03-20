from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHAPE_DATASET = ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv'
STAGE1_POSITIVE_CSV = ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'stage1_positive_shapes.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v10' / 'candidate_pool_v10_seed_only_refined'
POINT_MANIFEST = OUT_DIR / 'candidate_point_manifest.csv'
SEED_MANIFEST = OUT_DIR / 'candidate_seed_manifest.csv'
POOL_CSV = OUT_DIR / 'candidate_pool_v10.csv'
INFO_JSON = OUT_DIR / 'candidate_pool_info.json'

STAGE4_RESULT_FILES = [
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v2' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v3' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v5' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v6' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v7' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v8' / 'stage4_validation_results.csv',
    ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v9' / 'stage4_validation_results.csv',
]

POINT_SPEC = {
    'candidate_point_id': 'cp01',
    'pool_arm': 'exploitation',
    'pool_role': 'seed_only_family_discovery_exploitation',
    'point_strategy': 'v10_seed_only_refined',
    'family_prior_source': 'stage1_positive_family_best_seed_excluding_all_stage4_validated_families_through_v9',
    'seed_prior_source': 'stage1_positive_family_best_seed',
    'main_id': 'rf09',
    'point_id': 'rf09_h09_b5_002_a4_0015',
    'a1': 0.50,
    'a2': -0.12,
    'b1': 0.0,
    'b2': 0.04,
    'a3': 0.0,
    'b3': 0.0,
    'a4': 0.015,
    'b4': 0.0,
    'a5': 0.0,
    'b5': 0.02,
    'r0': 0.012,
    'shift': 200.0,
    'neigs': 20.0,
}

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


def collect_excluded_families() -> Set[str]:
    families: Set[str] = set()
    for path in STAGE4_RESULT_FILES:
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

    stage1 = stage1[~stage1['shape_family'].isin(excluded_families)].copy()
    stage1 = stage1[stage1['shape_id'].astype(str).isin(shape_lookup.index.astype(str))].copy()
    if stage1.empty:
        raise RuntimeError('No stage1 positive seeds remain after excluding validated families.')

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


def build_candidate_pool(shape_df: pd.DataFrame, seed_manifest: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    shape_lookup = shape_df.set_index('shape_id', drop=False)
    rows: List[Dict[str, object]] = []
    tier_counts: Dict[str, int] = {}

    for seed in seed_manifest:
        shape_id = str(seed['seed_shape_id'])
        if shape_id not in shape_lookup.index:
            raise RuntimeError(f'Missing shape features for {shape_id}')
        shape = shape_lookup.loc[shape_id]
        tier = str(seed['stage1_reference_candidate_tier'])
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        rows.append({
            'sample_id': f"candidate_pool_v10_{POINT_SPEC['candidate_point_id']}_{shape_id}",
            'source_stage': 'candidate_pool_v10',
            'source_role': POINT_SPEC['pool_role'],
            'pool_arm': POINT_SPEC['pool_arm'],
            'point_strategy': POINT_SPEC['point_strategy'],
            'family_prior_source': POINT_SPEC['family_prior_source'],
            'seed_prior_source': POINT_SPEC['seed_prior_source'],
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
            'target_rule': 'seed_only_family_discovery',
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
            'candidate_id': POINT_SPEC['candidate_point_id'],
            'main_id': POINT_SPEC['main_id'],
            'point_id': POINT_SPEC['point_id'],
            'a1': POINT_SPEC['a1'],
            'a2': POINT_SPEC['a2'],
            'b1': POINT_SPEC['b1'],
            'b2': POINT_SPEC['b2'],
            'a3': POINT_SPEC['a3'],
            'b3': POINT_SPEC['b3'],
            'a4': POINT_SPEC['a4'],
            'b4': POINT_SPEC['b4'],
            'a5': POINT_SPEC['a5'],
            'b5': POINT_SPEC['b5'],
            'r0': POINT_SPEC['r0'],
            'shift': POINT_SPEC['shift'],
            'neigs': POINT_SPEC['neigs'],
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

    rows.sort(key=lambda item: (-float(item['stage1_reference_gap_gain_Hz'] or 0.0), -float(item['stage1_reference_contact_length'] or 0.0), str(item['shape_id'])))
    info = {
        'shape_dataset': str(SHAPE_DATASET),
        'stage1_positive_csv': str(STAGE1_POSITIVE_CSV),
        'excluded_families_count': len(seed_manifest) and len(collect_excluded_families()) or 0,
        'point_id': POINT_SPEC['point_id'],
        'candidate_rows': len(rows),
        'family_count': len(rows),
        'counts_by_stage1_tier': tier_counts,
        'strategy': 'one best stage1-positive seed per never-stage4-validated family through v9; v10 shortlist prefers weak/strong tiers and reserves a few neutral probes',
    }
    return rows, info


def main() -> None:
    ensure_dir(OUT_DIR)
    shape_df = read_csv(SHAPE_DATASET)
    stage1_df = read_csv(STAGE1_POSITIVE_CSV)
    excluded_families = collect_excluded_families()
    seed_manifest = build_seed_manifest(shape_df, stage1_df, excluded_families)
    pool_rows, info = build_candidate_pool(shape_df, seed_manifest)
    info['excluded_families'] = sorted(excluded_families)

    write_csv(POINT_MANIFEST, [POINT_SPEC], [
        'candidate_point_id', 'pool_arm', 'pool_role', 'point_strategy', 'family_prior_source', 'seed_prior_source',
        'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    ])
    write_csv(SEED_MANIFEST, seed_manifest, [
        'seed_index', 'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
        'stage1_reference_sample_id', 'stage1_reference_fourier_id', 'stage1_reference_gap_Hz', 'stage1_reference_gap_gain_Hz',
        'stage1_reference_contact_length', 'stage1_reference_candidate_tier',
    ])
    write_csv(POOL_CSV, pool_rows, POOL_FIELDS)
    INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'[DONE] excluded families: {len(excluded_families)}')
    print(f'[DONE] seed candidates: {len(seed_manifest)}')
    print(f'[OUT] {POINT_MANIFEST}')
    print(f'[OUT] {SEED_MANIFEST}')
    print(f'[OUT] {POOL_CSV}')
    print(f'[OUT] {INFO_JSON}')


if __name__ == '__main__':
    main()
