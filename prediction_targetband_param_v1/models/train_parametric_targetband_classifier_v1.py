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
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_v3.models.feature_engineering import ENRICHED_FEATURE_SET_NAME, build_tail_prediction_frame
from shared.features.prediction import ALLOWED_GROUP_KEYS
from stage3_training.ml_common import classification_metrics, save_csv_rows, save_json

DEFAULT_DATASET = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_120_160__180_220__220_260' / 'targetband_parametric_v1.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1_runs'
BAND_FEATURES = ['target_band_low_Hz', 'target_band_high_Hz', 'target_band_center_Hz', 'target_band_width_Hz']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a parameterized target-band classifier from stacked fixed windows.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--eval-mode', default='stratified_group_kfold', choices=['stratified_group_kfold', 'leave_one_stage_out', 'leave_one_band_tag_out'])
    parser.add_argument('--group-key', default='shape_family', choices=ALLOWED_GROUP_KEYS)
    parser.add_argument('--n-splits', type=int, default=5)
    parser.add_argument('--min-stage-rows', type=int, default=10)
    parser.add_argument('--run-name', default='param_targetband_cls_v1')
    parser.add_argument('--model-family', default='random_forest', choices=['random_forest', 'hist_gradient_boosting'])
    parser.add_argument('--n-estimators', type=int, default=900)
    parser.add_argument('--min-samples-leaf', type=int, default=1)
    parser.add_argument('--max-features', default='1.0')
    parser.add_argument('--hgb-learning-rate', type=float, default=0.05)
    parser.add_argument('--hgb-max-iter', type=int, default=400)
    parser.add_argument('--hgb-max-leaf-nodes', type=int, default=31)
    parser.add_argument('--hgb-max-depth', type=int, default=8)
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


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


def iter_band_tag_loo_splits(df: pd.DataFrame) -> Iterable[Tuple[str, np.ndarray, np.ndarray]]:
    for band_tag in sorted(df['target_band_tag'].astype(str).unique().tolist()):
        test_mask = df['target_band_tag'].astype(str) == band_tag
        test_idx = np.flatnonzero(test_mask.to_numpy())
        train_idx = np.flatnonzero((~test_mask).to_numpy())
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue
        yield band_tag, train_idx, test_idx


def make_model(args: argparse.Namespace):
    if args.model_family == 'hist_gradient_boosting':
        return HistGradientBoostingClassifier(
            learning_rate=args.hgb_learning_rate,
            max_iter=args.hgb_max_iter,
            max_leaf_nodes=args.hgb_max_leaf_nodes,
            max_depth=args.hgb_max_depth,
            min_samples_leaf=args.min_samples_leaf,
            random_state=args.seed,
        )
    return RandomForestClassifier(
        n_estimators=args.n_estimators,
        min_samples_leaf=args.min_samples_leaf,
        max_features=parse_max_features(args.max_features),
        random_state=args.seed,
        class_weight='balanced',
        n_jobs=1,
    )


