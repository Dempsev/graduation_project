from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_DATASET_DIR = ROOT / 'stage3_dataset'
if str(STAGE3_DATASET_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE3_DATASET_DIR))

from stage3_dataset import build_v7_training_dataset as source
from shared.features.prediction import PURE_STRUCTURAL_EXTENDED_FEATURES
from shared.objectives.prediction import PURE_TARGET_FIELDS

OUT_DIR = ROOT / 'data' / 'pure_prediction_v2' / 'v1'
MASTER_CSV = OUT_DIR / 'master_pure_prediction_dataset_v2.csv'
TASK_CSV = OUT_DIR / 'pure_bandgap_regression_v2.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'pure_prediction_stage_summary_v2.csv'
DATASET_INFO_JSON = OUT_DIR / 'pure_prediction_dataset_info_v2.json'

PURE_FEATURE_FIELDS = list(PURE_STRUCTURAL_EXTENDED_FEATURES)

AGG_METADATA_FIELDS = [
    'sample_id',
    'design_id',
    'observation_count',
    'source_stage_count',
    'source_stage',
    'source_stage_list',
    'source_role',
    'candidate_id',
    'main_id',
    'point_id',
    'shape_id',
    'shape_family',
    'shape_role',
    'geometry_valid',
    'contact_valid',
    'solve_success',
    'is_training_ready',
    'label_definition',
    'error_message',
]

MASTER_FIELDS = [
    *AGG_METADATA_FIELDS,
    *PURE_FEATURE_FIELDS,
    *PURE_TARGET_FIELDS,
]

TASK_FIELDS = [
    'sample_id',
    'design_id',
    'observation_count',
    'source_stage',
    'source_stage_list',
    'point_id',
    'shape_id',
    'shape_family',
    'shape_role',
    *PURE_FEATURE_FIELDS,
    *PURE_TARGET_FIELDS,
]

_extended_shape_cache: Dict[str, Dict[str, float]] = {}


def _to_text(value: object) -> str:
    if value is None:
        return ''
    text = str(value).strip()
    return '' if text.lower() == 'nan' else text


def _to_float(value: object) -> float:
    try:
        out = float(value)
    except Exception:
        return math.nan
    return out if math.isfinite(out) else math.nan


def _canonical_point_id(value: object) -> str:
    text = _to_text(value)
    return text or '__baseline__'


def _stage_rank(stage_name: str) -> Tuple[int, int]:
    text = _to_text(stage_name)
    if text == 'stage1':
        return (1, 0)
    if text == 'stage2':
        return (2, 0)
    if text == 'stage2_refine':
        return (3, 0)
    if text == 'stage2_harmonics':
        return (4, 0)
    if text == 'stage2_harmonics_refine':
        return (5, 0)
    match = re.match(r'^stage4_validation_v(\d+)$', text)
    if match:
        return (10, int(match.group(1)))
    return (0, 0)


def _pick_representative(rows: List[Dict[str, object]]) -> Dict[str, object]:
    return max(rows, key=lambda item: (_stage_rank(_to_text(item.get('source_stage'))), _to_text(item.get('sample_id'))))


