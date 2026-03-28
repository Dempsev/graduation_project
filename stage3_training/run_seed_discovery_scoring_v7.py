from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from objective_registry import (
    DEFAULT_OBJECTIVE_NAME,
    GENERIC_OBJECTIVE_NAME_COLUMN,
    GENERIC_OBJECTIVE_PREDICTION_COLUMN,
    GENERIC_PREDICTION_COLUMN,
    get_objective,
    objective_choices,
)
from ml_common import DEFAULT_OUT_ROOT, MLP, save_csv_rows, save_json
from policy_resolution import load_policy_json, resolve_policy_settings

DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v8' / 'candidate_pool_v8_seed_only_discovery' / 'candidate_pool_v8.csv'
DEFAULT_CONTACT_RUN = DEFAULT_OUT_ROOT / 'mlp_contact_valid_parametric_seed_discovery_v7_full'
DEFAULT_POSITIVE_RUN = DEFAULT_OUT_ROOT / 'mlp_is_positive_shape_parametric_seed_discovery_v7_full'
DEFAULT_REG_RUN = DEFAULT_OUT_ROOT / 'mlp_gap34_gain_surrogate_v7_full'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run stage1-aware seed-only discovery scoring.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--positive-run-root', type=Path, default=DEFAULT_POSITIVE_RUN)
    parser.add_argument('--positive-split', default='shape_family')
    parser.add_argument('--reg-run-root', type=Path, default=DEFAULT_REG_RUN)
    parser.add_argument('--reg-split', default='shape_family')
    parser.add_argument('--objective', default=DEFAULT_OBJECTIVE_NAME, choices=objective_choices())
    parser.add_argument('--run-name', default='seed_discovery_scoring_v7')
    parser.add_argument('--contact-threshold', type=float, default=0.50)
    parser.add_argument('--positive-threshold', type=float, default=0.50)
    parser.add_argument('--contact-weight', type=float, default=0.70)
    parser.add_argument('--positive-weight', type=float, default=0.30)
    parser.add_argument('--calibration-json', type=Path, default=None)
    parser.add_argument('--policy-json', type=Path, default=None)
    parser.add_argument('--reg-min', type=float, default=0.0)
    parser.add_argument('--top-k', type=int, default=12)
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def resolve_path(path_text: str | Path | None) -> Path | None:
    if path_text in (None, ''):
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_scoring_policy(args: argparse.Namespace) -> Dict[str, object]:
    return load_policy_json(resolve_path(args.policy_json), section=None)


def resolve_runtime_config(args: argparse.Namespace) -> Dict[str, object]:
    policy = load_scoring_policy(args) if getattr(args, 'policy_json', None) else {}
    defaults = {
        'dataset': DEFAULT_DATASET,
        'contact_run_root': DEFAULT_CONTACT_RUN,
        'contact_split': 'shape_family',
        'positive_run_root': DEFAULT_POSITIVE_RUN,
        'positive_split': 'shape_family',
        'reg_run_root': DEFAULT_REG_RUN,
        'reg_split': 'shape_family',
        'objective_name': DEFAULT_OBJECTIVE_NAME,
        'calibration_json': None,
        'top_k': 12,
    }
    cli_values = {
        'dataset': getattr(args, 'dataset', None),
        'contact_run_root': getattr(args, 'contact_run_root', None),
        'contact_split': getattr(args, 'contact_split', None),
        'positive_run_root': getattr(args, 'positive_run_root', None),
        'positive_split': getattr(args, 'positive_split', None),
        'reg_run_root': getattr(args, 'reg_run_root', None),
        'reg_split': getattr(args, 'reg_split', None),
        'objective_name': getattr(args, 'objective', None),
        'calibration_json': getattr(args, 'calibration_json', None),
        'top_k': getattr(args, 'top_k', None),
    }
    resolved = resolve_policy_settings(defaults, policy, cli_values, defaults, policy_enabled=bool(getattr(args, 'policy_json', None)))
    resolved['dataset'] = resolve_path(resolved['dataset'])
    resolved['contact_run_root'] = resolve_path(resolved['contact_run_root'])
    resolved['positive_run_root'] = resolve_path(resolved['positive_run_root'])
    resolved['reg_run_root'] = resolve_path(resolved['reg_run_root'])
    resolved['calibration_json'] = resolve_path(resolved.get('calibration_json'))
    resolved['objective_name'] = str(resolved.get('objective_name', DEFAULT_OBJECTIVE_NAME))
    resolved['policy_json'] = str(resolve_path(args.policy_json)) if getattr(args, 'policy_json', None) else ''
    return resolved


