from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHAPE_DATASET = ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v7' / 'candidate_pool_v7_directional_transfer_probe'
POINT_MANIFEST = OUT_DIR / 'candidate_point_manifest.csv'
SEED_MANIFEST = OUT_DIR / 'candidate_seed_manifest.csv'
POOL_CSV = OUT_DIR / 'candidate_pool_v7.csv'
INFO_JSON = OUT_DIR / 'candidate_pool_info.json'

POINT_SPEC = {
    'candidate_point_id': 'cp01',
    'pool_arm': 'exploitation',
    'pool_role': 'directional_transfer_probe_exploitation',
    'point_strategy': 'v7_directional_transfer_probe',
    'family_prior_source': 'stage1_optional_seed_whitelist',
    'seed_prior_source': 'stage1_positive_optional_seed',
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

SEED_SPECS = [
    {
        'seed_index': 1,
        'seed_shape_id': 'ep119_step18_contour_xy',
        'seed_tier': 'optional',
        'seed_source': 'stage1_optional_seed',
    },
    {
        'seed_index': 2,
        'seed_shape_id': 'ep160_step15_contour_xy',
        'seed_tier': 'optional',
        'seed_source': 'stage1_optional_seed',
    },
    {
        'seed_index': 3,
        'seed_shape_id': 'ep172_step75_contour_xy',
        'seed_tier': 'optional',
        'seed_source': 'stage1_optional_seed',
    },
]

CANDIDATE_OFFSETS = [0, -3, 3, -6, 6]

POOL_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'shape_step', 'has_seed_context', 'step_num', 'step_offset', 'step_distance', 'step_direction_sign',
    'step_window', 'is_seed_shape', 'preferred_direction_sign', 'matches_preferred_direction', 'within_directional_window',
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
    if step_distance == 6:
        return 'pm6'
    return 'other'


def target_rule_for_distance(step_distance: int) -> str:
    if step_distance == 0:
        return 'optional_seed_anchor'
    if step_distance == 3:
        return 'optional_pm3_transfer_probe'
    if step_distance == 6:
        return 'optional_pm6_transfer_probe'
    return 'optional_other_probe'


def selection_priority_for_distance(step_distance: int) -> int:
    if step_distance == 0:
        return 0
    if step_distance == 3:
        return 1
    if step_distance == 6:
        return 2
    return 9


def sign_of(offset: int) -> int:
    if offset > 0:
        return 1
    if offset < 0:
        return -1
    return 0


def build_seed_manifest(shape_df: pd.DataFrame) -> List[Dict[str, object]]:
    parsed = shape_df['shape_id'].astype(str).map(parse_shape_id)
    working = shape_df.copy()
    working['shape_family'] = parsed.map(lambda item: item[0])
    working['step_num'] = parsed.map(lambda item: item[1])

    rows: List[Dict[str, object]] = []
    for seed in SEED_SPECS:
        seed_shape_id = str(seed['seed_shape_id'])
        seed_family, seed_step = parse_shape_id(seed_shape_id)
        subset = working[working['shape_family'].astype(str) == seed_family].copy()
        if subset.empty:
            raise RuntimeError(f'No shapes found for family {seed_family}')
        available_offsets = []
        available_shape_ids = []
        for offset in CANDIDATE_OFFSETS:
            target_step = seed_step + offset
            match = subset[subset['step_num'] == target_step]
            if match.empty:
                continue
            if len(match) > 1:
                raise RuntimeError(f'Ambiguous shape match for {seed_shape_id} offset {offset:+d}')
            available_offsets.append(offset)
            available_shape_ids.append(str(match.iloc[0]['shape_id']))
        if 0 not in available_offsets:
            raise RuntimeError(f'Seed shape missing from dataset: {seed_shape_id}')
        rows.append({
            'seed_index': seed['seed_index'],
            'seed_shape_id': seed_shape_id,
            'seed_family': seed_family,
            'seed_step': seed_step,
            'seed_tier': seed['seed_tier'],
            'seed_source': seed['seed_source'],
            'available_offsets': '|'.join(str(item) for item in available_offsets),
            'available_shape_ids': '|'.join(available_shape_ids),
            'candidate_count': len(available_offsets),
        })
    return rows


def build_candidate_pool(shape_df: pd.DataFrame, seed_manifest: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    working = shape_df.copy()
    parsed = working['shape_id'].astype(str).map(parse_shape_id)
    working['shape_family'] = parsed.map(lambda item: item[0])
    working['step_num'] = parsed.map(lambda item: item[1])

    rows: List[Dict[str, object]] = []
    counts_by_seed: Dict[str, int] = {}
    counts_by_rule: Dict[str, int] = {}

    for seed in seed_manifest:
        offsets = [int(item) for item in str(seed['available_offsets']).split('|') if item]
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
            step_distance = abs(offset)
            is_seed_shape = 1 if offset == 0 else 0
            target_rule = target_rule_for_distance(step_distance)
            counts_by_rule[target_rule] = counts_by_rule.get(target_rule, 0) + 1
            rows.append({
                'sample_id': f"candidate_pool_v7_{POINT_SPEC['candidate_point_id']}_{shape['shape_id']}",
                'source_stage': 'candidate_pool_v7',
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
                'shape_step': int(shape['step_num']),
                'has_seed_context': 1,
                'step_num': int(shape['step_num']),
                'step_offset': offset,
                'step_distance': step_distance,
                'step_direction_sign': sign_of(offset),
                'step_window': step_window(step_distance),
                'is_seed_shape': is_seed_shape,
                'preferred_direction_sign': 0,
                'matches_preferred_direction': 0,
                'within_directional_window': 1 if step_distance <= 3 else 0,
                'selection_priority': selection_priority_for_distance(step_distance),
                'target_rule': target_rule,
                'preferred_direction': '',
                'directional_offset': '',
                'allowed_offsets': seed['available_offsets'],
                'v5_reference_validation_id': '',
                'v5_reference_gain_Hz': '',
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

    rows.sort(key=lambda item: (int(item['selection_priority']), str(item['seed_shape_id']), int(item['step_offset'])))
    info = {
        'shape_dataset': str(SHAPE_DATASET),
        'point_id': str(POINT_SPEC['point_id']),
        'seed_count': len(seed_manifest),
        'candidate_rows': len(rows),
        'counts_by_seed': counts_by_seed,
        'counts_by_rule': counts_by_rule,
        'strategy': 'optional seeds only; use available seed/pm3/pm6 offsets to test directional generalization on new families',
    }
    return rows, info


def main() -> None:
    ensure_dir(OUT_DIR)
    shape_df = read_csv(SHAPE_DATASET)
    seed_manifest = build_seed_manifest(shape_df)
    pool_rows, info = build_candidate_pool(shape_df, seed_manifest)

    write_csv(POINT_MANIFEST, [POINT_SPEC], [
        'candidate_point_id', 'pool_arm', 'pool_role', 'point_strategy', 'family_prior_source', 'seed_prior_source',
        'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    ])
    write_csv(SEED_MANIFEST, seed_manifest, [
        'seed_index', 'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
        'available_offsets', 'available_shape_ids', 'candidate_count',
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
