from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml_common import DEFAULT_OUT_ROOT, save_csv_rows, save_json
from normalization_metrics import attach_normalization_columns
from objective_registry import (
    GENERIC_OBJECTIVE_PREDICTION_COLUMN,
    GENERIC_OBJECTIVE_NAME_COLUMN,
)
from analysis.objectives import analysis_metric_column, analysis_objective_names
from run_seed_discovery_scoring_v7 import ranked_frame

DEFAULT_PREDICTIONS = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'seed_discovery_predictions.csv'
DEFAULT_VALIDATION = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v10' / 'stage4_validation_results.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'robustness_analysis_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run normalization and robustness analysis on existing prediction/validation results.')
    parser.add_argument('--predictions-csv', type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument('--validation-csv', type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument('--material-scenario', action='append', default=[], help='Optional material scenario as label=path/to/validation_results.csv')
    parser.add_argument('--objective', default='gap34_gain_Hz', choices=sorted(analysis_objective_names()))
    parser.add_argument('--top-k', type=int, default=6)
    parser.add_argument('--validation-positive-threshold', type=float, default=0.0)
    parser.add_argument('--contact-threshold-delta', type=float, default=0.05)
    parser.add_argument('--positive-threshold-delta', type=float, default=0.05)
    parser.add_argument('--contact-weight-delta', type=float, default=0.10)
    parser.add_argument('--reg-min-delta', type=float, default=2.5)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def infer_prediction_column(df: pd.DataFrame) -> str:
    if GENERIC_OBJECTIVE_PREDICTION_COLUMN in df.columns and len(df):
        col = str(df[GENERIC_OBJECTIVE_PREDICTION_COLUMN].iloc[0])
        if col and col in df.columns:
            return col
    if 'surrogate_pred_gap34_gain_Hz' in df.columns:
        return 'surrogate_pred_gap34_gain_Hz'
    raise KeyError('Unable to infer prediction column from predictions csv.')


def detect_validation_key_column(df: pd.DataFrame) -> str:
    if 'source_sample_id' in df.columns:
        series = df['source_sample_id'].astype(str).str.strip()
        if series.ne('').any():
            return 'source_sample_id'
    if 'sample_id' in df.columns:
        return 'sample_id'
    raise KeyError('Validation file must contain source_sample_id or sample_id.')


def normalize_predictions(df: pd.DataFrame, prediction_col: str) -> pd.DataFrame:
    out = attach_normalization_columns(df, prediction_columns=[prediction_col], reference_candidates=('stage1_reference_gap_Hz', 'ref_gap34_Hz'))
    if GENERIC_OBJECTIVE_NAME_COLUMN not in out.columns:
        out[GENERIC_OBJECTIVE_NAME_COLUMN] = 'gap34_gain_Hz'
    return out


def normalize_validation(df: pd.DataFrame) -> pd.DataFrame:
    return attach_normalization_columns(df, prediction_columns=['surrogate_pred_gap34_gain_Hz'], reference_candidates=('ref_gap34_Hz', 'stage1_reference_gap_Hz'))


def build_threshold_scenarios(df: pd.DataFrame, args: argparse.Namespace, pred_col: str) -> List[Dict[str, Any]]:
    base_contact_threshold = float(pd.to_numeric(df.get('contact_threshold'), errors='coerce').dropna().iloc[0]) if 'contact_threshold' in df.columns and pd.to_numeric(df.get('contact_threshold'), errors='coerce').notna().any() else 0.5
    base_positive_threshold = float(pd.to_numeric(df.get('positive_threshold'), errors='coerce').dropna().iloc[0]) if 'positive_threshold' in df.columns and pd.to_numeric(df.get('positive_threshold'), errors='coerce').notna().any() else 0.5
    base_contact_weight = float(pd.to_numeric(df.get('contact_weight'), errors='coerce').dropna().iloc[0]) if 'contact_weight' in df.columns and pd.to_numeric(df.get('contact_weight'), errors='coerce').notna().any() else 0.7
    base_reg_min = 0.0
    if 'reg_positive_gate' in df.columns and pred_col in df.columns:
        gated = df[df['reg_positive_gate'].astype(bool)]
        if not gated.empty:
            base_reg_min = float(pd.to_numeric(gated[pred_col], errors='coerce').min())

    scenarios = [
        {'scenario_name': 'baseline', 'contact_threshold': base_contact_threshold, 'positive_threshold': base_positive_threshold, 'contact_weight': base_contact_weight, 'positive_weight': 1.0 - base_contact_weight, 'reg_min': base_reg_min},
        {'scenario_name': 'contact_threshold_minus', 'contact_threshold': clamp(base_contact_threshold - args.contact_threshold_delta, 0.0, 1.0), 'positive_threshold': base_positive_threshold, 'contact_weight': base_contact_weight, 'positive_weight': 1.0 - base_contact_weight, 'reg_min': base_reg_min},
        {'scenario_name': 'contact_threshold_plus', 'contact_threshold': clamp(base_contact_threshold + args.contact_threshold_delta, 0.0, 1.0), 'positive_threshold': base_positive_threshold, 'contact_weight': base_contact_weight, 'positive_weight': 1.0 - base_contact_weight, 'reg_min': base_reg_min},
        {'scenario_name': 'positive_threshold_minus', 'contact_threshold': base_contact_threshold, 'positive_threshold': clamp(base_positive_threshold - args.positive_threshold_delta, 0.0, 1.0), 'contact_weight': base_contact_weight, 'positive_weight': 1.0 - base_contact_weight, 'reg_min': base_reg_min},
        {'scenario_name': 'positive_threshold_plus', 'contact_threshold': base_contact_threshold, 'positive_threshold': clamp(base_positive_threshold + args.positive_threshold_delta, 0.0, 1.0), 'contact_weight': base_contact_weight, 'positive_weight': 1.0 - base_contact_weight, 'reg_min': base_reg_min},
        {'scenario_name': 'contact_weight_minus', 'contact_threshold': base_contact_threshold, 'positive_threshold': base_positive_threshold, 'contact_weight': clamp(base_contact_weight - args.contact_weight_delta, 0.0, 1.0), 'positive_weight': 1.0 - clamp(base_contact_weight - args.contact_weight_delta, 0.0, 1.0), 'reg_min': base_reg_min},
        {'scenario_name': 'contact_weight_plus', 'contact_threshold': base_contact_threshold, 'positive_threshold': base_positive_threshold, 'contact_weight': clamp(base_contact_weight + args.contact_weight_delta, 0.0, 1.0), 'positive_weight': 1.0 - clamp(base_contact_weight + args.contact_weight_delta, 0.0, 1.0), 'reg_min': base_reg_min},
        {'scenario_name': 'reg_min_plus', 'contact_threshold': base_contact_threshold, 'positive_threshold': base_positive_threshold, 'contact_weight': base_contact_weight, 'positive_weight': 1.0 - base_contact_weight, 'reg_min': base_reg_min + args.reg_min_delta},
    ]
    return scenarios


def apply_threshold_scenario(df: pd.DataFrame, scenario: Dict[str, Any], pred_col: str) -> pd.DataFrame:
    out = df.copy()
    out['contact_threshold'] = float(scenario['contact_threshold'])
    out['positive_threshold'] = float(scenario['positive_threshold'])
    out['contact_weight'] = float(scenario['contact_weight'])
    out['positive_weight'] = float(scenario['positive_weight'])
    out['contact_gate'] = pd.to_numeric(out['contact_prob'], errors='coerce').fillna(0.0) >= out['contact_threshold']
    out['positive_gate'] = pd.to_numeric(out['positive_prob'], errors='coerce').fillna(0.0) >= out['positive_threshold']
    out['reg_positive_gate'] = pd.to_numeric(out[pred_col], errors='coerce') > float(scenario['reg_min'])
    out['cascade_gate'] = out['contact_gate'] & out['positive_gate']
    out['class_score'] = pd.to_numeric(out['contact_prob'], errors='coerce').fillna(0.0) * pd.to_numeric(out['positive_prob'], errors='coerce').fillna(0.0)
    out['cascade_score'] = out['contact_weight'] * pd.to_numeric(out['contact_prob'], errors='coerce').fillna(0.0) + out['positive_weight'] * pd.to_numeric(out['positive_prob'], errors='coerce').fillna(0.0)
    return out


def rank_map_from_frame(df: pd.DataFrame, pred_col: str) -> Dict[str, int]:
    ranked = ranked_frame(df, pred_col).copy()
    return {str(sample_id): idx for idx, sample_id in enumerate(ranked['sample_id'].astype(str), start=1)}


def topk_ids_from_frame(df: pd.DataFrame, pred_col: str, top_k: int) -> List[str]:
    ranked = ranked_frame(df, pred_col).head(min(top_k, len(df)))
    return ranked['sample_id'].astype(str).tolist()


def build_validation_lookup(df: pd.DataFrame, objective_col: str) -> Dict[str, Dict[str, Any]]:
    key_col = detect_validation_key_column(df)
    out: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        key = str(row[key_col])
        if not key:
            continue
        out[key] = {
            'objective_value': float(pd.to_numeric(pd.Series([row.get(objective_col)]), errors='coerce').iloc[0]) if objective_col in df.columns else math.nan,
            'solve_success': bool(row.get('solve_success', False)),
            'contact_valid': bool(row.get('contact_valid', False)),
            'shape_family': str(row.get('shape_family', '')),
            'point_id': str(row.get('point_id', '')),
        }
    return out


def compute_selection_validation_metrics(selected_ids: List[str], validation_lookup: Dict[str, Dict[str, Any]], positive_threshold: float) -> Dict[str, Any]:
    matched = [validation_lookup[item] for item in selected_ids if item in validation_lookup]
    matched_values = [item.get('objective_value', math.nan) for item in matched]
    positive_hits = [value for value in matched_values if np.isfinite(value) and value > positive_threshold]
    return {
        'validated_selected_count': int(len(matched)),
        'validated_coverage_rate': float(len(matched) / len(selected_ids)) if selected_ids else math.nan,
        'validated_positive_hit_count': int(len(positive_hits)),
        'validated_positive_hit_rate': float(len(positive_hits) / len(matched)) if matched else math.nan,
    }


def spearman_rank_corr(rank_map_a: Dict[str, int], rank_map_b: Dict[str, int]) -> float:
    shared = sorted(set(rank_map_a) & set(rank_map_b))
    if len(shared) < 2:
        return math.nan
    a = pd.Series([rank_map_a[item] for item in shared])
    b = pd.Series([rank_map_b[item] for item in shared])
    return float(a.corr(b, method='spearman'))


def jaccard_similarity(items_a: Iterable[str], items_b: Iterable[str]) -> float:
    a = set(items_a)
    b = set(items_b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return float(len(a & b) / len(a | b))


def summarize_threshold_scenarios(pred_df: pd.DataFrame, val_lookup: Dict[str, Dict[str, Any]], pred_col: str, args: argparse.Namespace) -> Tuple[pd.DataFrame, pd.DataFrame]:
    scenarios = build_threshold_scenarios(pred_df, args, pred_col)
    baseline_rank_map: Dict[str, int] | None = None
    baseline_topk: List[str] = []
    rows: List[Dict[str, Any]] = []
    pairwise_rows: List[Dict[str, Any]] = []
    scenario_cache: Dict[str, Dict[str, Any]] = {}

    for scenario in scenarios:
        scenario_df = apply_threshold_scenario(pred_df, scenario, pred_col)
        rank_map = rank_map_from_frame(scenario_df, pred_col)
        topk_ids = topk_ids_from_frame(scenario_df, pred_col, args.top_k)
        gate_count = int(pd.Series(list(rank_map.values())).count())
        row = {
            'scenario_name': scenario['scenario_name'],
            **scenario,
            'rows_total': int(len(scenario_df)),
            'rows_cascade_gate': int(scenario_df['cascade_gate'].sum()),
            'rows_contact_gate': int(scenario_df['contact_gate'].sum()),
            'rows_positive_gate': int(scenario_df['positive_gate'].sum()),
            'rows_reg_positive_gate': int(scenario_df['reg_positive_gate'].sum()),
            'top_k': int(min(args.top_k, len(scenario_df))),
            'top_k_ids': '|'.join(topk_ids),
        }
        row.update(compute_selection_validation_metrics(topk_ids, val_lookup, args.validation_positive_threshold))
        rows.append(row)
        scenario_cache[scenario['scenario_name']] = {'rank_map': rank_map, 'topk_ids': topk_ids}
        if scenario['scenario_name'] == 'baseline':
            baseline_rank_map = rank_map
            baseline_topk = topk_ids

    if baseline_rank_map is None:
        raise RuntimeError('Threshold scenarios must include baseline.')

    for row in rows:
        name = row['scenario_name']
        rank_map = scenario_cache[name]['rank_map']
        topk_ids = scenario_cache[name]['topk_ids']
        row['rank_spearman_vs_baseline'] = spearman_rank_corr(baseline_rank_map, rank_map)
        row['topk_jaccard_vs_baseline'] = jaccard_similarity(baseline_topk, topk_ids)

    scenario_names = [row['scenario_name'] for row in rows]
    for i, name_a in enumerate(scenario_names):
        for name_b in scenario_names[i + 1:]:
            rank_a = scenario_cache[name_a]['rank_map']
            rank_b = scenario_cache[name_b]['rank_map']
            topk_a = scenario_cache[name_a]['topk_ids']
            topk_b = scenario_cache[name_b]['topk_ids']
            pairwise_rows.append({
                'scenario_a': name_a,
                'scenario_b': name_b,
                'shared_rank_count': int(len(set(rank_a) & set(rank_b))),
                'rank_spearman': spearman_rank_corr(rank_a, rank_b),
                'topk_jaccard': jaccard_similarity(topk_a, topk_b),
                'topk_overlap_count': int(len(set(topk_a) & set(topk_b))),
            })

    return pd.DataFrame(rows), pd.DataFrame(pairwise_rows)


def parse_material_scenarios(args: argparse.Namespace) -> List[Tuple[str, Path]]:
    scenarios: List[Tuple[str, Path]] = [('baseline_validation', args.validation_csv)]
    for item in args.material_scenario:
        if '=' not in item:
            raise ValueError('material-scenario must use label=path format.')
        label, path_text = item.split('=', 1)
        scenarios.append((label.strip(), Path(path_text.strip())))
    return scenarios


def summarize_material_scenarios(args: argparse.Namespace, objective_col: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    scenario_specs = parse_material_scenarios(args)
    scenario_frames: Dict[str, pd.DataFrame] = {}
    summary_rows: List[Dict[str, Any]] = []
    pairwise_rows: List[Dict[str, Any]] = []

    for label, path in scenario_specs:
        csv_path = path if path.is_absolute() else ROOT / path
        frame = normalize_validation(load_csv(csv_path))
        key_col = detect_validation_key_column(frame)
        if objective_col not in frame.columns:
            raise KeyError(f'Material scenario {label} is missing objective column {objective_col}.')
        frame['_scenario_objective_value'] = pd.to_numeric(frame[objective_col], errors='coerce')
        ranked = frame.sort_values(['_scenario_objective_value'], ascending=[False]).copy()
        topk = ranked.head(min(args.top_k, len(ranked)))
        positive_hits = topk['_scenario_objective_value'].gt(args.validation_positive_threshold).fillna(False)
        summary_rows.append({
            'scenario_name': label,
            'csv_path': str(csv_path),
            'rows_total': int(len(frame)),
            'solve_success_count': int(pd.to_numeric(frame.get('solve_success'), errors='coerce').fillna(0).astype(int).sum()) if 'solve_success' in frame.columns else 0,
            'objective_mean': float(frame['_scenario_objective_value'].mean()),
            'objective_median': float(frame['_scenario_objective_value'].median()),
            'objective_best': float(frame['_scenario_objective_value'].max()),
            'top_k': int(len(topk)),
            'top_k_positive_hit_count': int(positive_hits.sum()),
            'top_k_positive_hit_rate': float(positive_hits.mean()) if len(topk) else math.nan,
            'top_k_ids': '|'.join(topk[key_col].astype(str).tolist()),
        })
        scenario_frames[label] = frame[[key_col, '_scenario_objective_value']].copy().rename(columns={key_col: '_scenario_key'})

    labels = [row['scenario_name'] for row in summary_rows]
    for i, label_a in enumerate(labels):
        frame_a = scenario_frames[label_a]
        rank_a = {str(key): idx for idx, key in enumerate(frame_a.sort_values(['_scenario_objective_value'], ascending=[False])['_scenario_key'].astype(str), start=1)}
        topk_a = summary_rows[i]['top_k_ids'].split('|') if summary_rows[i]['top_k_ids'] else []
        for label_b in labels[i + 1:]:
            frame_b = scenario_frames[label_b]
            rank_b = {str(key): idx for idx, key in enumerate(frame_b.sort_values(['_scenario_objective_value'], ascending=[False])['_scenario_key'].astype(str), start=1)}
            topk_b = next(row['top_k_ids'].split('|') if row['top_k_ids'] else [] for row in summary_rows if row['scenario_name'] == label_b)
            pairwise_rows.append({
                'scenario_a': label_a,
                'scenario_b': label_b,
                'shared_rank_count': int(len(set(rank_a) & set(rank_b))),
                'rank_spearman': spearman_rank_corr(rank_a, rank_b),
                'topk_jaccard': jaccard_similarity(topk_a, topk_b),
                'topk_overlap_count': int(len(set(topk_a) & set(topk_b))),
            })

    return pd.DataFrame(summary_rows), pd.DataFrame(pairwise_rows)


def plot_threshold_overview(df: pd.DataFrame, out_path: Path) -> None:
    if df.empty:
        return
    work = df.copy()
    x = np.arange(len(work))
    labels = work['scenario_name'].astype(str).tolist()
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    axes[0].plot(x, work['rank_spearman_vs_baseline'], marker='o')
    axes[0].set_ylabel('Rank Spearman')
    axes[0].set_title('Threshold Perturbation Stability')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(x, work['topk_jaccard_vs_baseline'], marker='o', color='tab:orange')
    axes[1].set_ylabel('Top-k Jaccard')
    axes[1].grid(True, alpha=0.3)

    axes[2].bar(x, work['validated_positive_hit_rate'], color='tab:green')
    axes[2].set_ylabel('Validation Hit Rate')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels, rotation=30, ha='right')
    axes[2].grid(True, axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def plot_material_overview(df: pd.DataFrame, out_path: Path) -> None:
    if df.empty:
        return
    x = np.arange(len(df))
    labels = df['scenario_name'].astype(str).tolist()
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    axes[0].bar(x, df['objective_mean'], color='tab:blue')
    axes[0].set_ylabel('Mean Objective')
    axes[0].set_title('Material Scenario Objective Stability')
    axes[0].grid(True, axis='y', alpha=0.3)

    axes[1].bar(x, df['top_k_positive_hit_rate'], color='tab:red')
    axes[1].set_ylabel('Top-k Positive Rate')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=30, ha='right')
    axes[1].grid(True, axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    predictions_csv = args.predictions_csv if args.predictions_csv.is_absolute() else ROOT / args.predictions_csv
    validation_csv = args.validation_csv if args.validation_csv.is_absolute() else ROOT / args.validation_csv

    pred_raw = load_csv(predictions_csv)
    pred_col = infer_prediction_column(pred_raw)
    pred_df = normalize_predictions(pred_raw, pred_col)
    pred_df.to_csv(out_dir / 'normalized_seed_discovery_predictions.csv', index=False, encoding='utf-8-sig')

    val_df = normalize_validation(load_csv(validation_csv))
    val_df.to_csv(out_dir / 'normalized_validation_results.csv', index=False, encoding='utf-8-sig')

    objective_col = analysis_metric_column(args.objective)
    if objective_col not in val_df.columns:
        raise KeyError(f'Objective column {objective_col} not found in validation results.')
    validation_lookup = build_validation_lookup(val_df, objective_col)

    threshold_summary, threshold_pairwise = summarize_threshold_scenarios(pred_df, validation_lookup, pred_col, args)
    threshold_summary.to_csv(out_dir / 'threshold_scenario_summary.csv', index=False, encoding='utf-8-sig')
    threshold_pairwise.to_csv(out_dir / 'threshold_pairwise_stability.csv', index=False, encoding='utf-8-sig')
    plot_threshold_overview(threshold_summary, out_dir / 'threshold_stability_overview.png')

    material_summary, material_pairwise = summarize_material_scenarios(args, objective_col)
    material_summary.to_csv(out_dir / 'material_scenario_summary.csv', index=False, encoding='utf-8-sig')
    material_pairwise.to_csv(out_dir / 'material_pairwise_stability.csv', index=False, encoding='utf-8-sig')
    plot_material_overview(material_summary, out_dir / 'material_stability_overview.png')

    summary = {
        'predictions_csv': str(predictions_csv),
        'validation_csv': str(validation_csv),
        'objective': args.objective,
        'objective_column': objective_col,
        'prediction_column': pred_col,
        'top_k': args.top_k,
        'validation_positive_threshold': args.validation_positive_threshold,
        'threshold_scenarios': int(len(threshold_summary)),
        'material_scenarios': int(len(material_summary)),
    }
    save_json(out_dir / 'robustness_analysis_summary.json', summary)

    print('[DONE] robustness analysis complete')
    print(f'[OUT] {out_dir}')
    print(f'[OBJECTIVE] {args.objective} -> {objective_col}')


if __name__ == '__main__':
    main()

