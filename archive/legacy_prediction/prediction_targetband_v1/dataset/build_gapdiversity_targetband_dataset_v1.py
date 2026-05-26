from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_DATASET_DIR = ROOT / 'stage3_dataset'
if str(STAGE3_DATASET_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE3_DATASET_DIR))

from stage3_dataset import build_v7_training_dataset as source
from prediction_targetband_v1.dataset.build_targetband_dataset_v1 import (
    AGG_METADATA_FIELDS,
    MASTER_FIELDS,
    OUT_ROOT,
    TARGET_FIELDS,
    TASK_FIELDS,
    build_stage_summary,
    build_task_rows,
)
from prediction_v3.dataset.build_pure_prediction_dataset_v3 import (
    PURE_V3_FEATURE_FIELDS,
    _canonical_point_id,
    _stage_rank,
    _to_float,
    _to_text,
    compute_shape_features,
)

SOURCE_RESULTS_CSV = ROOT / 'data' / 'comsol_batch' / 'stage2_gapdiversity_exploration_v1' / 'stage2_gapdiversity_results.csv'
SOURCE_STAGE_NAME = 'stage2_gapdiversity'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a fixed-window target-band dataset from stage2 gap-diversity exploration results.')
    parser.add_argument('--band-low', type=float, required=True)
    parser.add_argument('--band-high', type=float, required=True)
    parser.add_argument('--dataset-tag', default='')
    parser.add_argument('--source-csv', default=str(SOURCE_RESULTS_CSV))
    return parser.parse_args()


def _default_dataset_tag(band_low: float, band_high: float) -> str:
    return f'band{int(round(band_low))}_{int(round(band_high))}_gapdiversity_v1'


def _compute_target_metrics(row: pd.Series, band_low: float, band_high: float) -> Dict[str, float]:
    metrics = {field: math.nan for field in TARGET_FIELDS}
    metrics['target_band_low_Hz'] = float(band_low)
    metrics['target_band_high_Hz'] = float(band_high)
    metrics['target_gap_is_open'] = 0
    metrics['target_gap_overlap_Hz'] = 0.0
    metrics['target_gap_cover_ratio'] = 0.0

    lower = _to_float(row.get('gap_lower_edge_Hz'))
    upper = _to_float(row.get('gap_upper_edge_Hz'))
    gap_width = _to_float(row.get('gap_target_Hz'))
    if not math.isfinite(gap_width) and math.isfinite(lower) and math.isfinite(upper):
        gap_width = upper - lower

    if not (math.isfinite(lower) and math.isfinite(upper) and math.isfinite(gap_width) and gap_width > 0):
        return metrics

    overlap = max(0.0, min(upper, band_high) - max(lower, band_low))
    if overlap <= 0:
        return metrics

    metrics['target_gap_is_open'] = 1
    metrics['target_gap_overlap_Hz'] = overlap
    metrics['target_gap_cover_ratio'] = overlap / max(1e-12, band_high - band_low)
    metrics['target_gap_best_width_Hz'] = gap_width
    metrics['target_gap_lower_edge_Hz'] = lower
    metrics['target_gap_upper_edge_Hz'] = upper
    metrics['target_gap_center_freq'] = _to_float(row.get('gap_center_freq'))
    metrics['target_gap_lower_band'] = _to_float(row.get('gap_lower_band'))
    metrics['target_gap_upper_band'] = _to_float(row.get('gap_upper_band'))
    return metrics


def build_rows(source_csv: Path, band_low: float, band_high: float) -> List[Dict[str, object]]:
    df = pd.read_csv(source_csv)
    rows: List[Dict[str, object]] = []
    for _, frame_row in df.iterrows():
        shape_id = _to_text(frame_row.get('shape_id'))
        point_id = _canonical_point_id(frame_row.get('point_id'))
        candidate_role = _to_text(frame_row.get('candidate_role'))
        sample_id = _to_text(frame_row.get('sample_id'))
        projected_row: Dict[str, object] = {
            'sample_id': sample_id,
            'design_id': f'{shape_id}::{point_id}',
            'observation_count': 1,
            'source_stage_count': 1,
            'source_stage': SOURCE_STAGE_NAME,
            'source_stage_list': SOURCE_STAGE_NAME,
            'source_role': candidate_role or 'gapdiversity_exploration',
            'candidate_id': _to_text(frame_row.get('candidate_id')),
            'main_id': _to_text(frame_row.get('candidate_id')),
            'point_id': point_id,
            'shape_id': shape_id,
            'shape_family': _to_text(frame_row.get('shape_family')),
            'shape_role': candidate_role,
            'geometry_valid': int(_to_float(frame_row.get('geometry_valid')) == 1.0),
            'contact_valid': int(_to_float(frame_row.get('contact_valid')) == 1.0),
            'solve_success': int(_to_float(frame_row.get('solve_success')) == 1.0),
            'label_definition': f'target_band_{int(round(band_low))}_{int(round(band_high))}_gapdiversity_recorded_gap_overlap',
            'error_message': _to_text(frame_row.get('error_message')),
        }
        for field in ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']:
            projected_row[field] = _to_float(frame_row.get(field))
        projected_row.update(compute_shape_features(shape_id))
        projected_row.update(_compute_target_metrics(frame_row, band_low, band_high))
        projected_row['is_training_ready'] = int(
            projected_row['geometry_valid'] == 1
            and projected_row['contact_valid'] == 1
            and projected_row['solve_success'] == 1
        )
        rows.append(projected_row)

    rows.sort(key=lambda item: (_stage_rank(_to_text(item.get('source_stage'))), _to_text(item.get('design_id'))))
    return rows


