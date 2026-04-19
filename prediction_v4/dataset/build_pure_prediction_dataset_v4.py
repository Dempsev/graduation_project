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

OUT_DIR = ROOT / 'data' / 'pure_prediction_v4' / 'v1'
MASTER_CSV = OUT_DIR / 'master_pure_prediction_dataset_v4.csv'
TASK_CSV = OUT_DIR / 'pure_bandgap_regression_v4.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'pure_prediction_stage_summary_v4.csv'
DATASET_INFO_JSON = OUT_DIR / 'pure_prediction_dataset_info_v4.json'

BASE_FEATURE_FIELDS = list(PURE_STRUCTURAL_EXTENDED_FEATURES)
COMSOL_CONTEXT_FIELDS = [
    'shift',
    'neigs',
    'contact_length',
    'n_domains',
    'has_tiny_fragments',
]
DISPERSION_BAND_COUNT = 6
DISPERSION_SAMPLE_K_INDEXES = [0, 10, 20, 30, 40]
DISPERSION_SUMMARY_SUFFIXES = [
    'min_hz',
    'max_hz',
    'mean_hz',
    'std_hz',
    'span_hz',
    'tv_hz',
    'slope_abs_mean',
    'slope_abs_max',
]
DISPERSION_FEATURE_FIELDS = [
    *(f'band{band_idx:02d}_k{k_idx:02d}_hz' for band_idx in range(1, DISPERSION_BAND_COUNT + 1) for k_idx in DISPERSION_SAMPLE_K_INDEXES),
    *(f'band{band_idx:02d}_{suffix}' for band_idx in range(1, DISPERSION_BAND_COUNT + 1) for suffix in DISPERSION_SUMMARY_SUFFIXES),
    'dispersion_k_count',
    'dispersion_band_count',
    'dispersion_lowband_mean_hz',
    'dispersion_lowband_std_hz',
    'dispersion_lowband_min_hz',
    'dispersion_lowband_max_hz',
    'band34_gap_proxy_hz',
    'band34_gap_path_min_hz',
    'band34_gap_path_max_hz',
    'band34_gap_path_mean_hz',
    'band34_gap_path_std_hz',
    'band34_gap_positive_frac',
    'band34_gap_path_argmin_k',
    'band34_gap_path_argmax_k',
    'legacy_band34_gap_proxy_hz',
    'legacy_band34_gap_path_min_hz',
    'legacy_band34_gap_path_max_hz',
    'legacy_band34_gap_path_mean_hz',
    'legacy_band34_gap_path_std_hz',
    'legacy_band34_gap_positive_frac',
]
PURE_V4_FEATURE_FIELDS = [*BASE_FEATURE_FIELDS, *COMSOL_CONTEXT_FIELDS, *DISPERSION_FEATURE_FIELDS]

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

MASTER_FIELDS = [*AGG_METADATA_FIELDS, *PURE_V4_FEATURE_FIELDS, *PURE_TARGET_FIELDS]
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
    *PURE_V4_FEATURE_FIELDS,
    *PURE_TARGET_FIELDS,
]

_extended_shape_cache: Dict[str, Dict[str, float]] = {}
_tbl1_path_by_stage: Dict[str, Path] = {}
_dispersion_cache: Dict[str, Dict[str, float]] = {}


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


def _to_complex_real(text: str) -> float:
    cleaned = _to_text(text)
    if not cleaned:
        return math.nan
    try:
        return float(cleaned)
    except Exception:
        pass
    try:
        return float(complex(cleaned.replace('i', 'j')).real)
    except Exception:
        return math.nan


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


def _build_stage_tbl1_lookup() -> Dict[str, Path]:
    global _tbl1_path_by_stage
    if _tbl1_path_by_stage:
        return _tbl1_path_by_stage
    lookup: Dict[str, Path] = {}
    for stage_cfg in source.STAGES:
        stage_name = _to_text(stage_cfg.get('name'))
        tbl1_dir = stage_cfg.get('tbl1_dir')
        if stage_name and tbl1_dir and stage_name not in lookup:
            lookup[stage_name] = Path(tbl1_dir)
    _tbl1_path_by_stage = lookup
    return lookup


def _tbl1_path(stage_name: str, sample_id: str) -> Path | None:
    stage_dir = _build_stage_tbl1_lookup().get(_to_text(stage_name))
    sample_text = _to_text(sample_id)
    if not stage_dir or not sample_text:
        return None
    path = stage_dir / f'{sample_text}_tbl1.csv'
    return path if path.exists() else None


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


