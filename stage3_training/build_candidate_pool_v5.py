from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHAPE_DATASET = ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v5' / 'candidate_pool_v5_step_targeted'
POINT_MANIFEST = OUT_DIR / 'candidate_point_manifest.csv'
SEED_MANIFEST = OUT_DIR / 'candidate_seed_manifest.csv'
POOL_CSV = OUT_DIR / 'candidate_pool_v5.csv'
INFO_JSON = OUT_DIR / 'candidate_pool_info.json'

POINT_SPEC = {
    'candidate_point_id': 'cp01',
    'pool_arm': 'exploitation',
    'pool_role': 'step_neighborhood_exploitation',
    'point_strategy': 'step_neighborhood_targeted',
    'family_prior_source': 'validated_step_seed_list',
    'seed_prior_source': 'v5_curated_seed_list',
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

CORE_SEEDS = [
    {'seed_shape_id': 'ep218_step36_contour_xy', 'seed_tier': 'core', 'seed_source': 'validated_success'},
    {'seed_shape_id': 'ep215_step51_contour_xy', 'seed_tier': 'core', 'seed_source': 'validated_success'},
    {'seed_shape_id': 'ep193_step51_contour_xy', 'seed_tier': 'core', 'seed_source': 'known_positive'},
    {'seed_shape_id': 'ep239_step27_contour_xy', 'seed_tier': 'core', 'seed_source': 'known_positive'},
    {'seed_shape_id': 'ep253_step54_contour_xy', 'seed_tier': 'core', 'seed_source': 'known_positive'},
    {'seed_shape_id': 'ep209_step63_contour_xy', 'seed_tier': 'core', 'seed_source': 'known_positive_specialcase'},
]

OPTIONAL_SEEDS = [
    {'seed_shape_id': 'ep119_step18_contour_xy', 'seed_tier': 'optional', 'seed_source': 'known_positive'},
    {'seed_shape_id': 'ep160_step15_contour_xy', 'seed_tier': 'optional', 'seed_source': 'known_positive'},
    {'seed_shape_id': 'ep172_step75_contour_xy', 'seed_tier': 'optional', 'seed_source': 'known_positive'},
]

TARGET_OFFSETS = {0, 3, 6}

POOL_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    'step_num', 'step_offset', 'step_distance', 'step_window', 'is_seed_shape',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height', 'shape_bbox_aspect_ratio',
    'shape_centroid_x', 'shape_centroid_y', 'shape_point_count',
    'contact_length', 'n_domains',
    'gap34_Hz', 'gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build v5 step-aware targeted candidate pool.')
    parser.add_argument('--include-optional-seeds', action='store_true')
    return parser.parse_args()


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
    return 'out_of_window'


def build_seed_manifest(include_optional: bool) -> List[Dict[str, object]]:
    seeds = list(CORE_SEEDS)
    if include_optional:
        seeds.extend(OPTIONAL_SEEDS)
    rows: List[Dict[str, object]] = []
    for index, seed in enumerate(seeds, start=1):
        family, step_num = parse_shape_id(str(seed['seed_shape_id']))
        rows.append({
            'seed_index': index,
            'seed_shape_id': seed['seed_shape_id'],
            'seed_family': family,
            'seed_step': step_num,
            'seed_tier': seed['seed_tier'],
            'seed_source': seed['seed_source'],
        })
    return rows


def candidate_preference(row: Dict[str, object]) -> Tuple[int, int, str]:
    tier_priority = 0 if str(row['seed_tier']) == 'core' else 1
    return tier_priority, int(row['step_distance']), str(row['seed_shape_id'])


