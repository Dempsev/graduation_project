from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_DATASET_DIR = ROOT / 'stage3_dataset'
if str(STAGE3_DATASET_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE3_DATASET_DIR))

from stage3_dataset import build_v7_training_dataset as source

OUT_DIR = ROOT / 'data' / 'pure_prediction' / 'v1'
MASTER_CSV = OUT_DIR / 'master_pure_prediction_dataset_v1.csv'
TASK_CSV = OUT_DIR / 'pure_bandgap_regression_v1.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'pure_prediction_stage_summary_v1.csv'
DATASET_INFO_JSON = OUT_DIR / 'pure_prediction_dataset_info_v1.json'

PURE_FEATURE_FIELDS = [
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0',
    *source.SHAPE_FEATURE_FIELDS,
    'shape_compactness', 'shape_extent', 'shape_mean_radius', 'shape_std_radius',
    'shape_min_radius', 'shape_max_radius', 'shape_radius_cv',
    'shape_edge_mean', 'shape_edge_std', 'shape_edge_cv',
]

PURE_TARGET_FIELDS = [
    'gap34_Hz', 'gap34_rel', 'gap34_width_Hz', 'gap34_width_rel', 'gap34_is_open',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_is_open',
]

PURE_METADATA_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'candidate_id', 'main_id', 'point_id',
    'shape_id', 'shape_family', 'shape_role',
    'geometry_valid', 'contact_valid', 'solve_success',
    'is_training_ready', 'label_definition', 'error_message',
]

MASTER_FIELDS = [
    *PURE_METADATA_FIELDS,
    *PURE_FEATURE_FIELDS,
    *PURE_TARGET_FIELDS,
]

TASK_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'candidate_id', 'main_id', 'point_id',
    'shape_id', 'shape_family', 'shape_role',
    *PURE_FEATURE_FIELDS,
    *PURE_TARGET_FIELDS,
]

_extended_shape_cache: Dict[str, Dict[str, float]] = {}


def _read_shape_points(shape_id: str) -> List[Tuple[float, float]]:
    if not shape_id or shape_id == '__baseline__':
        return []
    path = source.base.SHAPE_DIR / f'{shape_id}.csv'
    if not path.exists():
        return []

    pts: List[Tuple[float, float]] = []
    with path.open('r', encoding='utf-8-sig') as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(',')]
            if len(parts) < 2:
                continue
            x = source.base.to_float(parts[0])
            y = source.base.to_float(parts[1])
            if math.isfinite(x) and math.isfinite(y):
                pts.append((x, y))
    return pts


def compute_extended_shape_features(shape_id: str, row: Dict[str, object]) -> Dict[str, float]:
    if shape_id in _extended_shape_cache:
        return _extended_shape_cache[shape_id]

    default = {
        'shape_compactness': math.nan,
        'shape_extent': math.nan,
        'shape_mean_radius': math.nan,
        'shape_std_radius': math.nan,
        'shape_min_radius': math.nan,
        'shape_max_radius': math.nan,
        'shape_radius_cv': math.nan,
        'shape_edge_mean': math.nan,
        'shape_edge_std': math.nan,
        'shape_edge_cv': math.nan,
    }
    pts = _read_shape_points(shape_id)
    if len(pts) < 3:
        _extended_shape_cache[shape_id] = default
        return default

    area = float(row.get('shape_area', math.nan))
    perimeter = float(row.get('shape_perimeter', math.nan))
    bbox_width = float(row.get('shape_bbox_width', math.nan))
    bbox_height = float(row.get('shape_bbox_height', math.nan))
    cx = float(row.get('shape_centroid_x', math.nan))
    cy = float(row.get('shape_centroid_y', math.nan))

    edges = []
    for idx in range(len(pts)):
        x1, y1 = pts[idx]
        x2, y2 = pts[(idx + 1) % len(pts)]
        edges.append(math.hypot(x2 - x1, y2 - y1))
    radii = [math.hypot(x - cx, y - cy) for x, y in pts] if math.isfinite(cx) and math.isfinite(cy) else []

    extent = math.nan
    if math.isfinite(area) and math.isfinite(bbox_width) and math.isfinite(bbox_height) and bbox_width > 0 and bbox_height > 0:
        extent = area / (bbox_width * bbox_height)

    compactness = math.nan
    if math.isfinite(area) and math.isfinite(perimeter) and perimeter > 0:
        compactness = 4.0 * math.pi * area / (perimeter * perimeter)

    edge_mean = float(sum(edges) / len(edges)) if edges else math.nan
    edge_std = float((sum((x - edge_mean) ** 2 for x in edges) / len(edges)) ** 0.5) if edges and math.isfinite(edge_mean) else math.nan
    edge_cv = edge_std / edge_mean if math.isfinite(edge_std) and math.isfinite(edge_mean) and edge_mean > 0 else math.nan

    radius_mean = float(sum(radii) / len(radii)) if radii else math.nan
    radius_std = float((sum((x - radius_mean) ** 2 for x in radii) / len(radii)) ** 0.5) if radii and math.isfinite(radius_mean) else math.nan
    radius_cv = radius_std / radius_mean if math.isfinite(radius_std) and math.isfinite(radius_mean) and radius_mean > 0 else math.nan

    features = {
        'shape_compactness': compactness,
        'shape_extent': extent,
        'shape_mean_radius': radius_mean,
        'shape_std_radius': radius_std,
        'shape_min_radius': float(min(radii)) if radii else math.nan,
        'shape_max_radius': float(max(radii)) if radii else math.nan,
        'shape_radius_cv': radius_cv,
        'shape_edge_mean': edge_mean,
        'shape_edge_std': edge_std,
        'shape_edge_cv': edge_cv,
    }
    _extended_shape_cache[shape_id] = features
    return features


