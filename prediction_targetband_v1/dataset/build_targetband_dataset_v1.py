from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_DATASET_DIR = ROOT / 'stage3_dataset'
if str(STAGE3_DATASET_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE3_DATASET_DIR))

from stage3_dataset import build_v7_training_dataset as source
from prediction_v3.dataset.build_pure_prediction_dataset_v3 import (
    PURE_V3_FEATURE_FIELDS,
    compute_shape_features,
    _aggregate_mean,
    _canonical_point_id,
    _pick_representative,
    _stage_rank,
    _to_float,
    _to_text,
)

OUT_ROOT = ROOT / 'data' / 'prediction_targetband_v1'

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

TARGET_FIELDS = [
    'target_band_low_Hz',
    'target_band_high_Hz',
    'target_gap_is_open',
    'target_gap_overlap_Hz',
    'target_gap_cover_ratio',
    'target_gap_best_width_Hz',
    'target_gap_lower_edge_Hz',
    'target_gap_upper_edge_Hz',
    'target_gap_center_freq',
    'target_gap_lower_band',
    'target_gap_upper_band',
]

MASTER_FIELDS = [*AGG_METADATA_FIELDS, *PURE_V3_FEATURE_FIELDS, *TARGET_FIELDS]
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
    *PURE_V3_FEATURE_FIELDS,
    *TARGET_FIELDS,
]

_tbl1_path_by_stage: Dict[str, Path] = {}
_target_cache: Dict[str, Dict[str, float]] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a pure-structural target-band prediction dataset.')
    parser.add_argument('--band-low', type=float, default=120.0)
    parser.add_argument('--band-high', type=float, default=160.0)
    parser.add_argument('--dataset-tag', default='band120_160')
    return parser.parse_args()


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


def read_target_gap_metrics(stage_name: str, sample_id: str, band_low: float, band_high: float) -> Dict[str, float]:
    cache_key = f'{_to_text(stage_name)}::{_to_text(sample_id)}::{band_low:.6f}::{band_high:.6f}'
    if cache_key in _target_cache:
        return _target_cache[cache_key]

    metrics = {field: math.nan for field in TARGET_FIELDS}
    metrics['target_band_low_Hz'] = band_low
    metrics['target_band_high_Hz'] = band_high
    metrics['target_gap_is_open'] = 0
    metrics['target_gap_overlap_Hz'] = 0.0
    metrics['target_gap_cover_ratio'] = 0.0

    path = _tbl1_path(stage_name, sample_id)
    if path is None:
        _target_cache[cache_key] = metrics
        return metrics

    k_vals: List[float] = []
    freq_vals: List[float] = []
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
            freq_val = _to_complex_real(parts[-1])
            if math.isfinite(freq_val):
                k_vals.append(k_val)
                freq_vals.append(freq_val)

    if not k_vals:
        _target_cache[cache_key] = metrics
        return metrics

    unique_k = sorted(set(k_vals))
    bands_by_k: List[List[float]] = []
    max_bands = 0
    for k_val in unique_k:
        bands = sorted(freq_vals[idx] for idx, kv in enumerate(k_vals) if kv == k_val)
        bands_by_k.append(bands)
        max_bands = max(max_bands, len(bands))

    best_overlap = 0.0
    best_width = -math.inf
    best_lower = math.nan
    best_upper = math.nan
    best_lb = math.nan
    best_ub = math.nan
    for band_idx in range(max_bands - 1):
        lower: List[float] = []
        upper: List[float] = []
        for bands in bands_by_k:
            if len(bands) > band_idx + 1:
                lower.append(bands[band_idx])
                upper.append(bands[band_idx + 1])
        if not lower or not upper:
            continue
        lower_edge = max(lower)
        upper_edge = min(upper)
        gap_width = upper_edge - lower_edge
        if not math.isfinite(gap_width) or gap_width <= 0:
            continue
        overlap = max(0.0, min(upper_edge, band_high) - max(lower_edge, band_low))
        if overlap > best_overlap + 1e-12 or (abs(overlap - best_overlap) <= 1e-12 and gap_width > best_width):
            best_overlap = overlap
            best_width = gap_width
            best_lower = lower_edge
            best_upper = upper_edge
            best_lb = float(band_idx + 1)
            best_ub = float(band_idx + 2)

    if best_overlap > 0.0:
        metrics['target_gap_is_open'] = 1
        metrics['target_gap_overlap_Hz'] = best_overlap
        metrics['target_gap_cover_ratio'] = best_overlap / max(1e-12, band_high - band_low)
        metrics['target_gap_best_width_Hz'] = best_width
        metrics['target_gap_lower_edge_Hz'] = best_lower
        metrics['target_gap_upper_edge_Hz'] = best_upper
        metrics['target_gap_center_freq'] = 0.5 * (best_lower + best_upper)
        metrics['target_gap_lower_band'] = best_lb
        metrics['target_gap_upper_band'] = best_ub
    _target_cache[cache_key] = metrics
    return metrics


