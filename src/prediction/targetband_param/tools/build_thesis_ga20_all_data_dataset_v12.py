from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v12_all_history_ga20_clean_v1'
SOURCE_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1'

SOURCE_DATASETS = [
    'windows_120_160__180_220__220_260',
    'windows_curated_v1',
    'windows_multiscale_v2',
    'windows_dense_v4',
    'windows_dense_v5_gapdiversity_aug_v1',
    'windows_dense_v6_truth_assets_aug_v1',
    'windows_dense_v7_truth_plus_supplement_aug_v1',
    'windows_dense_v8_truth_plus_exploratory_aug_v1',
    'windows_dense_v9_active_ga_mid_aug_v1',
    'windows_dense_v10_multiband_active_ga_mid_aug_v1',
    'windows_dense_v11_12gen_freeze_v1',
]

SOURCE_PRIORITY = {name: idx for idx, name in enumerate(SOURCE_DATASETS, start=10)}
GA20_PRIORITY = 1000

THESIS_GA20_HISTORIES = {
    'band140_180': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band140_180_overlap_ga_v1' / 'ga_history_v1.csv',
    'band160_200': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band160_200_overlap_ga_v1' / 'ga_history_v1.csv',
    'band180_220': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_targetband180_220_overlap_ga_v1' / 'ga_history_v1.csv',
    'band200_240': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band200_240_overlap_ga_v1' / 'ga_history_v1.csv',
    'band220_260': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band220_260_overlap_ga_v1' / 'ga_history_v1.csv',
    'band240_280': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band240_280_overlap_ga_v1' / 'ga_history_v1.csv',
}

PARAM_COLS = ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']
BAND_COLS = ['target_band_low_Hz', 'target_band_high_Hz']
KEY_COLS = ['point_id', 'shape_id', *PARAM_COLS, *BAND_COLS]

SHAPE_FEATURE_COLS = [
    'shape_area',
    'shape_perimeter',
    'shape_bbox_width',
    'shape_bbox_height',
    'shape_bbox_aspect_ratio',
    'shape_centroid_x',
    'shape_centroid_y',
    'shape_point_count',
    'shape_compactness',
    'shape_extent',
    'shape_mean_radius',
    'shape_std_radius',
    'shape_min_radius',
    'shape_max_radius',
    'shape_radius_cv',
    'shape_edge_mean',
    'shape_edge_std',
    'shape_edge_cv',
    'shape_edge_min',
    'shape_edge_max',
    'shape_edge_range',
    'shape_edge_p10',
    'shape_edge_p90',
    'shape_turn_abs_mean',
    'shape_turn_abs_std',
    'shape_turn_abs_max',
    'shape_corner_frac_30',
    'shape_corner_frac_45',
    'shape_hull_area',
    'shape_hull_perimeter',
    'shape_solidity',
    'shape_convexity',
    'shape_pca_major_span',
    'shape_pca_minor_span',
    'shape_pca_aspect',
    'shape_axis_fill',
    'shape_centroid_offset',
    'shape_quadrant_balance',
]


def band_tag(low: float, high: float) -> str:
    return f'band{int(round(low))}_{int(round(high))}'


def as_float(value: object, default: float = np.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if np.isfinite(out) else default


def numeric_series(series: pd.Series, default: float = np.nan) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').fillna(default)


def load_source_datasets() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for dataset_name in SOURCE_DATASETS:
        path = SOURCE_ROOT / dataset_name / 'targetband_parametric_v1.csv'
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path, low_memory=False)
        df['source_dataset_version'] = dataset_name
        df['source_record_kind'] = 'historical_parametric_dataset'
        df['source_priority'] = SOURCE_PRIORITY[dataset_name]
        frames.append(df)
    return pd.concat(frames, ignore_index=True, sort=False)


def make_shape_lookup(df: pd.DataFrame) -> Dict[str, Dict[str, object]]:
    lookup: Dict[str, Dict[str, object]] = {}
    available_cols = [col for col in SHAPE_FEATURE_COLS if col in df.columns]
    for shape_id, subset in df.groupby(df['shape_id'].astype(str), sort=False):
        row = subset.iloc[0]
        lookup[str(shape_id)] = {col: row.get(col, np.nan) for col in available_cols}
    return lookup


