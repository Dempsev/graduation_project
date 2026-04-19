from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_TRAINING = ROOT / 'stage3_training'
if str(STAGE3_TRAINING) not in sys.path:
    sys.path.insert(0, str(STAGE3_TRAINING))

from prediction_targetband_param_v1.models.inference import build_targetband_prediction_frame
from shared.objectives.targetband import derive_band_tag
from stage3_training.ml_common import save_csv_rows, save_json
from stage3_training.run_seed_discovery_scoring_v7 import predict_classifier_rows, resolve_path


DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_optimization_v1' / 'candidate_pool_optimization_v1.csv'
DEFAULT_CONTACT_RUN = ROOT / 'data' / 'ml_runs' / 'mlp_contact_valid_parametric_seed_discovery_v7_full'
DEFAULT_CLASSIFIER_RUN = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cls_dense_family' / 'stratified_group_kfold'
DEFAULT_REGRESSOR_RUN = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cover_dense_family' / 'stratified_group_kfold'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'ml_runs'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Score optimization candidates under a target-band condition.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--classifier-run-root', type=Path, default=DEFAULT_CLASSIFIER_RUN)
    parser.add_argument('--regressor-run-root', type=Path, default=DEFAULT_REGRESSOR_RUN)
    parser.add_argument('--band-low', type=float, default=180.0)
    parser.add_argument('--band-high', type=float, default=220.0)
    parser.add_argument('--band-tag', default='')
    parser.add_argument('--contact-threshold', type=float, default=0.50)
    parser.add_argument('--open-threshold', type=float, default=0.50)
    parser.add_argument('--top-k', type=int, default=20)
    parser.add_argument('--run-name', default='targetband_seed_scoring_v1')
    return parser.parse_args()


def _clip_stage1_gain(df: pd.DataFrame) -> np.ndarray:
    gain = pd.to_numeric(df.get('stage1_reference_gap_gain_Hz'), errors='coerce').fillna(0.0).to_numpy(dtype=float)
    return np.clip(gain, 0.0, 20.0) / 20.0


def assign_targetband_scores(df: pd.DataFrame, contact_threshold: float, open_threshold: float) -> pd.DataFrame:
    out = df.copy()
    out['contact_gate'] = out['contact_prob'] >= float(contact_threshold)
    out['target_open_gate'] = out['target_open_prob'] >= float(open_threshold)
    out['targetband_gate'] = out['contact_gate'] & out['target_open_gate']
    out['stage1_gain_prior'] = _clip_stage1_gain(out)
    out['targetband_score'] = (
        0.30 * out['contact_prob'].to_numpy(dtype=float)
        + 0.45 * out['target_open_prob'].to_numpy(dtype=float)
        + 0.20 * out['target_gap_cover_ratio_pred'].to_numpy(dtype=float)
        + 0.05 * out['stage1_gain_prior'].to_numpy(dtype=float)
    )
    return out


def ranked_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        [
            'targetband_gate',
            'targetband_score',
            'target_gap_cover_ratio_pred',
            'target_open_prob',
            'contact_prob',
            'target_gap_overlap_pred_Hz',
            'stage1_reference_gap_gain_Hz',
        ],
        ascending=[False, False, False, False, False, False, False],
    ).copy()


