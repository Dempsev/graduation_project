from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v1'
FIXED_GAP_BAND = 3

STAGES = [
    {
        'name': 'stage1',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'stage1_screening_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'tbl1_exports',
        'baseline_mode': 'single',
        'baseline_sample_id': 'stage1_trusted_baseline_v1__baseline',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'tbl1_exports',
    },
    {
        'name': 'stage2',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_fourier_robustness' / 'stage2_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_fourier_robustness' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_fourier_robustness' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_fourier_robustness' / 'tbl1_exports',
    },
    {
        'name': 'stage2_refine',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_refine' / 'stage2_refine_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_refine' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_refine' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_refine' / 'tbl1_exports',
    },
    {
        'name': 'stage2_harmonics',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics' / 'stage2_harmonics_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics' / 'tbl1_exports',
    },
    {
        'name': 'stage2_harmonics_refine',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics_refine' / 'stage2_harmonics_refine_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics_refine' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics_refine' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage2_harmonics_refine' / 'tbl1_exports',
    },
]

SHAPE_DIR = ROOT / 'data' / 'shape_contours'
MASTER_CSV = OUT_DIR / 'master_dataset_v1.csv'
REGRESSION_CSV = OUT_DIR / 'mlp_gap34_regression_v1.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'dataset_stage_summary_v1.csv'
DATASET_INFO_JSON = OUT_DIR / 'dataset_info_v1.json'

MASTER_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'candidate_id', 'fourier_id', 'main_id', 'point_id',
    'shape_id', 'shape_family',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'geometry_valid', 'contact_valid', 'solve_success', 'contact_length', 'n_domains', 'has_tiny_fragments',
    'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height', 'shape_bbox_aspect_ratio',
    'shape_centroid_x', 'shape_centroid_y', 'shape_point_count',
    'stage_reported_gap_Hz', 'stage_reported_gap_rel', 'stage_reported_gap_lower_band', 'stage_reported_gap_upper_band',
    'gap34_Hz', 'gap34_rel', 'gap34_lower_edge_Hz', 'gap34_upper_edge_Hz', 'gap34_center_freq',
    'ref_gap34_Hz', 'ref_gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive', 'is_training_ready', 'label_definition', 'error_message'
]

REGRESSION_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'shape_id', 'shape_family', 'candidate_id', 'main_id', 'point_id',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'contact_length', 'n_domains', 'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height',
    'shape_bbox_aspect_ratio', 'shape_centroid_x', 'shape_centroid_y', 'shape_point_count',
    'gap34_Hz', 'gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive'
]

_tbl1_cache: Dict[str, Dict[str, float]] = {}
_shape_cache: Dict[str, Dict[str, float]] = {}
_baseline_cache: Dict[str, Dict[str, Dict[str, float]]] = {}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def to_text(value) -> str:
    if value is None:
        return ''
    return str(value).strip()


def to_float(value, default=math.nan) -> float:
    text = to_text(value)
    if text == '' or text.lower() == 'nan':
        return default
    try:
        return float(text)
    except Exception:
        try:
            return float(complex(text).real)
        except Exception:
            return default


def to_bool(value) -> int:
    text = to_text(value).lower()
    return 1 if text in {'1', 'true', 'yes'} else 0


def parse_shape_family(shape_id: str) -> str:
    m = re.match(r'^(ep\d+)', shape_id or '')
    return m.group(1) if m else ''


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in fieldnames})