def load_valid_ga20_rows() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for origin_tag, path in THESIS_GA20_HISTORIES.items():
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        df['ga20_origin_band_tag'] = origin_tag
        df['ga20_source_history'] = str(path)
        frames.append(df)
    work = pd.concat(frames, ignore_index=True, sort=False)
    for col in ['solve_success', 'contact_valid', 'geometry_valid']:
        work[col] = pd.to_numeric(work.get(col), errors='coerce').fillna(0).astype(int)
    work['generation'] = pd.to_numeric(work.get('generation'), errors='coerce').fillna(-1).astype(int)
    edge_cols = ['active_target_lower_edge_Hz', 'active_target_upper_edge_Hz']
    for col in [*edge_cols, 'active_target_overlap_Hz', 'active_target_cover_ratio']:
        work[col] = pd.to_numeric(work.get(col), errors='coerce')
    valid = work[
        (work['generation'].between(1, 20))
        & (work['solve_success'] > 0)
        & (work['contact_valid'] > 0)
        & (work['geometry_valid'] > 0)
        & np.isfinite(work['active_target_overlap_Hz'])
        & np.isfinite(work['active_target_cover_ratio'])
    ].copy()
    return valid.reset_index(drop=True)


def make_ga20_parametric_rows(ga_df: pd.DataFrame, shape_lookup: Dict[str, Dict[str, object]]) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    missing_shapes: set[str] = set()
    for _, src in ga_df.iterrows():
        low = as_float(src.get('active_band_low_Hz'))
        high = as_float(src.get('active_band_high_Hz'))
        if not (np.isfinite(low) and np.isfinite(high) and high > low):
            tag_text = str(src.get('active_band_tag', src.get('ga20_origin_band_tag', '')))
            parts = tag_text.replace('band', '').split('_')
            low, high = float(parts[0]), float(parts[1])
        width = high - low
        overlap = max(0.0, as_float(src.get('active_target_overlap_Hz'), 0.0))
        cover = as_float(src.get('active_target_cover_ratio'), overlap / width if width > 0 else 0.0)
        edge_low = as_float(src.get('active_target_lower_edge_Hz'))
        edge_high = as_float(src.get('active_target_upper_edge_Hz'))
        best_width = as_float(src.get('active_target_best_width_Hz'), max(0.0, edge_high - edge_low))
        shape_id = str(src.get('shape_id', ''))
        shape_features = shape_lookup.get(shape_id, {})
        if not shape_features:
            missing_shapes.add(shape_id)

        sample_id = str(src.get('sample_id', ''))
        candidate_id = str(src.get('candidate_id', sample_id))
        origin_tag = str(src.get('ga20_origin_band_tag', src.get('active_band_tag', band_tag(low, high))))
        generation = int(src.get('generation', -1))
        individual = int(src.get('individual_index', -1))
        design_id = f'active_ga20_clean_{origin_tag}__g{generation:02d}__i{individual:03d}__{shape_id}'

        row: Dict[str, object] = {
            'sample_id': sample_id,
            'design_id': design_id,
            'observation_count': 1,
            'source_stage': 'active_ga20_thesis_clean_v12',
            'source_stage_list': 'active_ga20_thesis_clean_v12',
            'point_id': str(src.get('point_id', '')),
            'shape_id': shape_id,
            'shape_family': str(src.get('shape_family', '')),
            'shape_role': str(src.get('shape_role', 'active_learning_ga20')),
            'target_band_low_Hz': low,
            'target_band_high_Hz': high,
            'target_gap_is_open': int(overlap > 0.0),
            'target_gap_overlap_Hz': overlap,
            'target_gap_cover_ratio': cover,
            'target_gap_best_width_Hz': best_width,
            'target_gap_lower_edge_Hz': edge_low,
            'target_gap_upper_edge_Hz': edge_high,
            'target_gap_center_freq': 0.5 * (edge_low + edge_high) if np.isfinite(edge_low) and np.isfinite(edge_high) else np.nan,
            'target_gap_lower_band': src.get('max_gap_lower_band', 3),
            'target_gap_upper_band': src.get('max_gap_upper_band', 4),
            'target_band_tag': band_tag(low, high),
            'target_band_center_Hz': 0.5 * (low + high),
            'target_band_width_Hz': width,
            'param_sample_id': f'{design_id}::{low:.6f}_{high:.6f}',
            'source_dataset_version': 'ga20_clean_active_band_truth_v12',
            'source_record_kind': 'ga20_active_band_truth',
            'source_priority': GA20_PRIORITY,
            'active_learning_generation': generation,
            'active_learning_individual': individual,
            'active_learning_origin_band_tag': origin_tag,
            'active_learning_origin_overlap_Hz': overlap,
            'active_learning_holdout_reason': '',
            'active_learning_source_ga_history': str(src.get('ga20_source_history', '')),
            'ga20_candidate_id': candidate_id,
            'ga20_gap_edge_source': 'active_target_edges',
        }
        for col in PARAM_COLS:
            row[col] = src.get(col, np.nan)
        row.update(shape_features)
        rows.append(row)
    if missing_shapes:
        print(f'[WARN] missing shape features for {len(missing_shapes)} shapes: {sorted(missing_shapes)[:8]}')
    return pd.DataFrame(rows)


