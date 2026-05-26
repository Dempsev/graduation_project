from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

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

OUT_ROOT = ROOT / 'data' / 'pure_prediction_v6'
ENGINEERING_WINDOWS: List[Tuple[str, float, float]] = [
    ('band120_160', 120.0, 160.0),
    ('band180_220', 180.0, 220.0),
    ('band220_260', 220.0, 260.0),
]

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

PURE_V6_TARGET_FIELDS = [
    'first_gap_Hz',
    'first_gap_rel',
    'first_gap_width_Hz',
    'first_gap_width_rel',
    'first_gap_is_open',
    'first_gap_lower_band',
    'first_gap_upper_band',
    'first_gap_lower_edge_Hz',
    'first_gap_upper_edge_Hz',
    'first_gap_center_freq',
    'first_gap_overlaps_band120_160',
    'first_gap_overlaps_band180_220',
    'first_gap_overlaps_band220_260',
    'first_gap_overlaps_any_curated',
]

MASTER_FIELDS = [*AGG_METADATA_FIELDS, *PURE_V3_FEATURE_FIELDS, *PURE_V6_TARGET_FIELDS]
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
    *PURE_V6_TARGET_FIELDS,
]

_tbl1_path_by_stage: Dict[str, Path] = {}
_first_gap_cache: Dict[str, Dict[str, float]] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a pure-structural dataset for the first complete gap above acoustic branches.')
    parser.add_argument('--dataset-tag', default='v1')
    parser.add_argument('--acoustic-branches', type=int, default=3)
    parser.add_argument('--gap-epsilon', type=float, default=1e-12)
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


def _gap_overlaps_window(lower_edge: float, upper_edge: float, band_low: float, band_high: float, eps: float) -> int:
    if not (math.isfinite(lower_edge) and math.isfinite(upper_edge)):
        return 0
    overlap = min(upper_edge, band_high) - max(lower_edge, band_low)
    return 1 if math.isfinite(overlap) and overlap > eps else 0


def read_first_gap_metrics(stage_name: str, sample_id: str, acoustic_branches: int, gap_epsilon: float) -> Dict[str, float]:
    cache_key = f'{_to_text(stage_name)}::{_to_text(sample_id)}::{acoustic_branches}::{gap_epsilon:.6e}'
    if cache_key in _first_gap_cache:
        return _first_gap_cache[cache_key]

    metrics = {field: math.nan for field in PURE_V6_TARGET_FIELDS}
    metrics['first_gap_Hz'] = 0.0
    metrics['first_gap_width_Hz'] = 0.0
    metrics['first_gap_width_rel'] = 0.0
    metrics['first_gap_is_open'] = 0
    for tag, _, _ in ENGINEERING_WINDOWS:
        metrics[f'first_gap_overlaps_{tag}'] = 0
    metrics['first_gap_overlaps_any_curated'] = 0

    path = _tbl1_path(stage_name, sample_id)
    if path is None:
        _first_gap_cache[cache_key] = metrics
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
        _first_gap_cache[cache_key] = metrics
        return metrics

    unique_k = sorted(set(k_vals))
    bands_by_k: List[List[float]] = []
    max_bands = 0
    for k_val in unique_k:
        bands = sorted(freq_vals[idx] for idx, kv in enumerate(k_vals) if kv == k_val)
        bands_by_k.append(bands)
        max_bands = max(max_bands, len(bands))

    start_idx = max(0, acoustic_branches - 1)
    chosen: Dict[str, float] | None = None
    for band_idx in range(start_idx, max_bands - 1):
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
        gap = upper_edge - lower_edge
        if math.isfinite(gap) and gap > gap_epsilon:
            center = 0.5 * (lower_edge + upper_edge)
            rel = gap / center if math.isfinite(center) and abs(center) > 1e-12 else math.nan
            chosen = {
                'first_gap_Hz': gap,
                'first_gap_rel': rel,
                'first_gap_width_Hz': gap,
                'first_gap_width_rel': rel,
                'first_gap_is_open': 1,
                'first_gap_lower_band': float(band_idx + 1),
                'first_gap_upper_band': float(band_idx + 2),
                'first_gap_lower_edge_Hz': lower_edge,
                'first_gap_upper_edge_Hz': upper_edge,
                'first_gap_center_freq': center,
            }
            break

    if chosen is not None:
        metrics.update(chosen)
        overlap_any = 0
        lower_edge = float(metrics['first_gap_lower_edge_Hz'])
        upper_edge = float(metrics['first_gap_upper_edge_Hz'])
        for tag, band_low, band_high in ENGINEERING_WINDOWS:
            hit = _gap_overlaps_window(lower_edge, upper_edge, band_low, band_high, gap_epsilon)
            metrics[f'first_gap_overlaps_{tag}'] = hit
            overlap_any = max(overlap_any, hit)
        metrics['first_gap_overlaps_any_curated'] = overlap_any

    _first_gap_cache[cache_key] = metrics
    return metrics


