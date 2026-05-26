from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BASE_DATASET = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v4' / 'targetband_parametric_v1.csv'
OUT_DIR = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1' / 'windows_dense_v11_12gen_freeze_v1'

THESIS_WINDOWS = [
    (140.0, 180.0),
    (160.0, 200.0),
    (180.0, 220.0),
    (200.0, 240.0),
    (220.0, 260.0),
    (240.0, 280.0),
]

GA_HISTORY_BY_BAND = {
    'band140_180': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band140_180_overlap_ga_v1' / 'ga_history_v1.csv',
    'band160_200': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band160_200_overlap_ga_v1' / 'ga_history_v1.csv',
    'band180_220': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band180_220_overlap_ga_v1' / 'ga_history_v1.csv',
    'band200_240': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band200_240_overlap_ga_v1' / 'ga_history_v1.csv',
    'band220_260': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band220_260_overlap_ga_v1' / 'ga_history_v1.csv',
    'band240_280': ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_thesis_band240_280_overlap_ga_v1' / 'ga_history_v1.csv',
}

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
    return f'band{int(low)}_{int(high)}'


def overlap_length(gap_low: float, gap_high: float, band_low: float, band_high: float) -> float:
    if not (np.isfinite(gap_low) and np.isfinite(gap_high)):
        return 0.0
    return float(max(0.0, min(gap_high, band_high) - max(gap_low, band_low)))


