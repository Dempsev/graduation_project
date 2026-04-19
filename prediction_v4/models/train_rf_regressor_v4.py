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
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_v4.dataset.build_pure_prediction_dataset_v4 import PURE_V4_FEATURE_FIELDS
from shared.features.prediction import ALLOWED_GROUP_KEYS
from shared.objectives.prediction import PURE_REGRESSION_TARGET_CHOICES
from stage3_training.ml_common import regression_metrics, save_csv_rows, save_json

DEFAULT_DATASET = ROOT / 'data' / 'pure_prediction_v4' / 'v1' / 'pure_bandgap_regression_v4.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'pure_prediction_v4_runs'
TARGET_CHOICES = PURE_REGRESSION_TARGET_CHOICES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a RandomForest regressor on the enriched v4 pure-prediction dataset.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--target', default='gap34_width_Hz', choices=TARGET_CHOICES)
    parser.add_argument('--eval-mode', default='stratified_group_kfold', choices=['stratified_group_kfold', 'leave_one_stage_out'])
    parser.add_argument('--group-key', default='shape_family', choices=ALLOWED_GROUP_KEYS)
    parser.add_argument('--n-splits', type=int, default=5)
    parser.add_argument('--min-stage-rows', type=int, default=10)
    parser.add_argument('--run-name', default='rf_gap34width_v4')
    parser.add_argument('--target-transform', default='log1p', choices=['none', 'log1p'])
    parser.add_argument('--n-estimators', type=int, default=700)
    parser.add_argument('--min-samples-leaf', type=int, default=2)
    parser.add_argument('--max-features', default='sqrt')
    parser.add_argument('--seed', type=int, default=42)
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


def parse_max_features(text: str) -> float | str | None:
    value = text.strip().lower()
    if value in {'auto', 'sqrt', 'log2'}:
        return value
    if value in {'none', 'all'}:
        return 1.0
    return float(value)


def fit_feature_matrix(train_df: pd.DataFrame, test_df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    train_x = train_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce')
    test_x = test_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce')
    fill_values = train_x.mean(axis=0, numeric_only=True).fillna(0.0).to_dict()
    train_x = train_x.fillna(fill_values)
    test_x = test_x.fillna(fill_values)
    return train_x.to_numpy(dtype=float), test_x.to_numpy(dtype=float), fill_values


def build_strat_labels(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    labels = np.zeros(len(y), dtype=int)
    labels[y > 0.0] = 1
    labels[y > 5.0] = 2
    labels[y > 20.0] = 3
    labels[y > 50.0] = 4
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


def compute_regression_weights(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    weights = np.ones(len(y), dtype=float)
    weights += 0.5 * (y > 0.0)
    weights += 0.5 * (y > 5.0)
    weights += 1.0 * (y > 20.0)
    weights += 1.0 * (y > 50.0)
    return weights


def build_bucket_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> List[Dict[str, object]]:
    bins = [-1e-9, 1e-12, 5.0, 20.0, 50.0, 100.0, 1e9]
    labels = ['closed', '(0,5]', '(5,20]', '(20,50]', '(50,100]', '>100']
    frame = pd.DataFrame({'y_true': y_true, 'y_pred': y_pred})
    frame['sqerr'] = (frame['y_true'] - frame['y_pred']) ** 2
    frame['abserr'] = (frame['y_true'] - frame['y_pred']).abs()
    frame['bucket'] = pd.cut(frame['y_true'], bins=bins, labels=labels)
    rows: List[Dict[str, object]] = []
    for bucket, subset in frame.groupby('bucket', observed=False):
        if subset.empty:
            continue
        rows.append({
            'bucket': str(bucket),
            'rows': int(len(subset)),
            'mean_true': float(subset['y_true'].mean()),
            'mean_pred': float(subset['y_pred'].mean()),
            'mae': float(subset['abserr'].mean()),
            'rmse': float(np.sqrt(subset['sqerr'].mean())),
        })
    return rows


def make_model(args: argparse.Namespace) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=args.n_estimators,
        min_samples_leaf=args.min_samples_leaf,
        max_features=parse_max_features(args.max_features),
        random_state=args.seed,
        n_jobs=1,
    )


def run_fold(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    feature_cols: List[str],
    args: argparse.Namespace,
    fold_name: str,
    fold_dir: Path,
) -> Tuple[Dict[str, float], List[Dict[str, object]], List[Dict[str, object]]]:
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    x_train, x_test, fill_values = fit_feature_matrix(train_df, test_df, feature_cols)
    y_train_raw = train_df[args.target].astype(float).to_numpy()
    y_test_raw = test_df[args.target].astype(float).to_numpy()
    y_train = transform_target(y_train_raw, args.target_transform)

    model = make_model(args)
    model.fit(x_train, y_train, sample_weight=compute_regression_weights(y_train_raw))
    pred_test = inverse_target(model.predict(x_test), args.target_transform)
    pred_test = np.clip(pred_test, 0.0, None) if args.target_transform == 'log1p' else pred_test
    metrics = regression_metrics(y_test_raw, pred_test)

    joblib.dump(
        {
            'model': model,
            'feature_cols': feature_cols,
            'fill_values': fill_values,
            'target': args.target,
            'target_transform': args.target_transform,
            'eval_mode': args.eval_mode,
            'fold_name': fold_name,
        },
        fold_dir / 'model.joblib',
    )
    save_json(fold_dir / 'metrics.json', {'fold_name': fold_name, 'rows': int(len(test_df)), **metrics})
    bucket_rows = build_bucket_metrics(y_test_raw, pred_test)
    for item in bucket_rows:
        item['fold'] = fold_name
    save_csv_rows(fold_dir / 'bucket_metrics.csv', ['fold', 'bucket', 'rows', 'mean_true', 'mean_pred', 'mae', 'rmse'], bucket_rows)

    rows: List[Dict[str, object]] = []
    for idx, row in test_df.iterrows():
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
            'y_pred': float(pred_test[idx]),
            'abs_error': float(abs(y_test_raw[idx] - pred_test[idx])),
        })
    return metrics, rows, bucket_rows