def build_raw_rows(acoustic_branches: int, gap_epsilon: float) -> List[Dict[str, object]]:
    rows = source.build_rows()
    projected: List[Dict[str, object]] = []
    for row in rows:
        shape_id = _to_text(row.get('shape_id'))
        point_id = _canonical_point_id(row.get('point_id'))
        stage_name = _to_text(row.get('source_stage'))
        sample_id = _to_text(row.get('sample_id'))
        first_gap = read_first_gap_metrics(stage_name, sample_id, acoustic_branches, gap_epsilon)

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
            'is_training_ready': int(
                _to_float(row.get('geometry_valid')) == 1.0
                and _to_float(row.get('contact_valid')) == 1.0
                and _to_float(row.get('solve_success')) == 1.0
                and math.isfinite(_to_float(first_gap.get('first_gap_width_Hz')))
            ),
            'label_definition': f'first_complete_gap_above_{acoustic_branches}_acoustic_branches_robust_tbl1_parser',
            'error_message': _to_text(row.get('error_message')),
        }
        for field in ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']:
            projected_row[field] = _to_float(row.get(field))
        projected_row.update(compute_shape_features(shape_id))
        projected_row.update(first_gap)
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
        for field in [
            'first_gap_Hz',
            'first_gap_rel',
            'first_gap_width_Hz',
            'first_gap_width_rel',
            'first_gap_lower_edge_Hz',
            'first_gap_upper_edge_Hz',
            'first_gap_center_freq',
            'first_gap_overlaps_band120_160',
            'first_gap_overlaps_band180_220',
            'first_gap_overlaps_band220_260',
            'first_gap_overlaps_any_curated',
        ]:
            agg_row[field] = _aggregate_mean(subset, field)
        agg_row['first_gap_is_open'] = 1 if _to_float(agg_row.get('first_gap_width_Hz')) > 1e-12 else 0
        agg_row['first_gap_lower_band'] = _to_float(representative.get('first_gap_lower_band'))
        agg_row['first_gap_upper_band'] = _to_float(representative.get('first_gap_upper_band'))
        for field in [
            'first_gap_overlaps_band120_160',
            'first_gap_overlaps_band180_220',
            'first_gap_overlaps_band220_260',
            'first_gap_overlaps_any_curated',
        ]:
            agg_row[field] = 1 if _to_float(agg_row.get(field)) >= 0.5 else 0
        aggregated.append(agg_row)

    aggregated.sort(key=lambda item: (_stage_rank(_to_text(item.get('source_stage'))), _to_text(item.get('design_id'))))
    return aggregated


def build_task_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_rows: List[Dict[str, object]] = []
    for row in rows:
        if int(row.get('is_training_ready', 0)) != 1:
            continue
        if not math.isfinite(_to_float(row.get('first_gap_width_Hz'))):
            continue
        task_rows.append({field: row.get(field, '') for field in TASK_FIELDS})
    return task_rows