def resolve_scoring_settings(args: argparse.Namespace, policy: Dict[str, object] | None = None) -> Dict[str, object]:
    policy = dict(policy or {})
    defaults = {
        'contact_threshold': 0.50,
        'positive_threshold': 0.50,
        'contact_weight': 0.70,
        'positive_weight': 0.30,
        'reg_min': 0.0,
        'calibration_json': None,
        'calibration_version': '',
    }
    calibration_path = resolve_path(getattr(args, 'calibration_json', None))
    calibration_defaults: Dict[str, object] = {}
    calibration_version = ''
    if calibration_path:
        payload = load_json(calibration_path)
        recommended = payload.get('recommended', payload)
        for key in ['contact_threshold', 'positive_threshold', 'contact_weight', 'positive_weight', 'reg_min']:
            if key in recommended and recommended[key] is not None:
                calibration_defaults[key] = float(recommended[key])
        calibration_version = str(payload.get('version', recommended.get('version', '')))

    policy_defaults = {
        key: policy.get(key)
        for key in ['contact_threshold', 'positive_threshold', 'contact_weight', 'positive_weight', 'reg_min']
        if key in policy
    }
    cli_values = {
        'contact_threshold': getattr(args, 'contact_threshold', None),
        'positive_threshold': getattr(args, 'positive_threshold', None),
        'contact_weight': getattr(args, 'contact_weight', None),
        'positive_weight': getattr(args, 'positive_weight', None),
        'reg_min': getattr(args, 'reg_min', None),
    }
    resolved = resolve_policy_settings(defaults, calibration_defaults, policy_enabled=True)
    resolved = resolve_policy_settings(resolved, policy_defaults, policy_enabled=bool(getattr(args, 'policy_json', None)))
    resolved = resolve_policy_settings(resolved, None, cli_values, defaults, policy_enabled=bool(getattr(args, 'policy_json', None)))
    resolved['calibration_json'] = str(calibration_path) if calibration_path else ''
    resolved['calibration_version'] = calibration_version

    total_weight = float(resolved['contact_weight']) + float(resolved['positive_weight'])
    if total_weight <= 0:
        raise ValueError('contact_weight + positive_weight must be positive.')
    resolved['contact_weight'] = float(resolved['contact_weight']) / total_weight
    resolved['positive_weight'] = float(resolved['positive_weight']) / total_weight
    return resolved


def load_checkpoint(run_root: Path, split_name: str) -> Dict[str, object]:
    model_path = run_root / split_name / 'model.pt'
    if not model_path.exists():
        raise FileNotFoundError(f'Model checkpoint not found: {model_path}')
    return torch.load(model_path, map_location='cpu')


