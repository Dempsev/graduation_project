from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from objective_registry import DEFAULT_OBJECTIVE_NAME
from run_seed_discovery_scoring_v7 import (
    attach_objective_predictions,
    predict_classifier_rows,
    predict_regressor,
    resolve_path,
)
from run_optimization_seed_scoring_v1 import (
    DEFAULT_CONTACT_RUN,
    DEFAULT_OPTIMIZATION_HISTORY_GLOBS,
    DEFAULT_POSITIVE_RUN,
    DEFAULT_REG_RUN,
    DEFAULT_STAGE4_GLOB,
    assign_scores,
    collect_optimization_history,
    collect_stage4_history,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Score local optimization candidates with predictor + historical truth priors.')
    parser.add_argument('--input-csv', type=Path, required=True)
    parser.add_argument('--output-csv', type=Path, required=True)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--positive-run-root', type=Path, default=DEFAULT_POSITIVE_RUN)
    parser.add_argument('--positive-split', default='shape_family')
    parser.add_argument('--reg-run-root', type=Path, default=DEFAULT_REG_RUN)
    parser.add_argument('--reg-split', default='shape_family')
    parser.add_argument('--objective', default=DEFAULT_OBJECTIVE_NAME)
    parser.add_argument('--stage4-shape-summary-glob', default=DEFAULT_STAGE4_GLOB)
    parser.add_argument('--optimization-history-glob', action='append', default=list(DEFAULT_OPTIMIZATION_HISTORY_GLOBS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_csv = resolve_path(args.input_csv)
    output_csv = resolve_path(args.output_csv)
    if input_csv is None or not input_csv.exists():
        raise FileNotFoundError(input_csv)
    if output_csv is None:
        raise FileNotFoundError(args.output_csv)

    df = pd.read_csv(input_csv)
    if df.empty:
        raise RuntimeError(f'Empty candidate csv: {input_csv}')

    df = df.copy()
    df['contact_prob'] = predict_classifier_rows(df, resolve_path(args.contact_run_root), str(args.contact_split))
    df['positive_prob'] = predict_classifier_rows(df, resolve_path(args.positive_run_root), str(args.positive_split))
    reg_predictions = predict_regressor(df, resolve_path(args.reg_run_root), str(args.reg_split), objective_name=args.objective)
    df, pred_col = attach_objective_predictions(df, args.objective, reg_predictions)
    if pred_col == 'surrogate_pred_gap34_gain_Hz':
        df['surrogate_pred_gap34_gain_Hz'] = df[pred_col]

    stage4_history = collect_stage4_history(args.stage4_shape_summary_glob)
    optimization_history = collect_optimization_history(args.optimization_history_glob)
    df = df.merge(stage4_history, on='shape_id', how='left')
    df = df.merge(optimization_history, on='shape_id', how='left')
    df = assign_scores(df, pred_col)

    current_best = pd.to_numeric(df.get('current_best_gap34_gain_Hz'), errors='coerce').fillna(0.0)
    pred_gain = pd.to_numeric(df[pred_col], errors='coerce').fillna(0.0)
    pred_delta = np.clip(pred_gain - current_best, -10.0, 20.0)
    distance = pd.to_numeric(df.get('distance_from_center'), errors='coerce').fillna(0.0)
    direction_bonus = pd.to_numeric(df.get('direction_bonus'), errors='coerce').fillna(0.0)

    df['prescreen_score'] = (
        0.45 * pd.to_numeric(df['optimization_seed_score'], errors='coerce').fillna(0.0)
        + 0.20 * np.clip(pred_gain, 0.0, 60.0)
        + 0.20 * np.clip(pred_delta, 0.0, 20.0)
        + 5.0 * pd.to_numeric(df['contact_prob'], errors='coerce').fillna(0.0)
        + 4.0 * pd.to_numeric(df['positive_prob'], errors='coerce').fillna(0.0)
        + 1.5 * direction_bonus
        - 1.2 * np.clip(distance, 0.0, 1.0)
    )

    sort_cols = ['prescreen_score', 'optimization_seed_score', 'contact_prob', 'positive_prob', pred_col]
    df = df.sort_values(sort_cols, ascending=[False, False, False, False, False]).copy()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f'[DONE] scored {len(df)} optimization candidates -> {output_csv}')


if __name__ == '__main__':
    main()