def build_stage_summary(rows: List[Dict[str, object]], task_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    task_counts: Dict[str, int] = {}
    pair_counts: Dict[str, Counter] = {}
    for row in task_rows:
        stage_name = _to_text(row.get('source_stage'))
        task_counts[stage_name] = task_counts.get(stage_name, 0) + 1
        lb = int(_to_float(row.get('first_gap_lower_band'))) if math.isfinite(_to_float(row.get('first_gap_lower_band'))) else -1
        ub = int(_to_float(row.get('first_gap_upper_band'))) if math.isfinite(_to_float(row.get('first_gap_upper_band'))) else -1
        pair_counts.setdefault(stage_name, Counter())[(lb, ub)] += 1

    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(_to_text(row.get('source_stage')), []).append(row)

    summary = []
    for stage_name, subset in grouped.items():
        common_pair = ''
        if pair_counts.get(stage_name):
            (lb, ub), count = pair_counts[stage_name].most_common(1)[0]
            common_pair = f'{lb}-{ub} ({count})'
        summary.append({
            'source_stage': stage_name,
            'rows_total': len(subset),
            'rows_training_ready': sum(int(row.get('is_training_ready', 0)) for row in subset),
            'rows_first_gap_open': sum(int(_to_float(row.get('first_gap_is_open')) > 0.5) for row in subset),
            'rows_first_gap_overlap_any_curated': sum(int(_to_float(row.get('first_gap_overlaps_any_curated')) > 0.5) for row in subset),
            'dominant_first_gap_pair': common_pair,
            'rows_pure_prediction': task_counts.get(stage_name, 0),
        })
    summary.sort(key=lambda item: (_stage_rank(item['source_stage']), item['source_stage']))
    return summary


def build_dataset_info(
    raw_rows: List[Dict[str, object]],
    rows: List[Dict[str, object]],
    task_rows: List[Dict[str, object]],
    stage_summary: List[Dict[str, object]],
    acoustic_branches: int,
    gap_epsilon: float,
    out_dir: Path,
    master_csv: Path,
    task_csv: Path,
    stage_summary_csv: Path,
) -> Dict[str, object]:
    pair_counter = Counter()
    curated_overlap_count = 0
    for row in task_rows:
        lb = int(_to_float(row.get('first_gap_lower_band'))) if math.isfinite(_to_float(row.get('first_gap_lower_band'))) else -1
        ub = int(_to_float(row.get('first_gap_upper_band'))) if math.isfinite(_to_float(row.get('first_gap_upper_band'))) else -1
        pair_counter[(lb, ub)] += 1
        curated_overlap_count += int(_to_float(row.get('first_gap_overlaps_any_curated')) > 0.5)
    return {
        'dataset_name': 'pure_prediction_dataset_v6',
        'source_profile': source.PROFILE['name'],
        'feature_definition': 'pure_structural_enriched_v3_features_only',
        'target_fields': PURE_V6_TARGET_FIELDS,
        'design_key': 'shape_id + point_id',
        'target_definition': 'first complete gap above acoustic branches',
        'acoustic_branches': acoustic_branches,
        'gap_epsilon': gap_epsilon,
        'engineering_windows': [
            {'tag': tag, 'low_Hz': low, 'high_Hz': high}
            for tag, low, high in ENGINEERING_WINDOWS
        ],
        'raw_rows': len(raw_rows),
        'master_rows': len(rows),
        'task_rows': len(task_rows),
        'master_csv': str(master_csv),
        'task_csv': str(task_csv),
        'stage_summary_csv': str(stage_summary_csv),
        'dominant_first_gap_pairs': [
            {'lower_band': lb, 'upper_band': ub, 'rows': count}
            for (lb, ub), count in pair_counter.most_common(10)
        ],
        'rows_overlapping_any_curated_window': curated_overlap_count,
        'stage_summary': stage_summary,
        'notes': [
            'This line keeps pure structural features only and defines the target as the first complete gap found above the configured number of acoustic branches.',
            'The parser keeps the real part of complex-valued frequencies and scans band pairs in ascending order until the first complete gap is found.',
            'Auxiliary fields record the discovered band pair, center frequency, and whether the first gap overlaps current engineering windows.',
        ],
    }


def main() -> None:
    args = parse_args()
    out_dir = OUT_ROOT / args.dataset_tag
    master_csv = out_dir / 'master_pure_prediction_dataset_v6.csv'
    task_csv = out_dir / 'pure_firstgap_regression_v6.csv'
    stage_summary_csv = out_dir / 'pure_prediction_stage_summary_v6.csv'
    dataset_info_json = out_dir / 'pure_prediction_dataset_info_v6.json'

    source.base.ensure_dir(out_dir)
    raw_rows = build_raw_rows(args.acoustic_branches, args.gap_epsilon)
    rows = aggregate_rows(raw_rows)
    task_rows = build_task_rows(rows)
    stage_summary = build_stage_summary(rows, task_rows)

    source.base.write_csv(master_csv, rows, MASTER_FIELDS)
    source.base.write_csv(task_csv, task_rows, TASK_FIELDS)
    source.base.write_csv(stage_summary_csv, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
    dataset_info_json.write_text(
        json.dumps(
            build_dataset_info(
                raw_rows,
                rows,
                task_rows,
                stage_summary,
                args.acoustic_branches,
                args.gap_epsilon,
                out_dir,
                master_csv,
                task_csv,
                stage_summary_csv,
            ),
            indent=2,
            ensure_ascii=False,
        ),
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