def build_model(checkpoint: Dict[str, object]) -> MLP:
    model = MLP(
        input_dim=int(checkpoint['input_dim']),
        hidden_dims=list(checkpoint['hidden_dims']),
        output_dim=1,
        dropout=float(checkpoint.get('dropout', 0.0)),
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model


def ensure_feature_columns(frame: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    work = frame.copy()
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}

    if 'stage1_reference_candidate_tier_rank' in feature_cols and 'stage1_reference_candidate_tier_rank' not in work.columns:
        work['stage1_reference_candidate_tier_rank'] = work.get('stage1_reference_candidate_tier', '').astype(str).map(tier_map).fillna(-1).astype(float)
    if 'has_stage1_reference' in feature_cols and 'has_stage1_reference' not in work.columns:
        has_ref = work.get('stage1_reference_sample_id', '').astype(str).str.strip().ne('')
        if 'stage1_reference_gap_Hz' in work.columns:
            has_ref = has_ref | pd.to_numeric(work['stage1_reference_gap_Hz'], errors='coerce').notna()
        work['has_stage1_reference'] = has_ref.astype(float)
    if 'stage1_reference_contact_valid' in feature_cols and 'stage1_reference_contact_valid' not in work.columns:
        contact_len = pd.to_numeric(work.get('stage1_reference_contact_length'), errors='coerce')
        work['stage1_reference_contact_valid'] = contact_len.gt(0).fillna(False).astype(float)
    if 'stage1_reference_solve_success' in feature_cols and 'stage1_reference_solve_success' not in work.columns:
        gap_ref = pd.to_numeric(work.get('stage1_reference_gap_Hz'), errors='coerce')
        work['stage1_reference_solve_success'] = gap_ref.notna().astype(float)
    if 'stage1_reference_is_positive_shape' in feature_cols and 'stage1_reference_is_positive_shape' not in work.columns:
        gain_ref = pd.to_numeric(work.get('stage1_reference_gap_gain_Hz'), errors='coerce')
        work['stage1_reference_is_positive_shape'] = gain_ref.gt(0).fillna(False).astype(float)

    for col in feature_cols:
        if col not in work.columns:
            work[col] = np.nan
    return work


def transform_with_checkpoint(frame: pd.DataFrame, feature_cols: List[str], checkpoint: Dict[str, object]) -> np.ndarray:
    work = ensure_feature_columns(frame, feature_cols)
    x_raw = work.loc[:, feature_cols].astype(float).to_numpy()
    means = np.asarray(checkpoint['x_mean'], dtype=float)
    stds = np.asarray(checkpoint['x_std'], dtype=float)
    filled = np.where(np.isfinite(x_raw), x_raw, means)
    return (filled - means) / stds


def predict_classifier_rows(frame: pd.DataFrame, run_root: Path, split_name: str) -> np.ndarray:
    checkpoint = load_checkpoint(run_root, split_name)
    model = build_model(checkpoint)
    feature_cols = list(checkpoint['feature_cols'])
    x = transform_with_checkpoint(frame, feature_cols, checkpoint)
    with torch.no_grad():
        logits = model(torch.tensor(x, dtype=torch.float32)).cpu().numpy().reshape(-1)
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -50.0, 50.0)))


def predict_regressor(frame: pd.DataFrame, run_root: Path, split_name: str, objective_name: str | None = None) -> np.ndarray:
    checkpoint = load_checkpoint(run_root, split_name)
    checkpoint_target = str(checkpoint.get('target', '')).strip()
    if objective_name and checkpoint_target and checkpoint_target != objective_name:
        raise ValueError(f'Regressor target mismatch: checkpoint target={checkpoint_target}, requested objective={objective_name}')
    model = build_model(checkpoint)
    feature_cols = list(checkpoint['feature_cols'])
    x = transform_with_checkpoint(frame, feature_cols, checkpoint)
    with torch.no_grad():
        pred_scaled = model(torch.tensor(x, dtype=torch.float32)).cpu().numpy().reshape(-1)
    y_mean = float(checkpoint['y_mean'])
    y_std = float(checkpoint['y_std'])
    return pred_scaled * y_std + y_mean


def attach_objective_predictions(df: pd.DataFrame, objective_name: str, predictions: np.ndarray) -> tuple[pd.DataFrame, str]:
    objective = get_objective(objective_name)
    pred_col = objective.prediction_column
    out = df.copy()
    out[pred_col] = predictions
    out[GENERIC_OBJECTIVE_NAME_COLUMN] = objective.name
    out[GENERIC_OBJECTIVE_PREDICTION_COLUMN] = pred_col
    out[GENERIC_PREDICTION_COLUMN] = out[pred_col]
    return out, pred_col