def read_tbl1_metrics(tbl1_path: Path) -> Dict[str, float]:
    key = str(tbl1_path)
    if key in _tbl1_cache:
        return _tbl1_cache[key]
    metrics = {
        'gap34_Hz': math.nan,
        'gap34_rel': math.nan,
        'gap34_lower_edge_Hz': math.nan,
        'gap34_upper_edge_Hz': math.nan,
        'gap34_center_freq': math.nan,
        'max_gap_Hz': math.nan,
        'max_gap_rel': math.nan,
        'max_gap_lower_band': math.nan,
        'max_gap_upper_band': math.nan,
        'max_gap_center_freq': math.nan,
    }
    if not tbl1_path.exists():
        _tbl1_cache[key] = metrics
        return metrics

    k_vals = []
    freq_vals = []
    with tbl1_path.open('r', encoding='utf-8-sig') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('%'):
                continue
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:
                continue
            k = to_float(parts[0])
            freq = to_float(parts[-1])
            if math.isfinite(k) and math.isfinite(freq):
                k_vals.append(k)
                freq_vals.append(freq)
    if not k_vals:
        _tbl1_cache[key] = metrics
        return metrics

    unique_k = sorted(set(k_vals))
    bands_by_k: List[List[float]] = []
    max_bands = 0
    for k in unique_k:
        bands = sorted(freq_vals[i] for i, kv in enumerate(k_vals) if kv == k)
        bands_by_k.append(bands)
        max_bands = max(max_bands, len(bands))

    def column(band_idx: int) -> List[float]:
        out = []
        for bands in bands_by_k:
            if band_idx < len(bands):
                out.append(bands[band_idx])
        return out

    # Fixed 3-4 gap.
    if max_bands >= FIXED_GAP_BAND + 1:
        lower = column(FIXED_GAP_BAND - 1)
        upper = column(FIXED_GAP_BAND)
        if lower and upper:
            lower_edge = max(lower)
            upper_edge = min(upper)
            gap = upper_edge - lower_edge
            center = 0.5 * (lower_edge + upper_edge)
            metrics['gap34_Hz'] = gap
            metrics['gap34_lower_edge_Hz'] = lower_edge
            metrics['gap34_upper_edge_Hz'] = upper_edge
            metrics['gap34_center_freq'] = center
            if center != 0 and math.isfinite(center):
                metrics['gap34_rel'] = gap / center

    best_gap = -math.inf
    best_band = math.nan
    best_center = math.nan
    for band_idx in range(max_bands - 1):
        lower = column(band_idx)
        upper = column(band_idx + 1)
        if not lower or not upper:
            continue
        lower_edge = max(lower)
        upper_edge = min(upper)
        gap = upper_edge - lower_edge
        if math.isfinite(gap) and gap > 0 and gap > best_gap:
            best_gap = gap
            best_band = band_idx + 1
            best_center = 0.5 * (lower_edge + upper_edge)
    if math.isfinite(best_gap) and best_gap > 0:
        metrics['max_gap_Hz'] = best_gap
        metrics['max_gap_lower_band'] = best_band
        metrics['max_gap_upper_band'] = best_band + 1
        metrics['max_gap_center_freq'] = best_center
        if best_center != 0 and math.isfinite(best_center):
            metrics['max_gap_rel'] = best_gap / best_center

    _tbl1_cache[key] = metrics
    return metrics


