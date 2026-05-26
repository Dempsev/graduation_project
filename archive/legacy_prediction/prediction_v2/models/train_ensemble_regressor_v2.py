from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_v2.models.feature_engineering import (
    BASE_FEATURE_SET_NAME,
    ENRICHED_FEATURE_SET_NAME,
    build_enriched_prediction_frame,
)
from shared.features.prediction import ALLOWED_GROUP_KEYS
from shared.objectives.prediction import PURE_REGRESSION_TARGET_CHOICES
from stage3_training.ml_common import regression_metrics, save_csv_rows, save_json, split_frame

DEFAULT_DATASET = ROOT / 'data' / 'pure_prediction_v2' / 'v1' / 'pure_bandgap_regression_v2.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'pure_prediction_v2_runs'
TARGET_CHOICES = PURE_REGRESSION_TARGET_CHOICES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a two-model ensemble pure-prediction regressor on the aggregated v2 dataset.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--target', default='gap34_width_Hz', choices=TARGET_CHOICES)
    parser.add_argument('--eval-mode', default='stratified_group_kfold', choices=['stratified_group_kfold', 'leave_one_stage_out'])
    parser.add_argument('--group-key', default='shape_family', choices=ALLOWED_GROUP_KEYS)
    parser.add_argument('--n-splits', type=int, default=5)
    parser.add_argument('--min-stage-rows', type=int, default=10)
    parser.add_argument('--run-name', default='ensemble_gap34width_v2')
    parser.add_argument('--target-transform', default='log1p', choices=['none', 'log1p'])
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--blend-steps', type=int, default=21)
    return parser.parse_args()


def select_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    work = df.copy()
    work = work[np.isfinite(pd.to_numeric(work[target], errors='coerce'))].copy()
    return work.reset_index(drop=True)


