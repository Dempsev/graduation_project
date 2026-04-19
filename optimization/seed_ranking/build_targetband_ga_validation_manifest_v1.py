from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


DEFAULT_GA_CSV = ROOT / 'data' / 'ml_runs' / 'targetband_local_ga_v1' / 'band180_220_center_probe' / 'targetband_ga_candidate_manifest_v1.csv'
DEFAULT_OUT_DIR = ROOT / 'data' / 'ml_runs' / 'targetband_local_ga_v1' / 'band180_220_center_probe' / 'validation_manifest_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a compact COMSOL-ready validation manifest from target-band GA candidates.')
    parser.add_argument('--ga-csv', type=Path, default=DEFAULT_GA_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--total-k', type=int, default=6)
    parser.add_argument('--per-shape-k', type=int, default=2)
    return parser.parse_args()


def rank_candidates(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        [
            'fitness',
            'targetband_score',
            'target_gap_cover_ratio_pred',
            'target_open_prob',
            'contact_prob',
            'target_gap_overlap_pred_Hz',
            'distance_from_base',
        ],
        ascending=[False, False, False, False, False, False, True],
    ).copy()


def ensure_stage4_compat_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    defaults: Dict[str, object] = {
        'positive_prob': pd.to_numeric(out.get('target_open_prob'), errors='coerce').fillna(0.0) if 'target_open_prob' in out.columns else 0.0,
        'surrogate_pred_gap34_gain_Hz': 0.0,
        'class_score': pd.to_numeric(out.get('target_open_prob'), errors='coerce').fillna(0.0) if 'target_open_prob' in out.columns else 0.0,
        'cascade_score': pd.to_numeric(out.get('targetband_score'), errors='coerce').fillna(0.0) if 'targetband_score' in out.columns else 0.0,
        'positive_gate': out.get('target_open_gate', False),
        'reg_positive_gate': out.get('target_open_gate', False),
        'cascade_gate': out.get('targetband_gate', False),
        'rank_cascade': pd.NA,
        'rank_surrogate': pd.NA,
    }
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default
    return out


def select_rows(df: pd.DataFrame, total_k: int, per_shape_k: int) -> pd.DataFrame:
    ranked = rank_candidates(df)
    selected_rows: List[Dict[str, object]] = []
    shape_col = 'ga_seed_shape_id' if 'ga_seed_shape_id' in ranked.columns else 'shape_id'
    for _, subset in ranked.groupby(shape_col, sort=False):
        selected_rows.extend(subset.head(max(1, int(per_shape_k))).to_dict(orient='records'))
    selected = rank_candidates(pd.DataFrame(selected_rows)).head(max(1, int(total_k))).copy()
    if selected.empty:
        raise RuntimeError('No target-band validation rows selected.')
    return selected


def build_selection_label(df: pd.DataFrame, total_k: int, per_shape_k: int) -> str:
    band_low = float(pd.to_numeric(df['target_band_low_Hz'], errors='coerce').dropna().iloc[0]) if 'target_band_low_Hz' in df.columns else 0.0
    band_high = float(pd.to_numeric(df['target_band_high_Hz'], errors='coerce').dropna().iloc[0]) if 'target_band_high_Hz' in df.columns else 0.0
    return f'targetband_{int(round(band_low))}_{int(round(band_high))}_top_{int(total_k)}_per_shape_{int(per_shape_k)}'


def main() -> None:
    args = parse_args()
    ga_csv = args.ga_csv if args.ga_csv.is_absolute() else ROOT / args.ga_csv
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir

    if not ga_csv.exists():
        raise FileNotFoundError(ga_csv)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ga_csv)
    if df.empty:
        raise RuntimeError('Target-band GA candidate manifest is empty.')

    selected = ensure_stage4_compat_columns(select_rows(df, args.total_k, args.per_shape_k))
    selected['validation_id'] = [f'targetband_val{i:03d}' for i in range(1, len(selected) + 1)]
    selected['selection_source'] = 'targetband_parametric_ga_v1'
    selected['selection_label'] = build_selection_label(selected, args.total_k, args.per_shape_k)
    selected['rank_within_source'] = range(1, len(selected) + 1)

    manifest_path = out_dir / 'targetband_ga_validation_manifest_v1.csv'
    summary_path = out_dir / 'targetband_ga_validation_manifest_summary.json'
    selected.to_csv(manifest_path, index=False, encoding='utf-8-sig')

    summary = {
        'ga_csv': str(ga_csv),
        'manifest_rows': int(len(selected)),
        'total_k': int(args.total_k),
        'per_shape_k': int(args.per_shape_k),
        'unique_shapes': int(selected['shape_id'].astype(str).nunique()),
        'unique_points': int(selected['point_id'].astype(str).nunique()),
        'band_low_Hz': float(pd.to_numeric(selected['target_band_low_Hz'], errors='coerce').dropna().iloc[0]) if 'target_band_low_Hz' in selected.columns else 0.0,
        'band_high_Hz': float(pd.to_numeric(selected['target_band_high_Hz'], errors='coerce').dropna().iloc[0]) if 'target_band_high_Hz' in selected.columns else 0.0,
        'mean_fitness': float(pd.to_numeric(selected['fitness'], errors='coerce').mean()),
        'mean_targetband_score': float(pd.to_numeric(selected['targetband_score'], errors='coerce').mean()),
        'mean_target_cover_ratio_pred': float(pd.to_numeric(selected['target_gap_cover_ratio_pred'], errors='coerce').mean()),
        'mean_target_overlap_pred_Hz': float(pd.to_numeric(selected['target_gap_overlap_pred_Hz'], errors='coerce').mean()),
    }
    summary_path.write_text(__import__('json').dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    print('[DONE] target-band GA validation manifest built')
    print(f'[OUT] {manifest_path}')
    print(f'[SUMMARY] total={len(selected)} unique_shapes={selected["shape_id"].astype(str).nunique()} unique_points={selected["point_id"].astype(str).nunique()}')


if __name__ == '__main__':
    main()
