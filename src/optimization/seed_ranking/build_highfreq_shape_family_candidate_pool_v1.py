from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BASE_POOL = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_active_ga_multiband_neighborhood_v1' / 'candidate_pool_active_ga_multiband_neighborhood_v1.csv'
SHAPE_DATASET = ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv'
TEMPLATE_CSV = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_active_ga_multiband_neighborhood_v1' / 'active_ga_multiband_parameter_templates_v1.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_highfreq_shape_family_v1'

PARAM_COLS = ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']
FIXED_COLS = ['shift', 'neigs']
HIGHFREQ_TEMPLATE_BANDS = {'band180_220', 'band200_240', 'band220_260', 'band240_280'}


def as_float(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').fillna(default).astype(float)


def zscore(series: pd.Series) -> pd.Series:
    values = as_float(series)
    std = float(values.std(ddof=0))
    if std <= 1e-12:
        return values * 0.0
    return (values - float(values.mean())) / std


def compute_highfreq_scores(shape_df: pd.DataFrame) -> pd.DataFrame:
    out = shape_df.copy()
    area = as_float(out['shape_area']).clip(lower=1e-12)
    perimeter = as_float(out['shape_perimeter']).clip(lower=1e-12)
    point_count = as_float(out['shape_point_count'])
    width = as_float(out['shape_bbox_width']).clip(lower=1e-12)
    height = as_float(out['shape_bbox_height']).clip(lower=1e-12)
    aspect = width / height

    slenderness = perimeter / np.sqrt(area)
    small_scale = 1.0 / np.sqrt(area)
    aspect_balance = -np.abs(np.log(np.clip(aspect, 1e-6, None)))
    out['highfreq_slenderness'] = slenderness
    out['highfreq_small_scale'] = small_scale
    out['highfreq_aspect_balance'] = aspect_balance
    out['highfreq_geom_score'] = (
        0.42 * zscore(slenderness)
        + 0.28 * zscore(point_count)
        + 0.22 * zscore(small_scale)
        + 0.08 * zscore(aspect_balance)
    )
    return out


def select_new_family_representatives(
    shape_df: pd.DataFrame,
    existing_families: set[str],
    max_families: int = 96,
) -> pd.DataFrame:
    work = compute_highfreq_scores(shape_df)
    work['shape_family'] = work['shape_family'].astype(str)
    work['shape_id'] = work['shape_id'].astype(str)
    work = work[~work['shape_family'].isin(existing_families)].copy()
    work = work[work['shape_id'].map(lambda sid: (ROOT / 'data' / 'shape_contours' / f'{sid}.csv').exists())].copy()
    if work.empty:
        raise RuntimeError('No new shape families remain after exclusions.')
    reps = (
        work.sort_values(['shape_family', 'highfreq_geom_score', 'shape_id'], ascending=[True, False, True])
        .groupby('shape_family', as_index=False)
        .head(1)
        .sort_values(['highfreq_geom_score', 'shape_id'], ascending=[False, True])
        .head(max_families)
        .reset_index(drop=True)
    )
    reps['highfreq_family_rank'] = np.arange(1, len(reps) + 1)
    return reps


def load_templates() -> pd.DataFrame:
    templates = pd.read_csv(TEMPLATE_CSV)
    templates['template_origin_band_tag'] = templates['template_origin_band_tag'].astype(str)
    templates = templates[templates['template_origin_band_tag'].isin(HIGHFREQ_TEMPLATE_BANDS)].copy()
    if templates.empty:
        raise RuntimeError('No high-frequency parameter templates found.')
    for col in [*PARAM_COLS, *FIXED_COLS]:
        templates[col] = as_float(templates[col])
    return templates.reset_index(drop=True)


def base_defaults(base: pd.DataFrame) -> Dict[str, object]:
    return {col: '' for col in base.columns}


def make_new_rows(base: pd.DataFrame, reps: pd.DataFrame, templates: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    defaults = base_defaults(base)
    for _, shape in reps.iterrows():
        shape_id = str(shape['shape_id'])
        family = str(shape['shape_family'])
        rank = int(shape['highfreq_family_rank'])
        for tindex, tpl in templates.iterrows():
            row = dict(defaults)
            template_id = str(tpl['template_id'])
            origin_band = str(tpl['template_origin_band_tag'])
            row.update({
                'sample_id': f'candidate_pool_highfreq_family_v1_hf{rank:03d}_tpl{tindex + 1:03d}_{shape_id}',
                'source_stage': 'candidate_pool_highfreq_shape_family_v1',
                'source_role': 'highfreq_shape_family_expansion',
                'pool_arm': 'highfreq_shape_family',
                'point_strategy': 'multiband_ga_templates_on_new_highfreq_shape_families_v1',
                'family_prior_source': 'shape_geometry_highfreq_score_v1',
                'seed_prior_source': 'geometry_selected_new_family',
                'seed_shape_id': shape_id,
                'seed_family': family,
                'seed_step': '',
                'seed_tier': 'highfreq_geometry_probe',
                'seed_source': 'shape_dataset_highfreq_rank',
                'shape_step': '',
                'has_seed_context': 0,
                'step_num': '',
                'step_offset': '',
                'step_distance': '',
                'step_direction_sign': '',
                'step_window': 'new_highfreq_family',
                'is_seed_shape': 1,
                'preferred_direction_sign': '',
                'matches_preferred_direction': '',
                'within_directional_window': '',
                'selection_priority': rank,
                'target_rule': 'highfreq_shape_family_expansion',
                'preferred_direction': 'highfreq_geom_score',
                'directional_offset': '',
                'allowed_offsets': '',
                'stage1_reference_sample_id': '',
                'stage1_reference_fourier_id': '',
                'stage1_reference_gap_Hz': '',
                'stage1_reference_gap_gain_Hz': '',
                'stage1_reference_contact_length': '',
                'stage1_reference_candidate_tier': 'highfreq_geometry_probe',
                'shape_id': shape_id,
                'shape_family': family,
                'shape_role': 'screening_highfreq_family_probe',
                'candidate_id': f'hf{rank:03d}_tpl{tindex + 1:03d}',
                'main_id': 'highfreq_shape_family_v1',
                'point_id': template_id,
                'shape_area': float(shape['shape_area']),
                'shape_perimeter': float(shape['shape_perimeter']),
                'shape_bbox_width': float(shape['shape_bbox_width']),
                'shape_bbox_height': float(shape['shape_bbox_height']),
                'shape_bbox_aspect_ratio': float(shape['shape_bbox_aspect_ratio']),
                'shape_centroid_x': float(shape['shape_centroid_x']),
                'shape_centroid_y': float(shape['shape_centroid_y']),
                'shape_point_count': float(shape['shape_point_count']),
                'active_ga_template_id': template_id,
                'active_ga_template_type': str(tpl['template_type']),
                'active_ga_template_origin_band_tag': origin_band,
                'active_ga_template_source_sample_id': str(tpl['template_source_sample_id']),
                'active_ga_template_source_shape_id': str(tpl['template_source_shape_id']),
                'active_ga_template_source_overlap_Hz': float(tpl['template_source_overlap_Hz']),
                'highfreq_family_rank': rank,
                'highfreq_geom_score': float(shape['highfreq_geom_score']),
                'highfreq_slenderness': float(shape['highfreq_slenderness']),
                'highfreq_small_scale': float(shape['highfreq_small_scale']),
            })
            for col in PARAM_COLS:
                row[col] = float(tpl[col])
            for col in FIXED_COLS:
                row[col] = float(tpl[col])
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    base = pd.read_csv(BASE_POOL)
    shape_df = pd.read_csv(SHAPE_DATASET)
    templates = load_templates()
    existing_families = set(base['shape_family'].astype(str))
    reps = select_new_family_representatives(shape_df, existing_families)
    new_rows = make_new_rows(base, reps, templates)

    all_cols = list(dict.fromkeys([*base.columns.tolist(), *new_rows.columns.tolist()]))
    out = pd.concat([base.reindex(columns=all_cols), new_rows.reindex(columns=all_cols)], ignore_index=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / 'candidate_pool_highfreq_shape_family_v1.csv'
    reps_csv = OUT_DIR / 'highfreq_shape_family_representatives_v1.csv'
    info_json = OUT_DIR / 'candidate_pool_highfreq_shape_family_info_v1.json'
    out.to_csv(out_csv, index=False, encoding='utf-8-sig')
    reps.to_csv(reps_csv, index=False, encoding='utf-8-sig')
    info = {
        'base_pool': str(BASE_POOL),
        'shape_dataset': str(SHAPE_DATASET),
        'template_csv': str(TEMPLATE_CSV),
        'out_csv': str(out_csv),
        'representatives_csv': str(reps_csv),
        'rows_base': int(len(base)),
        'new_shape_families': int(reps['shape_family'].nunique()),
        'templates_used': int(len(templates)),
        'rows_added': int(len(new_rows)),
        'rows_total': int(len(out)),
        'template_origin_bands': sorted(HIGHFREQ_TEMPLATE_BANDS),
        'selection_rule': 'select previously unused shape families by highfreq_geom_score = slenderness + point count + small scale + aspect balance',
        'notes': [
            'This is a predictor-side high-frequency family expansion; rows are not COMSOL truth.',
            'The selected shapes already exist under data/shape_contours and can be passed to COMSOL validation.',
            'Stage1 reference fields are intentionally left blank so the scorer relies on geometry, contact model, and target-band predictors.',
        ],
    }
    info_json.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[DONE] base rows: {len(base)}')
    print(f'[DONE] new shape families: {reps.shape_family.nunique()}')
    print(f'[DONE] templates used: {len(templates)}')
    print(f'[DONE] added rows: {len(new_rows)}')
    print(f'[DONE] total rows: {len(out)}')
    print(f'[OUT] {out_csv}')
    print(f'[OUT] {reps_csv}')
    print(f'[OUT] {info_json}')


if __name__ == '__main__':
    main()