def read_shape_features(shape_id: str) -> Dict[str, float]:
    if shape_id in _shape_cache:
        return _shape_cache[shape_id]
    features = {
        'shape_area': math.nan,
        'shape_perimeter': math.nan,
        'shape_bbox_width': math.nan,
        'shape_bbox_height': math.nan,
        'shape_bbox_aspect_ratio': math.nan,
        'shape_centroid_x': math.nan,
        'shape_centroid_y': math.nan,
        'shape_point_count': math.nan,
    }
    if not shape_id or shape_id == '__baseline__':
        _shape_cache[shape_id] = features
        return features

    path = SHAPE_DIR / f'{shape_id}.csv'
    if not path.exists():
        _shape_cache[shape_id] = features
        return features

    pts: List[Tuple[float, float]] = []
    with path.open('r', encoding='utf-8-sig') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:
                continue
            x = to_float(parts[0])
            y = to_float(parts[1])
            if math.isfinite(x) and math.isfinite(y):
                pts.append((x, y))
    if len(pts) < 3:
        _shape_cache[shape_id] = features
        return features

    if pts[0] != pts[-1]:
        pts.append(pts[0])
    xs = [p[0] for p in pts[:-1]]
    ys = [p[1] for p in pts[:-1]]
    area_acc = 0.0
    cx_acc = 0.0
    cy_acc = 0.0
    perimeter = 0.0
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        cross = x1 * y2 - x2 * y1
        area_acc += cross
        cx_acc += (x1 + x2) * cross
        cy_acc += (y1 + y2) * cross
        perimeter += math.hypot(x2 - x1, y2 - y1)
    area = 0.5 * abs(area_acc)
    bbox_width = max(xs) - min(xs)
    bbox_height = max(ys) - min(ys)
    aspect = bbox_width / bbox_height if bbox_height not in (0.0, math.nan) and bbox_height != 0 else math.nan
    if abs(area_acc) > 1e-12:
        centroid_x = cx_acc / (3.0 * area_acc)
        centroid_y = cy_acc / (3.0 * area_acc)
    else:
        centroid_x = sum(xs) / len(xs)
        centroid_y = sum(ys) / len(ys)
    features = {
        'shape_area': area,
        'shape_perimeter': perimeter,
        'shape_bbox_width': bbox_width,
        'shape_bbox_height': bbox_height,
        'shape_bbox_aspect_ratio': aspect,
        'shape_centroid_x': centroid_x,
        'shape_centroid_y': centroid_y,
        'shape_point_count': len(pts) - 1,
    }
    _shape_cache[shape_id] = features
    return features


def build_point_baseline_lookup(stage_cfg: Dict[str, object]) -> Dict[str, Dict[str, float]]:
    cache_key = stage_cfg['name']
    if cache_key in _baseline_cache:
        return _baseline_cache[cache_key]
    out: Dict[str, Dict[str, float]] = {}
    if stage_cfg.get('baseline_mode') != 'by_point':
        _baseline_cache[cache_key] = out
        return out
    rows = read_csv_rows(Path(stage_cfg['baseline_csv']))
    tbl1_dir = Path(stage_cfg['baseline_tbl1_dir'])
    for row in rows:
        point_id = to_text(row.get('point_id'))
        sample_id = to_text(row.get('sample_id'))
        if not point_id:
            continue
        metrics = {
            'ref_gap34_Hz': to_float(row.get('ref_gap34_Hz')),
            'ref_gap34_rel': to_float(row.get('ref_gap34_rel')),
        }
        if (not math.isfinite(metrics['ref_gap34_Hz'])) and sample_id:
            tbl1_metrics = read_tbl1_metrics(tbl1_dir / f'{sample_id}_tbl1.csv')
            metrics['ref_gap34_Hz'] = tbl1_metrics['gap34_Hz']
            metrics['ref_gap34_rel'] = tbl1_metrics['gap34_rel']
        out[point_id] = metrics
    _baseline_cache[cache_key] = out
    return out


def get_single_baseline_metrics(stage_cfg: Dict[str, object]) -> Dict[str, float]:
    cache_key = stage_cfg['name']
    if cache_key in _baseline_cache:
        return _baseline_cache[cache_key]['__single__']
    sample_id = stage_cfg['baseline_sample_id']
    tbl1_dir = Path(stage_cfg['baseline_tbl1_dir'])
    metrics = read_tbl1_metrics(tbl1_dir / f'{sample_id}_tbl1.csv')
    out = {'ref_gap34_Hz': metrics['gap34_Hz'], 'ref_gap34_rel': metrics['gap34_rel']}
    _baseline_cache[cache_key] = {'__single__': out}
    return out


