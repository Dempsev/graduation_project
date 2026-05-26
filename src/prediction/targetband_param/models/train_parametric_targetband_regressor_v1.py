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

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_v3.models.feature_engineering import ENRICHED_FEATURE_SET_NAME, build_tail_prediction_frame
from shared.features.prediction import ALLOWED_GROUP_KEYS
from stage3_training.ml_common import regression_metrics, save_csv_rows, save_json

DEFAULT_DATASET = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_120_160__180_220__220_260' / 'targetband_parametric_v1.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1_runs'
BAND_FEATURES = ['target_band_low_Hz', 'target_band_high_Hz', 'target_band_center_Hz', 'target_band_width_Hz']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a positive-only parametric regressor for target-band cover ratio.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--target', default='target_gap_cover_ratio', choices=['target_gap_cover_ratio', 'target_gap_overlap_Hz'])
    parser.add_argument('--eval-mode', default='stratified_group_kfold', choices=['stratified_group_kfold', 'leave_one_stage_out', 'leave_one_band_tag_out'])
    parser.add_argument('--group-key', default='shape_family', choices=ALLOWED_GROUP_KEYS)
    parser.add_argument('--n-splits', type=int, default=5)
    parser.add_argument('--min-stage-rows', type=int, default=10)
    parser.add_argument('--min-positive-stage-rows', type=int, default=10)
    parser.add_argument('--run-name', default='param_targetband_cover_v1')
    parser.add_argument('--model-family', default='random_forest', choices=['random_forest', 'hist_gradient_boosting'])
    parser.add_argument('--target-transform', default='none', choices=['none', 'log1p'])
    parser.add_argument('--n-estimators', type=int, default=900)
    parser.add_argument('--min-samples-leaf', type=int, default=2)
    parser.add_argument('--max-features', default='1.0')
    parser.add_argument('--hgb-learning-rate', type=float, default=0.05)
    parser.add_argument('--hgb-max-iter', type=int, default=400)
    parser.add_argument('--hgb-max-leaf-nodes', type=int, default=31)
    parser.add_argument('--hgb-max-depth', type=int, default=8)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def select_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    work = df.copy()
    work = work[pd.to_numeric(work['target_gap_is_open'], errors='coerce').fillna(0.0) > 0.5].copy()
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


def build_strat_labels(df: pd.DataFrame, target: str) -> np.ndarray:
    tag_codes = df['target_band_tag'].astype('category').cat.codes.to_numpy()
    y = pd.to_numeric(df[target], errors='coerce').fillna(0.0).to_numpy(dtype=float)
    if np.unique(y).size == 1:
        return tag_codes
    try:
        bins = pd.qcut(y, q=min(4, np.unique(y).size), labels=False, duplicates='drop')
        return tag_codes * 10 + bins.astype(int)
    except Exception:
        return tag_codes


def iter_stage_loo_splits(df: pd.DataFrame, min_stage_rows: int, min_positive_stage_rows: int) -> Iterable[Tuple[str, np.ndarray, np.ndarray]]:
    counts = df['source_stage'].astype(str).value_counts().sort_index()
    for stage_name, rows in counts.items():
        if rows < min_stage_rows:
            continue
        test_mask = df['source_stage'].astype(str) == stage_name
        test_idx = np.flatnonzero(test_mask.to_numpy())
        train_idx = np.flatnonzero((~test_mask).to_numpy())
        if len(train_idx) == 0 or len(test_idx) < min_positive_stage_rows:
            continue
        yield stage_name, train_idx, test_idx


def iter_band_tag_loo_splits(df: pd.DataFrame, min_positive_band_rows: int) -> Iterable[Tuple[str, np.ndarray, np.ndarray]]:
    for band_tag in sorted(df['target_band_tag'].astype(str).unique().tolist()):
        test_mask = df['target_band_tag'].astype(str) == band_tag
        test_idx = np.flatnonzero(test_mask.to_numpy())
        train_idx = np.flatnonzero((~test_mask).to_numpy())
        if len(train_idx) == 0 or len(test_idx) < min_positive_band_rows:
            continue
        yield band_tag, train_idx, test_idx