def normalize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    for col in [*PARAM_COLS, *BAND_COLS, 'target_gap_is_open', 'target_gap_overlap_Hz', 'target_gap_cover_ratio', 'target_gap_lower_edge_Hz', 'target_gap_upper_edge_Hz']:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors='coerce')
    return work


def make_physical_key(df: pd.DataFrame) -> pd.Series:
    work = normalize_numeric_columns(df)
    key = work['point_id'].astype(str).fillna('') + '|' + work['shape_id'].astype(str).fillna('')
    for col in [*PARAM_COLS, *BAND_COLS]:
        values = pd.to_numeric(work[col], errors='coerce').round(8).astype('string').fillna('')
        key = key + '|' + values
    return key


def make_label_key(df: pd.DataFrame) -> pd.Series:
    work = normalize_numeric_columns(df)
    key = pd.to_numeric(work['target_gap_is_open'], errors='coerce').fillna(-1).round(6).astype(str)
    for col in ['target_gap_overlap_Hz', 'target_gap_cover_ratio', 'target_gap_lower_edge_Hz', 'target_gap_upper_edge_Hz']:
        key = key + '|' + pd.to_numeric(work[col], errors='coerce').fillna(-999999.0).round(6).astype(str)
    return key


def origin_matches_target(df: pd.DataFrame) -> pd.Series:
    origin = df.get('active_learning_origin_band_tag', pd.Series('', index=df.index)).astype(str)
    target = df['target_band_tag'].astype(str)
    direct_ga20 = df['source_record_kind'].astype(str).eq('ga20_active_band_truth')
    return direct_ga20 | (origin.eq(target) & origin.ne(''))


def unique_text(values: Iterable[object]) -> str:
    return ';'.join(sorted({str(value) for value in values if str(value) and str(value) != 'nan'}))