def build_family_summary(df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for family, subset in df.groupby('shape_family'):
        rows.append(
            {
                'shape_family': str(family),
                'rows': int(len(subset)),
                'gate_rate': float(subset['targetband_gate'].mean()),
                'mean_targetband_score': float(subset['targetband_score'].mean()),
                'mean_contact_prob': float(subset['contact_prob'].mean()),
                'mean_target_open_prob': float(subset['target_open_prob'].mean()),
                'mean_target_cover_ratio_pred': float(subset['target_gap_cover_ratio_pred'].mean()),
                'mean_target_overlap_pred_Hz': float(subset['target_gap_overlap_pred_Hz'].mean()),
                'mean_stage1_reference_gap_gain_Hz': float(pd.to_numeric(subset['stage1_reference_gap_gain_Hz'], errors='coerce').fillna(0.0).mean()),
            }
        )
    rows.sort(key=lambda item: item['mean_targetband_score'], reverse=True)
    return rows


def main() -> None:
    args = parse_args()
    dataset = resolve_path(args.dataset)
    if dataset is None or not dataset.exists():
        raise FileNotFoundError(dataset)

    df = pd.read_csv(dataset)
    if df.empty:
        raise RuntimeError(f'Empty dataset: {dataset}')

    band_tag = args.band_tag.strip() or derive_band_tag(args.band_low, args.band_high)
    run_dir = DEFAULT_OUT_ROOT / args.run_name / band_tag
    run_dir.mkdir(parents=True, exist_ok=True)

    scored = build_targetband_prediction_frame(
        df,
        args.band_low,
        args.band_high,
        args.classifier_run_root,
        args.regressor_run_root,
        band_tag=band_tag,
    )
    scored['contact_prob'] = predict_classifier_rows(scored, resolve_path(args.contact_run_root), str(args.contact_split))
    scored = assign_targetband_scores(scored, args.contact_threshold, args.open_threshold)

    ranked = ranked_frame(scored)
    top_rows = ranked.head(min(int(args.top_k), len(ranked))).copy()
    family_rows = build_family_summary(scored)
    metrics = {
        'rows_total': int(len(scored)),
        'band_low_Hz': float(args.band_low),
        'band_high_Hz': float(args.band_high),
        'band_tag': band_tag,
        'contact_threshold': float(args.contact_threshold),
        'open_threshold': float(args.open_threshold),
        'rows_contact_gate': int(scored['contact_gate'].sum()),
        'rows_target_open_gate': int(scored['target_open_gate'].sum()),
        'rows_targetband_gate': int(scored['targetband_gate'].sum()),
        'targetband_gate_rate': float(scored['targetband_gate'].mean()),
        'top_k': int(len(top_rows)),
        'top_k_gate_count': int(top_rows['targetband_gate'].sum()),
        'top_k_best_target_overlap_pred_Hz': float(top_rows['target_gap_overlap_pred_Hz'].max()) if len(top_rows) else 0.0,
        'top_k_best_target_cover_ratio_pred': float(top_rows['target_gap_cover_ratio_pred'].max()) if len(top_rows) else 0.0,
    }
    config = {
        'dataset': str(dataset),
        'contact_run_root': str(args.contact_run_root),
        'contact_split': str(args.contact_split),
        'classifier_run_root': str(args.classifier_run_root),
        'regressor_run_root': str(args.regressor_run_root),
        'band_low_Hz': float(args.band_low),
        'band_high_Hz': float(args.band_high),
        'band_tag': band_tag,
        'score_definition': '0.30*contact_prob + 0.45*target_open_prob + 0.20*target_cover_ratio_pred + 0.05*stage1_gain_prior, with contact/open gates ranked first',
        'notes': [
            'This is the first target-band optimization scoring route.',
            'It treats target-band open probability and target-band cover ratio as the conditional objective.',
            'The current output is intended for seed ranking and shortlist generation before local refinement.',
        ],
    }

    ranked.to_csv(run_dir / 'targetband_seed_predictions.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(run_dir / 'targetband_seed_top_candidates.csv', list(top_rows.columns), top_rows.to_dict(orient='records'))
    save_csv_rows(run_dir / 'targetband_seed_family_summary.csv', list(family_rows[0].keys()) if family_rows else ['shape_family'], family_rows)
    save_json(run_dir / 'targetband_seed_metrics.json', metrics)
    save_json(run_dir / 'targetband_seed_config.json', config)

    print('[DONE] target-band seed scoring complete')
    print(f'[RUN] {run_dir}')
    print(f'[BAND] {band_tag} [{args.band_low:.1f}, {args.band_high:.1f}] Hz')
    print(f'[TOP] best_overlap_pred_Hz={metrics["top_k_best_target_overlap_pred_Hz"]:.4f} best_cover_ratio={metrics["top_k_best_target_cover_ratio_pred"]:.4f}')


if __name__ == '__main__':
    main()
