from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks'
SHAPE_DATASET = TASKS_DIR / 'shape_screening_contact_cls_v4.csv'
VALIDATION_RESULTS_V1 = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'stage4_validation_results.csv'
POINT_SUMMARY_V1 = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'stage4_validation_point_summary.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v4' / 'candidate_pool_v4'
POINT_MANIFEST = OUT_DIR / 'candidate_point_manifest.csv'
POOL_CSV = OUT_DIR / 'candidate_pool_v4.csv'
INFO_JSON = OUT_DIR / 'candidate_pool_info.json'

POINT_CONFIGS = [
    {
        'candidate_point_id': 'cp01',
        'pool_arm': 'broad',
        'pool_role': 'broad_exploration',
        'point_strategy': 'broad_transfer_anchor',
        'main_id': 'rf19_a050_a2m12_b000_r120',
        'point_id': 'rf19_a050_a2m12_b000_r120',
        'family_prior_source': 'none',
        'allow_positive_families_only': False,
    },
    {
        'candidate_point_id': 'cp02',
        'pool_arm': 'exploitation',
        'pool_role': 'targeted_exploitation',
        'point_strategy': 'v1_positive_family_whitelist',
        'main_id': 'rf19',
        'point_id': 'rf19_h07_a4_003',
        'family_prior_source': 'stage4_validation_ab_v1_positive_families',
        'allow_positive_families_only': True,
    },
    {
        'candidate_point_id': 'cp03',
        'pool_arm': 'exploitation',
        'pool_role': 'targeted_exploitation',
        'point_strategy': 'v1_positive_family_whitelist',
        'main_id': 'rf09',
        'point_id': 'rf09_h09_b5_002_a4_0015',
        'family_prior_source': 'stage4_validation_ab_v1_positive_families',
        'allow_positive_families_only': True,
    },
]

POOL_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'pool_arm', 'point_strategy', 'family_prior_source',
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


def normalize_float(value, default=0.0) -> float:
    try:
        val = float(value)
        if pd.isna(val):
            return float(default)
        return val
    except Exception:
        return float(default)


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def build_point_param_map() -> Dict[str, Dict[str, object]]:
    df = read_csv(POINT_SUMMARY_V1)
    point_map: Dict[str, Dict[str, object]] = {}
    for _, row in df.iterrows():
        point_id = str(row['point_id'])
        point_map[point_id] = {
            'main_id': str(row['main_id']),
            'point_id': point_id,
            'a1': normalize_float(row['a1']),
            'a2': normalize_float(row['a2']),
            'b1': 0.0,
            'b2': normalize_float(row['b2']),
            'a3': normalize_float(row.get('a3', 0.0)),
            'b3': normalize_float(row.get('b3', 0.0)),
            'a4': normalize_float(row.get('a4', 0.0)),
            'b4': normalize_float(row.get('b4', 0.0)),
            'a5': normalize_float(row.get('a5', 0.0)),
            'b5': normalize_float(row.get('b5', 0.0)),
            'r0': normalize_float(row['r0'], 0.012),
            'shift': 200.0,
            'neigs': 20.0,
            'score_proxy': normalize_float(row.get('mean_gap34_gain_Hz', 0.0)),
        }
    return point_map


def build_positive_family_map() -> Dict[str, List[str]]:
    df = read_csv(VALIDATION_RESULTS_V1)
    df['solve_success'] = pd.to_numeric(df['solve_success'], errors='coerce')
    df['gap34_gain_Hz'] = pd.to_numeric(df['gap34_gain_Hz'], errors='coerce')
    family_map: Dict[str, List[str]] = {}
    for point_id, subset in df.groupby('point_id'):
        valid = subset[(subset['solve_success'] == 1) & (subset['gap34_gain_Hz'] > 0)]
        family_map[str(point_id)] = sorted(valid['shape_family'].astype(str).unique().tolist())
    return family_map


def build_point_manifest() -> List[Dict[str, object]]:
    point_map = build_point_param_map()
    family_map = build_positive_family_map()
    rows: List[Dict[str, object]] = []
    for cfg in POINT_CONFIGS:
        point_id = cfg['point_id']
        if point_id not in point_map:
            raise KeyError(f'Missing point parameters for {point_id}')
        item = {**cfg, **point_map[point_id]}
        families = family_map.get(point_id, []) if cfg['allow_positive_families_only'] else []
        item['allowed_shape_families'] = '|'.join(families)
        item['allowed_family_count'] = len(families)
        rows.append(item)
    return rows