def deduplicate_by_physical_key(stacked: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    work = stacked.copy()
    work['physical_key'] = make_physical_key(work)
    work['label_key'] = make_label_key(work)
    work['origin_matches_target'] = origin_matches_target(work).astype(int)
    work['source_priority'] = pd.to_numeric(work['source_priority'], errors='coerce').fillna(0).astype(int)
    work['_row_order'] = np.arange(len(work))

    label_counts = work.groupby('physical_key')['label_key'].nunique().rename('conflict_label_count')
    member_counts = work.groupby('physical_key').size().rename('duplicate_member_count')
    work = work.join(label_counts, on='physical_key').join(member_counts, on='physical_key')

    sort_cols = [
        'physical_key',
        'origin_matches_target',
        'source_priority',
        'target_gap_cover_ratio',
        '_row_order',
    ]
    ascending = [True, False, False, False, True]
    ranked = work.sort_values(sort_cols, ascending=ascending)
    chosen = ranked.groupby('physical_key', sort=False).head(1).copy()

    source_trace = work.groupby('physical_key').agg(
        source_dataset_versions=('source_dataset_version', unique_text),
        source_record_kinds=('source_record_kind', unique_text),
        source_param_sample_ids=('param_sample_id', unique_text),
    )
    chosen = chosen.drop(columns=['source_dataset_versions', 'source_record_kinds', 'source_param_sample_ids'], errors='ignore')
    chosen = chosen.join(source_trace, on='physical_key')
    chosen['data_cleaning_conflict_flag'] = (chosen['conflict_label_count'] > 1).astype(int)
    chosen['data_cleaning_duplicate_member_count'] = chosen['duplicate_member_count'].astype(int)
    chosen['data_cleaning_rule'] = np.where(
        chosen['data_cleaning_conflict_flag'] > 0,
        'conflict_resolved_by_origin_match_then_source_priority',
        'duplicate_collapsed_by_physical_key',
    )
    conflicts = work[work['conflict_label_count'] > 1].copy()
    duplicates = work[work['duplicate_member_count'] > 1].copy()
    drop_cols = ['_row_order']
    chosen = chosen.drop(columns=drop_cols, errors='ignore').reset_index(drop=True)
    conflicts = conflicts.drop(columns=drop_cols, errors='ignore').reset_index(drop=True)
    duplicates = duplicates.drop(columns=drop_cols, errors='ignore').reset_index(drop=True)
    return chosen, conflicts, duplicates


def summarize_by_band(df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for tag, subset in df.groupby('target_band_tag', sort=True):
        is_open = pd.to_numeric(subset['target_gap_is_open'], errors='coerce').fillna(0)
        cover = pd.to_numeric(subset['target_gap_cover_ratio'], errors='coerce').fillna(0.0)
        rows.append({
            'target_band_tag': str(tag),
            'rows': int(len(subset)),
            'positive_rows': int(is_open.sum()),
            'positive_rate': float(is_open.mean()),
            'max_cover_ratio': float(cover.max()),
            'mean_cover_ratio': float(cover.mean()),
        })
    return rows


def summarize_ga_source(ga_df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for tag, subset in ga_df.groupby('ga20_origin_band_tag', sort=True):
        rows.append({
            'ga20_origin_band_tag': str(tag),
            'valid_rows': int(len(subset)),
            'generation_min': int(pd.to_numeric(subset['generation'], errors='coerce').min()),
            'generation_max': int(pd.to_numeric(subset['generation'], errors='coerce').max()),
            'best_active_overlap_Hz': float(pd.to_numeric(subset['active_target_overlap_Hz'], errors='coerce').max()),
            'best_active_cover_ratio': float(pd.to_numeric(subset['active_target_cover_ratio'], errors='coerce').max()),
        })
    return rows


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> None:
    historical = load_source_datasets()
    shape_lookup = make_shape_lookup(historical)
    ga20_source = load_valid_ga20_rows()
    ga20_rows = make_ga20_parametric_rows(ga20_source, shape_lookup)

    all_cols = list(dict.fromkeys([*historical.columns.tolist(), *ga20_rows.columns.tolist()]))
    stacked = pd.concat(
        [historical.reindex(columns=all_cols), ga20_rows.reindex(columns=all_cols)],
        ignore_index=True,
        sort=False,
    )
    stacked = normalize_numeric_columns(stacked)
    clean_df, conflicts_df, duplicates_df = deduplicate_by_physical_key(stacked)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset_csv = OUT_DIR / 'targetband_parametric_v1.csv'
    stacked_csv = OUT_DIR / 'stacked_before_cleaning_v1.csv'
    ga20_csv = OUT_DIR / 'ga20_active_band_added_rows_v1.csv'
    conflicts_csv = OUT_DIR / 'data_conflicts_resolved_v1.csv'
    duplicates_csv = OUT_DIR / 'duplicate_groups_before_cleaning_v1.csv'
    source_counts_csv = OUT_DIR / 'source_counts_v1.csv'
    info_json = OUT_DIR / 'dataset_info.json'

    clean_df.to_csv(dataset_csv, index=False, encoding='utf-8-sig')
    stacked.to_csv(stacked_csv, index=False, encoding='utf-8-sig')
    ga20_rows.to_csv(ga20_csv, index=False, encoding='utf-8-sig')
    conflicts_df.to_csv(conflicts_csv, index=False, encoding='utf-8-sig')
    duplicates_df.to_csv(duplicates_csv, index=False, encoding='utf-8-sig')

    source_counts = (
        stacked['source_dataset_version']
        .astype(str)
        .value_counts()
        .rename_axis('source_dataset_version')
        .reset_index(name='stacked_rows')
    )
    source_counts.to_csv(source_counts_csv, index=False, encoding='utf-8-sig')

    thesis_tags = ['band140_180', 'band160_200', 'band180_220', 'band200_240', 'band220_260', 'band240_280']
    info = {
        'dataset_name': 'prediction_targetband_param_v1',
        'dataset_version': 'windows_dense_v12_all_history_ga20_clean_v1',
        'dataset_csv': str(dataset_csv),
        'out_dir': str(OUT_DIR),
        'source_dataset_versions': SOURCE_DATASETS,
        'ga20_source_histories': {tag: str(path) for tag, path in THESIS_GA20_HISTORIES.items()},
        'rows_historical_stacked': int(len(historical)),
        'rows_ga20_valid_source': int(len(ga20_source)),
        'rows_ga20_added_active_band_only': int(len(ga20_rows)),
        'rows_stacked_before_cleaning': int(len(stacked)),
        'rows_clean_after_physical_key_dedup': int(len(clean_df)),
        'duplicate_physical_keys': int((duplicates_df['physical_key'].value_counts() > 0).sum()) if len(duplicates_df) else 0,
        'conflict_physical_keys': int(conflicts_df['physical_key'].nunique()) if len(conflicts_df) else 0,
        'rows_with_resolved_conflict': int(clean_df['data_cleaning_conflict_flag'].sum()),
        'unique_designs': int(clean_df['design_id'].astype(str).nunique()),
        'unique_shapes': int(clean_df['shape_id'].astype(str).nunique()),
        'unique_families': int(clean_df['shape_family'].astype(str).nunique()),
        'all_band_summary': summarize_by_band(clean_df),
        'thesis_band_summary': summarize_by_band(clean_df[clean_df['target_band_tag'].astype(str).isin(thesis_tags)]),
        'ga20_source_summary': summarize_ga_source(ga20_source),
        'cleaning_rule': [
            'A physical key is point_id + shape_id + Fourier/geometric parameters + target band bounds rounded to 8 decimals.',
            'Rows with the same physical key and identical label are collapsed into one row while keeping a source trace.',
            'Rows with conflicting labels are resolved by preferring active-band truth where origin band equals target band, then newer/higher-priority sources.',
            'The new 20-generation COMSOL-in-loop GA data are appended only for their active target band to avoid cross-band label extrapolation from an origin-specific active gap.',
        ],
        'thesis_note': [
            'This v12 dataset is intended for Chapter 3 predictor retraining and data accounting.',
            'The predictor remains a screening/ranking model; final optimization claims should still rely on COMSOL or COMSOL-in-loop GA validation.',
        ],
    }
    write_json(info_json, info)

    print(f'[DONE] historical stacked rows: {len(historical)}')
    print(f'[DONE] valid GA20 source rows: {len(ga20_source)}')
    print(f'[DONE] GA20 active-band rows added: {len(ga20_rows)}')
    print(f'[DONE] stacked before cleaning: {len(stacked)}')
    print(f'[DONE] clean rows: {len(clean_df)}')
    print(f'[DONE] conflict physical keys: {info["conflict_physical_keys"]}')
    print(f'[OUT] {dataset_csv}')
    print(f'[OUT] {info_json}')


if __name__ == '__main__':
    main()
