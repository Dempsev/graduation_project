from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHAPE_DATASET = ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv'
V5_RESULTS = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v5' / 'stage4_validation_results.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v6' / 'candidate_pool_v6_directional_targeted'
POINT_MANIFEST = OUT_DIR / 'candidate_point_manifest.csv'
SEED_MANIFEST = OUT_DIR / 'candidate_seed_manifest.csv'
POOL_CSV = OUT_DIR / 'candidate_pool_v6.csv'
INFO_JSON = OUT_DIR / 'candidate_pool_info.json'

POINT_SPEC = {
    'candidate_point_id': 'cp01',
    'pool_arm': 'exploitation',
    'pool_role': 'directional_step_neighborhood_exploitation',
    'point_strategy': 'v5_directional_step_targeted',
    'family_prior_source': 'stage4_validation_ab_v5_positive_directional_hits',
    'seed_prior_source': 'stage4_validation_ab_v5_positive_seeds',
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
    'step_num', 'step_offset', 'step_distance', 'step_window', 'is_seed_shape',
    'selection_priority', 'target_rule', 'preferred_direction', 'directional_offset', 'allowed_offsets',
    'v5_reference_validation_id', 'v5_reference_gain_Hz',
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
    parts = text.split('_')
    family = parts[0] if parts else text
    step_num = -1
    for part in parts:
        if part.startswith('step'):
            try:
                step_num = int(part[4:])
            except ValueError:
                step_num = -1
            break
    return family, step_num


def step_window(step_distance: int) -> str:
    if step_distance == 0:
        return 'seed'
    if step_distance == 3:
        return 'pm3'
    return 'other'


def direction_label(offset: int) -> str:
    if offset > 0:
        return 'plus'
    if offset < 0:
        return 'minus'
    return 'seed_only'


def build_seed_manifest() -> List[Dict[str, object]]:
    df = read_csv(V5_RESULTS)
    for col in ['gap34_gain_Hz', 'step_offset', 'is_seed_shape']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    targeted = df[df['selection_source'].astype(str) == 'cascade_targeted'].copy()
    positive = targeted[targeted['gap34_gain_Hz'] > 0].copy()
    seed_rows = positive[positive['is_seed_shape'] == 1].copy()
    if seed_rows.empty:
        raise RuntimeError('No positive seed rows found in v5 results.')

    rows: List[Dict[str, object]] = []
    seed_rows = seed_rows.sort_values(['gap34_gain_Hz', 'seed_shape_id'], ascending=[False, True])
    for index, (_, seed_row) in enumerate(seed_rows.iterrows(), start=1):
        seed_shape_id = str(seed_row['seed_shape_id'])
        seed_family, seed_step = parse_shape_id(seed_shape_id)
        directional = positive[(positive['seed_shape_id'].astype(str) == seed_shape_id) & (positive['step_offset'] != 0)].copy()
        if directional.empty:
            raise RuntimeError(f'No directional +3/-3 hit found for seed {seed_shape_id}')
        directional = directional.sort_values(['gap34_gain_Hz', 'step_offset'], ascending=[False, True])
        best_dir = directional.iloc[0]
        directional_offset = int(best_dir['step_offset'])
        allowed_offsets = [0, directional_offset]
        rows.append({
            'seed_index': index,
            'seed_shape_id': seed_shape_id,
            'seed_family': seed_family,
            'seed_step': seed_step,
            'seed_tier': 'core',
            'seed_source': str(seed_row.get('seed_source', 'validated_success')),
            'preferred_direction': direction_label(directional_offset),
            'directional_offset': directional_offset,
            'allowed_offsets': '|'.join(str(item) for item in allowed_offsets),
            'seed_validation_id': str(seed_row.get('validation_id', '')),
            'seed_gain_Hz': float(seed_row['gap34_gain_Hz']),
            'directional_shape_id': str(best_dir['shape_id']),
            'directional_validation_id': str(best_dir.get('validation_id', '')),
            'directional_gain_Hz': float(best_dir['gap34_gain_Hz']),
        })
    return rows


def build_candidate_pool(shape_df: pd.DataFrame, seed_manifest: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    working = shape_df.copy()
    parsed = working['shape_id'].astype(str).map(parse_shape_id)
    working['shape_family'] = parsed.map(lambda item: item[0])
    working['step_num'] = parsed.map(lambda item: item[1])

    rows: List[Dict[str, object]] = []
    counts_by_seed: Dict[str, int] = {}
    counts_by_rule: Dict[str, int] = {'seed_anchor': 0, 'directional_pm3_hit': 0}

    for seed in seed_manifest:
        offsets = [int(item) for item in str(seed['allowed_offsets']).split('|') if item]
        counts_by_seed[str(seed['seed_shape_id'])] = len(offsets)
        for offset in offsets:
            target_step = int(seed['seed_step']) + offset
            subset = working[
                (working['shape_family'].astype(str) == str(seed['seed_family']))
                & (working['step_num'] == target_step)
            ].copy()
            if subset.empty:
                raise RuntimeError(f'Missing shape for {seed["seed_shape_id"]} offset {offset:+d}')
            if len(subset) > 1:
                raise RuntimeError(f'Ambiguous shape match for {seed["seed_shape_id"]} offset {offset:+d}')
            shape = subset.iloc[0]
            is_seed_shape = 1 if offset == 0 else 0
            target_rule = 'seed_anchor' if is_seed_shape else 'directional_pm3_hit'
            reference_gain = float(seed['seed_gain_Hz']) if is_seed_shape else float(seed['directional_gain_Hz'])
            reference_validation_id = str(seed['seed_validation_id']) if is_seed_shape else str(seed['directional_validation_id'])
            counts_by_rule[target_rule] = counts_by_rule.get(target_rule, 0) + 1
            rows.append({
                'sample_id': f"candidate_pool_v6_{POINT_SPEC['candidate_point_id']}_{shape['shape_id']}",
                'source_stage': 'candidate_pool_v6',
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
                'step_num': int(shape['step_num']),
                'step_offset': offset,
                'step_distance': abs(offset),
                'step_window': step_window(abs(offset)),
                'is_seed_shape': is_seed_shape,
                'selection_priority': 0 if is_seed_shape else 1,
                'target_rule': target_rule,
                'preferred_direction': seed['preferred_direction'],
                'directional_offset': seed['directional_offset'],
                'allowed_offsets': seed['allowed_offsets'],
                'v5_reference_validation_id': reference_validation_id,
                'v5_reference_gain_Hz': reference_gain,
                'shape_id': shape['shape_id'],
                'shape_family': shape['shape_family'],
                'shape_role': shape.get('shape_role', 'screening'),
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

    rows.sort(key=lambda item: (int(item['selection_priority']), -float(item['v5_reference_gain_Hz']), str(item['shape_id'])))
    info = {
        'shape_dataset': str(SHAPE_DATASET),
        'source_results': str(V5_RESULTS),
        'point_id': POINT_SPEC['point_id'],
        'seed_count': len(seed_manifest),
        'candidate_rows': len(rows),
        'counts_by_seed': counts_by_seed,
        'counts_by_rule': counts_by_rule,
        'strategy': 'seed + family-specific successful one-sided pm3 only; pm6 removed',
    }
    return rows, info


def main() -> None:
    ensure_dir(OUT_DIR)
    shape_df = read_csv(SHAPE_DATASET)
    seed_manifest = build_seed_manifest()
    pool_rows, info = build_candidate_pool(shape_df, seed_manifest)

    write_csv(POINT_MANIFEST, [POINT_SPEC], [
        'candidate_point_id', 'pool_arm', 'pool_role', 'point_strategy', 'family_prior_source', 'seed_prior_source',
        'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    ])
    write_csv(SEED_MANIFEST, seed_manifest, [
        'seed_index', 'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
        'preferred_direction', 'directional_offset', 'allowed_offsets',
        'seed_validation_id', 'seed_gain_Hz',
        'directional_shape_id', 'directional_validation_id', 'directional_gain_Hz',
    ])
    write_csv(POOL_CSV, pool_rows, POOL_FIELDS)
    INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'[DONE] seeds: {len(seed_manifest)}')
    print(f'[DONE] candidate rows: {len(pool_rows)}')
    print(f'[OUT] {POINT_MANIFEST}')
    print(f'[OUT] {SEED_MANIFEST}')
    print(f'[OUT] {POOL_CSV}')
    print(f'[OUT] {INFO_JSON}')


if __name__ == '__main__':
    main()
