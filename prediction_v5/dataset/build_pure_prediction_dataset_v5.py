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
from shared.objectives.prediction import PURE_TARGET_FIELDS
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

OUT_DIR = ROOT / 'data' / 'pure_prediction_v5' / 'v1'
MASTER_CSV = OUT_DIR / 'master_pure_prediction_dataset_v5.csv'
TASK_CSV = OUT_DIR / 'pure_bandgap_regression_v5.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'pure_prediction_stage_summary_v5.csv'
DATASET_INFO_JSON = OUT_DIR / 'pure_prediction_dataset_info_v5.json'

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

MASTER_FIELDS = [*AGG_METADATA_FIELDS, *PURE_V3_FEATURE_FIELDS, *PURE_TARGET_FIELDS]
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
    *PURE_TARGET_FIELDS,
]

_tbl1_path_by_stage: Dict[str, Path] = {}
_tbl1_metrics_cache: Dict[str, Dict[str, float]] = {}


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


def read_tbl1_metrics_robust(stage_name: str, sample_id: str) -> Dict[str, float]:
    cache_key = f'{_to_text(stage_name)}::{_to_text(sample_id)}'
    if cache_key in _tbl1_metrics_cache:
        return _tbl1_metrics_cache[cache_key]

    metrics = {
        'gap34_Hz': math.nan,
        'gap34_rel': math.nan,
        'max_gap_Hz': math.nan,
        'max_gap_rel': math.nan,
    }
    path = _tbl1_path(stage_name, sample_id)
    if path is None:
        _tbl1_metrics_cache[cache_key] = metrics
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
        _tbl1_metrics_cache[cache_key] = metrics
        return metrics

    unique_k = sorted(set(k_vals))
    bands_by_k: List[List[float]] = []
    max_bands = 0
    for k_val in unique_k:
        bands = sorted(freq_vals[idx] for idx, kv in enumerate(k_vals) if kv == k_val)
        bands_by_k.append(bands)
        max_bands = max(max_bands, len(bands))

    def column(band_idx: int) -> List[float]:
        out: List[float] = []
        for bands in bands_by_k:
            if band_idx < len(bands):
                out.append(bands[band_idx])
        return out

    if max_bands >= 4:
        lower = column(2)
        upper = column(3)
        if lower and upper:
            lower_edge = max(lower)
            upper_edge = min(upper)
            gap = upper_edge - lower_edge
            center = 0.5 * (lower_edge + upper_edge)
            metrics['gap34_Hz'] = gap
            if center != 0 and math.isfinite(center):
                metrics['gap34_rel'] = gap / center

    best_gap = -math.inf
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
            best_center = 0.5 * (lower_edge + upper_edge)
    if math.isfinite(best_gap) and best_gap > 0:
        metrics['max_gap_Hz'] = best_gap
        if best_center != 0 and math.isfinite(best_center):
            metrics['max_gap_rel'] = best_gap / best_center

    _tbl1_metrics_cache[cache_key] = metrics
    return metrics


def build_raw_rows() -> List[Dict[str, object]]:
    rows = source.build_rows()
    projected: List[Dict[str, object]] = []
    for row in rows:
        shape_id = _to_text(row.get('shape_id'))
        point_id = _canonical_point_id(row.get('point_id'))
        stage_name = _to_text(row.get('source_stage'))
        sample_id = _to_text(row.get('sample_id'))
        robust = read_tbl1_metrics_robust(stage_name, sample_id)
        gap34_hz = _to_float(robust.get('gap34_Hz'))
        gap34_rel = _to_float(robust.get('gap34_rel'))
        max_gap_hz = _to_float(robust.get('max_gap_Hz'))
        max_gap_rel = _to_float(robust.get('max_gap_rel'))

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
            'is_training_ready': int(_to_float(row.get('geometry_valid')) == 1.0 and _to_float(row.get('contact_valid')) == 1.0 and _to_float(row.get('solve_success')) == 1.0 and math.isfinite(gap34_hz)),
            'label_definition': 'fixed_gap_band_3_4_robust_tbl1_parser',
            'error_message': _to_text(row.get('error_message')),
        }
        for field in ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']:
            projected_row[field] = _to_float(row.get(field))
        projected_row.update(compute_shape_features(shape_id))
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
            'label_definition': 'fixed_gap_band_3_4_robust_tbl1_parser',
            'error_message': '',
        }
        for field in PURE_V3_FEATURE_FIELDS:
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
        'dataset_name': 'pure_prediction_dataset_v5',
        'source_profile': source.PROFILE['name'],
        'feature_definition': 'pure_structural_features_with_robust_reparsed_gap_labels_design_point_aggregated',
        'feature_fields': PURE_V3_FEATURE_FIELDS,
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
            'This line keeps pure structural features only and reparses tbl1 to build physically consistent labels.',
            'Targets are recomputed with a robust parser that keeps the real part of complex-valued frequencies.',
            'No COMSOL result-derived features are included in the training inputs.',
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
