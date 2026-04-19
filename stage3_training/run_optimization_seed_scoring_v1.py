from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml_common import DEFAULT_OUT_ROOT, save_csv_rows, save_json
from objective_registry import DEFAULT_OBJECTIVE_NAME, objective_choices
from run_seed_discovery_scoring_v7 import (
    attach_objective_predictions,
    predict_classifier_rows,
    predict_regressor,
    resolve_path,
)

DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_optimization_v1' / 'candidate_pool_optimization_v1.csv'
DEFAULT_CONTACT_RUN = DEFAULT_OUT_ROOT / 'mlp_contact_valid_parametric_seed_discovery_v7_full'
DEFAULT_POSITIVE_RUN = DEFAULT_OUT_ROOT / 'mlp_is_positive_shape_parametric_seed_discovery_v7_full'
DEFAULT_REG_RUN = DEFAULT_OUT_ROOT / 'mlp_gap34_gain_surrogate_v7_full'
DEFAULT_STAGE4_GLOB = 'stage4_validation_ab_v*/stage4_validation_shape_summary.csv'
DEFAULT_OPTIMIZATION_HISTORY_GLOBS = [
    'comsol_in_loop_true_global_ga_v1/ga_history_v1.csv',
    'comsol_in_loop_ga_optimization_funnel_probe_v1/ga_history_v1.csv',
    'comsol_in_loop_ga_optimization_expansion_v1/ga_history_v1.csv',
    'comsol_in_loop_ga_optimization_duel_v2/ga_history_v1.csv',
    'comsol_in_loop_ga_optimization_champion_v2/ga_history_v1.csv',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run optimization-oriented high-recall seed scoring.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--positive-run-root', type=Path, default=DEFAULT_POSITIVE_RUN)
    parser.add_argument('--positive-split', default='shape_family')
    parser.add_argument('--reg-run-root', type=Path, default=DEFAULT_REG_RUN)
    parser.add_argument('--reg-split', default='shape_family')
    parser.add_argument('--objective', default=DEFAULT_OBJECTIVE_NAME, choices=objective_choices())
    parser.add_argument('--run-name', default='candidate_pool_optimization_v1')
    parser.add_argument('--stage4-shape-summary-glob', default=DEFAULT_STAGE4_GLOB)
    parser.add_argument(
        '--optimization-history-glob',
        action='append',
        default=list(DEFAULT_OPTIMIZATION_HISTORY_GLOBS),
        help='Relative glob(s) under data/comsol_batch for recent optimization truth history.',
    )
    parser.add_argument('--top-k', type=int, default=24)
    return parser.parse_args()


def tier_rank(series: pd.Series) -> pd.Series:
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    return series.astype(str).map(tier_map).fillna(-1).astype(float)


def _empty_history(columns: Sequence[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def collect_stage4_history(pattern: str) -> pd.DataFrame:
    paths = sorted((ROOT / 'data' / 'comsol_batch').glob(pattern))
    rows: List[pd.DataFrame] = []
    for path in paths:
        df = pd.read_csv(path)
        required = {'shape_id', 'rows_total', 'solve_success_count', 'positive_gap34_gain_rate', 'mean_gap34_gain_Hz', 'best_gap34_gain_Hz'}
        if not required.issubset(df.columns):
            continue
        work = df.loc[:, list(required)].copy()
        work['shape_id'] = work['shape_id'].astype(str)
        work['rows_total'] = pd.to_numeric(work['rows_total'], errors='coerce').fillna(0.0)
        work['solve_success_count'] = pd.to_numeric(work['solve_success_count'], errors='coerce').fillna(0.0)
        work['positive_gap34_gain_rate'] = pd.to_numeric(work['positive_gap34_gain_rate'], errors='coerce').fillna(0.0)
        work['mean_gap34_gain_Hz'] = pd.to_numeric(work['mean_gap34_gain_Hz'], errors='coerce').fillna(0.0)
        work['best_gap34_gain_Hz'] = pd.to_numeric(work['best_gap34_gain_Hz'], errors='coerce').fillna(0.0)
        work['positive_count'] = work['rows_total'] * work['positive_gap34_gain_rate']
        rows.append(work)

    output_cols = [
        'shape_id',
        'historical_rows_total',
        'historical_solve_success_count',
        'historical_positive_rate',
        'historical_mean_real_gain_Hz',
        'historical_best_real_gain_Hz',
    ]
    if not rows:
        return _empty_history(output_cols)

    merged = pd.concat(rows, ignore_index=True)
    grouped = merged.groupby('shape_id', as_index=False).agg(
        historical_rows_total=('rows_total', 'sum'),
        historical_solve_success_count=('solve_success_count', 'sum'),
        historical_positive_count=('positive_count', 'sum'),
        historical_weighted_gain=('mean_gap34_gain_Hz', lambda s: float(np.sum(s * merged.loc[s.index, 'rows_total']))),
        historical_best_real_gain_Hz=('best_gap34_gain_Hz', 'max'),
    )
    grouped['historical_positive_rate'] = np.where(
        grouped['historical_rows_total'] > 0,
        grouped['historical_positive_count'] / grouped['historical_rows_total'],
        0.0,
    )
    grouped['historical_mean_real_gain_Hz'] = np.where(
        grouped['historical_rows_total'] > 0,
        grouped['historical_weighted_gain'] / grouped['historical_rows_total'],
        0.0,
    )
    grouped = grouped.drop(columns=['historical_positive_count', 'historical_weighted_gain'])
    return grouped


def collect_optimization_history(patterns: Iterable[str]) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []
    for pattern in patterns:
        for path in sorted((ROOT / 'data' / 'comsol_batch').glob(pattern)):
            df = pd.read_csv(path)
            required = {'shape_id', 'solve_success', 'gap34_gain_Hz'}
            if not required.issubset(df.columns):
                continue
            work = df.loc[:, ['shape_id', 'solve_success', 'gap34_gain_Hz']].copy()
            work['shape_id'] = work['shape_id'].astype(str)
            work['solve_success'] = pd.to_numeric(work['solve_success'], errors='coerce').fillna(0.0)
            work['gap34_gain_Hz'] = pd.to_numeric(work['gap34_gain_Hz'], errors='coerce')
            work['rows_total'] = 1.0
            work['positive_count'] = np.where(
                (work['solve_success'] > 0) & (work['gap34_gain_Hz'] > 0.0),
                1.0,
                0.0,
            )
            work['solve_gain'] = np.where(work['solve_success'] > 0, work['gap34_gain_Hz'], np.nan)
            rows.append(work)

    output_cols = [
        'shape_id',
        'optimization_rows_total',
        'optimization_solve_success_count',
        'optimization_positive_rate',
        'optimization_mean_real_gain_Hz',
        'optimization_best_real_gain_Hz',
    ]
    if not rows:
        return _empty_history(output_cols)

    merged = pd.concat(rows, ignore_index=True)
    grouped = merged.groupby('shape_id', as_index=False).agg(
        optimization_rows_total=('rows_total', 'sum'),
        optimization_solve_success_count=('solve_success', 'sum'),
        optimization_positive_count=('positive_count', 'sum'),
        optimization_mean_real_gain_Hz=('solve_gain', 'mean'),
        optimization_best_real_gain_Hz=('solve_gain', 'max'),
    )
    grouped['optimization_positive_rate'] = np.where(
        grouped['optimization_rows_total'] > 0,
        grouped['optimization_positive_count'] / grouped['optimization_rows_total'],
        0.0,
    )
    grouped['optimization_mean_real_gain_Hz'] = pd.to_numeric(
        grouped['optimization_mean_real_gain_Hz'], errors='coerce'
    ).fillna(0.0)
    grouped['optimization_best_real_gain_Hz'] = pd.to_numeric(
        grouped['optimization_best_real_gain_Hz'], errors='coerce'
    ).fillna(0.0)
    grouped = grouped.drop(columns=['optimization_positive_count'])
    return grouped


def _series_or_default(work: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col in work.columns:
        return pd.to_numeric(work[col], errors='coerce').fillna(default)
    return pd.Series(default, index=work.index, dtype='float64')


def _object_series_or_default(work: pd.DataFrame, col: str, default: str = '') -> pd.Series:
    if col in work.columns:
        return work[col].fillna(default).astype('string')
    return pd.Series([default] * len(work), index=work.index, dtype='string')


def assign_scores(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    work = df.copy()
    work['stage1_reference_gap_gain_Hz'] = _series_or_default(work, 'stage1_reference_gap_gain_Hz', 0.0)
    work[pred_col] = _series_or_default(work, pred_col, 0.0)
    work['contact_prob'] = _series_or_default(work, 'contact_prob', 0.0)
    work['positive_prob'] = _series_or_default(work, 'positive_prob', 0.0)
    work['stage1_candidate_tier_rank'] = tier_rank(_object_series_or_default(work, 'stage1_reference_candidate_tier', ''))

    for col in [
        'historical_rows_total',
        'historical_solve_success_count',
        'historical_positive_rate',
        'historical_mean_real_gain_Hz',
        'historical_best_real_gain_Hz',
        'optimization_rows_total',
        'optimization_solve_success_count',
        'optimization_positive_rate',
        'optimization_mean_real_gain_Hz',
        'optimization_best_real_gain_Hz',
    ]:
        work[col] = _series_or_default(work, col, 0.0)

    work['class_score'] = work['contact_prob'] * work['positive_prob']
    work['cascade_score'] = 0.70 * work['contact_prob'] + 0.30 * work['positive_prob']
    work['contact_gate'] = work['contact_prob'] >= 0.01
    work['positive_gate'] = work['positive_prob'] >= 0.50
    work['reg_positive_gate'] = work[pred_col] > 0.0
    work['cascade_gate'] = work['contact_gate'] & work['positive_gate']

    history_confidence = np.clip(work['historical_rows_total'], 0.0, 3.0) / 3.0
    historical_real_score = history_confidence * (
        0.65 * np.clip(work['historical_best_real_gain_Hz'], 0.0, 50.0)
        + 0.35 * np.clip(work['historical_mean_real_gain_Hz'], 0.0, 40.0)
    )
    optimization_confidence = np.clip(np.log1p(work['optimization_rows_total']) / np.log(61.0), 0.0, 1.0)
    optimization_real_score = optimization_confidence * (
        0.55 * np.clip(work['optimization_best_real_gain_Hz'], 0.0, 50.0)
        + 0.25 * np.clip(work['optimization_mean_real_gain_Hz'], 0.0, 40.0)
        + 8.0 * np.clip(work['optimization_positive_rate'], 0.0, 1.0)
    )
    novelty_bonus = np.where(work['historical_rows_total'] <= 0, 2.0, 0.0)

    work['optimization_seed_score'] = (
        16.0 * work['contact_prob']
        + 14.0 * work['positive_prob']
        + 0.25 * np.clip(work[pred_col], 0.0, 60.0)
        + 0.35 * np.clip(work['stage1_reference_gap_gain_Hz'], 0.0, 20.0)
        + 0.55 * historical_real_score
        + 0.75 * optimization_real_score
        + 1.50 * work['stage1_candidate_tier_rank']
        + novelty_bonus
    )
    work['historical_real_score'] = historical_real_score
    work['optimization_real_score'] = optimization_real_score
    work['novelty_bonus'] = novelty_bonus
    return work


def ranked_frame(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    return df.sort_values(
        [
            'optimization_seed_score',
            'optimization_best_real_gain_Hz',
            'historical_best_real_gain_Hz',
            'contact_prob',
            'positive_prob',
            pred_col,
            'stage1_reference_gap_gain_Hz',
        ],
        ascending=[False, False, False, False, False, False, False],
    ).copy()


def build_family_summary(df: pd.DataFrame, pred_col: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for family, subset in df.groupby('shape_family'):
        rows.append({
            'shape_family': family,
            'rows': int(len(subset)),
            'mean_optimization_seed_score': float(np.mean(subset['optimization_seed_score'])),
            'mean_contact_prob': float(np.mean(subset['contact_prob'])),
            'mean_positive_prob': float(np.mean(subset['positive_prob'])),
            'mean_stage1_reference_gap_gain_Hz': float(np.mean(subset['stage1_reference_gap_gain_Hz'])),
            'mean_historical_best_real_gain_Hz': float(np.mean(subset['historical_best_real_gain_Hz'])),
            'mean_optimization_best_real_gain_Hz': float(np.mean(subset['optimization_best_real_gain_Hz'])),
            f'mean_{pred_col}': float(np.mean(subset[pred_col])),
        })
    rows.sort(key=lambda item: item['mean_optimization_seed_score'], reverse=True)
    return rows


def main() -> None:
    args = parse_args()
    dataset = resolve_path(args.dataset)
    if dataset is None or not dataset.exists():
        raise FileNotFoundError(dataset)

    df = pd.read_csv(dataset)
    if df.empty:
        raise RuntimeError(f'Empty dataset: {dataset}')

    df = df.copy()
    df['contact_prob'] = predict_classifier_rows(df, resolve_path(args.contact_run_root), str(args.contact_split))
    df['positive_prob'] = predict_classifier_rows(df, resolve_path(args.positive_run_root), str(args.positive_split))
    reg_predictions = predict_regressor(df, resolve_path(args.reg_run_root), str(args.reg_split), objective_name=args.objective)
    df, pred_col = attach_objective_predictions(df, args.objective, reg_predictions)
    if pred_col == 'surrogate_pred_gap34_gain_Hz':
        df['surrogate_pred_gap34_gain_Hz'] = df[pred_col]

    history = collect_stage4_history(args.stage4_shape_summary_glob)
    df = df.merge(history, on='shape_id', how='left')
    optimization_history = collect_optimization_history(args.optimization_history_glob)
    df = df.merge(optimization_history, on='shape_id', how='left')
    df = assign_scores(df, pred_col)

    run_dir = DEFAULT_OUT_ROOT / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    ranked = ranked_frame(df, pred_col)
    top_rows = ranked.head(min(int(args.top_k), len(ranked))).copy()
    family_rows = build_family_summary(df, pred_col)
    metrics = {
        'rows_total': int(len(df)),
        'history_seen_rows': int((pd.to_numeric(df['historical_rows_total'], errors='coerce').fillna(0.0) > 0).sum()),
        'optimization_history_seen_rows': int((pd.to_numeric(df['optimization_rows_total'], errors='coerce').fillna(0.0) > 0).sum()),
        'top_k': int(len(top_rows)),
        'top_k_history_seen_count': int((top_rows['historical_rows_total'] > 0).sum()),
        'top_k_optimization_history_seen_count': int((top_rows['optimization_rows_total'] > 0).sum()),
        'top_k_strong_positive_count': int((top_rows['stage1_reference_candidate_tier'].astype(str) == 'strong_positive').sum()),
        'top_k_positive_gate_count': int(top_rows['positive_gate'].sum()),
        'top_k_contact_gate_count': int(top_rows['contact_gate'].sum()),
        'prediction_column': pred_col,
    }
    config = {
        'dataset': str(dataset),
        'contact_run_root': str(resolve_path(args.contact_run_root)),
        'contact_split': args.contact_split,
        'positive_run_root': str(resolve_path(args.positive_run_root)),
        'positive_split': args.positive_split,
        'reg_run_root': str(resolve_path(args.reg_run_root)),
        'reg_split': args.reg_split,
        'objective': args.objective,
        'prediction_column': pred_col,
        'stage4_shape_summary_glob': args.stage4_shape_summary_glob,
        'optimization_history_globs': list(args.optimization_history_glob),
        'top_k': int(args.top_k),
        'score_definition': 'optimization-oriented high-recall score: classifier promise + surrogate promise + stage1 baseline + stage4 historical truth prior + optimization historical truth prior with soft novelty bonus',
        'history_channels': 'stage4 historical summaries remain a broad screening prior; recent optimization runs are merged as a separate optimization-memory prior',
    }

    df.to_csv(run_dir / 'optimization_seed_predictions.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(run_dir / 'optimization_seed_family_summary.csv', list(family_rows[0].keys()) if family_rows else ['shape_family'], family_rows)
    save_csv_rows(run_dir / 'optimization_seed_top_candidates.csv', list(top_rows.columns), top_rows.to_dict(orient='records'))
    save_json(run_dir / 'optimization_seed_metrics.json', metrics)
    save_json(run_dir / 'optimization_seed_config.json', config)

    print('[DONE] optimization-oriented seed scoring complete')
    print(f'[RUN] {run_dir}')
    print(f'[TOP] top_k={len(top_rows)} prediction_column={pred_col}')


if __name__ == '__main__':
    main()