def build_candidate_pool(shape_df: pd.DataFrame, seed_manifest: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    working = shape_df.copy()
    parsed = working['shape_id'].astype(str).map(parse_shape_id)
    working['shape_family'] = parsed.map(lambda item: item[0])
    working['step_num'] = parsed.map(lambda item: item[1])

    deduped: Dict[str, Dict[str, object]] = {}
    counts_by_seed: Dict[str, int] = {}
    counts_by_window: Dict[str, int] = {'seed': 0, 'pm3': 0, 'pm6': 0}

    for seed in seed_manifest:
        family = str(seed['seed_family'])
        seed_step = int(seed['seed_step'])
        subset = working[(working['shape_family'].astype(str) == family) & (working['step_num'] >= 0)].copy()
        subset['step_offset'] = subset['step_num'] - seed_step
        subset['step_distance'] = subset['step_offset'].abs()
        subset = subset[subset['step_distance'].isin(TARGET_OFFSETS)].copy()

        counts_by_seed[str(seed['seed_shape_id'])] = int(len(subset))
        for _, shape in subset.iterrows():
            shape_id = str(shape['shape_id'])
            step_distance = int(shape['step_distance'])
            step_offset = int(shape['step_offset'])
            window = step_window(step_distance)
            candidate = {
                'sample_id': f"candidate_pool_v5_{POINT_SPEC['candidate_point_id']}_{shape_id}",
                'source_stage': 'candidate_pool_v5',
                'source_role': POINT_SPEC['pool_role'],
                'pool_arm': POINT_SPEC['pool_arm'],
                'point_strategy': POINT_SPEC['point_strategy'],
                'family_prior_source': POINT_SPEC['family_prior_source'],
                'seed_prior_source': POINT_SPEC['seed_prior_source'],
                'seed_shape_id': seed['seed_shape_id'],
                'seed_family': family,
                'seed_step': seed_step,
                'seed_tier': seed['seed_tier'],
                'seed_source': seed['seed_source'],
                'step_num': int(shape['step_num']),
                'step_offset': step_offset,
                'step_distance': step_distance,
                'step_window': window,
                'is_seed_shape': 1 if step_distance == 0 else 0,
                'shape_id': shape_id,
                'shape_family': str(shape['shape_family']),
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
            }
            existing = deduped.get(shape_id)
            if existing is None or candidate_preference(candidate) < candidate_preference(existing):
                deduped[shape_id] = candidate

    rows = list(deduped.values())
    rows.sort(
        key=lambda item: (
            0 if str(item['seed_tier']) == 'core' else 1,
            str(item['seed_family']),
            int(item['step_distance']),
            int(item['step_num']),
        )
    )
    for row in rows:
        counts_by_window[str(row['step_window'])] = counts_by_window.get(str(row['step_window']), 0) + 1

    info = {
        'shape_dataset': str(SHAPE_DATASET),
        'model_base_version': 'v4',
        'point_id': POINT_SPEC['point_id'],
        'include_optional_seeds': any(str(seed['seed_tier']) == 'optional' for seed in seed_manifest),
        'seed_count': len(seed_manifest),
        'candidate_rows': len(rows),
        'counts_by_seed': counts_by_seed,
        'counts_by_window': counts_by_window,
        'target_offsets': sorted(TARGET_OFFSETS),
    }
    return rows, info


def main() -> None:
    args = parse_args()
    ensure_dir(OUT_DIR)
    shape_df = read_csv(SHAPE_DATASET)
    seed_manifest = build_seed_manifest(args.include_optional_seeds)
    pool_rows, info = build_candidate_pool(shape_df, seed_manifest)

    write_csv(POINT_MANIFEST, [POINT_SPEC], [
        'candidate_point_id', 'pool_arm', 'pool_role', 'point_strategy', 'family_prior_source', 'seed_prior_source',
        'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    ])
    write_csv(SEED_MANIFEST, seed_manifest, [
        'seed_index', 'seed_shape_id', 'seed_family', 'seed_step', 'seed_tier', 'seed_source',
    ])
    write_csv(POOL_CSV, pool_rows, POOL_FIELDS)
    INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'[DONE] active seeds: {len(seed_manifest)}')
    print(f'[DONE] candidate rows: {len(pool_rows)}')
    print(f'[OUT] {POINT_MANIFEST}')
    print(f'[OUT] {SEED_MANIFEST}')
    print(f'[OUT] {POOL_CSV}')
    print(f'[OUT] {INFO_JSON}')


if __name__ == '__main__':
    main()
