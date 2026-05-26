from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_v3.models.feature_engineering import ENRICHED_FEATURE_SET_NAME, build_tail_prediction_frame
from stage3_training.ml_common import classification_metrics, regression_metrics, save_json


DEFAULT_DATASET = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v12_all_history_ga20_clean_v1' / 'targetband_parametric_v1.csv'
DEFAULT_OUT_DIR = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_final_hgb_dense_v12_all_history_ga20_clean_v1'
BAND_FEATURES = ['target_band_low_Hz', 'target_band_high_Hz', 'target_band_center_Hz', 'target_band_width_Hz']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a final full-data parametric target-band predictor bundle.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--learning-rate', type=float, default=0.04)
    parser.add_argument('--max-iter', type=int, default=500)
    parser.add_argument('--max-leaf-nodes', type=int, default=31)
    parser.add_argument('--max-depth', type=int, default=8)
    parser.add_argument('--min-samples-leaf', type=int, default=5)
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def fit_matrix(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, Dict[str, float]]:
    x = df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce')
    fill_values = x.mean(axis=0, numeric_only=True).fillna(0.0).to_dict()
    return x.fillna(fill_values).to_numpy(dtype=float), fill_values


def make_classifier(args: argparse.Namespace) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=args.learning_rate,
        max_iter=args.max_iter,
        max_leaf_nodes=args.max_leaf_nodes,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.seed,
    )


def make_regressor(args: argparse.Namespace) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=args.learning_rate,
        max_iter=args.max_iter,
        max_leaf_nodes=args.max_leaf_nodes,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.seed,
    )


def summarize_by_band(df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for tag, subset in df.groupby('target_band_tag', sort=True):
        is_open = pd.to_numeric(subset['target_gap_is_open'], errors='coerce').fillna(0)
        cover = pd.to_numeric(subset['target_gap_cover_ratio'], errors='coerce').fillna(0.0)
        rows.append({
            'target_band_tag': str(tag),
            'rows': int(len(subset)),
            'positive_rows': int(is_open.sum()),
            'positive_rate': float(is_open.mean()),
            'max_cover_ratio': float(cover.max()),
            'mean_cover_ratio': float(cover.mean()),
        })
    return rows


def main() -> None:
    args = parse_args()
    df_raw = pd.read_csv(args.dataset, low_memory=False)
    df, feature_sets = build_tail_prediction_frame(df_raw)
    feature_cols = [col for col in feature_sets[ENRICHED_FEATURE_SET_NAME] if col in df.columns]
    feature_cols = [*feature_cols, *[col for col in BAND_FEATURES if col in df.columns]]
    if not feature_cols:
        raise RuntimeError('No usable feature columns found.')

    x_all, fill_values = fit_matrix(df, feature_cols)
    y_cls = pd.to_numeric(df['target_gap_is_open'], errors='coerce').fillna(0).astype(int).to_numpy()
    classifier = make_classifier(args)
    classifier.fit(x_all, y_cls)
    train_prob = classifier.predict_proba(x_all)[:, 1]
    train_cls_metrics = classification_metrics(y_cls, train_prob, threshold=args.threshold)

    pos_df = df[pd.to_numeric(df['target_gap_is_open'], errors='coerce').fillna(0) > 0.5].copy()
    x_pos = pos_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce').fillna(fill_values).to_numpy(dtype=float)
    y_reg = pd.to_numeric(pos_df['target_gap_cover_ratio'], errors='coerce').fillna(0.0).to_numpy(dtype=float)
    regressor = make_regressor(args)
    regressor.fit(x_pos, y_reg)
    train_cover = np.clip(regressor.predict(x_pos), 0.0, 1.0)
    train_reg_metrics = regression_metrics(y_reg, train_cover)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = args.out_dir / 'final_predictor_bundle.joblib'
    config_path = args.out_dir / 'final_predictor_config.json'
    summary_path = args.out_dir / 'final_predictor_summary.json'

    bundle = {
        'classifier': classifier,
        'regressor': regressor,
        'feature_cols': feature_cols,
        'fill_values': fill_values,
        'threshold': args.threshold,
        'feature_set': ENRICHED_FEATURE_SET_NAME,
        'band_features': BAND_FEATURES,
        'dataset': str(args.dataset),
        'classifier_target': 'target_gap_is_open',
        'regressor_target': 'target_gap_cover_ratio',
        'regressor_positive_only': True,
    }
    joblib.dump(bundle, bundle_path)

    config = {
        'dataset': str(args.dataset),
        'out_dir': str(args.out_dir),
        'bundle_path': str(bundle_path),
        'feature_set': ENRICHED_FEATURE_SET_NAME,
        'feature_cols': feature_cols,
        'model_family': 'hist_gradient_boosting',
        'learning_rate': args.learning_rate,
        'max_iter': args.max_iter,
        'max_leaf_nodes': args.max_leaf_nodes,
        'max_depth': args.max_depth,
        'min_samples_leaf': args.min_samples_leaf,
        'threshold': args.threshold,
        'seed': args.seed,
    }
    summary = {
        'rows_total': int(len(df)),
        'rows_positive_for_regression': int(len(pos_df)),
        'positive_rate': float(y_cls.mean()),
        'train_resubstitution_classifier_metrics': train_cls_metrics,
        'train_resubstitution_regressor_metrics': train_reg_metrics,
        'band_summary': summarize_by_band(df),
        'warning': 'Training metrics in this file are resubstitution diagnostics only; report cross-validation metrics for thesis validation.',
    }
    save_json(config_path, config)
    save_json(summary_path, summary)

    print(f'[DONE] final predictor bundle: {bundle_path}')
    print(f'[DONE] rows={len(df)} positive_rows={len(pos_df)}')
    print(f"[TRAIN] classifier_f1={train_cls_metrics['f1']:.4f} balanced_accuracy={train_cls_metrics['balanced_accuracy']:.4f}")
    print(f"[TRAIN] regressor_mae={train_reg_metrics['mae']:.4f} r2={train_reg_metrics['r2']:.4f}")


if __name__ == '__main__':
    main()