def summarize_per_band(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    df = pd.DataFrame(rows)
    summary_rows: List[Dict[str, object]] = []
    for band_tag, subset in df.groupby('target_band_tag'):
        metrics = classification_metrics(subset['y_true'].to_numpy(dtype=float), subset['y_prob'].to_numpy(dtype=float))
        summary_rows.append({
            'target_band_tag': str(band_tag),
            'rows': int(len(subset)),
            'positive_rate': float(subset['y_true'].mean()),
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
    y_train = train_df['target_gap_is_open'].astype(int).to_numpy()
    y_test = test_df['target_gap_is_open'].astype(int).to_numpy()

    model = make_model(args)
    model.fit(x_train, y_train)
    y_prob = model.predict_proba(x_test)[:, 1]
    metrics = classification_metrics(y_test, y_prob, threshold=args.threshold)

    joblib.dump(
        {
            'model': model,
            'feature_cols': feature_cols,
            'fill_values': fill_values,
            'threshold': args.threshold,
            'eval_mode': args.eval_mode,
            'fold_name': fold_name,
        },
        fold_dir / 'model.joblib',
    )
    save_json(fold_dir / 'metrics.json', {'fold_name': fold_name, 'rows': int(len(test_df)), **metrics})

    rows: List[Dict[str, object]] = []
    pred = (y_prob >= args.threshold).astype(int)
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
            'target_gap_cover_ratio': float(row['target_gap_cover_ratio']),
            'y_true': int(y_test[idx]),
            'y_prob': float(y_prob[idx]),
            'y_pred': int(pred[idx]),
        })
    save_csv_rows(
        fold_dir / 'predictions.csv',
        ['fold', 'param_sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'target_band_tag', 'target_band_low_Hz', 'target_band_high_Hz', 'target_gap_cover_ratio', 'y_true', 'y_prob', 'y_pred'],
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
    threshold = float(bundle.get('threshold', args.threshold))
    model = bundle['model']

    test_x = test_df.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce').fillna(fill_values)
    y_test = test_df['target_gap_is_open'].astype(int).to_numpy()
    y_prob = model.predict_proba(test_x.to_numpy(dtype=float))[:, 1]
    metrics = classification_metrics(y_test, y_prob, threshold=threshold)

    rows: List[Dict[str, object]] = []
    pred = (y_prob >= threshold).astype(int)
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
            'target_gap_cover_ratio': float(row['target_gap_cover_ratio']),
            'y_true': int(y_test[idx]),
            'y_prob': float(y_prob[idx]),
            'y_pred': int(pred[idx]),
        })
    save_json(fold_dir / 'metrics.json', {'fold_name': fold_name, 'rows': int(len(test_df)), **metrics})
    save_csv_rows(
        fold_dir / 'predictions.csv',
        ['fold', 'param_sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'target_band_tag', 'target_band_low_Hz', 'target_band_high_Hz', 'target_gap_cover_ratio', 'y_true', 'y_prob', 'y_pred'],
        rows,
    )
    return metrics, rows


def summarize_metrics(fold_metrics: List[Dict[str, float]]) -> Dict[str, object]:
    summary: Dict[str, object] = {'fold_count': len(fold_metrics)}
    for metric_name in ['accuracy', 'precision', 'recall', 'f1', 'balanced_accuracy']:
        values = np.array([fold[metric_name] for fold in fold_metrics], dtype=float)
        summary[f'{metric_name}_mean'] = float(np.mean(values))
        summary[f'{metric_name}_std'] = float(np.std(values))
    return summary


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.dataset)
    df, feature_sets = build_tail_prediction_frame(df)
    feature_cols = [col for col in feature_sets[ENRICHED_FEATURE_SET_NAME] if col in df.columns]
    feature_cols = [*feature_cols, *[col for col in BAND_FEATURES if col in df.columns]]
    if not feature_cols:
        raise RuntimeError('No usable feature columns found for parametric target-band classifier.')

    run_root = DEFAULT_OUT_ROOT / args.run_name / args.eval_mode
    run_root.mkdir(parents=True, exist_ok=True)

    fold_metrics: List[Dict[str, float]] = []
    prediction_rows: List[Dict[str, object]] = []

    if args.eval_mode == 'stratified_group_kfold':
        if args.group_key == 'none':
            raise RuntimeError('stratified_group_kfold requires a non-none group key.')
        groups = df[args.group_key].astype(str).fillna('')
        y_labels = df['target_gap_is_open'].astype(int).to_numpy()
        splitter = StratifiedGroupKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
        split_iter = [(f'fold_{fold_idx + 1}', train_idx, test_idx) for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(df, y_labels, groups=groups))]
    elif args.eval_mode == 'leave_one_stage_out':
        split_iter = list(iter_stage_loo_splits(df, args.min_stage_rows))
        if not split_iter:
            raise RuntimeError('No leave-one-stage-out folds satisfy the min-stage-rows requirement.')
    else:
        split_iter = list(iter_band_tag_loo_splits(df))
        if not split_iter:
            raise RuntimeError('No leave-one-band-tag-out folds available.')

    for fold_name, train_idx, test_idx in split_iter:
        fold_dir = run_root / fold_name
        fold_dir.mkdir(parents=True, exist_ok=True)
        if (fold_dir / 'model.joblib').exists() and (fold_dir / 'metrics.json').exists():
            metrics, rows = load_completed_fold(df, test_idx, args, fold_name, fold_dir)
        else:
            metrics, rows = run_fold(df, train_idx, test_idx, feature_cols, args, fold_name, fold_dir)
        fold_metrics.append({'fold': fold_name, 'rows': len(test_idx), **metrics})
        prediction_rows.extend(rows)

    save_csv_rows(
        run_root / 'fold_metrics.csv',
        ['fold', 'rows', 'accuracy', 'precision', 'recall', 'f1', 'balanced_accuracy'],
        fold_metrics,
    )
    save_csv_rows(
        run_root / 'predictions.csv',
        ['fold', 'param_sample_id', 'design_id', 'source_stage', 'shape_id', 'shape_family', 'target_band_tag', 'target_band_low_Hz', 'target_band_high_Hz', 'target_gap_cover_ratio', 'y_true', 'y_prob', 'y_pred'],
        prediction_rows,
    )
    save_csv_rows(
        run_root / 'per_band_metrics.csv',
        ['target_band_tag', 'rows', 'positive_rate', 'accuracy', 'precision', 'recall', 'f1', 'balanced_accuracy'],
        summarize_per_band(prediction_rows),
    )
    save_json(
        run_root / 'run_config.json',
        {
            'dataset': str(args.dataset),
            'feature_set': ENRICHED_FEATURE_SET_NAME,
            'feature_cols': feature_cols,
            'eval_mode': args.eval_mode,
            'group_key': args.group_key,
            'n_splits': args.n_splits,
            'min_stage_rows': args.min_stage_rows,
            'n_estimators': args.n_estimators,
            'min_samples_leaf': args.min_samples_leaf,
            'max_features': args.max_features,
            'threshold': args.threshold,
            'seed': args.seed,
            'model_family': args.model_family,
            'band_features': BAND_FEATURES,
            'hgb_learning_rate': args.hgb_learning_rate,
            'hgb_max_iter': args.hgb_max_iter,
            'hgb_max_leaf_nodes': args.hgb_max_leaf_nodes,
            'hgb_max_depth': args.hgb_max_depth,
        },
    )
    summary = summarize_metrics(fold_metrics)
    summary['positive_rate'] = float(df['target_gap_is_open'].mean())
    save_json(run_root / 'metrics_summary.json', summary)

    print('[DONE] parametric target-band classifier training complete')
    print(f'[RUN] {run_root}')
    print(
        f"[OOF] f1={summary['f1_mean']:.4f} "
        f"bal_acc={summary['balanced_accuracy_mean']:.4f} "
        f"positive_rate={summary['positive_rate']:.4f}"
    )


if __name__ == '__main__':
    main()
