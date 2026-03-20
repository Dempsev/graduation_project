from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / 'data' / 'ml_dataset' / 'v3' / 'tasks'
SHAPE_DATASET = TASKS_DIR / 'shape_screening_contact_cls_v3.csv'
VALIDATED_POINTS = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'stage4_validation_point_summary.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v3' / 'candidate_pool_v3'
POINT_MANIFEST = OUT_DIR / 'candidate_point_manifest.csv'
POOL_CSV = OUT_DIR / 'candidate_pool_v3.csv'
INFO_JSON = OUT_DIR / 'candidate_pool_info.json'

POOL_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'shape_id', 'shape_family', 'shape_role',
    'candidate_id', 'main_id', 'point_id',
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


def point_signature(row: Dict[str, object]) -> Tuple[float, ...]:
    return (
        round(normalize_float(row.get('a1')), 8),
        round(normalize_float(row.get('a2')), 8),
        round(normalize_float(row.get('b1')), 8),
        round(normalize_float(row.get('b2')), 8),
        round(normalize_float(row.get('a3')), 8),
        round(normalize_float(row.get('b3')), 8),
        round(normalize_float(row.get('a4')), 8),
        round(normalize_float(row.get('b4')), 8),
        round(normalize_float(row.get('a5')), 8),
        round(normalize_float(row.get('b5')), 8),
        round(normalize_float(row.get('r0'), 0.012), 8),
    )


def build_point_manifest() -> List[Dict[str, object]]:
    df = read_csv(VALIDATED_POINTS)
    for col in ['solve_success_count', 'positive_gap34_gain_count', 'positive_gap34_gain_rate', 'mean_gap34_gain_Hz']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df[(df['solve_success_count'] > 0) & (df['positive_gap34_gain_count'] > 0)].copy()
    df = df.sort_values(['positive_gap34_gain_rate', 'mean_gap34_gain_Hz'], ascending=[False, False])

    rows: List[Dict[str, object]] = []
    seen = set()
    for _, row in df.iterrows():
        item = {
            'pool_role': 'validated_point',
            'pool_source': 'stage4_validation_ab_v1',
            'main_id': row['main_id'],
            'point_id': row['point_id'],
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
            'score_proxy': normalize_float(row['mean_gap34_gain_Hz']),
        }
        sig = point_signature(item)
        if sig in seen:
            continue
        seen.add(sig)
        rows.append(item)
    for idx, item in enumerate(rows, start=1):
        item['candidate_point_id'] = f'cp{idx:02d}'
    return rows


def build_candidate_pool(point_manifest: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    shape_df = read_csv(SHAPE_DATASET)
    rows: List[Dict[str, object]] = []
    for point in point_manifest:
        for _, shape in shape_df.iterrows():
            shape_id = str(shape['shape_id'])
            rows.append({
                'sample_id': f"candidate_pool_v3_{point['candidate_point_id']}_{shape_id}",
                'source_stage': 'candidate_pool_v3',
                'source_role': point['pool_role'],
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
        'point_source': str(VALIDATED_POINTS),
        'shape_dataset': str(SHAPE_DATASET),
        'pool_roles': sorted({row['pool_role'] for row in point_manifest}),
    }
    return rows, info


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def main() -> None:
    ensure_dir(OUT_DIR)
    point_manifest = build_point_manifest()
    pool_rows, info = build_candidate_pool(point_manifest)
    write_csv(POINT_MANIFEST, point_manifest, ['candidate_point_id', 'pool_role', 'pool_source', 'main_id', 'point_id', 'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs', 'score_proxy'])
    write_csv(POOL_CSV, pool_rows, POOL_FIELDS)
    INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[DONE] candidate point rows: {len(point_manifest)}')
    print(f'[DONE] candidate pool rows: {len(pool_rows)}')
    print(f'[OUT] {POINT_MANIFEST}')
    print(f'[OUT] {POOL_CSV}')
    print(f'[OUT] {INFO_JSON}')


if __name__ == '__main__':
    main()
