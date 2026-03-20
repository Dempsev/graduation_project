from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch

from ml_common import DEFAULT_OUT_ROOT, MLP, save_csv_rows, save_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v8' / 'candidate_pool_v8_seed_only_discovery' / 'candidate_pool_v8.csv'
DEFAULT_CONTACT_RUN = DEFAULT_OUT_ROOT / 'mlp_contact_valid_parametric_directional_v6_full'
DEFAULT_POSITIVE_RUN = DEFAULT_OUT_ROOT / 'mlp_is_positive_shape_parametric_directional_v6_full'
DEFAULT_REG_RUN = DEFAULT_OUT_ROOT / 'mlp_gap34_gain_surrogate_v6_full'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run v8 seed-only discovery cascade scoring.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--positive-run-root', type=Path, default=DEFAULT_POSITIVE_RUN)
    parser.add_argument('--positive-split', default='shape_family')
    parser.add_argument('--reg-run-root', type=Path, default=DEFAULT_REG_RUN)
    parser.add_argument('--reg-split', default='shape_family')
    parser.add_argument('--run-name', default='candidate_pool_cascade_v8')
    parser.add_argument('--contact-threshold', type=float, default=0.50)
    parser.add_argument('--positive-threshold', type=float, default=0.50)
    parser.add_argument('--reg-min', type=float, default=0.0)
    parser.add_argument('--top-k', type=int, default=12)
    return parser.parse_args()


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


def transform_with_checkpoint(frame: pd.DataFrame, feature_cols: List[str], checkpoint: Dict[str, object]) -> np.ndarray:
    x_raw = frame.loc[:, feature_cols].astype(float).to_numpy()
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


def predict_regressor(frame: pd.DataFrame, run_root: Path, split_name: str) -> np.ndarray:
    checkpoint = load_checkpoint(run_root, split_name)
    model = build_model(checkpoint)
    feature_cols = list(checkpoint['feature_cols'])
    x = transform_with_checkpoint(frame, feature_cols, checkpoint)
    with torch.no_grad():
        pred_scaled = model(torch.tensor(x, dtype=torch.float32)).cpu().numpy().reshape(-1)
    y_mean = float(checkpoint['y_mean'])
    y_std = float(checkpoint['y_std'])
    return pred_scaled * y_std + y_mean