def select_shapes(shape_df: pd.DataFrame, point_cfg: Dict[str, object]) -> pd.DataFrame:
    if point_cfg['pool_arm'] == 'broad':
        return shape_df.copy()
    allowed = [item for item in str(point_cfg.get('allowed_shape_families', '')).split('|') if item]
    if not allowed:
        return shape_df.iloc[0:0].copy()
    return shape_df[shape_df['shape_family'].astype(str).isin(allowed)].copy()


def build_candidate_pool(point_manifest: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    shape_df = read_csv(SHAPE_DATASET)
    rows: List[Dict[str, object]] = []
    counts_by_arm: Dict[str, int] = {'broad': 0, 'exploitation': 0}
    for point in point_manifest:
        selected_shapes = select_shapes(shape_df, point)
        counts_by_arm[point['pool_arm']] = counts_by_arm.get(point['pool_arm'], 0) + int(len(selected_shapes))
        for _, shape in selected_shapes.iterrows():
            shape_id = str(shape['shape_id'])
            rows.append({
                'sample_id': f"candidate_pool_v4_{point['candidate_point_id']}_{shape_id}",
                'source_stage': 'candidate_pool_v4',
                'source_role': point['pool_role'],
                'pool_arm': point['pool_arm'],
                'point_strategy': point['point_strategy'],
                'family_prior_source': point['family_prior_source'],
                'shape_id': shape_id,
                'shape_family': shape['shape_family'],
                'shape_role': shape.get('shape_role', 'screening'),
                'candidate_id': point['candidate_point_id'],
                'main_id': point['main_id'],
                'point_id': point['point_id'],
                'a1': point['a1'], 'a2': point['a2'], 'b1': point['b1'], 'b2': point['b2'],
                'a3': point['a3'], 'b3': point['b3'], 'a4': point['a4'], 'b4': point['b4'], 'a5': point['a5'], 'b5': point['b5'],
                'r0': point['r0'], 'shift': point['shift'], 'neigs': point['neigs'],
                'shape_area': shape['shape_area'], 'shape_perimeter': shape['shape_perimeter'],
                'shape_bbox_width': shape['shape_bbox_width'], 'shape_bbox_height': shape['shape_bbox_height'], 'shape_bbox_aspect_ratio': shape['shape_bbox_aspect_ratio'],
                'shape_centroid_x': shape['shape_centroid_x'], 'shape_centroid_y': shape['shape_centroid_y'], 'shape_point_count': shape['shape_point_count'],
                'contact_length': '', 'n_domains': '',
                'gap34_Hz': '', 'gap34_rel': '', 'gap34_gain_Hz': '', 'gap34_gain_rel': '',
                'max_gap_Hz': '', 'max_gap_rel': '', 'max_gap_lower_band': '', 'max_gap_upper_band': '', 'max_gap_center_freq': '',
                'is_gap34_positive': '', 'is_gap34_gain_positive': '',
            })
    info = {
        'shape_rows': int(len(shape_df)),
        'point_rows': int(len(point_manifest)),
        'candidate_rows': int(len(rows)),
        'shape_dataset': str(SHAPE_DATASET),
        'point_summary_source': str(POINT_SUMMARY_V1),
        'validation_result_source': str(VALIDATION_RESULTS_V1),
        'rows_by_arm': counts_by_arm,
        'point_manifest': point_manifest,
    }
    return rows, info


def main() -> None:
    ensure_dir(OUT_DIR)
    point_manifest = build_point_manifest()
    pool_rows, info = build_candidate_pool(point_manifest)
    write_csv(POINT_MANIFEST, point_manifest, [
        'candidate_point_id', 'pool_arm', 'pool_role', 'point_strategy', 'family_prior_source',
        'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
        'score_proxy', 'allowed_shape_families', 'allowed_family_count'
    ])
    write_csv(POOL_CSV, pool_rows, POOL_FIELDS)
    INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[DONE] candidate point rows: {len(point_manifest)}')
    print(f'[DONE] candidate pool rows: {len(pool_rows)}')
    print(f'[OUT] {POINT_MANIFEST}')
    print(f'[OUT] {POOL_CSV}')
    print(f'[OUT] {INFO_JSON}')


if __name__ == '__main__':
    main()
