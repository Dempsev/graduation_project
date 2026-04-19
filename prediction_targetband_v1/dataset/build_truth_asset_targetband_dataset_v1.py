from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_DATASET_DIR = ROOT / 'stage3_dataset'
if str(STAGE3_DATASET_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE3_DATASET_DIR))

from stage3_dataset import build_v7_training_dataset as source
from prediction_targetband_v1.dataset.build_targetband_dataset_v1 import (
    MASTER_FIELDS,
    OUT_ROOT,
    TARGET_FIELDS,
    TASK_FIELDS,
    build_stage_summary,
    build_task_rows,
)
from prediction_v3.dataset.build_pure_prediction_dataset_v3 import (
    _canonical_point_id,
    _stage_rank,
    _to_float,
    _to_text,
    compute_shape_features,
)

DEFAULT_CATALOG = ROOT / 'prediction_targetband_param_v1' / 'configs' / 'thesis_band_catalog_v2.json'

SOURCE_SPECS = [
    {
        'source_name': 'true_global_ga',
        'source_stage': 'comsol_in_loop_true_global_ga_v1',
        'csv_path': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_true_global_ga_v1' / 'ga_history_v1.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_true_global_ga_v1' / 'tbl1_exports',
    },
    {
        'source_name': 'band_catalog_ga',
        'source_stage': 'comsol_in_loop_band_catalog_ga_v1',
        'csv_path': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_band_catalog_ga_v1' / 'ga_history_v1.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_band_catalog_ga_v1' / 'tbl1_exports',
    },
    {
        'source_name': 'band_supplement_ga',
        'source_stage': 'comsol_in_loop_band_supplement_ga_v1',
        'csv_path': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_band_supplement_ga_v1' / 'ga_history_v1.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_band_supplement_ga_v1' / 'tbl1_exports',
    },
    {
        'source_name': 'targetband_validation',
        'source_stage': 'stage4_validation_targetband_v1',
        'csv_path': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_targetband_v1' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_targetband_v1' / 'tbl1_exports',
    },
    {
        'source_name': 'targetband_validation_top6',
        'source_stage': 'stage4_validation_targetband_top6_v1',
        'csv_path': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_targetband_top6_v1' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_targetband_top6_v1' / 'tbl1_exports',
    },
]

TARGET_PARAM_FIELDS = ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Harvest previously computed COMSOL truth assets into fixed-window target-band datasets.')
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--dataset-suffix', default='truth_assets_v1')
    return parser.parse_args()


