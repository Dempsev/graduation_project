from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / 'data' / 'ml_runs' / 'seed_discovery_scoring_calibration_v1'
DEFAULT_TOP_K = 8
DEFAULT_RECALL_FLOOR = 0.60
DEFAULT_CONTACT_WEIGHT = 0.70
DEFAULT_POSITIVE_WEIGHT = 0.30

DEFAULT_SOURCES = [
    {
        'tag': 'v9',
        'scored_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v9' / 'seed_discovery_predictions.csv',
        'validation_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v9' / 'stage4_validation_results.csv',
    },
    {
        'tag': 'v10',
        'scored_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v10' / 'seed_discovery_predictions.csv',
        'validation_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v10' / 'stage4_validation_results.csv',
    },
]

OPTIONAL_V8_SOURCE = {
    'tag': 'v8',
    'scored_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_cascade_v8' / 'cascade_predictions.csv',
    'validation_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v8' / 'stage4_validation_results.csv',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Calibrate seed discovery thresholds from historical stage4 validation results.')
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--include-v8', action='store_true')
    parser.add_argument('--top-k', type=int, default=DEFAULT_TOP_K)
    parser.add_argument('--recall-floor', type=float, default=DEFAULT_RECALL_FLOOR)
    parser.add_argument('--default-contact-weight', type=float, default=DEFAULT_CONTACT_WEIGHT)
    parser.add_argument('--default-positive-weight', type=float, default=DEFAULT_POSITIVE_WEIGHT)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_source_rows(cfg: Dict[str, object]) -> pd.DataFrame:
    scored_csv = Path(cfg['scored_csv'])
    validation_csv = Path(cfg['validation_csv'])
    if not scored_csv.exists():
        raise FileNotFoundError(scored_csv)
    if not validation_csv.exists():
        raise FileNotFoundError(validation_csv)

    scored = pd.read_csv(scored_csv)
    validation = pd.read_csv(validation_csv)

    keep_cols = [
        'sample_id',
        'contact_prob',
        'positive_prob',
        'surrogate_pred_gap34_gain_Hz',
        'class_score',
        'cascade_score',
        'stage1_reference_candidate_tier',
        'point_id',
        'shape_id',
        'shape_family',
    ]
    available_cols = [col for col in keep_cols if col in scored.columns]
    scored = scored.loc[:, available_cols].copy()

    merged = validation.merge(scored, left_on='source_sample_id', right_on='sample_id', how='left', suffixes=('', '_scored'))
    for col in ['contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'class_score', 'cascade_score']:
        scored_col = f'{col}_scored'
        if scored_col in merged.columns:
            merged[col] = pd.to_numeric(merged[scored_col], errors='coerce').fillna(pd.to_numeric(merged.get(col), errors='coerce'))
    for col in ['stage1_reference_candidate_tier', 'point_id', 'shape_id', 'shape_family']:
        scored_col = f'{col}_scored'
        if scored_col in merged.columns:
            merged[col] = merged[scored_col].fillna(merged.get(col))

    merged['run_tag'] = str(cfg['tag'])
    merged['target_contact_valid'] = pd.to_numeric(merged['contact_valid'], errors='coerce').fillna(0).astype(int)
    merged['target_positive_gain'] = pd.to_numeric(merged['gap34_gain_Hz'], errors='coerce').gt(0).fillna(False).astype(int)
    merged['target_joint'] = ((merged['target_contact_valid'] == 1) & (merged['target_positive_gain'] == 1)).astype(int)
    return merged


def build_dataset(args: argparse.Namespace) -> Tuple[pd.DataFrame, List[Dict[str, object]]]:
    sources = list(DEFAULT_SOURCES)
    if args.include_v8:
        sources = [OPTIONAL_V8_SOURCE, *sources]

    frames: List[pd.DataFrame] = []
    source_rows: List[Dict[str, object]] = []
    for source in sources:
        frame = load_source_rows(source)
        frames.append(frame)
        source_rows.append({
            'tag': source['tag'],
            'scored_csv': str(source['scored_csv']),
            'validation_csv': str(source['validation_csv']),
            'rows': int(len(frame)),
            'joint_positive_rate': float(frame['target_joint'].mean()) if len(frame) else 0.0,
        })

    if not frames:
        raise RuntimeError('No calibration sources were loaded.')
    df = pd.concat(frames, ignore_index=True)
    for col in ['contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'gap34_gain_Hz']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df, source_rows


def gate_metrics(df: pd.DataFrame, contact_threshold: float, positive_threshold: float) -> Dict[str, object]:
    gated = (df['contact_prob'] >= contact_threshold) & (df['positive_prob'] >= positive_threshold)
    tp = int(((gated) & (df['target_joint'] == 1)).sum())
    fp = int(((gated) & (df['target_joint'] == 0)).sum())
    fn = int(((~gated) & (df['target_joint'] == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    gated_count = int(gated.sum())
    mean_gain = float(df.loc[gated, 'gap34_gain_Hz'].fillna(0.0).mean()) if gated_count else 0.0
    return {
        'contact_threshold': float(contact_threshold),
        'positive_threshold': float(positive_threshold),
        'gated_count': gated_count,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'mean_gain_Hz': float(mean_gain),
    }


def search_gate(df: pd.DataFrame, recall_floor: float) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    contact_grid = [0.0, 1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9]
    positive_grid = [0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.999]
    candidates: List[Dict[str, object]] = []
    best: Dict[str, object] | None = None
    best_key = None

    for contact_threshold in contact_grid:
        for positive_threshold in positive_grid:
            metrics = gate_metrics(df, contact_threshold, positive_threshold)
            candidates.append(metrics)
            key = (
                metrics['recall'] >= recall_floor,
                round(metrics['precision'], 6),
                round(metrics['f1'], 6),
                -int(metrics['gated_count']),
                round(metrics['recall'], 6),
                round(metrics['mean_gain_Hz'], 6),
            )
            if best is None or key > best_key:
                best = metrics
                best_key = key

    candidates.sort(
        key=lambda item: (
            item['recall'] >= recall_floor,
            item['precision'],
            item['f1'],
            -item['gated_count'],
            item['recall'],
            item['mean_gain_Hz'],
        ),
        reverse=True,
    )
    assert best is not None
    return best, candidates[:10]


def rank_metrics(df: pd.DataFrame, contact_weight: float, positive_weight: float, top_k: int) -> Dict[str, object]:
    total = contact_weight + positive_weight
    if total <= 0:
        raise ValueError('Weights must sum to a positive value.')
    cw = contact_weight / total
    pw = positive_weight / total
    ranked = df.assign(
        calibration_score=cw * df['contact_prob'].fillna(0.0) + pw * df['positive_prob'].fillna(0.0)
    ).sort_values(['calibration_score', 'surrogate_pred_gap34_gain_Hz'], ascending=[False, False]).head(min(top_k, len(df))).copy()
    return {
        'contact_weight': float(cw),
        'positive_weight': float(pw),
        'top_k': int(len(ranked)),
        'top_k_joint_hits': int(ranked['target_joint'].sum()),
        'top_k_mean_gain_Hz': float(ranked['gap34_gain_Hz'].fillna(0.0).mean()) if len(ranked) else 0.0,
        'top_k_mean_contact_prob': float(ranked['contact_prob'].fillna(0.0).mean()) if len(ranked) else 0.0,
    }


def search_weights(df: pd.DataFrame, top_k: int, default_contact_weight: float, default_positive_weight: float) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    default_total = default_contact_weight + default_positive_weight
    default_contact_ratio = (default_contact_weight / default_total) if default_total > 0 else DEFAULT_CONTACT_WEIGHT
    candidates: List[Dict[str, object]] = []
    best: Dict[str, object] | None = None
    best_key = None

    for contact_weight in np.linspace(0.0, 1.0, 21):
        positive_weight = 1.0 - float(contact_weight)
        metrics = rank_metrics(df, float(contact_weight), float(positive_weight), top_k)
        metrics['distance_to_default_contact_weight'] = abs(metrics['contact_weight'] - default_contact_ratio)
        candidates.append(metrics)
        key = (
            int(metrics['top_k_joint_hits']),
            round(metrics['top_k_mean_gain_Hz'], 6),
            round(-metrics['distance_to_default_contact_weight'], 6),
            round(metrics['top_k_mean_contact_prob'], 6),
        )
        if best is None or key > best_key:
            best = metrics
            best_key = key

    candidates.sort(
        key=lambda item: (
            item['top_k_joint_hits'],
            item['top_k_mean_gain_Hz'],
            -item['distance_to_default_contact_weight'],
            item['top_k_mean_contact_prob'],
        ),
        reverse=True,
    )
    assert best is not None
    return best, candidates[:10]


def build_summary(df: pd.DataFrame) -> Dict[str, object]:
    return {
        'rows_total': int(len(df)),
        'joint_positive_rows': int(df['target_joint'].sum()),
        'joint_positive_rate': float(df['target_joint'].mean()) if len(df) else 0.0,
        'contact_prob_min': float(df['contact_prob'].min()) if len(df) else 0.0,
        'contact_prob_max': float(df['contact_prob'].max()) if len(df) else 0.0,
        'positive_prob_min': float(df['positive_prob'].min()) if len(df) else 0.0,
        'positive_prob_max': float(df['positive_prob'].max()) if len(df) else 0.0,
    }


def main() -> None:
    args = parse_args()
    ensure_dir(args.out_dir)

    df, source_rows = build_dataset(args)
    dataset_summary = build_summary(df)
    best_gate, gate_top = search_gate(df, args.recall_floor)
    best_weight, weight_top = search_weights(df, args.top_k, args.default_contact_weight, args.default_positive_weight)

    recommended = {
        'contact_threshold': float(best_gate['contact_threshold']),
        'positive_threshold': float(best_gate['positive_threshold']),
        'contact_weight': float(best_weight['contact_weight']),
        'positive_weight': float(best_weight['positive_weight']),
        'reg_min': 0.0,
        'top_k': int(args.top_k),
        'recall_floor': float(args.recall_floor),
        'selection_target': 'contact_valid_and_positive_gap_gain',
        'source_tags': [item['tag'] for item in source_rows],
    }

    report = {
        'version': 'seed_discovery_scoring_calibration_v1',
        'dataset_summary': dataset_summary,
        'sources': source_rows,
        'recommended': recommended,
        'best_gate': best_gate,
        'best_weight': best_weight,
        'gate_search_top10': gate_top,
        'weight_search_top10': weight_top,
    }

    joined_csv = args.out_dir / 'calibration_joined_rows.csv'
    report_json = args.out_dir / 'calibration_report.json'
    recommended_json = args.out_dir / 'recommended_scoring_calibration.json'

    df.to_csv(joined_csv, index=False, encoding='utf-8-sig')
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    recommended_json.write_text(json.dumps({'recommended': recommended}, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] seed discovery scoring calibration complete')
    print(f'[OUT] {joined_csv}')
    print(f'[OUT] {report_json}')
    print(f'[OUT] {recommended_json}')
    print(f"[RECOMMENDED] contact_threshold={recommended['contact_threshold']:.6g} positive_threshold={recommended['positive_threshold']:.6g} contact_weight={recommended['contact_weight']:.3f} positive_weight={recommended['positive_weight']:.3f}")


if __name__ == '__main__':
    main()