def summarize_metrics(fold_metrics: List[Dict[str, float]], all_truth: np.ndarray, all_pred: np.ndarray) -> Dict[str, object]:
    summary: Dict[str, object] = {
        'overall': regression_metrics(all_truth, all_pred),
        'fold_count': len(fold_metrics),
        'bucket_metrics': build_bucket_metrics(all_truth, all_pred),
    }
    for metric_name in ['mae', 'rmse', 'r2']:
        values = np.array([fold[metric_name] for fold in fold_metrics], dtype=float)
        summary[f'{metric_name}_mean'] = float(np.mean(values))
        summary[f'{metric_name}_std'] = float(np.std(values))
    return summary


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.dataset)
    df = select_rows(df, args.target)
    feature_cols = [col for col in PURE_V4_FEATURE_FIELDS if col in df.columns]
    if not feature_cols:
        raise RuntimeError('No usable feature columns found for v4 RandomForest regressor.')

    run_root = DEFAULT_OUT_ROOT / args.run_name / args.eval_mode
    run_root.mkdir(parents=True, exist_ok=True)

    fold_metrics: List[Dict[str, float]] = []
    prediction_rows: List[Dict[str, object]] = []
    bucket_rows: List[Dict[str, object]] = []

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
        metrics, rows, fold_bucket_rows = run_fold(df, train_idx, test_idx, feature_cols, args, fold_name, fold_dir)
        fold_metrics.append({'fold': fold_name, 'rows': len(test_idx), **metrics})
        prediction_rows.extend(rows)
        bucket_rows.extend(fold_bucket_rows)

    prediction_df = pd.DataFrame(prediction_rows)
    all_truth = prediction_df['y_true'].to_numpy(dtype=float)
    all_pred = prediction_df['y_pred'].to_numpy(dtype=float)
    summary = summarize_metrics(fold_metrics, all_truth, all_pred)

    save_csv_rows(run_root / 'fold_metrics.csv', ['fold', 'rows', 'mae', 'rmse', 'r2'], fold_metrics)
    save_csv_rows(
        run_root / 'predictions.csv',
        ['fold', 'sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'point_id', 'target_name', 'y_true', 'y_pred', 'abs_error'],
        prediction_rows,
    )
    save_csv_rows(
        run_root / 'bucket_metrics.csv',
        ['fold', 'bucket', 'rows', 'mean_true', 'mean_pred', 'mae', 'rmse'],
        bucket_rows,
    )
    save_json(
        run_root / 'run_config.json',
        {
            'dataset': str(args.dataset),
            'feature_cols': feature_cols,
            'target': args.target,
            'eval_mode': args.eval_mode,
            'group_key': args.group_key,
            'n_splits': args.n_splits,
            'min_stage_rows': args.min_stage_rows,
            'target_transform': args.target_transform,
            'n_estimators': args.n_estimators,
            'min_samples_leaf': args.min_samples_leaf,
            'max_features': args.max_features,
            'seed': args.seed,
            'model_family': 'random_forest_regressor',
        },
    )
    save_json(run_root / 'metrics_summary.json', summary)

    print('[DONE] prediction_v4 RandomForest training complete')
    print(f'[RUN] {run_root}')
    print(
        f"[OOF] mae={summary['overall']['mae']:.4f} "
        f"rmse={summary['overall']['rmse']:.4f} "
        f"r2={summary['overall']['r2']:.4f}"
    )


if __name__ == '__main__':
    main()