def get_reference_metrics(stage_cfg: Dict[str, object], row: Dict[str, str]) -> Tuple[float, float]:
    mode = stage_cfg.get('baseline_mode')
    if mode == 'single':
        m = get_single_baseline_metrics(stage_cfg)
        return m['ref_gap34_Hz'], m['ref_gap34_rel']
    if mode == 'by_point':
        point_id = to_text(row.get('point_id'))
        m = build_point_baseline_lookup(stage_cfg).get(point_id, {})
        return to_float(m.get('ref_gap34_Hz')), to_float(m.get('ref_gap34_rel'))
    return math.nan, math.nan


def stage_reported_gap_fields(row: Dict[str, str]) -> Tuple[float, float, float, float]:
    hz = to_float(row.get('gap_target_Hz', row.get('gap34_Hz')))
    rel = to_float(row.get('gap_target_rel', row.get('gap34_rel')))
    lb = to_float(row.get('gap_lower_band', row.get('max_gap_lower_band')))
    ub = to_float(row.get('gap_upper_band', row.get('max_gap_upper_band')))
    return hz, rel, lb, ub


def standardize_row(stage_cfg: Dict[str, object], row: Dict[str, str]) -> Dict[str, object]:
    stage_name = stage_cfg['name']
    sample_id = to_text(row.get('sample_id'))
    tbl1_path = Path(stage_cfg['tbl1_dir']) / f'{sample_id}_tbl1.csv'
    tbl1_metrics = read_tbl1_metrics(tbl1_path) if sample_id else {
        'gap34_Hz': math.nan, 'gap34_rel': math.nan, 'gap34_lower_edge_Hz': math.nan, 'gap34_upper_edge_Hz': math.nan,
        'gap34_center_freq': math.nan, 'max_gap_Hz': math.nan, 'max_gap_rel': math.nan,
        'max_gap_lower_band': math.nan, 'max_gap_upper_band': math.nan, 'max_gap_center_freq': math.nan,
    }
    explicit_gap34_hz = to_float(row.get('gap34_Hz'))
    explicit_gap34_rel = to_float(row.get('gap34_rel'))
    explicit_gap34_lower = to_float(row.get('gap34_lower_edge_Hz'))
    explicit_gap34_upper = to_float(row.get('gap34_upper_edge_Hz'))
    explicit_gap34_center = to_float(row.get('gap34_center_freq'))
    explicit_ref_gap34_hz = to_float(row.get('ref_gap34_Hz'))
    explicit_ref_gap34_rel = to_float(row.get('ref_gap34_rel'))
    explicit_gap34_gain_hz = to_float(row.get('gap34_gain_Hz'))
    explicit_gap34_gain_rel = to_float(row.get('gap34_gain_rel'))
    explicit_max_gap_hz = to_float(row.get('max_gap_Hz'))
    explicit_max_gap_rel = to_float(row.get('max_gap_rel'))
    explicit_max_gap_lb = to_float(row.get('max_gap_lower_band'))
    explicit_max_gap_ub = to_float(row.get('max_gap_upper_band'))
    explicit_max_gap_center = to_float(row.get('max_gap_center_freq'))
    shape_id = to_text(row.get('shape_id'))
    shape_features = read_shape_features(shape_id)
    ref_gap34_hz, ref_gap34_rel = get_reference_metrics(stage_cfg, row)
    gap34_hz = explicit_gap34_hz if math.isfinite(explicit_gap34_hz) else (tbl1_metrics['gap34_Hz'] if to_bool(row.get('solve_success')) else math.nan)
    gap34_rel = explicit_gap34_rel if math.isfinite(explicit_gap34_rel) else (tbl1_metrics['gap34_rel'] if to_bool(row.get('solve_success')) else math.nan)
    gap34_lower_edge = explicit_gap34_lower if math.isfinite(explicit_gap34_lower) else (tbl1_metrics['gap34_lower_edge_Hz'] if to_bool(row.get('solve_success')) else math.nan)
    gap34_upper_edge = explicit_gap34_upper if math.isfinite(explicit_gap34_upper) else (tbl1_metrics['gap34_upper_edge_Hz'] if to_bool(row.get('solve_success')) else math.nan)
    gap34_center = explicit_gap34_center if math.isfinite(explicit_gap34_center) else (tbl1_metrics['gap34_center_freq'] if to_bool(row.get('solve_success')) else math.nan)
    ref_gap34_hz = explicit_ref_gap34_hz if math.isfinite(explicit_ref_gap34_hz) else ref_gap34_hz
    ref_gap34_rel = explicit_ref_gap34_rel if math.isfinite(explicit_ref_gap34_rel) else ref_gap34_rel
    gap34_gain_hz = explicit_gap34_gain_hz if math.isfinite(explicit_gap34_gain_hz) else (gap34_hz - ref_gap34_hz if math.isfinite(gap34_hz) and math.isfinite(ref_gap34_hz) else math.nan)
    gap34_gain_rel = explicit_gap34_gain_rel if math.isfinite(explicit_gap34_gain_rel) else (gap34_rel - ref_gap34_rel if math.isfinite(gap34_rel) and math.isfinite(ref_gap34_rel) else math.nan)
    max_gap_hz = explicit_max_gap_hz if math.isfinite(explicit_max_gap_hz) else (tbl1_metrics['max_gap_Hz'] if to_bool(row.get('solve_success')) else math.nan)
    max_gap_rel = explicit_max_gap_rel if math.isfinite(explicit_max_gap_rel) else (tbl1_metrics['max_gap_rel'] if to_bool(row.get('solve_success')) else math.nan)
    max_gap_lb = explicit_max_gap_lb if math.isfinite(explicit_max_gap_lb) else (tbl1_metrics['max_gap_lower_band'] if to_bool(row.get('solve_success')) else math.nan)
    max_gap_ub = explicit_max_gap_ub if math.isfinite(explicit_max_gap_ub) else (tbl1_metrics['max_gap_upper_band'] if to_bool(row.get('solve_success')) else math.nan)
    max_gap_center = explicit_max_gap_center if math.isfinite(explicit_max_gap_center) else (tbl1_metrics['max_gap_center_freq'] if to_bool(row.get('solve_success')) else math.nan)
    stage_gap_hz, stage_gap_rel, stage_gap_lb, stage_gap_ub = stage_reported_gap_fields(row)

    source_role = to_text(row.get('shape_role')) or to_text(row.get('candidate_role')) or ('screening' if stage_name == 'stage1' else '')
    out = {
        'sample_id': sample_id,
        'source_stage': stage_name,
        'source_role': source_role,
        'candidate_id': to_text(row.get('candidate_id')),
        'fourier_id': to_text(row.get('fourier_id')),
        'main_id': to_text(row.get('main_id')),
        'point_id': to_text(row.get('point_id')),
        'shape_id': shape_id,
        'shape_family': parse_shape_family(shape_id),
        'a1': to_float(row.get('a1'), 0.0),
        'a2': to_float(row.get('a2'), 0.0),
        'b1': to_float(row.get('b1'), 0.0),
        'b2': to_float(row.get('b2'), 0.0),
        'a3': to_float(row.get('a3'), 0.0),
        'b3': to_float(row.get('b3'), 0.0),
        'a4': to_float(row.get('a4'), 0.0),
        'b4': to_float(row.get('b4'), 0.0),
        'a5': to_float(row.get('a5'), 0.0),
        'b5': to_float(row.get('b5'), 0.0),
        'r0': to_float(row.get('r0'), math.nan),
        'shift': to_float(row.get('shift'), math.nan),
        'neigs': to_float(row.get('neigs'), math.nan),
        'geometry_valid': to_bool(row.get('geometry_valid')),
        'contact_valid': to_bool(row.get('contact_valid')),
        'solve_success': to_bool(row.get('solve_success')),
        'contact_length': to_float(row.get('contact_length')),
        'n_domains': to_float(row.get('n_domains')),
        'has_tiny_fragments': to_bool(row.get('has_tiny_fragments')),
        'stage_reported_gap_Hz': stage_gap_hz,
        'stage_reported_gap_rel': stage_gap_rel,
        'stage_reported_gap_lower_band': stage_gap_lb,
        'stage_reported_gap_upper_band': stage_gap_ub,
        'gap34_Hz': gap34_hz,
        'gap34_rel': gap34_rel,
        'gap34_lower_edge_Hz': gap34_lower_edge,
        'gap34_upper_edge_Hz': gap34_upper_edge,
        'gap34_center_freq': gap34_center,
        'ref_gap34_Hz': ref_gap34_hz,
        'ref_gap34_rel': ref_gap34_rel,
        'gap34_gain_Hz': gap34_gain_hz,
        'gap34_gain_rel': gap34_gain_rel,
        'max_gap_Hz': max_gap_hz,
        'max_gap_rel': max_gap_rel,
        'max_gap_lower_band': max_gap_lb,
        'max_gap_upper_band': max_gap_ub,
        'max_gap_center_freq': max_gap_center,
        'is_gap34_positive': 1 if math.isfinite(gap34_hz) and gap34_hz > 0 else 0,
        'is_gap34_gain_positive': 1 if math.isfinite(gap34_gain_hz) and gap34_gain_hz > 0 else 0,
        'is_training_ready': 1 if to_bool(row.get('geometry_valid')) and to_bool(row.get('contact_valid')) and to_bool(row.get('solve_success')) and math.isfinite(gap34_hz) else 0,
        'label_definition': 'fixed_gap_band_3_4',
        'error_message': to_text(row.get('error_message')),
    }
    out.update(shape_features)
    return out