def build_dataset_info(rows: List[Dict[str, object]], task_rows: List[Dict[str, object]], stage_summary: List[Dict[str, object]], band_low: float, band_high: float, out_dir: Path, master_csv: Path, task_csv: Path, stage_summary_csv: Path, source_csv: Path) -> Dict[str, object]:
    solve_success_rows = sum(int(row.get('solve_success', 0)) for row in rows)
    positive_rows = sum(int(row.get('target_gap_is_open', 0)) for row in rows)
    return {
        'dataset_name': 'prediction_targetband_v1_gapdiversity',
        'source_profile': 'stage2_gapdiversity_exploration_v1',
        'source_csv': str(source_csv),
        'feature_definition': 'pure_structural_enriched_v3_features_only',
        'feature_fields': PURE_V3_FEATURE_FIELDS,
        'target_fields': TARGET_FIELDS,
        'design_key': 'shape_id + point_id',
        'target_band_low_Hz': band_low,
        'target_band_high_Hz': band_high,
        'task_definition': 'recorded dominant-gap overlap inside the fixed target frequency window',
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
            'This augmentation is built from the stage2 gap-diversity exploration line rather than the legacy 3-4-gap-focused truth pool.',
            'Labels are computed from the recorded dominant gap edges in stage2_gapdiversity_results.csv rather than a full tbl1 re-scan.',
            'Use this dataset to augment target-band and band-catalog prediction, especially for windows underrepresented in the legacy truth pool.',
        ],
    }


def main() -> None:
    args = parse_args()
    source_csv = Path(args.source_csv)
    if not source_csv.exists():
        raise FileNotFoundError(f'missing gap-diversity source csv: {source_csv}')
    if not math.isfinite(args.band_low) or not math.isfinite(args.band_high) or args.band_high <= args.band_low:
        raise ValueError('band_high must be greater than band_low')

    dataset_tag = args.dataset_tag.strip() or _default_dataset_tag(args.band_low, args.band_high)
    out_dir = OUT_ROOT / dataset_tag
    master_csv = out_dir / 'master_targetband_dataset_v1.csv'
    task_csv = out_dir / 'targetband_prediction_v1.csv'
    stage_summary_csv = out_dir / 'targetband_stage_summary_v1.csv'
    dataset_info_json = out_dir / 'targetband_dataset_info_v1.json'

    source.base.ensure_dir(out_dir)
    rows = build_rows(source_csv, args.band_low, args.band_high)
    task_rows = build_task_rows(rows)
    stage_summary = build_stage_summary(rows, task_rows)

    source.base.write_csv(master_csv, rows, MASTER_FIELDS)
    source.base.write_csv(task_csv, task_rows, TASK_FIELDS)
    source.base.write_csv(stage_summary_csv, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
    dataset_info_json.write_text(
        json.dumps(
            build_dataset_info(
                rows=rows,
                task_rows=task_rows,
                stage_summary=stage_summary,
                band_low=args.band_low,
                band_high=args.band_high,
                out_dir=out_dir,
                master_csv=master_csv,
                task_csv=task_csv,
                stage_summary_csv=stage_summary_csv,
                source_csv=source_csv,
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding='utf-8',
    )

    print(f'[DONE] rows: {len(rows)}')
    print(f'[DONE] training task rows: {len(task_rows)}')
    print(f'[OUT] {master_csv}')
    print(f'[OUT] {task_csv}')
    print(f'[OUT] {stage_summary_csv}')
    print(f'[OUT] {dataset_info_json}')


if __name__ == '__main__':
    main()
