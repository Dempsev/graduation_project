from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CATALOG = ROOT / 'src' / 'prediction' / 'targetband_param' / 'configs' / 'thesis_band_catalog_v2.json'
DEFAULT_V7_INFO = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v7_truth_plus_supplement_aug_v1' / 'dataset_info.json'
TARGETBAND_ROOT = ROOT / 'data' / 'prediction_targetband_v1'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'analysis' / 'targetband_shape_atlas_v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a target-band-aware shape atlas and family-balanced shape pools.')
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--v7-info', type=Path, default=DEFAULT_V7_INFO)
    parser.add_argument('--out-root', type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument('--min-hard-negative-rows', type=int, default=3)
    parser.add_argument('--max-strong-per-family', type=int, default=2)
    parser.add_argument('--max-near-miss-per-family', type=int, default=1)
    parser.add_argument('--max-hard-negative-per-family', type=int, default=1)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_catalog(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    bands = payload.get('bands', [])
    if not bands:
        raise RuntimeError(f'No bands found in catalog: {path}')
    return bands


def load_v7_source_tags(path: Path) -> List[str]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    tags = [str(tag) for tag in payload.get('source_tags', [])]
    if not tags:
        raise RuntimeError(f'No source_tags found in dataset info: {path}')
    return tags


def iter_band_source_specs(catalog: List[Dict[str, object]], v7_source_tags: List[str]) -> Iterable[Tuple[Dict[str, object], List[Tuple[str, Path]]]]:
    for band in catalog:
        band_tag = str(band['target_band_tag'])
        source_specs: List[Tuple[str, Path]] = []
        for source_tag in v7_source_tags:
            if source_tag == band_tag or source_tag.startswith(f'{band_tag}_'):
                csv_path = TARGETBAND_ROOT / source_tag / 'master_targetband_dataset_v1.csv'
                if csv_path.exists():
                    source_specs.append((source_tag, csv_path))
        if not source_specs:
            raise RuntimeError(f'No targetband master datasets found for {band_tag}')
        yield band, source_specs


def load_band_rows(source_specs: List[Tuple[str, Path]], band_tag: str) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for source_tag, csv_path in source_specs:
        df = pd.read_csv(csv_path)
        df['source_dataset_tag'] = source_tag
        df['atlas_band_tag'] = band_tag
        frames.append(df)
    merged = pd.concat(frames, ignore_index=True)
    merged['shape_id'] = merged['shape_id'].astype(str)
    merged['shape_family'] = merged['shape_family'].astype(str)
    merged['target_gap_is_open'] = pd.to_numeric(merged['target_gap_is_open'], errors='coerce').fillna(0).astype(int)
    merged['target_gap_cover_ratio'] = pd.to_numeric(merged['target_gap_cover_ratio'], errors='coerce').fillna(0.0)
    merged['target_gap_overlap_Hz'] = pd.to_numeric(merged['target_gap_overlap_Hz'], errors='coerce').fillna(0.0)
    merged['geometry_valid'] = pd.to_numeric(merged['geometry_valid'], errors='coerce').fillna(0).astype(int)
    merged['contact_valid'] = pd.to_numeric(merged['contact_valid'], errors='coerce').fillna(0).astype(int)
    merged['solve_success'] = pd.to_numeric(merged['solve_success'], errors='coerce').fillna(0).astype(int)
    merged['is_training_ready'] = pd.to_numeric(merged.get('is_training_ready', 0), errors='coerce').fillna(0).astype(int)
    return merged


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def classify_shape_role(best_cover: float, positive_count: int, hard_negative_count: int, solve_success_rate: float, rows: int, min_hard_negative_rows: int) -> str:
    if positive_count > 0:
        if best_cover >= 0.50:
            return 'target_band_strong'
        if best_cover >= 0.15:
            return 'weak_band_contributor'
        return 'near_miss'
    if rows >= min_hard_negative_rows and solve_success_rate >= 0.80 and hard_negative_count == rows:
        return 'hard_negative'
    return 'inactive_or_sparse'


def score_shape(best_cover: float, mean_positive_cover: float, positive_rate: float, solve_success_rate: float, hard_negative_rate: float, positive_count: int) -> float:
    return (
        4.0 * best_cover
        + 2.0 * mean_positive_cover
        + 0.75 * positive_rate
        + 0.25 * solve_success_rate
        + 0.08 * math.log1p(max(0, positive_count))
        - 0.50 * hard_negative_rate
    )


def score_family(best_shape_score: float, best_cover: float, family_positive_rate: float, family_solve_success_rate: float, contributing_shapes: int, role_diversity: int) -> float:
    return (
        0.60 * best_shape_score
        + 2.0 * best_cover
        + 0.60 * family_positive_rate
        + 0.20 * family_solve_success_rate
        + 0.05 * math.log1p(max(0, contributing_shapes))
        + 0.03 * max(0, role_diversity)
    )


def build_shape_band_summary(df: pd.DataFrame, band_tag: str, band_meta: Dict[str, object], min_hard_negative_rows: int) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for (shape_id, shape_family), subset in df.groupby(['shape_id', 'shape_family'], sort=True):
        rows_count = int(len(subset))
        solve_success_count = int(subset['solve_success'].sum())
        training_ready_count = int(subset['is_training_ready'].sum())
        positive_mask = subset['target_gap_is_open'] > 0
        positive_count = int(positive_mask.sum())
        hard_negative_count = int(((subset['solve_success'] > 0) & (subset['target_gap_is_open'] == 0)).sum())
        best_cover = float(subset['target_gap_cover_ratio'].max()) if rows_count else 0.0
        best_overlap = float(subset['target_gap_overlap_Hz'].max()) if rows_count else 0.0
        mean_positive_cover = float(subset.loc[positive_mask, 'target_gap_cover_ratio'].mean()) if positive_count > 0 else 0.0
        mean_positive_overlap = float(subset.loc[positive_mask, 'target_gap_overlap_Hz'].mean()) if positive_count > 0 else 0.0
        positive_rate = safe_rate(positive_count, rows_count)
        solve_success_rate = safe_rate(solve_success_count, rows_count)
        training_ready_rate = safe_rate(training_ready_count, rows_count)
        hard_negative_rate = safe_rate(hard_negative_count, rows_count)
        source_dataset_count = int(subset['source_dataset_tag'].nunique())
        source_stage_count = int(subset['source_stage'].nunique())
        role = classify_shape_role(best_cover, positive_count, hard_negative_count, solve_success_rate, rows_count, min_hard_negative_rows)
        shape_band_score = score_shape(best_cover, mean_positive_cover, positive_rate, solve_success_rate, hard_negative_rate, positive_count)
        rows.append({
            'target_band_tag': band_tag,
            'band_low_Hz': float(band_meta['band_low_Hz']),
            'band_high_Hz': float(band_meta['band_high_Hz']),
            'shape_id': shape_id,
            'shape_family': shape_family,
            'rows': rows_count,
            'solve_success_count': solve_success_count,
            'solve_success_rate': solve_success_rate,
            'training_ready_count': training_ready_count,
            'training_ready_rate': training_ready_rate,
            'positive_count': positive_count,
            'positive_rate': positive_rate,
            'hard_negative_count': hard_negative_count,
            'hard_negative_rate': hard_negative_rate,
            'best_cover_ratio': best_cover,
            'best_overlap_Hz': best_overlap,
            'mean_positive_cover_ratio': mean_positive_cover,
            'mean_positive_overlap_Hz': mean_positive_overlap,
            'source_dataset_count': source_dataset_count,
            'source_stage_count': source_stage_count,
            'shape_role_band': role,
            'shape_band_score': shape_band_score,
        })
    summary = pd.DataFrame(rows)
    summary = summary.sort_values(['target_band_tag', 'shape_band_score', 'best_cover_ratio', 'shape_id'], ascending=[True, False, False, True]).reset_index(drop=True)
    return summary


def build_family_band_summary(shape_band_df: pd.DataFrame, band_tag: str, band_meta: Dict[str, object]) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for family, subset in shape_band_df.groupby('shape_family', sort=True):
        best_row = subset.sort_values(['shape_band_score', 'best_cover_ratio', 'shape_id'], ascending=[False, False, True]).iloc[0]
        contributing_shapes = int((subset['positive_count'] > 0).sum())
        role_diversity = int(subset['shape_role_band'].nunique())
        family_positive_rate = float(subset['positive_count'].sum()) / max(1, int(subset['rows'].sum()))
        family_solve_success_rate = float(subset['solve_success_count'].sum()) / max(1, int(subset['rows'].sum()))
        best_cover = float(subset['best_cover_ratio'].max())
        family_band_score = score_family(
            best_shape_score=float(best_row['shape_band_score']),
            best_cover=best_cover,
            family_positive_rate=family_positive_rate,
            family_solve_success_rate=family_solve_success_rate,
            contributing_shapes=contributing_shapes,
            role_diversity=role_diversity,
        )
        rows.append({
            'target_band_tag': band_tag,
            'band_low_Hz': float(band_meta['band_low_Hz']),
            'band_high_Hz': float(band_meta['band_high_Hz']),
            'shape_family': family,
            'family_shape_count': int(len(subset)),
            'contributing_shape_count': contributing_shapes,
            'role_diversity': role_diversity,
            'family_positive_rate': family_positive_rate,
            'family_solve_success_rate': family_solve_success_rate,
            'family_best_cover_ratio': best_cover,
            'family_best_shape_id': str(best_row['shape_id']),
            'family_best_shape_role_band': str(best_row['shape_role_band']),
            'family_band_score': family_band_score,
        })
    summary = pd.DataFrame(rows)
    summary = summary.sort_values(['target_band_tag', 'family_band_score', 'family_best_cover_ratio', 'shape_family'], ascending=[True, False, False, True]).reset_index(drop=True)
    return summary


def build_shape_role_catalog(shape_band_all: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for shape_id, subset in shape_band_all.groupby('shape_id', sort=True):
        best_row = subset.sort_values(['shape_band_score', 'best_cover_ratio', 'target_band_tag'], ascending=[False, False, True]).iloc[0]
        positive_band_count = int((subset['positive_count'] > 0).sum())
        rows.append({
            'shape_id': str(shape_id),
            'shape_family': str(best_row['shape_family']),
            'best_band_tag': str(best_row['target_band_tag']),
            'best_band_score': float(best_row['shape_band_score']),
            'best_cover_ratio': float(best_row['best_cover_ratio']),
            'best_overlap_Hz': float(best_row['best_overlap_Hz']),
            'positive_band_count': positive_band_count,
            'primary_shape_role': str(best_row['shape_role_band']),
            'band_role_signature': '|'.join(
                f"{row.target_band_tag}:{row.shape_role_band}"
                for row in subset.sort_values(['target_band_tag']).itertuples()
            ),
        })
    summary = pd.DataFrame(rows)
    summary = summary.sort_values(['best_band_score', 'best_cover_ratio', 'shape_id'], ascending=[False, False, True]).reset_index(drop=True)
    return summary


def assign_selection_bucket(role: str) -> str:
    if role == 'target_band_strong':
        return 'target-band strong'
    if role == 'weak_band_contributor':
        return 'weak-band contributor'
    if role == 'near_miss':
        return 'near-miss'
    if role == 'hard_negative':
        return 'hard negative'
    return 'inactive'


def build_band_shape_pool(
    shape_band_df: pd.DataFrame,
    family_band_df: pd.DataFrame,
    max_strong_per_family: int,
    max_near_miss_per_family: int,
    max_hard_negative_per_family: int,
) -> pd.DataFrame:
    family_score_map = family_band_df.set_index('shape_family')['family_band_score'].to_dict()
    rows: List[Dict[str, object]] = []
    for family, subset in shape_band_df.groupby('shape_family', sort=True):
        subset = subset.copy()
        subset['selection_bucket'] = subset['shape_role_band'].map(assign_selection_bucket)
        subset = subset.sort_values(['shape_band_score', 'best_cover_ratio', 'shape_id'], ascending=[False, False, True])

        family_rows: List[pd.Series] = []
        strong_rows = subset[subset['shape_role_band'].isin(['target_band_strong', 'weak_band_contributor'])].head(max_strong_per_family)
        family_rows.extend(list(strong_rows.itertuples(index=False)))

        used_shape_ids = {str(row.shape_id) for row in family_rows}

        near_miss_rows = subset[(subset['shape_role_band'] == 'near_miss') & (~subset['shape_id'].astype(str).isin(used_shape_ids))].head(max_near_miss_per_family)
        family_rows.extend(list(near_miss_rows.itertuples(index=False)))
        used_shape_ids.update(str(row.shape_id) for row in near_miss_rows.itertuples(index=False))

        hard_negative_rows = subset[(subset['shape_role_band'] == 'hard_negative') & (~subset['shape_id'].astype(str).isin(used_shape_ids))].head(max_hard_negative_per_family)
        family_rows.extend(list(hard_negative_rows.itertuples(index=False)))

        for rank_within_family, row in enumerate(family_rows, start=1):
            rows.append({
                'target_band_tag': str(row.target_band_tag),
                'shape_family': str(row.shape_family),
                'shape_id': str(row.shape_id),
                'shape_role_band': str(row.shape_role_band),
                'selection_bucket': assign_selection_bucket(str(row.shape_role_band)),
                'family_band_score': float(family_score_map.get(str(row.shape_family), 0.0)),
                'shape_band_score': float(row.shape_band_score),
                'best_cover_ratio': float(row.best_cover_ratio),
                'best_overlap_Hz': float(row.best_overlap_Hz),
                'positive_count': int(row.positive_count),
                'solve_success_rate': float(row.solve_success_rate),
                'rows': int(row.rows),
                'rank_within_family': rank_within_family,
            })
    pool = pd.DataFrame(rows)
    if pool.empty:
        return pool
    bucket_order = {
        'target-band strong': 0,
        'weak-band contributor': 1,
        'near-miss': 2,
        'hard negative': 3,
        'inactive': 4,
    }
    pool['selection_bucket_order'] = pool['selection_bucket'].map(bucket_order).fillna(99).astype(int)
    pool = pool.sort_values(
        ['target_band_tag', 'family_band_score', 'selection_bucket_order', 'shape_band_score', 'best_cover_ratio', 'shape_family', 'shape_id'],
        ascending=[True, False, True, False, False, True, True],
    ).reset_index(drop=True)
    pool['rank_global'] = pool.groupby('target_band_tag').cumcount() + 1
    return pool.drop(columns=['selection_bucket_order'])


def write_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    df.to_csv(path, index=False, encoding='utf-8-sig')


def main() -> None:
    args = parse_args()
    catalog = load_catalog(args.catalog)
    v7_source_tags = load_v7_source_tags(args.v7_info)
    ensure_dir(args.out_root)

    shape_band_frames: List[pd.DataFrame] = []
    family_band_frames: List[pd.DataFrame] = []
    band_pool_frames: List[pd.DataFrame] = []
    band_source_rows: List[Dict[str, object]] = []

    for band_meta, source_specs in iter_band_source_specs(catalog, v7_source_tags):
        band_tag = str(band_meta['target_band_tag'])
        band_rows = load_band_rows(source_specs, band_tag)
        shape_band_df = build_shape_band_summary(band_rows, band_tag, band_meta, args.min_hard_negative_rows)
        family_band_df = build_family_band_summary(shape_band_df, band_tag, band_meta)
        band_pool_df = build_band_shape_pool(
            shape_band_df,
            family_band_df,
            max_strong_per_family=args.max_strong_per_family,
            max_near_miss_per_family=args.max_near_miss_per_family,
            max_hard_negative_per_family=args.max_hard_negative_per_family,
        )

        band_dir = args.out_root / band_tag
        ensure_dir(band_dir)
        write_csv(shape_band_df, band_dir / 'shape_band_summary_v1.csv')
        write_csv(family_band_df, band_dir / 'family_band_summary_v1.csv')
        write_csv(band_pool_df, band_dir / 'shape_pool_v1.csv')

        shape_band_frames.append(shape_band_df)
        family_band_frames.append(family_band_df)
        band_pool_frames.append(band_pool_df)

        for source_tag, csv_path in source_specs:
            band_source_rows.append({
                'target_band_tag': band_tag,
                'source_dataset_tag': source_tag,
                'master_csv': str(csv_path),
            })

        print(
            f"[DONE] {band_tag}: shape_rows={len(shape_band_df)} "
            f"family_rows={len(family_band_df)} pool_rows={len(band_pool_df)}"
        )

    shape_band_all = pd.concat(shape_band_frames, ignore_index=True)
    family_band_all = pd.concat(family_band_frames, ignore_index=True)
    band_pool_all = pd.concat(band_pool_frames, ignore_index=True)
    shape_role_catalog = build_shape_role_catalog(shape_band_all)

    write_csv(shape_band_all, args.out_root / 'shape_band_summary_all_v1.csv')
    write_csv(family_band_all, args.out_root / 'family_band_summary_all_v1.csv')
    write_csv(shape_role_catalog, args.out_root / 'shape_role_catalog_v1.csv')
    write_csv(band_pool_all, args.out_root / 'shape_pool_all_v1.csv')
    write_csv(pd.DataFrame(band_source_rows), args.out_root / 'band_source_manifest_v1.csv')

    summary = {
        'catalog': str(args.catalog),
        'v7_info': str(args.v7_info),
        'bands': [str(band['target_band_tag']) for band in catalog],
        'shape_band_rows': int(len(shape_band_all)),
        'family_band_rows': int(len(family_band_all)),
        'shape_role_rows': int(len(shape_role_catalog)),
        'shape_pool_rows': int(len(band_pool_all)),
        'pool_policy': {
            'max_strong_per_family': args.max_strong_per_family,
            'max_near_miss_per_family': args.max_near_miss_per_family,
            'max_hard_negative_per_family': args.max_hard_negative_per_family,
        },
        'shape_role_policy': {
            'target_band_strong': 'best_cover_ratio >= 0.50 and positive_count > 0',
            'weak_band_contributor': '0.15 <= best_cover_ratio < 0.50 and positive_count > 0',
            'near_miss': '0 < best_cover_ratio < 0.15',
            'hard_negative': f'positive_count == 0 and rows >= {args.min_hard_negative_rows} and solve_success_rate >= 0.80',
        },
        'notes': [
            'This atlas is band-aware: every thesis band gets its own shape and family ranking.',
            'Pools are family-balanced so one historically strong family cannot dominate the whole search front-end.',
            'The main intended use is to replace or augment old gap34-first shape pools in target-band search and supplementation.',
        ],
    }
    (args.out_root / 'shape_atlas_info_v1.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(f"[DONE] atlas_out={args.out_root}")


if __name__ == '__main__':
    main()