def assign_thresholds(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    df = df.copy()
    df['stage1_reference_gap_gain_Hz'] = pd.to_numeric(df['stage1_reference_gap_gain_Hz'], errors='coerce').fillna(-1.0)
    df['stage1_reference_contact_length'] = pd.to_numeric(df['stage1_reference_contact_length'], errors='coerce').fillna(-1.0)
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    df['stage1_candidate_tier_rank'] = df['stage1_reference_candidate_tier'].astype(str).map(tier_map).fillna(-1).astype(int)
    df['contact_prob_bucket'] = np.round(df['contact_prob'], 4)
    df['positive_prob_bucket'] = np.round(df['positive_prob'], 4)
    df['contact_threshold'] = args.contact_threshold
    df['positive_threshold'] = args.positive_threshold
    df['contact_gate'] = df['contact_prob'] >= df['contact_threshold']
    df['positive_gate'] = df['positive_prob'] >= df['positive_threshold']
    df['reg_positive_gate'] = df['surrogate_pred_gap34_gain_Hz'] > args.reg_min
    df['cascade_gate'] = df['contact_gate'] & df['positive_gate']
    df['class_score'] = df['contact_prob'] * df['positive_prob']
    df['cascade_score'] = df['contact_prob']
    return df


def ranked_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ['cascade_gate', 'contact_prob_bucket', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', 'positive_prob_bucket', 'surrogate_pred_gap34_gain_Hz', 'stage1_reference_contact_length', 'contact_prob'],
        ascending=[False, False, False, False, False, False, False, False],
    ).copy()


def sort_for_cascade(df: pd.DataFrame) -> pd.DataFrame:
    return ranked_frame(df)


def sort_for_surrogate(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(['surrogate_pred_gap34_gain_Hz', 'contact_prob_bucket', 'stage1_candidate_tier_rank', 'stage1_reference_gap_gain_Hz', 'contact_prob'], ascending=[False, False, False, False, False]).copy()


def compute_gate_metrics(df: pd.DataFrame, top_k: int) -> Dict[str, object]:
    ranked = ranked_frame(df).head(min(top_k, len(df))).copy()
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
    }


def build_group_summary(df: pd.DataFrame, group_col: str, extra_cols: List[str]) -> List[Dict[str, object]]:
    rows = []
    for key, subset in df.groupby(group_col):
        row = {
            group_col: key,
            'rows': int(len(subset)),
            'contact_gate_rate': float(subset['contact_gate'].mean()),
            'positive_gate_rate': float(subset['positive_gate'].mean()),
            'cascade_gate_rate': float(subset['cascade_gate'].mean()),
            'mean_contact_prob': float(np.mean(subset['contact_prob'])),
            'mean_positive_prob': float(np.mean(subset['positive_prob'])),
            'mean_stage1_reference_gap_gain_Hz': float(np.mean(subset['stage1_reference_gap_gain_Hz'])),
            'mean_surrogate_pred_gap34_gain': float(np.mean(subset['surrogate_pred_gap34_gain_Hz'])),
            'mean_cascade_score': float(np.mean(subset['cascade_score'])),
        }
        for extra in extra_cols:
            if extra in subset.columns:
                row[extra] = subset[extra].iloc[0]
        rows.append(row)
    rows.sort(key=lambda item: (item.get('mean_cascade_score', 0.0), item.get('mean_stage1_reference_gap_gain_Hz', 0.0)), reverse=True)
    return rows


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.dataset)
    if df.empty:
        raise RuntimeError(f'Empty dataset: {args.dataset}')

    df = df.copy()
    df['contact_prob'] = predict_classifier_rows(df, args.contact_run_root, args.contact_split)
    df['positive_prob'] = predict_classifier_rows(df, args.positive_run_root, args.positive_split)
    df['surrogate_pred_gap34_gain_Hz'] = predict_regressor(df, args.reg_run_root, args.reg_split)
    df = assign_thresholds(df, args)

    run_dir = DEFAULT_OUT_ROOT / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    family_rows = build_group_summary(df, 'shape_family', ['stage1_reference_candidate_tier'])
    tier_rows = build_group_summary(df, 'stage1_reference_candidate_tier', [])
    top_rows = ranked_frame(df).head(min(args.top_k, len(df))).copy()
    metrics = compute_gate_metrics(df, args.top_k)
    config = {
        'dataset': str(args.dataset),
        'contact_run_root': str(args.contact_run_root),
        'contact_split': args.contact_split,
        'positive_run_root': str(args.positive_run_root),
        'positive_split': args.positive_split,
        'reg_run_root': str(args.reg_run_root),
        'reg_split': args.reg_split,
        'contact_threshold': args.contact_threshold,
        'positive_threshold': args.positive_threshold,
        'reg_min': args.reg_min,
        'top_k': args.top_k,
        'base_model_version': 'v6_directional',
        'score_definition': 'seed-only discovery; contact_prob primary, positive_prob secondary, stage1 baseline gain tertiary, surrogate for annotation',
    }

    df.to_csv(run_dir / 'cascade_predictions.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(run_dir / 'cascade_family_summary.csv', list(family_rows[0].keys()) if family_rows else ['shape_family'], family_rows)
    save_csv_rows(run_dir / 'cascade_stage1_tier_summary.csv', list(tier_rows[0].keys()) if tier_rows else ['stage1_reference_candidate_tier'], tier_rows)
    save_csv_rows(run_dir / 'cascade_top_candidates.csv', list(top_rows.columns), top_rows.to_dict(orient='records'))
    save_json(run_dir / 'cascade_metrics.json', metrics)
    save_json(run_dir / 'cascade_config.json', config)

    print('[DONE] cascade v8 scoring complete')
    print(f'[RUN] {run_dir}')
    print(f"[GATE] kept={metrics['rows_cascade_gate']}/{metrics['rows_total']} rate={metrics['cascade_gate_rate']:.4f}")


if __name__ == '__main__':
    main()