def assign_scores(df: pd.DataFrame, settings: Dict[str, object], pred_col: str) -> pd.DataFrame:
    df = df.copy()
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    df['stage1_reference_gap_gain_Hz'] = pd.to_numeric(df.get('stage1_reference_gap_gain_Hz'), errors='coerce').fillna(-1.0)
    df['stage1_reference_contact_length'] = pd.to_numeric(df.get('stage1_reference_contact_length'), errors='coerce').fillna(-1.0)
    df[pred_col] = pd.to_numeric(df.get(pred_col), errors='coerce')
    df[GENERIC_PREDICTION_COLUMN] = pd.to_numeric(df.get(GENERIC_PREDICTION_COLUMN), errors='coerce')
    df['stage1_candidate_tier_rank'] = df.get('stage1_reference_candidate_tier', '').astype(str).map(tier_map).fillna(-1).astype(int)
    df['contact_threshold'] = float(settings['contact_threshold'])
    df['positive_threshold'] = float(settings['positive_threshold'])
    df['contact_weight'] = float(settings['contact_weight'])
    df['positive_weight'] = float(settings['positive_weight'])
    df['contact_gate'] = df['contact_prob'] >= df['contact_threshold']
    df['positive_gate'] = df['positive_prob'] >= df['positive_threshold']
    df['reg_positive_gate'] = df[pred_col] > float(settings['reg_min'])
    df['cascade_gate'] = df['contact_gate'] & df['positive_gate']
    df['class_score'] = df['contact_prob'] * df['positive_prob']
    df['cascade_score'] = df['contact_weight'] * df['contact_prob'] + df['positive_weight'] * df['positive_prob']
    return df


