from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from objective_registry import (
    DEFAULT_OBJECTIVE_NAME,
    GENERIC_OBJECTIVE_NAME_COLUMN,
    GENERIC_OBJECTIVE_PREDICTION_COLUMN,
    GENERIC_PREDICTION_COLUMN,
    get_objective,
)
from analysis.objectives import analysis_metric_column, analysis_objective_names
from ml_common import DEFAULT_OUT_ROOT, save_csv_rows, save_json
from policy_resolution import merge_policy_layers
from run_seed_discovery_scoring_v7 import (
    assign_scores,
    attach_objective_predictions,
    build_group_summary,
    compute_gate_metrics,
    predict_classifier_rows,
    predict_regressor,
    ranked_frame,
    resolve_scoring_settings,
)

DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'experiment_scaffold_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run configurable family/point/objective comparison experiments.')
    parser.add_argument('--config', type=Path, required=True, help='JSON config under configs/experiments/ or any readable path.')
    parser.add_argument('--out-root', type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
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


def ensure_bool_column(df: pd.DataFrame, column: str, default_value: bool = False) -> pd.Series:
    if column not in df.columns:
        return pd.Series([default_value] * len(df), index=df.index, dtype=bool)
    raw = df[column]
    if raw.dtype == bool:
        return raw.fillna(default_value)
    return pd.to_numeric(raw, errors='coerce').fillna(1.0 if default_value else 0.0).astype(int).astype(bool)


def ensure_stage1_tier_rank(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    tier_map = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    if 'stage1_reference_candidate_tier' not in out.columns:
        out['stage1_reference_candidate_tier'] = ''
    out['stage1_candidate_tier_rank'] = out['stage1_reference_candidate_tier'].astype(str).map(tier_map).fillna(-1).astype(int)
    return out


def filter_frame(df: pd.DataFrame, experiment_cfg: Dict[str, Any]) -> pd.DataFrame:
    out = df.copy()
    family_list = {str(item) for item in experiment_cfg.get('shape_family_list', []) if str(item).strip()}
    shape_list = {str(item) for item in experiment_cfg.get('shape_id_list', []) if str(item).strip()}
    point_list = {str(item) for item in experiment_cfg.get('point_id_list', []) if str(item).strip()}

    if family_list:
        out = out[out['shape_family'].astype(str).isin(family_list)].copy()
    if shape_list:
        out = out[out['shape_id'].astype(str).isin(shape_list)].copy()
    if point_list:
        out = out[out['point_id'].astype(str).isin(point_list)].copy()
    return out


def make_scoring_namespace(source_csv: Path, experiment_name: str, objective_name: str, scoring_cfg: Dict[str, Any], suite_defaults: Dict[str, Any]) -> SimpleNamespace:
    merged = merge_policy_layers(suite_defaults, scoring_cfg)
    return SimpleNamespace(
        dataset=source_csv,
        contact_run_root=resolve_path(merged.get('contact_run_root')),
        contact_split=str(merged.get('contact_split', 'shape_family')),
        positive_run_root=resolve_path(merged.get('positive_run_root')),
        positive_split=str(merged.get('positive_split', 'shape_family')),
        reg_run_root=resolve_path(merged.get('reg_run_root')),
        reg_split=str(merged.get('reg_split', 'shape_family')),
        objective=objective_name,
        run_name=f'experiment_scaffold__{experiment_name}',
        contact_threshold=float(merged.get('contact_threshold', 0.50)),
        positive_threshold=float(merged.get('positive_threshold', 0.50)),
        contact_weight=float(merged.get('contact_weight', 0.70)),
        positive_weight=float(merged.get('positive_weight', 0.30)),
        calibration_json=resolve_path(merged.get('calibration_json')),
        reg_min=float(merged.get('reg_min', 0.0)),
        top_k=int(merged.get('top_k', 12)),
    )


def score_with_surrogate(df: pd.DataFrame, objective_name: str, scoring_cfg: Dict[str, Any], suite_defaults: Dict[str, Any], experiment_name: str, source_csv: Path) -> tuple[pd.DataFrame, str, Dict[str, Any]]:
    if df.empty:
        raise RuntimeError('Filtered source frame is empty before surrogate scoring.')
    args = make_scoring_namespace(source_csv, experiment_name, objective_name, scoring_cfg, suite_defaults)
    settings = resolve_scoring_settings(args)
    out = df.copy()
    out['contact_prob'] = predict_classifier_rows(out, args.contact_run_root, args.contact_split)
    out['positive_prob'] = predict_classifier_rows(out, args.positive_run_root, args.positive_split)
    reg_predictions = predict_regressor(out, args.reg_run_root, args.reg_split, objective_name=objective_name)
    out, pred_col = attach_objective_predictions(out, objective_name, reg_predictions)
    out = assign_scores(out, settings, pred_col)
    out = ensure_stage1_tier_rank(out)
    return out, pred_col, settings


def score_with_observed_objective(df: pd.DataFrame, objective_name: str, scoring_cfg: Dict[str, Any]) -> tuple[pd.DataFrame, str, Dict[str, Any]]:
    if df.empty:
        raise RuntimeError('Filtered source frame is empty before observed-objective scoring.')
    metric_col = analysis_metric_column(objective_name)
    if metric_col not in df.columns:
        raise KeyError(f'Observed-objective mode requires column "{metric_col}" in the source csv.')

    positive_threshold = float(scoring_cfg.get('positive_threshold', 0.0))
    out = df.copy()
    out[metric_col] = pd.to_numeric(out[metric_col], errors='coerce')
    out[GENERIC_OBJECTIVE_NAME_COLUMN] = str(objective_name)
    out[GENERIC_OBJECTIVE_PREDICTION_COLUMN] = metric_col
    out[GENERIC_PREDICTION_COLUMN] = out[metric_col]

    if 'contact_prob' not in out.columns:
        if 'solve_success' in out.columns:
            out['contact_prob'] = ensure_bool_column(out, 'solve_success').astype(float)
        elif 'contact_valid' in out.columns:
            out['contact_prob'] = ensure_bool_column(out, 'contact_valid').astype(float)
        else:
            out['contact_prob'] = out[metric_col].notna().astype(float)
    else:
        out['contact_prob'] = pd.to_numeric(out['contact_prob'], errors='coerce').fillna(0.0)

    if 'positive_prob' not in out.columns:
        out['positive_prob'] = (out[metric_col] > positive_threshold).astype(float)
    else:
        out['positive_prob'] = pd.to_numeric(out['positive_prob'], errors='coerce').fillna(0.0)

    out['contact_gate'] = out['contact_prob'] >= float(scoring_cfg.get('contact_threshold', 0.5))
    out['positive_gate'] = out[metric_col] > positive_threshold
    out['reg_positive_gate'] = out['positive_gate']
    out['cascade_gate'] = out['contact_gate'] & out['positive_gate']
    out['class_score'] = out['positive_prob']
    out['cascade_score'] = out[metric_col]
    out = ensure_stage1_tier_rank(out)
    settings = {
        'mode': 'observed_objective',
        'positive_threshold': positive_threshold,
        'contact_threshold': float(scoring_cfg.get('contact_threshold', 0.5)),
    }
    return out, metric_col, settings


def can_take(row: pd.Series, shape_counts: Dict[str, int], family_counts: Dict[str, int], max_per_shape: int, max_per_family: int) -> bool:
    shape_id = str(row.get('shape_id', ''))
    family_id = str(row.get('shape_family', ''))
    if max_per_shape > 0 and shape_counts.get(shape_id, 0) >= max_per_shape:
        return False
    if max_per_family > 0 and family_counts.get(family_id, 0) >= max_per_family:
        return False
    return True


def register_selection(row: pd.Series, bucket: str, sample_ids: set[str], shape_counts: Dict[str, int], family_counts: Dict[str, int], point_counts: Dict[str, int]) -> Dict[str, Any]:
    item = row.to_dict()
    item['selection_bucket'] = bucket
    sample_id = str(row['sample_id'])
    shape_id = str(row.get('shape_id', ''))
    family_id = str(row.get('shape_family', ''))
    point_id = str(row.get('point_id', ''))
    sample_ids.add(sample_id)
    shape_counts[shape_id] = shape_counts.get(shape_id, 0) + 1
    family_counts[family_id] = family_counts.get(family_id, 0) + 1
    point_counts[point_id] = point_counts.get(point_id, 0) + 1
    return item


def sort_for_selection(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    work = ensure_stage1_tier_rank(df)
    if 'stage1_reference_gap_gain_Hz' not in work.columns:
        work['stage1_reference_gap_gain_Hz'] = np.nan
    return work.sort_values(
        ['cascade_gate', 'cascade_score', 'contact_prob', 'positive_prob', 'stage1_candidate_tier_rank', pred_col, 'stage1_reference_gap_gain_Hz'],
        ascending=[False, False, False, False, False, False, False],
    ).copy()


def select_top_k(df: pd.DataFrame, pred_col: str, rule_cfg: Dict[str, Any]) -> pd.DataFrame:
    limit = int(rule_cfg.get('k', rule_cfg.get('top_k', 0)))
    if limit <= 0:
        raise ValueError('top_k selection requires k > 0')
    max_per_shape = int(rule_cfg.get('max_per_shape', 0))
    max_per_family = int(rule_cfg.get('max_per_family', 0))

    rows: List[Dict[str, Any]] = []
    shape_counts: Dict[str, int] = {}
    family_counts: Dict[str, int] = {}
    point_counts: Dict[str, int] = {}
    sample_ids: set[str] = set()

    for _, row in sort_for_selection(df, pred_col).iterrows():
        if not can_take(row, shape_counts, family_counts, max_per_shape, max_per_family):
            continue
        rows.append(register_selection(row, 'top_k', sample_ids, shape_counts, family_counts, point_counts))
        if len(rows) >= limit:
            break
    return pd.DataFrame(rows)


def take_rows(sorted_df: pd.DataFrame, limit: int, bucket: str, sample_ids: set[str], shape_counts: Dict[str, int], family_counts: Dict[str, int], point_counts: Dict[str, int], max_per_shape: int, max_per_family: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if limit <= 0:
        return rows
    for _, row in sorted_df.iterrows():
        sample_id = str(row['sample_id'])
        if sample_id in sample_ids:
            continue
        if not can_take(row, shape_counts, family_counts, max_per_shape, max_per_family):
            continue
        rows.append(register_selection(row, bucket, sample_ids, shape_counts, family_counts, point_counts))
        if len(rows) >= limit:
            break
    return rows


def sort_diversity(df: pd.DataFrame, pred_col: str, point_counts: Dict[str, int], family_counts: Dict[str, int]) -> pd.DataFrame:
    work = sort_for_selection(df, pred_col)
    work['diversity_new_point'] = work['point_id'].astype(str).map(lambda x: 1 if point_counts.get(x, 0) == 0 else 0)
    work['diversity_new_family'] = work['shape_family'].astype(str).map(lambda x: 1 if family_counts.get(x, 0) == 0 else 0)
    return work.sort_values(
        ['diversity_new_point', 'diversity_new_family', 'cascade_gate', 'cascade_score', 'contact_prob', 'stage1_candidate_tier_rank', pred_col],
        ascending=[False, False, False, False, False, False, False],
    ).copy()


def take_diversity_rows(df: pd.DataFrame, pred_col: str, limit: int, sample_ids: set[str], shape_counts: Dict[str, int], family_counts: Dict[str, int], point_counts: Dict[str, int], max_per_shape: int, max_per_family: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if limit <= 0:
        return rows
    while len(rows) < limit:
        remaining = df[~df['sample_id'].astype(str).isin(sample_ids)].copy()
        if remaining.empty:
            break
        sorted_df = sort_diversity(remaining, pred_col, point_counts, family_counts)
        picked = False
        for _, row in sorted_df.iterrows():
            if not can_take(row, shape_counts, family_counts, max_per_shape, max_per_family):
                continue
            rows.append(register_selection(row, 'diversity', sample_ids, shape_counts, family_counts, point_counts))
            picked = True
            break
        if not picked:
            break
    return rows


def select_primary_probe(df: pd.DataFrame, pred_col: str, rule_cfg: Dict[str, Any]) -> pd.DataFrame:
    work = ensure_stage1_tier_rank(df)
    if 'stage1_reference_candidate_tier' not in work.columns:
        work['stage1_reference_candidate_tier'] = ''
    work['selection_bucket'] = work['stage1_reference_candidate_tier'].astype(str).map(
        lambda item: 'primary' if item in {'strong_positive', 'weak_positive'} else ('probe' if item == 'neutral_or_baseline_like' else 'other')
    )

    sample_ids: set[str] = set()
    shape_counts: Dict[str, int] = {}
    family_counts: Dict[str, int] = {}
    point_counts: Dict[str, int] = {}
    max_per_shape = int(rule_cfg.get('max_per_shape', 0))
    max_per_family = int(rule_cfg.get('max_per_family', 0))

    selected_rows: List[Dict[str, Any]] = []
    selected_rows.extend(
        take_rows(
            sort_for_selection(work[work['selection_bucket'] == 'primary'], pred_col),
            int(rule_cfg.get('primary_k', 0)),
            'primary',
            sample_ids,
            shape_counts,
            family_counts,
            point_counts,
            max_per_shape,
            max_per_family,
        )
    )
    selected_rows.extend(
        take_rows(
            sort_for_selection(work[work['selection_bucket'] == 'probe'], pred_col),
            int(rule_cfg.get('probe_k', 0)),
            'probe',
            sample_ids,
            shape_counts,
            family_counts,
            point_counts,
            max_per_shape,
            max_per_family,
        )
    )
    selected_rows.extend(
        take_diversity_rows(
            work,
            pred_col,
            int(rule_cfg.get('diversity_k', 0)),
            sample_ids,
            shape_counts,
            family_counts,
            point_counts,
            max_per_shape,
            max_per_family,
        )
    )
    return pd.DataFrame(selected_rows)


def select_rows(df: pd.DataFrame, pred_col: str, rule_cfg: Dict[str, Any]) -> pd.DataFrame:
    rule_name = str(rule_cfg.get('rule', 'top_k'))
    if rule_name == 'top_k':
        selected = select_top_k(df, pred_col, rule_cfg)
    elif rule_name == 'primary_probe':
        selected = select_primary_probe(df, pred_col, rule_cfg)
    else:
        raise ValueError(f'Unsupported validation selection rule: {rule_name}')

    if selected.empty:
        return selected
    selected = selected.copy()
    selected['experiment_rank'] = np.arange(1, len(selected) + 1)
    selected['selection_rule'] = rule_name
    return selected


def summarize_selected(selected: pd.DataFrame, pred_col: str) -> Dict[str, Any]:
    if selected.empty:
        return {
            'selected_rows': 0,
            'selected_unique_shape_count': 0,
            'selected_unique_family_count': 0,
            'selected_unique_point_count': 0,
            'selected_mean_objective_value': np.nan,
            'selected_best_objective_value': np.nan,
        }
    values = pd.to_numeric(selected[pred_col], errors='coerce')
    return {
        'selected_rows': int(len(selected)),
        'selected_unique_shape_count': int(selected['shape_id'].astype(str).nunique()) if 'shape_id' in selected.columns else 0,
        'selected_unique_family_count': int(selected['shape_family'].astype(str).nunique()) if 'shape_family' in selected.columns else 0,
        'selected_unique_point_count': int(selected['point_id'].astype(str).nunique()) if 'point_id' in selected.columns else 0,
        'selected_mean_objective_value': float(values.mean()) if len(values) else np.nan,
        'selected_best_objective_value': float(values.max()) if len(values) else np.nan,
    }


def records_with_experiment_name(rows: Iterable[Dict[str, Any]], experiment_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item['experiment_name'] = experiment_name
        out.append(item)
    return out


def run_experiment(experiment_cfg: Dict[str, Any], suite_defaults: Dict[str, Any], suite_out_dir: Path) -> Dict[str, Any]:
    experiment_name = str(experiment_cfg['experiment_name'])
    source_csv = resolve_path(experiment_cfg.get('source_csv', suite_defaults.get('source_csv')))
    if source_csv is None:
        raise ValueError(f'Experiment {experiment_name} is missing source_csv.')
    source_df = pd.read_csv(source_csv)
    filtered = filter_frame(source_df, experiment_cfg)
    if filtered.empty:
        raise RuntimeError(f'Experiment {experiment_name} has no rows after family/shape/point filtering.')

    objective_name = str(experiment_cfg.get('objective_name', DEFAULT_OBJECTIVE_NAME))
    scoring_cfg = dict(suite_defaults.get('scoring_setting', {}))
    scoring_cfg.update(experiment_cfg.get('scoring_setting', {}))
    scoring_mode = str(scoring_cfg.get('mode', 'surrogate'))

    if scoring_mode == 'surrogate':
        scored, pred_col, scoring_settings = score_with_surrogate(filtered, objective_name, scoring_cfg, suite_defaults, experiment_name, source_csv)
    elif scoring_mode == 'observed_objective':
        scored, pred_col, scoring_settings = score_with_observed_objective(filtered, objective_name, scoring_cfg)
    else:
        raise ValueError(f'Unsupported scoring mode: {scoring_mode}')

    rule_cfg = dict(suite_defaults.get('validation_selection_rule', {}))
    rule_cfg.update(experiment_cfg.get('validation_selection_rule', {}))
    selected = select_rows(scored, pred_col, rule_cfg)

    family_rows = build_group_summary(scored, 'shape_family', ['stage1_reference_candidate_tier'], pred_col) if 'shape_family' in scored.columns else []
    point_rows = build_group_summary(scored, 'point_id', ['main_id'], pred_col) if 'point_id' in scored.columns else []
    shape_rows = build_group_summary(scored, 'shape_id', ['shape_family', 'shape_role'], pred_col) if 'shape_id' in scored.columns else []
    metric_top_k = int(rule_cfg.get('k', rule_cfg.get('primary_k', 0) + rule_cfg.get('probe_k', 0) + rule_cfg.get('diversity_k', 0) or 12))
    metrics = compute_gate_metrics(scored, metric_top_k, pred_col)
    selected_summary = summarize_selected(selected, pred_col)

    experiment_dir = suite_out_dir / experiment_name
    experiment_dir.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(experiment_dir / 'filtered_input.csv', index=False, encoding='utf-8-sig')
    scored.to_csv(experiment_dir / 'scored_candidates.csv', index=False, encoding='utf-8-sig')
    selected.to_csv(experiment_dir / 'selected_candidates.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(experiment_dir / 'family_summary.csv', list(family_rows[0].keys()) if family_rows else ['shape_family'], family_rows)
    save_csv_rows(experiment_dir / 'point_summary.csv', list(point_rows[0].keys()) if point_rows else ['point_id'], point_rows)
    save_csv_rows(experiment_dir / 'shape_summary.csv', list(shape_rows[0].keys()) if shape_rows else ['shape_id'], shape_rows)

    experiment_summary = {
        'experiment_name': experiment_name,
        'source_csv': str(source_csv),
        'objective_name': objective_name,
        'objective_metric_column': analysis_metric_column(objective_name),
        'prediction_column': pred_col,
        'scoring_mode': scoring_mode,
        'validation_selection_rule': str(rule_cfg.get('rule', 'top_k')),
        'rows_input': int(len(source_df)),
        'rows_filtered': int(len(filtered)),
        'filtered_unique_shape_count': int(filtered['shape_id'].astype(str).nunique()) if 'shape_id' in filtered.columns else 0,
        'filtered_unique_family_count': int(filtered['shape_family'].astype(str).nunique()) if 'shape_family' in filtered.columns else 0,
        'filtered_unique_point_count': int(filtered['point_id'].astype(str).nunique()) if 'point_id' in filtered.columns else 0,
        **metrics,
        **selected_summary,
        'shape_family_list': experiment_cfg.get('shape_family_list', []),
        'shape_id_list': experiment_cfg.get('shape_id_list', []),
        'point_id_list': experiment_cfg.get('point_id_list', []),
        'scoring_setting': scoring_settings,
        'validation_selection_rule_config': rule_cfg,
    }
    save_json(experiment_dir / 'experiment_summary.json', experiment_summary)

    return {
        'summary': experiment_summary,
        'family_rows': records_with_experiment_name(family_rows, experiment_name),
        'point_rows': records_with_experiment_name(point_rows, experiment_name),
        'shape_rows': records_with_experiment_name(shape_rows, experiment_name),
    }


def main() -> None:
    args = parse_args()
    config_path = resolve_path(args.config) if not args.config.is_absolute() else args.config
    config = load_json(config_path)
    suite_name = str(config.get('suite_name', config_path.stem))
    experiments = list(config.get('experiments', []))
    if not experiments:
        raise ValueError('Config must contain a non-empty experiments list.')

    suite_out_dir = args.out_root / suite_name
    suite_out_dir.mkdir(parents=True, exist_ok=True)

    suite_defaults = {
        'source_csv': config.get('source_csv', ''),
        'scoring_setting': config.get('scoring_setting', {}),
        'validation_selection_rule': config.get('validation_selection_rule', {}),
    }

    summary_rows: List[Dict[str, Any]] = []
    combined_family_rows: List[Dict[str, Any]] = []
    combined_point_rows: List[Dict[str, Any]] = []
    combined_shape_rows: List[Dict[str, Any]] = []

    for experiment_cfg in experiments:
        result = run_experiment(experiment_cfg, suite_defaults, suite_out_dir)
        summary_rows.append(result['summary'])
        combined_family_rows.extend(result['family_rows'])
        combined_point_rows.extend(result['point_rows'])
        combined_shape_rows.extend(result['shape_rows'])

    save_csv_rows(suite_out_dir / 'suite_summary.csv', list(summary_rows[0].keys()), summary_rows)
    save_json(suite_out_dir / 'suite_summary.json', {'suite_name': suite_name, 'config_path': str(config_path), 'experiments': summary_rows})
    save_csv_rows(suite_out_dir / 'combined_family_summary.csv', list(combined_family_rows[0].keys()) if combined_family_rows else ['experiment_name', 'shape_family'], combined_family_rows)
    save_csv_rows(suite_out_dir / 'combined_point_summary.csv', list(combined_point_rows[0].keys()) if combined_point_rows else ['experiment_name', 'point_id'], combined_point_rows)
    save_csv_rows(suite_out_dir / 'combined_shape_summary.csv', list(combined_shape_rows[0].keys()) if combined_shape_rows else ['experiment_name', 'shape_id'], combined_shape_rows)
    save_json(suite_out_dir / 'resolved_config.json', config)

    print('[DONE] experiment scaffold complete')
    print(f'[SUITE] {suite_name}')
    print(f'[OUT] {suite_out_dir}')
    print(f'[EXPERIMENTS] {len(summary_rows)}')


if __name__ == '__main__':
    main()