def build_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for stage_cfg in STAGES:
        stage_rows = read_csv_rows(Path(stage_cfg['results_csv']))
        for row in stage_rows:
            rows.append(standardize_row(stage_cfg, row))
    rows.sort(key=lambda r: (r['source_stage'], r['sample_id']))
    return rows


def build_stage_summary(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(row['source_stage'], []).append(row)
    summary: List[Dict[str, object]] = []
    for stage, sub in grouped.items():
        summary.append({
            'source_stage': stage,
            'rows_total': len(sub),
            'rows_training_ready': sum(int(r['is_training_ready']) for r in sub),
            'rows_gap34_positive': sum(int(r['is_gap34_positive']) for r in sub),
            'rows_gap34_gain_positive': sum(int(r['is_gap34_gain_positive']) for r in sub),
            'rows_contact_valid': sum(int(r['contact_valid']) for r in sub),
            'rows_solve_success': sum(int(r['solve_success']) for r in sub),
        })
    summary.sort(key=lambda r: r['source_stage'])
    return summary


def main() -> None:
    ensure_dir(OUT_DIR)
    rows = build_rows()
    regression_rows = [row for row in rows if int(row['is_training_ready']) == 1]
    stage_summary = build_stage_summary(rows)
    write_csv(MASTER_CSV, rows, MASTER_FIELDS)
    write_csv(REGRESSION_CSV, regression_rows, REGRESSION_FIELDS)
    write_csv(STAGE_SUMMARY_CSV, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
    info = {
        'label_definition': 'fixed_gap_band_3_4',
        'fixed_gap_band': FIXED_GAP_BAND,
        'master_rows': len(rows),
        'regression_rows': len(regression_rows),
        'source_stages': [cfg['name'] for cfg in STAGES],
        'master_csv': str(MASTER_CSV),
        'regression_csv': str(REGRESSION_CSV),
        'stage_summary_csv': str(STAGE_SUMMARY_CSV),
    }
    DATASET_INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[DONE] master rows: {len(rows)}')
    print(f'[DONE] regression rows: {len(regression_rows)}')
    print(f'[OUT] {MASTER_CSV}')
    print(f'[OUT] {REGRESSION_CSV}')
    print(f'[OUT] {STAGE_SUMMARY_CSV}')


if __name__ == '__main__':
    main()