def ranked_frame(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    return df.sort_values(
        [
            'cascade_gate',
            'cascade_score',
            'contact_prob',
            'positive_prob',
            'stage1_candidate_tier_rank',
            'stage1_reference_gap_gain_Hz',
            pred_col,
            'stage1_reference_contact_length',
        ],
        ascending=[False, False, False, False, False, False, False, False],
    ).copy()


def build_group_summary(df: pd.DataFrame, group_col: str, extra_cols: List[str], pred_col: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    pred_summary_col = f'mean_{pred_col}'
    for key, subset in df.groupby(group_col):
        row = {
            group_col: key,
            'rows': int(len(subset)),
            'contact_gate_rate': float(subset['contact_gate'].mean()),
            'positive_gate_rate': float(subset['positive_gate'].mean()),
            'cascade_gate_rate': float(subset['cascade_gate'].mean()),
            'mean_contact_prob': float(np.mean(subset['contact_prob'])),
            'mean_positive_prob': float(np.mean(subset['positive_prob'])),
            'mean_cascade_score': float(np.mean(subset['cascade_score'])),
            'mean_stage1_reference_gap_gain_Hz': float(np.mean(subset['stage1_reference_gap_gain_Hz'])),
            pred_summary_col: float(np.mean(subset[pred_col])),
            GENERIC_OBJECTIVE_NAME_COLUMN: str(subset[GENERIC_OBJECTIVE_NAME_COLUMN].iloc[0]),
        }
        for extra in extra_cols:
            if extra in subset.columns:
                row[extra] = subset[extra].iloc[0]
        rows.append(row)
    rows.sort(key=lambda item: (item.get('mean_cascade_score', 0.0), item.get('mean_stage1_reference_gap_gain_Hz', 0.0)), reverse=True)
    return rows


def compute_gate_metrics(df: pd.DataFrame, top_k: int, pred_col: str) -> Dict[str, object]:
    ranked = ranked_frame(df, pred_col).head(min(top_k, len(df))).copy()
    return {
        'rows_total': int(len(df)),
        'rows_contact_gate': int(df['contact_gate'].sum()),
        'rows_positive_gate': int(df['positive_gate'].sum()),
        'rows_reg_positive_gate': int(df['reg_positive_gate'].sum()),
        'rows_cascade_gate': int(df['cascade_gate'].sum()),
        'contact_gate_rate': float(df['contact_gate'].mean()),
        'positive_gate_rate': float(df['positive_gate'].mean()),
        'reg_positive_gate_rate': float(df['reg_positive_gate'].mean()),
        'cascade_gate_rate': float(df['cascade_gate'].mean()),
        'top_k': int(len(ranked)),
        'top_k_gate_count': int(ranked['cascade_gate'].sum()),
        'top_k_strong_positive_count': int((ranked['stage1_reference_candidate_tier'].astype(str) == 'strong_positive').sum()),
        'top_k_weak_positive_count': int((ranked['stage1_reference_candidate_tier'].astype(str) == 'weak_positive').sum()),
        'objective': str(df[GENERIC_OBJECTIVE_NAME_COLUMN].iloc[0]) if len(df) else '',
    }


def main() -> None:
    args = parse_args()
    runtime = resolve_runtime_config(args)
    objective = get_objective(runtime['objective_name'])
    policy = load_scoring_policy(args) if args.policy_json else {}
    settings = resolve_scoring_settings(args, policy=policy)
    df = pd.read_csv(runtime['dataset'])
    if df.empty:
        raise RuntimeError(f'Empty dataset: {runtime["dataset"]}')

    df = df.copy()
    df['contact_prob'] = predict_classifier_rows(df, runtime['contact_run_root'], str(runtime['contact_split']))
    df['positive_prob'] = predict_classifier_rows(df, runtime['positive_run_root'], str(runtime['positive_split']))
    reg_predictions = predict_regressor(df, runtime['reg_run_root'], str(runtime['reg_split']), objective_name=objective.name)
    df, pred_col = attach_objective_predictions(df, objective.name, reg_predictions)
    df = assign_scores(df, settings, pred_col)
    if pred_col == 'surrogate_pred_gap34_gain_Hz':
        df['surrogate_pred_gap34_gain_Hz'] = df[pred_col]

    run_dir = DEFAULT_OUT_ROOT / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    family_rows = build_group_summary(df, 'shape_family', ['stage1_reference_candidate_tier'], pred_col)
    tier_rows = build_group_summary(df, 'stage1_reference_candidate_tier', [], pred_col)
    top_rows = ranked_frame(df, pred_col).head(min(int(runtime['top_k']), len(df))).copy()
    metrics = compute_gate_metrics(df, int(runtime['top_k']), pred_col)
    config = {
        'dataset': str(runtime['dataset']),
        'contact_run_root': str(runtime['contact_run_root']),
        'contact_split': runtime['contact_split'],
        'positive_run_root': str(runtime['positive_run_root']),
        'positive_split': runtime['positive_split'],
        'reg_run_root': str(runtime['reg_run_root']),
        'reg_split': runtime['reg_split'],
        'objective': objective.name,
        'objective_metric_column': objective.metric_column,
        'prediction_column': pred_col,
        'contact_threshold': settings['contact_threshold'],
        'positive_threshold': settings['positive_threshold'],
        'contact_weight': settings['contact_weight'],
        'positive_weight': settings['positive_weight'],
        'reg_min': settings['reg_min'],
        'calibration_json': settings['calibration_json'],
        'calibration_version': settings['calibration_version'],
        'policy_json': runtime['policy_json'],
        'top_k': int(runtime['top_k']),
        'base_model_version': 'v7_seed_discovery',
        'score_definition': f'stage1-aware seed discovery: calibrated cascade score with model scores first, stage1 baseline as tie-breaker, surrogate objective={objective.metric_column} for annotation',
    }

    df.to_csv(run_dir / 'seed_discovery_predictions.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(run_dir / 'seed_discovery_family_summary.csv', list(family_rows[0].keys()) if family_rows else ['shape_family'], family_rows)
    save_csv_rows(run_dir / 'seed_discovery_tier_summary.csv', list(tier_rows[0].keys()) if tier_rows else ['stage1_reference_candidate_tier'], tier_rows)
    save_csv_rows(run_dir / 'seed_discovery_top_candidates.csv', list(top_rows.columns), top_rows.to_dict(orient='records'))
    save_json(run_dir / 'seed_discovery_metrics.json', metrics)
    save_json(run_dir / 'seed_discovery_config.json', config)

    print('[DONE] stage1-aware seed discovery scoring complete')
    print(f'[RUN] {run_dir}')
    print(f'[OBJECTIVE] {objective.name} prediction_column={pred_col}')
    print(f"[SETTINGS] contact_threshold={settings['contact_threshold']:.6g} positive_threshold={settings['positive_threshold']:.6g} contact_weight={settings['contact_weight']:.3f} positive_weight={settings['positive_weight']:.3f}")
    print(f"[GATE] kept={metrics['rows_cascade_gate']}/{metrics['rows_total']} rate={metrics['cascade_gate_rate']:.4f}")


if __name__ == '__main__':
    main()