def is_finite(row: Dict[str, object], field: str) -> bool:
    value = row.get(field, math.nan)
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def build_rows() -> List[Dict[str, object]]:
    rows = source.build_rows()
    projected = []
    for row in rows:
        projected_row = {field: row.get(field, '') for field in MASTER_FIELDS}
        projected_row.update(compute_extended_shape_features(str(projected_row.get('shape_id', '')), projected_row))
        gap34_hz = projected_row.get('gap34_Hz', math.nan)
        gap34_rel = projected_row.get('gap34_rel', math.nan)
        try:
            gap34_hz = float(gap34_hz)
        except Exception:
            gap34_hz = math.nan
        try:
            gap34_rel = float(gap34_rel)
        except Exception:
            gap34_rel = math.nan
        projected_row['gap34_width_Hz'] = max(gap34_hz, 0.0) if math.isfinite(gap34_hz) else math.nan
        projected_row['gap34_width_rel'] = max(gap34_rel, 0.0) if math.isfinite(gap34_rel) else math.nan
        projected_row['gap34_is_open'] = 1 if math.isfinite(projected_row['gap34_width_Hz']) and projected_row['gap34_width_Hz'] > 1e-12 else 0
        try:
            max_gap_hz = float(projected_row.get('max_gap_Hz', math.nan))
        except Exception:
            max_gap_hz = math.nan
        projected_row['max_gap_is_open'] = 1 if math.isfinite(max_gap_hz) and max_gap_hz > 1e-12 else 0
        projected.append(projected_row)
    return projected


def build_task_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_rows = []
    for row in rows:
        if int(row.get('is_training_ready', 0)) != 1:
            continue
        if not all(is_finite(row, field) for field in PURE_TARGET_FIELDS):
            continue
        task_rows.append({field: row.get(field, '') for field in TASK_FIELDS})
    return task_rows


def build_stage_summary(rows: List[Dict[str, object]], task_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_counts: Dict[str, int] = {}
    for row in task_rows:
        stage_name = str(row.get('source_stage', ''))
        task_counts[stage_name] = task_counts.get(stage_name, 0) + 1

    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get('source_stage', '')), []).append(row)

    summary = []
    for stage_name, subset in grouped.items():
        summary.append({
            'source_stage': stage_name,
            'rows_total': len(subset),
            'rows_training_ready': sum(int(row.get('is_training_ready', 0)) for row in subset),
            'rows_pure_prediction': task_counts.get(stage_name, 0),
        })
    summary.sort(key=lambda item: item['source_stage'])
    return summary


def build_dataset_info(rows: List[Dict[str, object]], task_rows: List[Dict[str, object]], stage_summary: List[Dict[str, object]]) -> Dict[str, object]:
    return {
        'dataset_name': 'pure_prediction_dataset_v1',
        'source_profile': source.PROFILE['name'],
        'source_stage_names': list(source.PROFILE['stage_names']),
        'feature_definition': 'structure_parameters_plus_shape_geometry_only',
        'feature_fields': PURE_FEATURE_FIELDS,
        'target_fields': PURE_TARGET_FIELDS,
        'row_filter': 'is_training_ready=1 && finite(gap34_Hz,gap34_rel,gap34_width_Hz,gap34_width_rel,max_gap_Hz,max_gap_rel)',
        'master_rows': len(rows),
        'task_rows': len(task_rows),
        'master_csv': str(MASTER_CSV),
        'task_csv': str(TASK_CSV),
        'stage_summary_csv': str(STAGE_SUMMARY_CSV),
        'stage_summary': stage_summary,
        'notes': [
            'This branch is prediction-only and excludes gain-based labels and optimization-side context features.',
            'Rows still originate from the unified stage3 dataset builder so physical truth stays consistent with the mainline.',
        ],
    }


def main() -> None:
    source.base.ensure_dir(OUT_DIR)
    rows = build_rows()
    task_rows = build_task_rows(rows)
    stage_summary = build_stage_summary(rows, task_rows)

    source.base.write_csv(MASTER_CSV, rows, MASTER_FIELDS)
    source.base.write_csv(TASK_CSV, task_rows, TASK_FIELDS)
    source.base.write_csv(
        STAGE_SUMMARY_CSV,
        stage_summary,
        list(stage_summary[0].keys()) if stage_summary else ['source_stage'],
    )
    DATASET_INFO_JSON.write_text(
        json.dumps(build_dataset_info(rows, task_rows, stage_summary), indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    print(f'[DONE] pure prediction master rows: {len(rows)}')
    print(f'[DONE] pure prediction task rows: {len(task_rows)}')
    print(f'[OUT] {MASTER_CSV}')
    print(f'[OUT] {TASK_CSV}')
    print(f'[OUT] {STAGE_SUMMARY_CSV}')


if __name__ == '__main__':
    main()
