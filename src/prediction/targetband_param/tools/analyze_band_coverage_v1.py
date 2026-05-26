from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATASET = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v5_gapdiversity_aug_v1' / 'targetband_parametric_v1.csv'
DEFAULT_CATALOG = ROOT / 'src' / 'prediction' / 'targetband_param' / 'configs' / 'thesis_band_catalog_v2.json'
DEFAULT_OUT_DIR = ROOT / 'data' / 'analysis' / 'targetband_band_coverage_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Audit target-band coverage and supplementation priority inside a fixed band catalog.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--out-tag', default='thesis_band_catalog_v2')
    return parser.parse_args()


def load_catalog_windows(path: Path) -> List[Tuple[float, float, str]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    rows = payload.get('bands', [])
    windows: List[Tuple[float, float, str]] = []
    for row in rows:
        low = float(row['band_low_Hz'])
        high = float(row['band_high_Hz'])
        windows.append((low, high, str(row['target_band_tag'])))
    if not windows:
        raise RuntimeError(f'No bands found in catalog: {path}')
    return windows


def summarize_band(subset: pd.DataFrame, band_tag_hint: str) -> Dict[str, object]:
    work = subset.copy()
    y = pd.to_numeric(work['target_gap_is_open'], errors='coerce').fillna(0.0)
    positive = work.loc[y > 0.5].copy()
    source_tags = sorted(work['target_band_tag'].astype(str).unique().tolist())

    positive_rows = int(len(positive))
    positive_designs = int(positive['design_id'].astype(str).nunique()) if positive_rows else 0
    positive_families = int(positive['shape_family'].astype(str).nunique()) if positive_rows else 0
    positive_stages = int(positive['source_stage'].astype(str).nunique()) if positive_rows else 0

    mean_cover = float(pd.to_numeric(positive['target_gap_cover_ratio'], errors='coerce').mean()) if positive_rows else 0.0
    median_cover = float(pd.to_numeric(positive['target_gap_cover_ratio'], errors='coerce').median()) if positive_rows else 0.0
    p90_cover = float(pd.to_numeric(positive['target_gap_cover_ratio'], errors='coerce').quantile(0.9)) if positive_rows else 0.0

    deficiency = (
        (1.0 / max(1, positive_rows)) * 2000.0
        + (1.0 / max(1, positive_designs)) * 400.0
        + (1.0 / max(1, positive_families)) * 200.0
        + max(0.0, 0.35 - mean_cover) * 5.0
    )

    return {
        'target_band_tag': band_tag_hint,
        'target_band_low_Hz': float(pd.to_numeric(work['target_band_low_Hz'], errors='coerce').iloc[0]),
        'target_band_high_Hz': float(pd.to_numeric(work['target_band_high_Hz'], errors='coerce').iloc[0]),
        'rows_total': int(len(work)),
        'positive_rows': positive_rows,
        'positive_rate': float(y.mean()),
        'unique_designs_total': int(work['design_id'].astype(str).nunique()),
        'unique_families_total': int(work['shape_family'].astype(str).nunique()),
        'positive_designs': positive_designs,
        'positive_families': positive_families,
        'positive_source_stages': positive_stages,
        'cover_ratio_mean_positive': mean_cover,
        'cover_ratio_median_positive': median_cover,
        'cover_ratio_p90_positive': p90_cover,
        'source_band_tags': '|'.join(source_tags),
        'supplement_deficiency_score': deficiency,
    }


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.dataset)
    windows = load_catalog_windows(args.catalog)

    rows: List[Dict[str, object]] = []
    for low, high, band_tag in windows:
        mask = (
            pd.to_numeric(df['target_band_low_Hz'], errors='coerce').round(6) == round(low, 6)
        ) & (
            pd.to_numeric(df['target_band_high_Hz'], errors='coerce').round(6) == round(high, 6)
        )
        subset = df.loc[mask].copy()
        if subset.empty:
            continue
        rows.append(summarize_band(subset, band_tag))

    if not rows:
        raise RuntimeError('No matching band windows found in dataset.')

    summary_df = pd.DataFrame(rows).sort_values(
        ['supplement_deficiency_score', 'positive_rows', 'positive_families'],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    summary_df.insert(0, 'supplement_priority_rank', range(1, len(summary_df) + 1))

    out_dir = DEFAULT_OUT_DIR / args.out_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / 'band_coverage_summary_v1.csv'
    out_json = out_dir / 'band_coverage_summary_v1.json'

    summary_df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    out_json.write_text(summary_df.to_json(orient='records', force_ascii=False, indent=2), encoding='utf-8')

    print(f'[DONE] analyzed bands: {len(summary_df)}')
    print(f'[OUT] {out_csv}')
    print(f'[OUT] {out_json}')


if __name__ == '__main__':
    main()
