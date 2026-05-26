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

HOLDOUT_CSV = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v10_multiband_active_ga_mid_aug_v1' / 'active_ga_multiband_near_best_holdout_rows_v1.csv'
OUT_DIR = ROOT / 'data' / 'analysis' / 'targetband_active_learning_v10'

RUNS = {
    'v9_single_band_active_ga': {
        'classifier': ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cls_hgb_dense_v9_active_mid_aug_v1' / 'stratified_group_kfold',
        'regressor': ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cover_hgb_dense_v9_active_mid_aug_v1' / 'stratified_group_kfold',
    },
    'v10_multiband_active_ga': {
        'classifier': ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cls_hgb_dense_v10_multiband_active_mid_aug_v1' / 'stratified_group_kfold',
        'regressor': ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cover_hgb_dense_v10_multiband_active_mid_aug_v1' / 'stratified_group_kfold',
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


def main() -> None:
    holdout = pd.read_csv(HOLDOUT_CSV)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pred_frames = [predict_for_run(holdout, name, paths) for name, paths in RUNS.items()]
    pred_df = pd.concat(pred_frames, ignore_index=True)
    summary = summarize(pred_df)

    pred_csv = OUT_DIR / 'holdout_prediction_comparison_v1.csv'
    summary_csv = OUT_DIR / 'holdout_prediction_summary_v1.csv'
    summary_json = OUT_DIR / 'holdout_prediction_summary_v1.json'
    pred_df.to_csv(pred_csv, index=False, encoding='utf-8-sig')
    pd.DataFrame(summary).to_csv(summary_csv, index=False, encoding='utf-8-sig')
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[DONE] wrote {pred_csv}')
    print(f'[DONE] wrote {summary_csv}')
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == '__main__':
    main()