def as_float(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').fillna(default).astype(float)


def base_shape_lookup(base_df: pd.DataFrame) -> Dict[str, Dict[str, object]]:
    lookup: Dict[str, Dict[str, object]] = {}
    for shape_id, subset in base_df.groupby(base_df['shape_id'].astype(str)):
        row = subset.iloc[0]
        lookup[str(shape_id)] = {col: row[col] if col in row.index else np.nan for col in SHAPE_FEATURE_COLS}
    return lookup


def load_valid_ga_rows() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for tag, path in GA_HISTORY_BY_BAND.items():
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        df['source_ga_band_tag'] = tag
        df['source_ga_history'] = str(path)
        frames.append(df)
    work = pd.concat(frames, ignore_index=True)
    for col in ['solve_success', 'contact_valid', 'geometry_valid']:
        work[col] = pd.to_numeric(work.get(col), errors='coerce').fillna(0).astype(int)
    work['generation'] = pd.to_numeric(work.get('generation'), errors='coerce').fillna(-1).astype(int)
    work['active_target_overlap_Hz'] = as_float(work.get('active_target_overlap_Hz'))
    work['active_target_lower_edge_Hz'] = as_float(work.get('active_target_lower_edge_Hz'), default=np.nan)
    work['active_target_upper_edge_Hz'] = as_float(work.get('active_target_upper_edge_Hz'), default=np.nan)
    work['gap34_lower_edge_Hz'] = as_float(work.get('gap34_lower_edge_Hz'), default=np.nan)
    work['gap34_upper_edge_Hz'] = as_float(work.get('gap34_upper_edge_Hz'), default=np.nan)
    work = work[
        (work['generation'].between(1, 12))
        & (work['solve_success'] > 0)
        & (work['contact_valid'] > 0)
        & (work['geometry_valid'] > 0)
        & np.isfinite(work['gap34_lower_edge_Hz'])
        & np.isfinite(work['gap34_upper_edge_Hz'])
    ].copy()
    return work.reset_index(drop=True)


def split_train_and_top1_holdout(ga_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    holdout_indices: List[int] = []
    for _, subset in ga_df.groupby('source_ga_band_tag', sort=True):
        scores = as_float(subset['active_target_overlap_Hz'])
        holdout_indices.append(int(scores.idxmax()))
    holdout_mask = ga_df.index.isin(holdout_indices)
    holdout = ga_df[holdout_mask].copy()
    train = ga_df[~holdout_mask].copy()
    holdout['holdout_reason'] = 'origin_band_top1_12gen_freeze'
    train['holdout_reason'] = ''
    return train.reset_index(drop=True), holdout.reset_index(drop=True)


def make_augmented_rows(
    ga_df: pd.DataFrame,
    shape_lookup: Dict[str, Dict[str, object]],
    source_stage: str,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for _, src in ga_df.iterrows():
        shape_id = str(src['shape_id'])
        shape_features = shape_lookup.get(shape_id)
        if shape_features is None:
            raise KeyError(f'missing shape features for {shape_id}')

        active_overlap = float(src.get('active_target_overlap_Hz', 0.0))
        active_low = float(src.get('active_target_lower_edge_Hz', np.nan))
        active_high = float(src.get('active_target_upper_edge_Hz', np.nan))
        if active_overlap > 0.0 and np.isfinite(active_low) and np.isfinite(active_high):
            gap_low = active_low
            gap_high = active_high
            gap_source = 'active_target_edges'
        else:
            gap_low = float(src['gap34_lower_edge_Hz'])
            gap_high = float(src['gap34_upper_edge_Hz'])
            gap_source = 'gap34_edges'
        gap_width = max(0.0, gap_high - gap_low)
        gap_center = 0.5 * (gap_low + gap_high)
        sample_id = str(src['sample_id'])
        generation = int(float(src.get('generation', -1)))
        individual = int(float(src.get('individual_index', -1)))
        origin_band = str(src.get('source_ga_band_tag', src.get('active_band_tag', '')))
        design_id = f'active_ga_12gen_freeze_{sample_id}'

        for low, high in THESIS_WINDOWS:
            width = high - low
            overlap = overlap_length(gap_low, gap_high, low, high)
            tag = band_tag(low, high)
            row: Dict[str, object] = {
                'sample_id': sample_id,
                'design_id': design_id,
                'observation_count': 1,
                'source_stage': source_stage,
                'source_stage_list': source_stage,
                'point_id': str(src.get('point_id', '')),
                'shape_id': shape_id,
                'shape_family': str(src.get('shape_family', '')),
                'shape_role': 'active_learning_12gen_freeze_train_or_holdout',
                'a1': src.get('a1', np.nan),
                'a2': src.get('a2', np.nan),
                'b1': src.get('b1', np.nan),
                'b2': src.get('b2', np.nan),
                'a3': src.get('a3', np.nan),
                'b3': src.get('b3', np.nan),
                'a4': src.get('a4', np.nan),
                'b4': src.get('b4', np.nan),
                'a5': src.get('a5', np.nan),
                'b5': src.get('b5', np.nan),
                'r0': src.get('r0', np.nan),
                'target_band_low_Hz': low,
                'target_band_high_Hz': high,
                'target_gap_is_open': int(overlap > 0.0),
                'target_gap_overlap_Hz': overlap,
                'target_gap_cover_ratio': overlap / width,
                'target_gap_best_width_Hz': gap_width,
                'target_gap_lower_edge_Hz': gap_low,
                'target_gap_upper_edge_Hz': gap_high,
                'target_gap_center_freq': gap_center,
                'target_gap_lower_band': src.get('max_gap_lower_band', 3),
                'target_gap_upper_band': src.get('max_gap_upper_band', 4),
                'target_band_tag': tag,
                'target_band_center_Hz': 0.5 * (low + high),
                'target_band_width_Hz': width,
                'param_sample_id': f'{design_id}::{low:.6f}_{high:.6f}',
                'active_learning_generation': generation,
                'active_learning_individual': individual,
                'active_learning_origin_band_tag': origin_band,
                'active_learning_origin_overlap_Hz': float(src.get('active_target_overlap_Hz', overlap)),
                'active_learning_holdout_reason': str(src.get('holdout_reason', '')),
                'active_learning_source_ga_history': str(src.get('source_ga_history', '')),
                'active_learning_gap_edge_source': gap_source,
            }
            row.update(shape_features)
            rows.append(row)
    return rows


def summarize(df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for tag, subset in df.groupby('target_band_tag'):
        is_open = pd.to_numeric(subset['target_gap_is_open'], errors='coerce').fillna(0.0)
        cover = pd.to_numeric(subset['target_gap_cover_ratio'], errors='coerce').fillna(0.0)
        rows.append({
            'target_band_tag': str(tag),
            'rows': int(len(subset)),
            'positive_rows': int(is_open.sum()),
            'positive_rate': float(is_open.mean()),
            'max_cover_ratio': float(cover.max()),
            'mean_cover_ratio': float(cover.mean()),
        })
    return sorted(rows, key=lambda item: item['target_band_tag'])


def origin_summary(df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for tag, subset in df.groupby('source_ga_band_tag'):
        rows.append({
            'source_ga_band_tag': str(tag),
            'rows': int(len(subset)),
            'max_origin_overlap_Hz': float(as_float(subset['active_target_overlap_Hz']).max()),
            'mean_origin_overlap_Hz': float(as_float(subset['active_target_overlap_Hz']).mean()),
            'generation_min': int(pd.to_numeric(subset['generation'], errors='coerce').min()),
            'generation_max': int(pd.to_numeric(subset['generation'], errors='coerce').max()),
        })
    return sorted(rows, key=lambda item: item['source_ga_band_tag'])


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> None:
    base_df = pd.read_csv(BASE_DATASET)
    ga_df = load_valid_ga_rows()
    train_source, holdout_source = split_train_and_top1_holdout(ga_df)
    shape_lookup = base_shape_lookup(base_df)

    added_df = pd.DataFrame(make_augmented_rows(
        train_source,
        shape_lookup,
        source_stage='active_ga_multiband_12gen_train_v11_freeze',
    ))
    holdout_df = pd.DataFrame(make_augmented_rows(
        holdout_source,
        shape_lookup,
        source_stage='active_ga_multiband_12gen_top1_holdout_v11_freeze',
    ))

    all_cols = list(dict.fromkeys([*base_df.columns.tolist(), *added_df.columns.tolist()]))
    out_df = pd.concat(
        [base_df.reindex(columns=all_cols), added_df.reindex(columns=all_cols)],
        ignore_index=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / 'targetband_parametric_v1.csv'
    added_csv = OUT_DIR / 'active_ga_multiband_12gen_train_added_rows_v1.csv'
    holdout_csv = OUT_DIR / 'active_ga_multiband_12gen_top1_holdout_rows_v1.csv'
    source_valid_csv = OUT_DIR / 'active_ga_multiband_12gen_valid_source_rows_v1.csv'
    info_json = OUT_DIR / 'dataset_info.json'

    out_df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    added_df.to_csv(added_csv, index=False, encoding='utf-8-sig')
    holdout_df.to_csv(holdout_csv, index=False, encoding='utf-8-sig')
    ga_df.to_csv(source_valid_csv, index=False, encoding='utf-8-sig')

    selected_tags = [band_tag(low, high) for low, high in THESIS_WINDOWS]
    info = {
        'dataset_name': 'prediction_targetband_param_v1',
        'dataset_version': 'windows_dense_v11_12gen_freeze_v1',
        'source_dataset': str(BASE_DATASET),
        'source_ga_histories': {tag: str(path) for tag, path in GA_HISTORY_BY_BAND.items()},
        'out_dir': str(OUT_DIR),
        'dataset_csv': str(out_csv),
        'rows_base': int(len(base_df)),
        'rows_valid_ga_source': int(len(ga_df)),
        'rows_train_source': int(len(train_source)),
        'rows_holdout_source': int(len(holdout_source)),
        'rows_added': int(len(added_df)),
        'rows_holdout': int(len(holdout_df)),
        'rows_total': int(len(out_df)),
        'thesis_windows': [{'low_Hz': low, 'high_Hz': high, 'tag': band_tag(low, high)} for low, high in THESIS_WINDOWS],
        'holdout_rule': 'for each origin target band, withhold exactly the valid 12-generation GA source row with maximum active_target_overlap_Hz; all other valid 12-generation rows are appended to training',
        'origin_summary_all_valid': origin_summary(ga_df),
        'origin_summary_train': origin_summary(train_source),
        'origin_summary_holdout': origin_summary(holdout_source),
        'added_summary': summarize(added_df),
        'holdout_summary': summarize(holdout_df),
        'full_summary_selected_windows': summarize(out_df[out_df['target_band_tag'].isin(selected_tags)]),
        'notes': [
            'This freeze dataset uses windows_dense_v4 as the base dataset to avoid later truth-asset and long-GA leakage from v6-v10 base data.',
            'Only valid COMSOL-in-loop GA rows from six thesis windows with generation in [1, 12] are considered.',
            'The best source row from each origin band is withheld before expanding rows to all thesis windows.',
            'Withheld rows are not appended to the training dataset and are reserved for leakage checks and thesis holdout figures.',
            'The separate 180-220 Hz long-budget 20-generation GA trace is not used here.',
        ],
    }
    write_json(info_json, info)

    print(f'[DONE] base rows: {len(base_df)}')
    print(f'[DONE] valid 12-gen GA source rows: {len(ga_df)}')
    print(f'[DONE] train source rows: {len(train_source)}')
    print(f'[DONE] holdout source rows: {len(holdout_source)}')
    print(f'[DONE] added rows: {len(added_df)}')
    print(f'[DONE] holdout rows: {len(holdout_df)}')
    print(f'[DONE] total rows: {len(out_df)}')
    print(f'[OUT] {out_csv}')
    print(f'[OUT] {added_csv}')
    print(f'[OUT] {holdout_csv}')
    print(f'[OUT] {info_json}')


if __name__ == '__main__':
    main()