def _read_dispersion_features(stage_name: str, sample_id: str) -> Dict[str, float]:
    cache_key = f'{_to_text(stage_name)}::{_to_text(sample_id)}'
    if cache_key in _dispersion_cache:
        return _dispersion_cache[cache_key]

    features = {field: math.nan for field in DISPERSION_FEATURE_FIELDS}
    path = _tbl1_path(stage_name, sample_id)
    if path is None:
        _dispersion_cache[cache_key] = features
        return features

    k_vals: List[float] = []
    freq_vals: List[float] = []
    legacy_k_vals: List[float] = []
    legacy_freq_vals: List[float] = []
    with path.open('r', encoding='utf-8-sig') as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith('%'):
                continue
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:
                continue
            try:
                k_val = float(parts[0])
            except Exception:
                continue
            legacy_freq_val = _to_float(parts[-1])
            if math.isfinite(legacy_freq_val):
                legacy_k_vals.append(k_val)
                legacy_freq_vals.append(legacy_freq_val)
            freq_val = _to_complex_real(parts[-1])
            if math.isfinite(freq_val):
                k_vals.append(k_val)
                freq_vals.append(freq_val)

    if not k_vals:
        _dispersion_cache[cache_key] = features
        return features

    unique_k = sorted(set(k_vals))
    band_rows: List[List[float]] = []
    band_count = 0
    for k_val in unique_k:
        band_row = sorted(freq_vals[idx] for idx, kv in enumerate(k_vals) if kv == k_val)
        band_rows.append(band_row)
        band_count = max(band_count, len(band_row))

    matrix = np.full((len(unique_k), DISPERSION_BAND_COUNT), np.nan, dtype=float)
    for row_idx, band_row in enumerate(band_rows):
        for col_idx in range(min(DISPERSION_BAND_COUNT, len(band_row))):
            matrix[row_idx, col_idx] = band_row[col_idx]

    features['dispersion_k_count'] = float(len(unique_k))
    features['dispersion_band_count'] = float(min(DISPERSION_BAND_COUNT, band_count))
    finite_matrix = matrix[np.isfinite(matrix)]
    if finite_matrix.size > 0:
        features['dispersion_lowband_mean_hz'] = float(np.mean(finite_matrix))
        features['dispersion_lowband_std_hz'] = float(np.std(finite_matrix))
        features['dispersion_lowband_min_hz'] = float(np.min(finite_matrix))
        features['dispersion_lowband_max_hz'] = float(np.max(finite_matrix))

    if DISPERSION_BAND_COUNT >= 4:
        lower = matrix[:, 2]
        upper = matrix[:, 3]
        gap_mask = np.isfinite(lower) & np.isfinite(upper)
        if np.any(gap_mask):
            gap_path = upper[gap_mask] - lower[gap_mask]
            gap_k = np.asarray(unique_k, dtype=float)[gap_mask]
            features['band34_gap_proxy_hz'] = float(np.min(upper[gap_mask]) - np.max(lower[gap_mask]))
            features['band34_gap_path_min_hz'] = float(np.min(gap_path))
            features['band34_gap_path_max_hz'] = float(np.max(gap_path))
            features['band34_gap_path_mean_hz'] = float(np.mean(gap_path))
            features['band34_gap_path_std_hz'] = float(np.std(gap_path))
            features['band34_gap_positive_frac'] = float(np.mean(gap_path > 0.0))
            features['band34_gap_path_argmin_k'] = float(gap_k[int(np.argmin(gap_path))])
            features['band34_gap_path_argmax_k'] = float(gap_k[int(np.argmax(gap_path))])

    if legacy_k_vals:
        legacy_unique_k = sorted(set(legacy_k_vals))
        legacy_lower: List[float] = []
        legacy_upper: List[float] = []
        for k_val in legacy_unique_k:
            band_row = sorted(legacy_freq_vals[idx] for idx, kv in enumerate(legacy_k_vals) if kv == k_val)
            if len(band_row) >= 4:
                legacy_lower.append(band_row[2])
                legacy_upper.append(band_row[3])
        if legacy_lower and legacy_upper:
            legacy_lower_arr = np.asarray(legacy_lower, dtype=float)
            legacy_upper_arr = np.asarray(legacy_upper, dtype=float)
            legacy_gap_path = legacy_upper_arr - legacy_lower_arr
            features['legacy_band34_gap_proxy_hz'] = float(np.min(legacy_upper_arr) - np.max(legacy_lower_arr))
            features['legacy_band34_gap_path_min_hz'] = float(np.min(legacy_gap_path))
            features['legacy_band34_gap_path_max_hz'] = float(np.max(legacy_gap_path))
            features['legacy_band34_gap_path_mean_hz'] = float(np.mean(legacy_gap_path))
            features['legacy_band34_gap_path_std_hz'] = float(np.std(legacy_gap_path))
            features['legacy_band34_gap_positive_frac'] = float(np.mean(legacy_gap_path > 0.0))

    for band_idx in range(DISPERSION_BAND_COUNT):
        band_vals = matrix[:, band_idx]
        finite_vals = band_vals[np.isfinite(band_vals)]
        band_name = f'band{band_idx + 1:02d}'
        if finite_vals.size == 0:
            continue

        for k_idx in DISPERSION_SAMPLE_K_INDEXES:
            if k_idx < len(unique_k) and math.isfinite(band_vals[k_idx]):
                features[f'{band_name}_k{k_idx:02d}_hz'] = float(band_vals[k_idx])
        features[f'{band_name}_min_hz'] = float(np.min(finite_vals))
        features[f'{band_name}_max_hz'] = float(np.max(finite_vals))
        features[f'{band_name}_mean_hz'] = float(np.mean(finite_vals))
        features[f'{band_name}_std_hz'] = float(np.std(finite_vals))
        features[f'{band_name}_span_hz'] = float(np.max(finite_vals) - np.min(finite_vals))

        if finite_vals.size >= 2:
            diffs = np.diff(band_vals)
            finite_diffs = diffs[np.isfinite(diffs)]
            if finite_diffs.size > 0:
                features[f'{band_name}_tv_hz'] = float(np.sum(np.abs(finite_diffs)))
                features[f'{band_name}_slope_abs_mean'] = float(np.mean(np.abs(finite_diffs)))
                features[f'{band_name}_slope_abs_max'] = float(np.max(np.abs(finite_diffs)))

    _dispersion_cache[cache_key] = features
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
        for field in BASE_FEATURE_FIELDS:
            projected_row[field] = _to_float(row.get(field))
        projected_row.update(compute_extended_shape_features(shape_id, projected_row))
        for field in COMSOL_CONTEXT_FIELDS:
            projected_row[field] = _to_float(row.get(field))
        projected_row.update(_read_dispersion_features(_to_text(row.get('source_stage')), _to_text(row.get('sample_id'))))

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
        for field in PURE_V4_FEATURE_FIELDS:
            agg_row[field] = _aggregate_mean(subset, field)
        for field in ['gap34_Hz', 'gap34_rel', 'gap34_width_Hz', 'gap34_width_rel', 'max_gap_Hz', 'max_gap_rel']:
            agg_row[field] = _aggregate_mean(subset, field)
        agg_row['gap34_is_open'] = 1 if math.isfinite(_to_float(agg_row['gap34_width_Hz'])) and _to_float(agg_row['gap34_width_Hz']) > 1e-12 else 0
        agg_row['max_gap_is_open'] = 1 if math.isfinite(_to_float(agg_row['max_gap_Hz'])) and _to_float(agg_row['max_gap_Hz']) > 1e-12 else 0
        aggregated.append(agg_row)

    aggregated.sort(key=lambda item: (_stage_rank(_to_text(item.get('source_stage'))), _to_text(item.get('design_id'))))
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
        'dataset_name': 'pure_prediction_dataset_v4',
        'source_profile': source.PROFILE['name'],
        'feature_definition': 'design_point_aggregated_with_comsol_context_and_tbl1_dispersion_features',
        'feature_fields': PURE_V4_FEATURE_FIELDS,
        'base_feature_fields': BASE_FEATURE_FIELDS,
        'comsol_context_fields': COMSOL_CONTEXT_FIELDS,
        'dispersion_feature_fields': DISPERSION_FEATURE_FIELDS,
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
            'This v4 line is a diagnostic enriched predictor: it adds existing COMSOL context scalars plus dispersion features derived from tbl1 exports.',
            'The tbl1 parser keeps the real part of complex-valued frequencies instead of silently dropping rows with small imaginary parts.',
            'Because tbl1-derived features are post-solve signals, this line is not a strict apples-to-apples replacement for the original pre-solve pure prediction line.',
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