def load_catalog(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    bands = payload.get('bands', [])
    if not bands:
        raise RuntimeError(f'No bands found in catalog: {path}')
    return bands


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


def read_target_gap_metrics(tbl1_path: Path, band_low: float, band_high: float) -> Dict[str, float]:
    metrics = {field: math.nan for field in TARGET_FIELDS}
    metrics['target_band_low_Hz'] = band_low
    metrics['target_band_high_Hz'] = band_high
    metrics['target_gap_is_open'] = 0
    metrics['target_gap_overlap_Hz'] = 0.0
    metrics['target_gap_cover_ratio'] = 0.0

    if not tbl1_path.exists():
        return metrics

    k_vals: List[float] = []
    freq_vals: List[float] = []
    with tbl1_path.open('r', encoding='utf-8-sig') as handle:
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
    return metrics


def iter_source_rows() -> Iterable[Dict[str, object]]:
    for spec in SOURCE_SPECS:
        csv_path = Path(spec['csv_path'])
        tbl1_dir = Path(spec['tbl1_dir'])
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        for _, frame_row in df.iterrows():
            row = frame_row.to_dict()
            row['_harvest_source_name'] = spec['source_name']
            row['_harvest_source_stage'] = spec['source_stage']
            row['_harvest_tbl1_dir'] = str(tbl1_dir)
            yield row


def build_rows_for_band(band_low: float, band_high: float) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    seen_keys = set()
    for raw in iter_source_rows():
        sample_id = _to_text(raw.get('sample_id'))
        source_stage = _to_text(raw.get('_harvest_source_stage'))
        key = (source_stage, sample_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        shape_id = _to_text(raw.get('shape_id'))
        point_id = _canonical_point_id(raw.get('point_id'))
        tbl1_path = Path(_to_text(raw.get('_harvest_tbl1_dir'))) / f'{sample_id}_tbl1.csv'

        projected_row: Dict[str, object] = {
            'sample_id': sample_id,
            'design_id': f'{shape_id}::{point_id}',
            'observation_count': 1,
            'source_stage_count': 1,
            'source_stage': source_stage,
            'source_stage_list': source_stage,
            'source_role': _to_text(raw.get('selection_source')) or _to_text(raw.get('shape_role')) or _to_text(raw.get('_harvest_source_name')),
            'candidate_id': _to_text(raw.get('candidate_id')) or _to_text(raw.get('validation_id')),
            'main_id': _to_text(raw.get('main_id')),
            'point_id': point_id,
            'shape_id': shape_id,
            'shape_family': _to_text(raw.get('shape_family')),
            'shape_role': _to_text(raw.get('shape_role')),
            'geometry_valid': int(_to_float(raw.get('geometry_valid')) == 1.0),
            'contact_valid': int(_to_float(raw.get('contact_valid')) == 1.0),
            'solve_success': int(_to_float(raw.get('solve_success')) == 1.0),
            'label_definition': f'target_band_{int(round(band_low))}_{int(round(band_high))}_harvested_truth_asset_overlap',
            'error_message': _to_text(raw.get('error_message')),
        }
        for field in TARGET_PARAM_FIELDS:
            projected_row[field] = _to_float(raw.get(field))
        projected_row.update(compute_shape_features(shape_id))
        projected_row.update(read_target_gap_metrics(tbl1_path, band_low, band_high))
        projected_row['is_training_ready'] = int(
            projected_row['geometry_valid'] == 1
            and projected_row['contact_valid'] == 1
            and projected_row['solve_success'] == 1
        )
        rows.append(projected_row)

    rows.sort(key=lambda item: (_stage_rank(_to_text(item.get('source_stage'))), _to_text(item.get('sample_id'))))
    return rows


def build_dataset_info(rows: List[Dict[str, object]], task_rows: List[Dict[str, object]], stage_summary: List[Dict[str, object]], band_low: float, band_high: float, out_dir: Path, master_csv: Path, task_csv: Path, stage_summary_csv: Path, source_names: List[str]) -> Dict[str, object]:
    positive_rows = sum(int(row.get('target_gap_is_open', 0)) for row in rows)
    solve_success_rows = sum(int(row.get('solve_success', 0)) for row in rows)
    return {
        'dataset_name': 'prediction_targetband_v1_truth_assets',
        'source_names': source_names,
        'feature_definition': 'pure_structural_enriched_v3_features_only',
        'design_key': 'shape_id + point_id',
        'target_band_low_Hz': band_low,
        'target_band_high_Hz': band_high,
        'task_definition': 'best complete-gap overlap inside the fixed target frequency window using harvested historical truth assets',
        'master_rows': len(rows),
        'task_rows': len(task_rows),
        'solve_success_rows': solve_success_rows,
        'positive_rows': positive_rows,
        'positive_rate_all_rows': positive_rows / max(1, len(rows)),
        'positive_rate_solve_success_rows': positive_rows / max(1, solve_success_rows),
        'out_dir': str(out_dir),
        'master_csv': str(master_csv),
        'task_csv': str(task_csv),
        'stage_summary_csv': str(stage_summary_csv),
        'stage_summary': stage_summary,
        'notes': [
            'This dataset harvests previously computed COMSOL truth assets instead of requesting new simulations.',
            'Labels are rebuilt from archived tbl1 exports so one historical run can serve multiple target bands.',
        ],
    }


def main() -> None:
    args = parse_args()
    catalog = load_catalog(args.catalog)
    source_names = [str(spec['source_name']) for spec in SOURCE_SPECS if Path(spec['csv_path']).exists()]

    for band in catalog:
        band_tag = _to_text(band.get('target_band_tag'))
        band_low = float(band['band_low_Hz'])
        band_high = float(band['band_high_Hz'])
        dataset_tag = f'{band_tag}_{args.dataset_suffix}'
        out_dir = OUT_ROOT / dataset_tag
        master_csv = out_dir / 'master_targetband_dataset_v1.csv'
        task_csv = out_dir / 'targetband_prediction_v1.csv'
        stage_summary_csv = out_dir / 'targetband_stage_summary_v1.csv'
        dataset_info_json = out_dir / 'targetband_dataset_info_v1.json'

        source.base.ensure_dir(out_dir)
        rows = build_rows_for_band(band_low, band_high)
        task_rows = build_task_rows(rows)
        stage_summary = build_stage_summary(rows, task_rows)

        source.base.write_csv(master_csv, rows, MASTER_FIELDS)
        source.base.write_csv(task_csv, task_rows, TASK_FIELDS)
        source.base.write_csv(stage_summary_csv, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
        dataset_info_json.write_text(
            json.dumps(
                build_dataset_info(rows, task_rows, stage_summary, band_low, band_high, out_dir, master_csv, task_csv, stage_summary_csv, source_names),
                indent=2,
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        print(f'[DONE] {dataset_tag}: rows={len(rows)}, task_rows={len(task_rows)}')


if __name__ == '__main__':
    main()