def build_raw_rows(band_low: float, band_high: float) -> List[Dict[str, object]]:
    rows = source.build_rows()
    projected: List[Dict[str, object]] = []
    for row in rows:
        shape_id = _to_text(row.get('shape_id'))
        point_id = _canonical_point_id(row.get('point_id'))
        stage_name = _to_text(row.get('source_stage'))
        sample_id = _to_text(row.get('sample_id'))
        target_metrics = read_target_gap_metrics(stage_name, sample_id, band_low, band_high)
        projected_row: Dict[str, object] = {
            'sample_id': sample_id,
            'source_stage': stage_name,
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
            'label_definition': f'target_band_{int(round(band_low))}_{int(round(band_high))}_robust_complete_gap_overlap',
            'error_message': _to_text(row.get('error_message')),
        }
        for field in ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']:
            projected_row[field] = _to_float(row.get(field))
        projected_row.update(compute_shape_features(shape_id))
        projected_row.update(target_metrics)
        projected_row['is_training_ready'] = int(
            projected_row['geometry_valid'] == 1
            and projected_row['contact_valid'] == 1
            and projected_row['solve_success'] == 1
        )
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
        agg_row: Dict[str, object] = {
            'sample_id': design_id,
            'design_id': design_id,
            'observation_count': len(subset),
            'source_stage_count': len(stage_names),
            'source_stage': _to_text(representative.get('source_stage')),
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
        for field in PURE_V3_FEATURE_FIELDS:
            agg_row[field] = _aggregate_mean(subset, field)
        for field in TARGET_FIELDS:
            agg_row[field] = _aggregate_mean(subset, field)
        agg_row['target_gap_is_open'] = 1 if _to_float(agg_row.get('target_gap_overlap_Hz')) > 1e-12 else 0
        aggregated.append(agg_row)

    aggregated.sort(key=lambda item: (_stage_rank(_to_text(item.get('source_stage'))), _to_text(item.get('design_id'))))
    return aggregated


def build_task_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_rows: List[Dict[str, object]] = []
    for row in rows:
        if int(row.get('is_training_ready', 0)) != 1:
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
            'rows_targetband_prediction': task_counts.get(stage_name, 0),
        })
    summary.sort(key=lambda item: (_stage_rank(item['source_stage']), item['source_stage']))
    return summary


def build_dataset_info(raw_rows: List[Dict[str, object]], rows: List[Dict[str, object]], task_rows: List[Dict[str, object]], stage_summary: List[Dict[str, object]], band_low: float, band_high: float, out_dir: Path, master_csv: Path, task_csv: Path, stage_summary_csv: Path) -> Dict[str, object]:
    return {
        'dataset_name': 'prediction_targetband_v1',
        'source_profile': source.PROFILE['name'],
        'feature_definition': 'pure_structural_enriched_v3_features_only',
        'feature_fields': PURE_V3_FEATURE_FIELDS,
        'target_fields': TARGET_FIELDS,
        'design_key': 'shape_id + point_id',
        'target_band_low_Hz': band_low,
        'target_band_high_Hz': band_high,
        'task_definition': 'best complete-gap overlap inside the fixed target frequency window',
        'raw_rows': len(raw_rows),
        'master_rows': len(rows),
        'task_rows': len(task_rows),
        'out_dir': str(out_dir),
        'master_csv': str(master_csv),
        'task_csv': str(task_csv),
        'stage_summary_csv': str(stage_summary_csv),
        'stage_summary': stage_summary,
        'notes': [
            'This line keeps inputs purely structural and builds labels from robust complete-gap overlap with a fixed frequency window.',
            'The fixed-band task is intended as a design-oriented companion to the global pure-prediction mainline.',
        ],
    }


def main() -> None:
    args = parse_args()
    out_dir = OUT_ROOT / args.dataset_tag
    master_csv = out_dir / 'master_targetband_dataset_v1.csv'
    task_csv = out_dir / 'targetband_prediction_v1.csv'
    stage_summary_csv = out_dir / 'targetband_stage_summary_v1.csv'
    dataset_info_json = out_dir / 'targetband_dataset_info_v1.json'

    source.base.ensure_dir(out_dir)
    raw_rows = build_raw_rows(args.band_low, args.band_high)
    rows = aggregate_rows(raw_rows)
    task_rows = build_task_rows(rows)
    stage_summary = build_stage_summary(rows, task_rows)

    source.base.write_csv(master_csv, rows, MASTER_FIELDS)
    source.base.write_csv(task_csv, task_rows, TASK_FIELDS)
    source.base.write_csv(stage_summary_csv, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
    dataset_info_json.write_text(
        json.dumps(build_dataset_info(raw_rows, rows, task_rows, stage_summary, args.band_low, args.band_high, out_dir, master_csv, task_csv, stage_summary_csv), indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    print(f'[DONE] raw rows: {len(raw_rows)}')
    print(f'[DONE] aggregated rows: {len(rows)}')
    print(f'[DONE] aggregated task rows: {len(task_rows)}')
    print(f'[OUT] {master_csv}')
    print(f'[OUT] {task_csv}')
    print(f'[OUT] {stage_summary_csv}')


if __name__ == '__main__':
    main()