def _aggregate_mean(rows: Iterable[Dict[str, object]], field: str) -> float:
    values = [_to_float(row.get(field)) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return math.nan
    return float(np.mean(finite))


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

    area = _to_float(row.get('shape_area'))
    perimeter = _to_float(row.get('shape_perimeter'))
    bbox_width = _to_float(row.get('shape_bbox_width'))
    bbox_height = _to_float(row.get('shape_bbox_height'))
    cx = _to_float(row.get('shape_centroid_x'))
    cy = _to_float(row.get('shape_centroid_y'))

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


def build_raw_rows() -> List[Dict[str, object]]:
    rows = source.build_rows()
    projected: List[Dict[str, object]] = []
    for row in rows:
        shape_id = _to_text(row.get('shape_id'))
        point_id = _canonical_point_id(row.get('point_id'))
        projected_row: Dict[str, object] = {
            'sample_id': _to_text(row.get('sample_id')),
            'source_stage': _to_text(row.get('source_stage')),
            'source_role': _to_text(row.get('source_role')),
            'candidate_id': _to_text(row.get('candidate_id')),
            'main_id': _to_text(row.get('main_id')),
            'point_id': point_id,
            'shape_id': shape_id,
            'shape_family': _to_text(row.get('shape_family')),
            'shape_role': _to_text(row.get('shape_role')),
            'geometry_valid': int(_to_float(row.get('geometry_valid')) == 1.0),
            'contact_valid': int(_to_float(row.get('contact_valid')) == 1.0),
            'solve_success': int(_to_float(row.get('solve_success')) == 1.0),
            'is_training_ready': int(_to_float(row.get('is_training_ready')) == 1.0),
            'label_definition': _to_text(row.get('label_definition')),
            'error_message': _to_text(row.get('error_message')),
        }
        for field in PURE_FEATURE_FIELDS:
            projected_row[field] = _to_float(row.get(field))
        projected_row.update(compute_extended_shape_features(shape_id, projected_row))

        gap34_hz = _to_float(row.get('gap34_Hz'))
        gap34_rel = _to_float(row.get('gap34_rel'))
        max_gap_hz = _to_float(row.get('max_gap_Hz'))
        max_gap_rel = _to_float(row.get('max_gap_rel'))
        projected_row['gap34_Hz'] = gap34_hz
        projected_row['gap34_rel'] = gap34_rel
        projected_row['gap34_width_Hz'] = max(gap34_hz, 0.0) if math.isfinite(gap34_hz) else math.nan
        projected_row['gap34_width_rel'] = max(gap34_rel, 0.0) if math.isfinite(gap34_rel) else math.nan
        projected_row['gap34_is_open'] = 1 if math.isfinite(projected_row['gap34_width_Hz']) and projected_row['gap34_width_Hz'] > 1e-12 else 0
        projected_row['max_gap_Hz'] = max_gap_hz
        projected_row['max_gap_rel'] = max_gap_rel
        projected_row['max_gap_is_open'] = 1 if math.isfinite(max_gap_hz) and max_gap_hz > 1e-12 else 0
        projected.append(projected_row)
    return projected


def aggregate_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        design_id = f"{_to_text(row.get('shape_id'))}::{_canonical_point_id(row.get('point_id'))}"
        grouped.setdefault(design_id, []).append(row)

    aggregated: List[Dict[str, object]] = []
    for design_id, subset in grouped.items():
        representative = _pick_representative(subset)
        stage_names = sorted({_to_text(row.get('source_stage')) for row in subset if _to_text(row.get('source_stage'))})
        primary_stage = _to_text(representative.get('source_stage'))
        agg_row: Dict[str, object] = {
            'sample_id': design_id,
            'design_id': design_id,
            'observation_count': len(subset),
            'source_stage_count': len(stage_names),
            'source_stage': primary_stage,
            'source_stage_list': '|'.join(stage_names),
            'source_role': _to_text(representative.get('source_role')) if len(subset) == 1 else 'aggregated_design_point',
            'candidate_id': _to_text(representative.get('candidate_id')),
            'main_id': _to_text(representative.get('main_id')),
            'point_id': _canonical_point_id(representative.get('point_id')),
            'shape_id': _to_text(representative.get('shape_id')),
            'shape_family': _to_text(representative.get('shape_family')),
            'shape_role': _to_text(representative.get('shape_role')),
            'geometry_valid': int(any(int(_to_float(row.get('geometry_valid')) == 1.0) for row in subset)),
            'contact_valid': int(any(int(_to_float(row.get('contact_valid')) == 1.0) for row in subset)),
            'solve_success': int(any(int(_to_float(row.get('solve_success')) == 1.0) for row in subset)),
            'is_training_ready': int(any(int(_to_float(row.get('is_training_ready')) == 1.0) for row in subset)),
            'label_definition': _to_text(representative.get('label_definition')),
            'error_message': '',
        }
        for field in PURE_FEATURE_FIELDS:
            agg_row[field] = _aggregate_mean(subset, field)
        for field in ['gap34_Hz', 'gap34_rel', 'gap34_width_Hz', 'gap34_width_rel', 'max_gap_Hz', 'max_gap_rel']:
            agg_row[field] = _aggregate_mean(subset, field)
        agg_row['gap34_is_open'] = 1 if math.isfinite(_to_float(agg_row['gap34_width_Hz'])) and _to_float(agg_row['gap34_width_Hz']) > 1e-12 else 0
        agg_row['max_gap_is_open'] = 1 if math.isfinite(_to_float(agg_row['max_gap_Hz'])) and _to_float(agg_row['max_gap_Hz']) > 1e-12 else 0
        aggregated.append(agg_row)

    aggregated.sort(key=lambda item: (_to_text(item.get('source_stage')), _to_text(item.get('design_id'))))
    return aggregated


def _is_finite(row: Dict[str, object], field: str) -> bool:
    return math.isfinite(_to_float(row.get(field)))


def build_task_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_rows: List[Dict[str, object]] = []
    for row in rows:
        if int(row.get('is_training_ready', 0)) != 1:
            continue
        if not all(_is_finite(row, field) for field in PURE_TARGET_FIELDS):
            continue
        task_rows.append({field: row.get(field, '') for field in TASK_FIELDS})
    return task_rows


def build_stage_summary(rows: List[Dict[str, object]], task_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_counts: Dict[str, int] = {}
    for row in task_rows:
        stage_name = _to_text(row.get('source_stage'))
        task_counts[stage_name] = task_counts.get(stage_name, 0) + 1

    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(_to_text(row.get('source_stage')), []).append(row)

    summary = []
    for stage_name, subset in grouped.items():
        summary.append({
            'source_stage': stage_name,
            'rows_total': len(subset),
            'rows_training_ready': sum(int(row.get('is_training_ready', 0)) for row in subset),
            'rows_pure_prediction': task_counts.get(stage_name, 0),
        })
    summary.sort(key=lambda item: (_stage_rank(item['source_stage']), item['source_stage']))
    return summary


def build_dataset_info(raw_rows: List[Dict[str, object]], rows: List[Dict[str, object]], task_rows: List[Dict[str, object]], stage_summary: List[Dict[str, object]]) -> Dict[str, object]:
    dedup_ratio = (1.0 - len(rows) / len(raw_rows)) if raw_rows else 0.0
    return {
        'dataset_name': 'pure_prediction_dataset_v2',
        'source_profile': source.PROFILE['name'],
        'feature_definition': 'structure_parameters_plus_shape_geometry_only_design_point_aggregated',
        'feature_fields': PURE_FEATURE_FIELDS,
        'target_fields': PURE_TARGET_FIELDS,
        'design_key': 'shape_id + point_id',
        'primary_stage_rule': 'latest_stage_rank_within_design_point',
        'target_aggregation': 'mean_over_repeated_measurements',
        'row_filter': 'is_training_ready=1 && finite(gap34_Hz,gap34_rel,gap34_width_Hz,gap34_width_rel,max_gap_Hz,max_gap_rel)',
        'raw_rows': len(raw_rows),
        'master_rows': len(rows),
        'task_rows': len(task_rows),
        'dedup_ratio': dedup_ratio,
        'master_csv': str(MASTER_CSV),
        'task_csv': str(TASK_CSV),
        'stage_summary_csv': str(STAGE_SUMMARY_CSV),
        'stage_summary': stage_summary,
        'notes': [
            'This line keeps the original prediction branch intact and adds a design-point aggregated comparison dataset.',
            'Repeated measurements are aggregated by design point while the latest stage is kept as the primary split label.',
        ],
    }


def main() -> None:
    source.base.ensure_dir(OUT_DIR)
    raw_rows = build_raw_rows()
    rows = aggregate_rows(raw_rows)
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
        json.dumps(build_dataset_info(raw_rows, rows, task_rows, stage_summary), indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    print(f'[DONE] raw rows: {len(raw_rows)}')
    print(f'[DONE] aggregated rows: {len(rows)}')
    print(f'[DONE] aggregated task rows: {len(task_rows)}')
    print(f'[OUT] {MASTER_CSV}')
    print(f'[OUT] {TASK_CSV}')
    print(f'[OUT] {STAGE_SUMMARY_CSV}')


if __name__ == '__main__':
    main()
