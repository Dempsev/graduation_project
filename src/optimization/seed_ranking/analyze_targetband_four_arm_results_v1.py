from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ABC_RESULTS = (
    ROOT
    / 'data'
    / 'comsol_batch'
    / 'stage4_validation_targetband_baseline_abc_v1'
    / 'stage4_validation_results.csv'
)
DEFAULT_LEGACY_C_RESULTS = (
    ROOT
    / 'data'
    / 'comsol_batch'
    / 'stage4_validation_targetband_top6_v1'
    / 'stage4_validation_results.csv'
)
DEFAULT_REAL_GA_HISTORY = (
    ROOT
    / 'data'
    / 'comsol_batch'
    / 'comsol_in_loop_targetband180_220_overlap_ga_v1'
    / 'ga_history_v1.csv'
)
DEFAULT_REAL_GA_SUMMARY = (
    ROOT
    / 'data'
    / 'comsol_batch'
    / 'comsol_in_loop_targetband180_220_overlap_ga_v1'
    / 'ga_search_summary_v1.csv'
)
DEFAULT_OUT_DIR = ROOT / 'data' / 'analysis' / 'targetband_four_arm_baseline_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Summarize target-band baseline arms A/B/C/D.')
    parser.add_argument('--abc-results', type=Path, default=DEFAULT_ABC_RESULTS)
    parser.add_argument('--legacy-c-results', type=Path, default=DEFAULT_LEGACY_C_RESULTS)
    parser.add_argument('--real-ga-history', type=Path, default=DEFAULT_REAL_GA_HISTORY)
    parser.add_argument('--real-ga-summary', type=Path, default=DEFAULT_REAL_GA_SUMMARY)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--band-low', type=float, default=180.0)
    parser.add_argument('--band-high', type=float, default=220.0)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def target_overlap(lower: pd.Series, upper: pd.Series, band_low: float, band_high: float) -> pd.Series:
    lo = pd.to_numeric(lower, errors='coerce')
    hi = pd.to_numeric(upper, errors='coerce')
    overlap = pd.Series(np.minimum(hi, band_high) - np.maximum(lo, band_low), index=lower.index)
    overlap = overlap.clip(lower=0.0)
    overlap.loc[~np.isfinite(overlap)] = np.nan
    return overlap


def load_stage4_results(path: Path, band_low: float, band_high: float) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    df = df.copy()
    df['method_arm'] = df['selection_source'].astype(str)
    df['target_overlap_Hz'] = target_overlap(df['gap34_lower_edge_Hz'], df['gap34_upper_edge_Hz'], band_low, band_high)
    df['target_cover_ratio'] = df['target_overlap_Hz'] / max(1e-12, band_high - band_low)
    return df


def load_real_ga(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    out = df.copy()
    out['method_arm'] = 'real_comsol_in_loop_ga_v1'
    out['selection_source'] = 'real_comsol_in_loop_ga_v1'
    out['selection_label'] = 'real_ga_fitness_target_overlap_Hz'
    out['target_overlap_Hz'] = pd.to_numeric(out.get('active_target_overlap_Hz'), errors='coerce')
    out['target_cover_ratio'] = pd.to_numeric(out.get('active_target_cover_ratio'), errors='coerce')
    return out


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    if df.empty:
        return pd.DataFrame(rows)
    for arm, sub in df.groupby('method_arm', sort=False):
        solve_mask = parse_bool_series(sub['solve_success']) if 'solve_success' in sub.columns else pd.Series(False, index=sub.index)
        contact_mask = parse_bool_series(sub['contact_valid']) if 'contact_valid' in sub.columns else pd.Series(False, index=sub.index)
        solved = sub[solve_mask]
        contact = sub[contact_mask]
        positive_overlap = pd.to_numeric(sub['target_overlap_Hz'], errors='coerce').fillna(0) > 0
        rows.append(
            {
                'method_arm': arm,
                'rows_total': int(len(sub)),
                'solve_success_count': int(len(solved)),
                'contact_valid_count': int(len(contact)),
                'target_open_count': int(positive_overlap.sum()),
                'target_open_rate': float(positive_overlap.mean()) if len(sub) else np.nan,
                'mean_target_overlap_Hz': float(pd.to_numeric(solved['target_overlap_Hz'], errors='coerce').mean()) if len(solved) else np.nan,
                'median_target_overlap_Hz': float(pd.to_numeric(solved['target_overlap_Hz'], errors='coerce').median()) if len(solved) else np.nan,
                'best_target_overlap_Hz': float(pd.to_numeric(sub['target_overlap_Hz'], errors='coerce').max()) if len(sub) else np.nan,
                'mean_target_cover_ratio': float(pd.to_numeric(solved['target_cover_ratio'], errors='coerce').mean()) if len(solved) else np.nan,
                'best_target_cover_ratio': float(pd.to_numeric(sub['target_cover_ratio'], errors='coerce').max()) if len(sub) else np.nan,
                'mean_gap34_gain_Hz': float(pd.to_numeric(solved.get('gap34_gain_Hz'), errors='coerce').mean()) if len(solved) and 'gap34_gain_Hz' in solved.columns else np.nan,
                'best_gap34_gain_Hz': float(pd.to_numeric(sub.get('gap34_gain_Hz'), errors='coerce').max()) if 'gap34_gain_Hz' in sub.columns else np.nan,
            }
        )
    return pd.DataFrame(rows)


def parse_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.isin({'true', '1', 'yes'})


def best_so_far(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    work['eval_index'] = range(1, len(work) + 1)
    work['best_so_far_target_overlap_Hz'] = pd.to_numeric(work['target_overlap_Hz'], errors='coerce').fillna(0).cummax()
    return work[['eval_index', 'method_arm', 'sample_id', 'shape_id', 'fitness', 'target_overlap_Hz', 'target_cover_ratio', 'best_so_far_target_overlap_Hz']]


def main() -> None:
    args = parse_args()
    out_dir = resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    abc = load_stage4_results(resolve_path(args.abc_results), args.band_low, args.band_high)
    real_ga = load_real_ga(resolve_path(args.real_ga_history))

    frames = []
    if not abc.empty:
        frames.append(abc)
    elif resolve_path(args.legacy_c_results).exists():
        legacy_c = load_stage4_results(resolve_path(args.legacy_c_results), args.band_low, args.band_high)
        legacy_c['method_arm'] = 'predictor_local_ga_v1'
        frames.append(legacy_c)
    if not real_ga.empty:
        frames.append(real_ga)
    combined = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    summary = summarize(combined)

    combined.to_csv(out_dir / 'targetband_four_arm_rows_v1.csv', index=False, encoding='utf-8-sig')
    summary.to_csv(out_dir / 'targetband_four_arm_summary_v1.csv', index=False, encoding='utf-8-sig')
    if not real_ga.empty:
        best_so_far(real_ga).to_csv(out_dir / 'real_ga_best_so_far_v1.csv', index=False, encoding='utf-8-sig')

    payload = {
        'band_low_Hz': float(args.band_low),
        'band_high_Hz': float(args.band_high),
        'abc_results': str(resolve_path(args.abc_results)),
        'real_ga_history': str(resolve_path(args.real_ga_history)),
        'available_arms': summary['method_arm'].tolist() if not summary.empty else [],
    }
    (out_dir / 'targetband_four_arm_summary_v1.json').write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(f'[DONE] wrote target-band four-arm analysis to {out_dir}')
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