def make_model(args: argparse.Namespace):
    if args.model_family == 'hist_gradient_boosting':
        return HistGradientBoostingRegressor(
            learning_rate=args.hgb_learning_rate,
            max_iter=args.hgb_max_iter,
            max_leaf_nodes=args.hgb_max_leaf_nodes,
            max_depth=args.hgb_max_depth,
            min_samples_leaf=args.min_samples_leaf,
            random_state=args.seed,
        )
    return RandomForestRegressor(
        n_estimators=args.n_estimators,
        min_samples_leaf=args.min_samples_leaf,
        max_features=parse_max_features(args.max_features),
        random_state=args.seed,
        n_jobs=1,
    )


def summarize_per_band(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    df = pd.DataFrame(rows)
    summary_rows: List[Dict[str, object]] = []
    for band_tag, subset in df.groupby('target_band_tag'):
        metrics = regression_metrics(subset['y_true'].to_numpy(dtype=float), subset['y_pred'].to_numpy(dtype=float))
        summary_rows.append({
            'target_band_tag': str(band_tag),
            'rows': int(len(subset)),
            'target_mean': float(subset['y_true'].mean()),
            **metrics,
        })
    return summary_rows


def run_fold(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    feature_cols: List[str],
    args: argparse.Namespace,
    fold_name: str,
    fold_dir: Path,
) -> Tuple[Dict[str, float], List[Dict[str, object]]]:
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    x_train, x_test, fill_values = fit_feature_matrix(train_df, test_df, feature_cols)
    y_train_raw = train_df[args.target].astype(float).to_numpy()
    y_test_raw = test_df[args.target].astype(float).to_numpy()
    y_train = transform_target(y_train_raw, args.target_transform)

    model = make_model(args)
    model.fit(x_train, y_train)
    pred_test = inverse_target(model.predict(x_test), args.target_transform)
    pred_test = np.clip(pred_test, 0.0, None)
    if args.target == 'target_gap_cover_ratio':
        pred_test = np.clip(pred_test, 0.0, 1.0)
    metrics = regression_metrics(y_test_raw, pred_test)

    joblib.dump(
        {
            'model': model,
            'feature_cols': feature_cols,
            'fill_values': fill_values,
            'target': args.target,
            'target_transform': args.target_transform,
            'feature_set': ENRICHED_FEATURE_SET_NAME,
            'eval_mode': args.eval_mode,
            'fold_name': fold_name,
        },
        fold_dir / 'model.joblib',
    )
    save_json(fold_dir / 'metrics.json', {'fold_name': fold_name, 'rows': int(len(test_df)), **metrics})

    rows: List[Dict[str, object]] = []
    for idx, row in test_df.iterrows():
        rows.append({
            'fold': fold_name,
            'param_sample_id': row['param_sample_id'],
            'design_id': row['design_id'],
            'source_stage': row['source_stage'],
            'shape_id': row['shape_id'],
            'shape_family': row['shape_family'],
            'target_band_tag': row['target_band_tag'],
            'target_band_low_Hz': float(row['target_band_low_Hz']),
            'target_band_high_Hz': float(row['target_band_high_Hz']),
            'target_name': args.target,
            'y_true': float(y_test_raw[idx]),
            'y_pred': float(pred_test[idx]),
            'abs_error': float(abs(y_test_raw[idx] - pred_test[idx])),
        })
    save_csv_rows(
        fold_dir / 'predictions.csv',
        ['fold', 'param_sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'target_band_tag', 'target_band_low_Hz', 'target_band_high_Hz', 'target_name', 'y_true', 'y_pred', 'abs_error'],
        rows,
    )
    return metrics, rows


def load_completed_fold(
    df: pd.DataFrame,
    test_idx: np.ndarray,
    args: argparse.Namespace,
    fold_name: str,
    fold_dir: Path,
) -> Tuple[Dict[str, float], List[Dict[str, object]]]:
    bundle = joblib.load(fold_dir / 'model.joblib')
    test_df = df.iloc[test_idx].reset_index(drop=True)
    feature_cols = list(bundle['feature_cols'])
    fill_values = dict(bundle['fill_values'])
    model = bundle['model']
    target_transform = str(bundle.get('target_transform', args.target_transform))

    test_x = test_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce').fillna(fill_values)
    y_test_raw = test_df[args.target].astype(float).to_numpy()
    pred_test = inverse_target(model.predict(test_x.to_numpy(dtype=float)), target_transform)
    pred_test = np.clip(pred_test, 0.0, None)
    if args.target == 'target_gap_cover_ratio':
        pred_test = np.clip(pred_test, 0.0, 1.0)
    metrics = regression_metrics(y_test_raw, pred_test)

    rows: List[Dict[str, object]] = []
    for idx, row in test_df.iterrows():
        rows.append({
            'fold': fold_name,
            'param_sample_id': row['param_sample_id'],
            'design_id': row['design_id'],
            'source_stage': row['source_stage'],
            'shape_id': row['shape_id'],
            'shape_family': row['shape_family'],
            'target_band_tag': row['target_band_tag'],
            'target_band_low_Hz': float(row['target_band_low_Hz']),
            'target_band_high_Hz': float(row['target_band_high_Hz']),
            'target_name': args.target,
            'y_true': float(y_test_raw[idx]),
            'y_pred': float(pred_test[idx]),
            'abs_error': float(abs(y_test_raw[idx] - pred_test[idx])),
        })
    save_json(fold_dir / 'metrics.json', {'fold_name': fold_name, 'rows': int(len(test_df)), **metrics})
    save_csv_rows(
        fold_dir / 'predictions.csv',
        ['fold', 'param_sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'target_band_tag', 'target_band_low_Hz', 'target_band_high_Hz', 'target_name', 'y_true', 'y_pred', 'abs_error'],
        rows,
    )
    return metrics, rows


def summarize_metrics(fold_metrics: List[Dict[str, float]], all_truth: np.ndarray, all_pred: np.ndarray) -> Dict[str, object]:
    summary: Dict[str, object] = {
        'overall': regression_metrics(all_truth, all_pred),
        'fold_count': len(fold_metrics),
    }
    for metric_name in ['mae', 'rmse', 'r2']:
        values = np.array([fold[metric_name] for fold in fold_metrics], dtype=float)
        summary[f'{metric_name}_mean'] = float(np.mean(values))
        summary[f'{metric_name}_std'] = float(np.std(values))
    return summary


def write_run_outputs(
    run_root: Path,
    args: argparse.Namespace,
    feature_cols: List[str],
    fold_metrics: List[Dict[str, float]],
    prediction_rows: List[Dict[str, object]],
    positive_rows: int,
    target_mean: float,
    target_median: float,
) -> Dict[str, object]:
    prediction_df = pd.DataFrame(prediction_rows)
    if len(prediction_df) > 0:
        all_truth = prediction_df['y_true'].to_numpy(dtype=float)
        all_pred = prediction_df['y_pred'].to_numpy(dtype=float)
        summary = summarize_metrics(fold_metrics, all_truth, all_pred)
        per_band_rows = summarize_per_band(prediction_rows)
    else:
        summary = {'overall': {'mae': 0.0, 'rmse': 0.0, 'r2': 0.0}, 'fold_count': 0}
        per_band_rows = []
    summary['positive_rows'] = positive_rows
    summary['target_mean'] = target_mean
    summary['target_median'] = target_median

    save_csv_rows(run_root / 'fold_metrics.csv', ['fold', 'rows', 'mae', 'rmse', 'r2'], fold_metrics)
    save_csv_rows(
        run_root / 'predictions.csv',
        ['fold', 'param_sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'target_band_tag', 'target_band_low_Hz', 'target_band_high_Hz', 'target_name', 'y_true', 'y_pred', 'abs_error'],
        prediction_rows,
    )
    save_csv_rows(
        run_root / 'per_band_metrics.csv',
        ['target_band_tag', 'rows', 'target_mean', 'mae', 'rmse', 'r2'],
        per_band_rows,
    )
    save_json(
        run_root / 'run_config.json',
        {
            'dataset': str(args.dataset),
            'feature_set': ENRICHED_FEATURE_SET_NAME,
            'feature_cols': feature_cols,
            'target': args.target,
            'eval_mode': args.eval_mode,
            'group_key': args.group_key,
            'n_splits': args.n_splits,
            'min_stage_rows': args.min_stage_rows,
            'min_positive_stage_rows': args.min_positive_stage_rows,
            'target_transform': args.target_transform,
            'n_estimators': args.n_estimators,
            'min_samples_leaf': args.min_samples_leaf,
            'max_features': args.max_features,
            'seed': args.seed,
            'model_family': args.model_family,
            'positive_only': True,
            'band_features': BAND_FEATURES,
            'hgb_learning_rate': args.hgb_learning_rate,
            'hgb_max_iter': args.hgb_max_iter,
            'hgb_max_leaf_nodes': args.hgb_max_leaf_nodes,
            'hgb_max_depth': args.hgb_max_depth,
        },
    )
    save_json(run_root / 'metrics_summary.json', summary)
    return summary


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.dataset)
    df = select_rows(df, args.target)
    df, feature_sets = build_tail_prediction_frame(df)
    feature_cols = [col for col in feature_sets[ENRICHED_FEATURE_SET_NAME] if col in df.columns]
    feature_cols = [*feature_cols, *[col for col in BAND_FEATURES if col in df.columns]]
    if not feature_cols:
        raise RuntimeError('No usable feature columns found for parametric target-band regressor.')
    if len(df) == 0:
        raise RuntimeError('No positive rows available for parametric target-band regression.')

    run_root = DEFAULT_OUT_ROOT / args.run_name / args.eval_mode
    run_root.mkdir(parents=True, exist_ok=True)

    fold_metrics: List[Dict[str, float]] = []
    prediction_rows: List[Dict[str, object]] = []

    if args.eval_mode == 'stratified_group_kfold':
        if args.group_key == 'none':
            raise RuntimeError('stratified_group_kfold requires a non-none group key.')
        groups = df[args.group_key].astype(str).fillna('')
        y_labels = build_strat_labels(df, args.target)
        splitter = StratifiedGroupKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
        split_iter = [(f'fold_{fold_idx + 1}', train_idx, test_idx) for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(df, y_labels, groups=groups))]
    elif args.eval_mode == 'leave_one_stage_out':
        split_iter = list(iter_stage_loo_splits(df, args.min_stage_rows, args.min_positive_stage_rows))
        if not split_iter:
            raise RuntimeError('No leave-one-stage-out folds satisfy the positive-row requirement.')
    else:
        split_iter = list(iter_band_tag_loo_splits(df, args.min_positive_stage_rows))
        if not split_iter:
            raise RuntimeError('No leave-one-band-tag-out folds satisfy the positive-row requirement.')

    total_folds = len(split_iter)
    print(f'[START] regressor run_root={run_root}')
    print(f'[START] total_folds={total_folds} eval_mode={args.eval_mode} model_family={args.model_family}')

    for fold_idx, (fold_name, train_idx, test_idx) in enumerate(split_iter, start=1):
        fold_dir = run_root / fold_name
        fold_dir.mkdir(parents=True, exist_ok=True)
        if (fold_dir / 'model.joblib').exists() and (fold_dir / 'metrics.json').exists():
            print(f'[{fold_idx}/{total_folds}] REUSE {fold_name} rows={len(test_idx)}')
            metrics, rows = load_completed_fold(df, test_idx, args, fold_name, fold_dir)
        else:
            print(f'[{fold_idx}/{total_folds}] TRAIN {fold_name} rows={len(test_idx)}')
            metrics, rows = run_fold(df, train_idx, test_idx, feature_cols, args, fold_name, fold_dir)
        print(
            f'[{fold_idx}/{total_folds}] DONE {fold_name} '
            f"mae={metrics['mae']:.4f} r2={metrics['r2']:.4f}"
        )
        fold_metrics.append({'fold': fold_name, 'rows': len(test_idx), **metrics})
        prediction_rows.extend(rows)
        summary = write_run_outputs(
            run_root,
            args,
            feature_cols,
            fold_metrics,
            prediction_rows,
            positive_rows=int(len(df)),
            target_mean=float(df[args.target].mean()),
            target_median=float(df[args.target].median()),
        )
        print(
            f'[{fold_idx}/{total_folds}] PROGRESS '
            f"mae={summary['overall']['mae']:.4f} "
            f"r2={summary['overall']['r2']:.4f}"
        )

    print('[DONE] parametric target-band regression training complete')
    print(f'[RUN] {run_root}')
    print(
        f"[OOF] mae={summary['overall']['mae']:.4f} "
        f"rmse={summary['overall']['rmse']:.4f} "
        f"r2={summary['overall']['r2']:.4f} "
        f"positive_rows={summary['positive_rows']}"
    )


if __name__ == '__main__':
    main()
