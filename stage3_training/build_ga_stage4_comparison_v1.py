from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import ROOT, save_json

DEFAULT_SEED_VALIDATION_CSV = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v10' / 'stage4_validation_results.csv'
DEFAULT_GA_VALIDATION_CSV = ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_ga_v1' / 'stage4_validation_results.csv'
DEFAULT_OUT_DIR = ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1' / 'real_validation_comparison_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a real Stage4 comparison table for seed-only v10 versus GA local tuning.')
    parser.add_argument('--seed-validation-csv', type=Path, default=DEFAULT_SEED_VALIDATION_CSV)
    parser.add_argument('--ga-validation-csv', type=Path, default=DEFAULT_GA_VALIDATION_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--seed-selection-source', default='seed_only_refined')
    parser.add_argument('--ga-selection-source', default='parametric_ga_v1')
    return parser.parse_args()


def ensure_required_columns(df: pd.DataFrame, defaults: Dict[str, object]) -> pd.DataFrame:
    out = df.copy()
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default
    return out


def prepare_validation_frame(df: pd.DataFrame) -> pd.DataFrame:
    work = ensure_required_columns(
        df,
        {
            'validation_id': '',
            'sample_id': '',
            'selection_source': '',
            'shape_id': '',
            'seed_shape_id': '',
            'shape_family': '',
            'point_id': '',
            'contact_valid': 0,
            'solve_success': 0,
            'gap34_gain_Hz': float('nan'),
        },
    )
    work['gap34_gain_Hz'] = pd.to_numeric(work['gap34_gain_Hz'], errors='coerce')
    for col in ['contact_valid', 'solve_success']:
        work[col] = pd.to_numeric(work[col], errors='coerce').fillna(0).astype(int)
    for col in ['validation_id', 'sample_id', 'selection_source', 'shape_id', 'seed_shape_id', 'shape_family', 'point_id']:
        work[col] = work[col].astype(str)
    return work


def summarize_subset(subset: pd.DataFrame, prefix: str) -> Dict[str, object]:
    gains = pd.to_numeric(subset['gap34_gain_Hz'], errors='coerce')
    best_idx = gains.idxmax() if gains.notna().any() else subset.index[0]
    best_row = subset.loc[best_idx]
    positive_mask = gains.gt(0).fillna(False)
    return {
        f'{prefix}_rows': int(len(subset)),
        f'{prefix}_solve_success_count': int(subset['solve_success'].sum()),
        f'{prefix}_contact_valid_count': int(subset['contact_valid'].sum()),
        f'{prefix}_positive_gain_count': int(positive_mask.sum()),
        f'{prefix}_solve_success_rate': float(subset['solve_success'].mean()) if len(subset) else 0.0,
        f'{prefix}_contact_valid_rate': float(subset['contact_valid'].mean()) if len(subset) else 0.0,
        f'{prefix}_positive_gain_rate': float(positive_mask.mean()) if len(subset) else 0.0,
        f'{prefix}_mean_gap34_gain_Hz': float(gains.mean()) if gains.notna().any() else float('nan'),
        f'{prefix}_median_gap34_gain_Hz': float(gains.median()) if gains.notna().any() else float('nan'),
        f'{prefix}_best_gap34_gain_Hz': float(gains.loc[best_idx]) if pd.notna(gains.loc[best_idx]) else float('nan'),
        f'{prefix}_best_validation_id': str(best_row['validation_id']),
        f'{prefix}_best_sample_id': str(best_row['sample_id']),
        f'{prefix}_validation_ids': '|'.join(subset['validation_id'].astype(str).tolist()),
    }


def build_seed_summary(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for (shape_id, point_id), subset in seed_df.groupby(['shape_id', 'point_id'], dropna=False, sort=True):
        row = {
            'comparison_shape_id': str(shape_id),
            'point_id': str(point_id),
            'seed_shape_family': str(subset['shape_family'].iloc[0]),
        }
        row.update(summarize_subset(subset, 'seed'))
        rows.append(row)
    return pd.DataFrame(rows)


def build_ga_summary(ga_df: pd.DataFrame) -> pd.DataFrame:
    work = ga_df.copy()
    work['comparison_shape_id'] = work['seed_shape_id'].where(work['seed_shape_id'].str.len() > 0, work['shape_id'])
    rows: List[Dict[str, object]] = []
    for (shape_id, point_id), subset in work.groupby(['comparison_shape_id', 'point_id'], dropna=False, sort=True):
        row = {
            'comparison_shape_id': str(shape_id),
            'point_id': str(point_id),
            'ga_shape_family': str(subset['shape_family'].iloc[0]),
            'ga_shape_ids': '|'.join(sorted(subset['shape_id'].astype(str).unique().tolist())),
        }
        row.update(summarize_subset(subset, 'ga'))
        rows.append(row)
    return pd.DataFrame(rows)


def build_detail_rows(ga_df: pd.DataFrame, seed_summary: pd.DataFrame) -> pd.DataFrame:
    work = ga_df.copy()
    work['comparison_shape_id'] = work['seed_shape_id'].where(work['seed_shape_id'].str.len() > 0, work['shape_id'])
    detail = work.merge(seed_summary, on=['comparison_shape_id', 'point_id'], how='left', suffixes=('', '_seed'))
    detail['delta_vs_seed_best_gap34_gain_Hz'] = pd.to_numeric(detail['gap34_gain_Hz'], errors='coerce') - pd.to_numeric(detail['seed_best_gap34_gain_Hz'], errors='coerce')
    detail['delta_vs_seed_mean_gap34_gain_Hz'] = pd.to_numeric(detail['gap34_gain_Hz'], errors='coerce') - pd.to_numeric(detail['seed_mean_gap34_gain_Hz'], errors='coerce')
    return detail.sort_values(['comparison_shape_id', 'point_id', 'gap34_gain_Hz'], ascending=[True, True, False]).copy()


def build_comparison(seed_df: pd.DataFrame, ga_df: pd.DataFrame) -> pd.DataFrame:
    seed_summary = build_seed_summary(seed_df)
    ga_summary = build_ga_summary(ga_df)
    comparison = ga_summary.merge(seed_summary, on=['comparison_shape_id', 'point_id'], how='left')
    comparison['delta_best_gap34_gain_Hz'] = pd.to_numeric(comparison['ga_best_gap34_gain_Hz'], errors='coerce') - pd.to_numeric(comparison['seed_best_gap34_gain_Hz'], errors='coerce')
    comparison['delta_mean_gap34_gain_Hz'] = pd.to_numeric(comparison['ga_mean_gap34_gain_Hz'], errors='coerce') - pd.to_numeric(comparison['seed_mean_gap34_gain_Hz'], errors='coerce')
    comparison['ga_beats_seed_best'] = comparison['delta_best_gap34_gain_Hz'].fillna(float('-inf')) > 0
    comparison['ga_beats_seed_mean'] = comparison['delta_mean_gap34_gain_Hz'].fillna(float('-inf')) > 0
    comparison['seed_baseline_available'] = comparison['seed_rows'].fillna(0).astype(int) > 0
    return comparison.sort_values(['seed_baseline_available', 'delta_best_gap34_gain_Hz', 'ga_best_gap34_gain_Hz'], ascending=[False, False, False]).copy()


def build_summary_payload(comparison: pd.DataFrame, seed_df: pd.DataFrame, ga_df: pd.DataFrame) -> Dict[str, object]:
    matched = comparison[comparison['seed_baseline_available'] == True].copy()
    return {
        'seed_rows_total': int(len(seed_df)),
        'ga_rows_total': int(len(ga_df)),
        'shapes_compared': int(len(comparison)),
        'shapes_with_seed_baseline': int(len(matched)),
        'shapes_missing_seed_baseline': int(len(comparison) - len(matched)),
        'improved_vs_seed_best_count': int(matched['ga_beats_seed_best'].sum()) if len(matched) else 0,
        'improved_vs_seed_mean_count': int(matched['ga_beats_seed_mean'].sum()) if len(matched) else 0,
        'mean_delta_best_gap34_gain_Hz': float(matched['delta_best_gap34_gain_Hz'].mean()) if len(matched) else 0.0,
        'mean_delta_mean_gap34_gain_Hz': float(matched['delta_mean_gap34_gain_Hz'].mean()) if len(matched) else 0.0,
        'best_delta_best_gap34_gain_Hz': float(matched['delta_best_gap34_gain_Hz'].max()) if len(matched) else 0.0,
    }


def main() -> None:
    args = parse_args()
    if not args.seed_validation_csv.exists():
        raise FileNotFoundError(args.seed_validation_csv)
    if not args.ga_validation_csv.exists():
        raise FileNotFoundError(args.ga_validation_csv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    seed_df = prepare_validation_frame(pd.read_csv(args.seed_validation_csv))
    ga_df = prepare_validation_frame(pd.read_csv(args.ga_validation_csv))
    seed_df = seed_df[seed_df['selection_source'] == args.seed_selection_source].copy()
    ga_df = ga_df[ga_df['selection_source'] == args.ga_selection_source].copy()
    if seed_df.empty:
        raise RuntimeError(f'No seed validation rows found for selection_source={args.seed_selection_source}')
    if ga_df.empty:
        raise RuntimeError(f'No GA validation rows found for selection_source={args.ga_selection_source}')

    seed_summary = build_seed_summary(seed_df)
    comparison = build_comparison(seed_df, ga_df)
    detail = build_detail_rows(ga_df, seed_summary)
    summary = build_summary_payload(comparison, seed_df, ga_df)
    summary.update({
        'seed_validation_csv': str(args.seed_validation_csv),
        'ga_validation_csv': str(args.ga_validation_csv),
        'seed_selection_source': args.seed_selection_source,
        'ga_selection_source': args.ga_selection_source,
    })

    comparison_path = args.out_dir / 'ga_stage4_seed_vs_ga_comparison_v1.csv'
    detail_path = args.out_dir / 'ga_stage4_seed_vs_ga_detail_v1.csv'
    summary_path = args.out_dir / 'ga_stage4_seed_vs_ga_summary_v1.json'
    comparison.to_csv(comparison_path, index=False, encoding='utf-8-sig')
    detail.to_csv(detail_path, index=False, encoding='utf-8-sig')
    save_json(summary_path, summary)

    print('[DONE] GA stage4 comparison built')
    print(f'[OUT] {comparison_path}')
    print(f'[OUT] {detail_path}')
    print(f'[OUT] {summary_path}')
    print(
        f"[SUMMARY] compared={summary['shapes_compared']} "
        f"matched_seed={summary['shapes_with_seed_baseline']} "
        f"improved_best={summary['improved_vs_seed_best_count']}"
    )


if __name__ == '__main__':
    main()