def transform_target(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == 'log1p':
        return np.log1p(np.clip(y, 0.0, None))
    return y


def inverse_target(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == 'log1p':
        return np.expm1(y)
    return y


def fit_feature_matrix(train_df: pd.DataFrame, test_df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    train_x = train_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce')
    test_x = test_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce')
    fill_values = train_x.mean(axis=0, numeric_only=True).fillna(0.0).to_dict()
    train_x = train_x.fillna(fill_values)
    test_x = test_x.fillna(fill_values)
    return train_x.to_numpy(dtype=float), test_x.to_numpy(dtype=float), fill_values


def build_strat_labels(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    open_mask = y > 1e-12
    labels = np.zeros(len(y), dtype=int)
    positive_values = y[open_mask]
    if positive_values.size == 0:
        return labels
    if np.unique(positive_values).size == 1:
        labels[open_mask] = 1
        return labels
    n_bins = int(min(4, np.unique(positive_values).size))
    try:
        bins = pd.qcut(positive_values, q=n_bins, labels=False, duplicates='drop')
        labels[open_mask] = bins.astype(int) + 1
    except Exception:
        labels[open_mask] = 1
    return labels


def iter_stage_loo_splits(df: pd.DataFrame, min_stage_rows: int) -> Iterable[Tuple[str, np.ndarray, np.ndarray]]:
    counts = df['source_stage'].astype(str).value_counts().sort_index()
    for stage_name, rows in counts.items():
        if rows < min_stage_rows:
            continue
        test_mask = df['source_stage'].astype(str) == stage_name
        test_idx = np.flatnonzero(test_mask.to_numpy())
        train_idx = np.flatnonzero((~test_mask).to_numpy())
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue
        yield stage_name, train_idx, test_idx


def fit_histgb(args: argparse.Namespace) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss='absolute_error',
        max_iter=300,
        learning_rate=0.05,
        max_depth=6,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        validation_fraction=0.15,
        early_stopping=True,
        random_state=args.seed,
    )


def fit_rf(args: argparse.Namespace) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=800,
        min_samples_leaf=3,
        max_features=1.0,
        random_state=args.seed,
        n_jobs=1,
    )


def choose_blend_weight(y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray, blend_steps: int) -> float:
    best_alpha = 0.5
    best_rmse = np.inf
    for alpha in np.linspace(0.0, 1.0, blend_steps):
        pred = alpha * pred_a + (1.0 - alpha) * pred_b
        rmse = regression_metrics(y_true, pred)['rmse']
        if rmse < best_rmse:
            best_rmse = float(rmse)
            best_alpha = float(alpha)
    return best_alpha


def run_fold(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    args: argparse.Namespace,
    fold_name: str,
    fold_dir: Path,
) -> Tuple[Dict[str, float], List[Dict[str, object]], float]:
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    inner_train_df, inner_val_df, _ = split_frame(train_df, args.group_key, args.seed, 0.8, 0.1)
    if inner_train_df.empty or inner_val_df.empty:
        inner_train_df = train_df
        inner_val_df = train_df.iloc[: max(1, len(train_df) // 5)].copy()
        if inner_val_df.empty:
            inner_val_df = train_df.iloc[:1].copy()

    work_inner_train, feature_sets = build_enriched_prediction_frame(inner_train_df)
    work_inner_val, _ = build_enriched_prediction_frame(inner_val_df)
    work_outer_train, _ = build_enriched_prediction_frame(train_df)
    work_test, _ = build_enriched_prediction_frame(test_df)

    base_features = [col for col in feature_sets[BASE_FEATURE_SET_NAME] if col in work_outer_train.columns]
    enriched_features = [col for col in feature_sets[ENRICHED_FEATURE_SET_NAME] if col in work_outer_train.columns]

    x_hist_tr, x_hist_val, fill_hist = fit_feature_matrix(work_inner_train, work_inner_val, base_features)
    x_rf_tr, x_rf_val, fill_rf = fit_feature_matrix(work_inner_train, work_inner_val, enriched_features)
    y_inner_train_raw = work_inner_train[args.target].astype(float).to_numpy()
    y_inner_val_raw = work_inner_val[args.target].astype(float).to_numpy()
    y_inner_train = transform_target(y_inner_train_raw, args.target_transform)

    hist = fit_histgb(args)
    rf = fit_rf(args)
    hist.fit(x_hist_tr, y_inner_train)
    rf.fit(x_rf_tr, y_inner_train)
    hist_val_pred = inverse_target(hist.predict(x_hist_val), args.target_transform)
    rf_val_pred = inverse_target(rf.predict(x_rf_val), args.target_transform)
    hist_val_pred = np.clip(hist_val_pred, 0.0, None) if args.target_transform == 'log1p' else hist_val_pred
    rf_val_pred = np.clip(rf_val_pred, 0.0, None) if args.target_transform == 'log1p' else rf_val_pred
    alpha = choose_blend_weight(y_inner_val_raw, hist_val_pred, rf_val_pred, args.blend_steps)

    x_hist_full, x_hist_test, _ = fit_feature_matrix(work_outer_train, work_test, base_features)
    x_rf_full, x_rf_test, _ = fit_feature_matrix(work_outer_train, work_test, enriched_features)
    y_outer_train_raw = work_outer_train[args.target].astype(float).to_numpy()
    y_test_raw = work_test[args.target].astype(float).to_numpy()
    y_outer_train = transform_target(y_outer_train_raw, args.target_transform)

    hist = fit_histgb(args)
    rf = fit_rf(args)
    hist.fit(x_hist_full, y_outer_train)
    rf.fit(x_rf_full, y_outer_train)
    hist_test_pred = inverse_target(hist.predict(x_hist_test), args.target_transform)
    rf_test_pred = inverse_target(rf.predict(x_rf_test), args.target_transform)
    hist_test_pred = np.clip(hist_test_pred, 0.0, None) if args.target_transform == 'log1p' else hist_test_pred
    rf_test_pred = np.clip(rf_test_pred, 0.0, None) if args.target_transform == 'log1p' else rf_test_pred
    blend_pred = alpha * hist_test_pred + (1.0 - alpha) * rf_test_pred
    metrics = regression_metrics(y_test_raw, blend_pred)

    joblib.dump(
        {
            'hist_model': hist,
            'rf_model': rf,
            'hist_feature_cols': base_features,
            'rf_feature_cols': enriched_features,
            'hist_fill_values': fit_feature_matrix(work_outer_train, work_test, base_features)[2],
            'rf_fill_values': fit_feature_matrix(work_outer_train, work_test, enriched_features)[2],
            'target': args.target,
            'target_transform': args.target_transform,
            'blend_alpha_hist': alpha,
            'fold_name': fold_name,
        },
        fold_dir / 'model.joblib',
    )
    save_json(fold_dir / 'metrics.json', {'fold_name': fold_name, 'rows': int(len(test_df)), 'blend_alpha_hist': alpha, **metrics})

    rows: List[Dict[str, object]] = []
    for idx, row in work_test.iterrows():
        rows.append({
            'fold': fold_name,
            'sample_id': row['sample_id'],
            'design_id': row.get('design_id', ''),
            'source_stage': row['source_stage'],
            'shape_id': row['shape_id'],
            'shape_family': row['shape_family'],
            'point_id': row.get('point_id', ''),
            'target_name': args.target,
            'y_true': float(y_test_raw[idx]),
            'y_pred': float(blend_pred[idx]),
            'abs_error': float(abs(y_test_raw[idx] - blend_pred[idx])),
        })
    return metrics, rows, alpha


def summarize_metrics(fold_metrics: List[Dict[str, float]], all_truth: np.ndarray, all_pred: np.ndarray) -> Dict[str, object]:
    summary: Dict[str, object] = {
        'overall': regression_metrics(all_truth, all_pred),
        'fold_count': len(fold_metrics),
    }
    for metric_name in ['mae', 'rmse', 'r2']:
        values = np.array([fold[metric_name] for fold in fold_metrics], dtype=float)
        summary[f'{metric_name}_mean'] = float(np.mean(values))
        summary[f'{metric_name}_std'] = float(np.std(values))
    summary['blend_alpha_hist_mean'] = float(np.mean([fold.get('blend_alpha_hist', 0.5) for fold in fold_metrics]))
    summary['blend_alpha_hist_std'] = float(np.std([fold.get('blend_alpha_hist', 0.5) for fold in fold_metrics]))
    return summary


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.dataset)
    df = select_rows(df, args.target)
    if df.empty:
        raise RuntimeError('No rows remain after target filtering.')

    run_root = DEFAULT_OUT_ROOT / args.run_name / args.eval_mode
    run_root.mkdir(parents=True, exist_ok=True)

    fold_metrics: List[Dict[str, float]] = []
    prediction_rows: List[Dict[str, object]] = []

    if args.eval_mode == 'stratified_group_kfold':
        if args.group_key == 'none':
            raise RuntimeError('stratified_group_kfold requires a non-none group key.')
        groups = df[args.group_key].astype(str).fillna('')
        y_labels = build_strat_labels(df[args.target].astype(float).to_numpy())
        splitter = StratifiedGroupKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
        split_iter = [(f'fold_{fold_idx + 1}', train_idx, test_idx) for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(df, y_labels, groups=groups))]
    else:
        split_iter = list(iter_stage_loo_splits(df, args.min_stage_rows))
        if not split_iter:
            raise RuntimeError('No leave-one-stage-out folds satisfy the min-stage-rows requirement.')

    for fold_name, train_idx, test_idx in split_iter:
        fold_dir = run_root / fold_name
        fold_dir.mkdir(parents=True, exist_ok=True)
        metrics, rows, alpha = run_fold(df, train_idx, test_idx, args, fold_name, fold_dir)
        fold_metrics.append({'fold': fold_name, 'rows': len(test_idx), 'blend_alpha_hist': alpha, **metrics})
        prediction_rows.extend(rows)

    prediction_df = pd.DataFrame(prediction_rows)
    all_truth = prediction_df['y_true'].to_numpy(dtype=float)
    all_pred = prediction_df['y_pred'].to_numpy(dtype=float)
    summary = summarize_metrics(fold_metrics, all_truth, all_pred)

    save_csv_rows(run_root / 'fold_metrics.csv', ['fold', 'rows', 'blend_alpha_hist', 'mae', 'rmse', 'r2'], fold_metrics)
    save_csv_rows(
        run_root / 'predictions.csv',
        ['fold', 'sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'point_id', 'target_name', 'y_true', 'y_pred', 'abs_error'],
        prediction_rows,
    )
    save_json(
        run_root / 'run_config.json',
        {
            'dataset': str(args.dataset),
            'target': args.target,
            'eval_mode': args.eval_mode,
            'group_key': args.group_key,
            'n_splits': args.n_splits,
            'min_stage_rows': args.min_stage_rows,
            'target_transform': args.target_transform,
            'seed': args.seed,
            'blend_steps': args.blend_steps,
            'model_family': 'histgb_plus_random_forest_ensemble',
            'base_model': 'hist_gradient_boosting_regressor',
            'aux_model': 'random_forest_regressor',
        },
    )
    save_json(run_root / 'metrics_summary.json', summary)

    print('[DONE] prediction_v2 ensemble training complete')
    print(f'[RUN] {run_root}')
    print(
        f"[OOF] mae={summary['overall']['mae']:.4f} "
        f"rmse={summary['overall']['rmse']:.4f} "
        f"r2={summary['overall']['r2']:.4f} "
        f"blend_alpha_hist_mean={summary['blend_alpha_hist_mean']:.3f}"
    )


if __name__ == '__main__':
    main()
