from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_targetband_param_v1.models.inference import build_targetband_prediction_frame

DATASET_DIR = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v11_12gen_freeze_v1'
HOLDOUT_CSV = DATASET_DIR / 'active_ga_multiband_12gen_top1_holdout_rows_v1.csv'
OUT_DIR = ROOT / 'data' / 'analysis' / 'targetband_active_learning_v11_12gen_freeze_v1'

RUNS = {
    'v11_12gen_freeze': {
        'classifier': ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cls_hgb_dense_v11_12gen_freeze_v1' / 'stratified_group_kfold',
        'regressor': ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cover_hgb_dense_v11_12gen_freeze_v1' / 'stratified_group_kfold',
    },
}


def predict_for_run(df: pd.DataFrame, run_name: str, paths: Dict[str, Path]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for tag, subset in df.groupby('target_band_tag', sort=True):
        low = float(subset['target_band_low_Hz'].iloc[0])
        high = float(subset['target_band_high_Hz'].iloc[0])
        pred = build_targetband_prediction_frame(
            subset.copy(),
            low,
            high,
            paths['classifier'],
            paths['regressor'],
            band_tag=str(tag),
        )
        out = subset[[
            'sample_id',
            'design_id',
            'shape_id',
            'shape_family',
            'target_band_tag',
            'target_band_low_Hz',
            'target_band_high_Hz',
            'target_gap_overlap_Hz',
            'target_gap_cover_ratio',
            'target_gap_lower_edge_Hz',
            'target_gap_upper_edge_Hz',
            'active_learning_origin_band_tag',
            'active_learning_origin_overlap_Hz',
            'active_learning_holdout_reason',
        ]].copy()
        out['model_run'] = run_name
        out['target_open_prob_pred'] = pred['target_open_prob'].to_numpy(dtype=float)
        out['target_gap_cover_ratio_pred'] = pred['target_gap_cover_ratio_pred'].to_numpy(dtype=float)
        out['target_gap_overlap_pred_Hz'] = pred['target_gap_overlap_pred_Hz'].to_numpy(dtype=float)
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def summarize(pred_df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for (run_name, tag), subset in pred_df.groupby(['model_run', 'target_band_tag']):
        truth = subset['target_gap_overlap_Hz'].to_numpy(dtype=float)
        pred = subset['target_gap_overlap_pred_Hz'].to_numpy(dtype=float)
        rows.append({
            'model_run': str(run_name),
            'target_band_tag': str(tag),
            'rows': int(len(subset)),
            'truth_mean_overlap_Hz': float(np.mean(truth)),
            'truth_max_overlap_Hz': float(np.max(truth)),
            'pred_mean_overlap_Hz': float(np.mean(pred)),
            'pred_max_overlap_Hz': float(np.max(pred)),
            'mean_abs_error_Hz': float(np.mean(np.abs(truth - pred))),
            'truth_mean_cover_ratio': float(subset['target_gap_cover_ratio'].mean()),
            'pred_mean_cover_ratio': float(subset['target_gap_cover_ratio_pred'].mean()),
            'pred_mean_open_prob': float(subset['target_open_prob_pred'].mean()),
        })
    return sorted(rows, key=lambda item: (item['target_band_tag'], item['model_run']))


def summarize_origin_top1(pred_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for origin_tag, subset in pred_df.groupby('active_learning_origin_band_tag', sort=True):
        same_band = subset[subset['target_band_tag'].astype(str) == str(origin_tag)].copy()
        if same_band.empty:
            continue
        row = same_band.iloc[0]
        rows.append({
            'origin_band_tag': str(origin_tag),
            'sample_id': str(row['sample_id']),
            'shape_id': str(row['shape_id']),
            'shape_family': str(row['shape_family']),
            'truth_overlap_Hz': float(row['target_gap_overlap_Hz']),
            'pred_overlap_Hz': float(row['target_gap_overlap_pred_Hz']),
            'abs_error_Hz': float(abs(row['target_gap_overlap_Hz'] - row['target_gap_overlap_pred_Hz'])),
            'open_prob_pred': float(row['target_open_prob_pred']),
            'truth_cover_ratio': float(row['target_gap_cover_ratio']),
            'pred_cover_ratio': float(row['target_gap_cover_ratio_pred']),
        })
    return pd.DataFrame(rows)


def main() -> None:
    holdout = pd.read_csv(HOLDOUT_CSV)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pred_frames = [predict_for_run(holdout, name, paths) for name, paths in RUNS.items()]
    pred_df = pd.concat(pred_frames, ignore_index=True)
    summary = summarize(pred_df)
    origin_top1 = summarize_origin_top1(pred_df)

    pred_csv = OUT_DIR / 'holdout_prediction_v11_12gen_freeze_v1.csv'
    summary_csv = OUT_DIR / 'holdout_prediction_summary_v11_12gen_freeze_v1.csv'
    origin_csv = OUT_DIR / 'holdout_origin_band_top1_prediction_v11_12gen_freeze_v1.csv'
    summary_json = OUT_DIR / 'holdout_prediction_summary_v11_12gen_freeze_v1.json'
    pred_df.to_csv(pred_csv, index=False, encoding='utf-8-sig')
    pd.DataFrame(summary).to_csv(summary_csv, index=False, encoding='utf-8-sig')
    origin_top1.to_csv(origin_csv, index=False, encoding='utf-8-sig')
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[DONE] wrote {pred_csv}')
    print(f'[DONE] wrote {summary_csv}')
    print(f'[DONE] wrote {origin_csv}')
    print(origin_top1.to_string(index=False))


if __name__ == '__main__':
    main()
