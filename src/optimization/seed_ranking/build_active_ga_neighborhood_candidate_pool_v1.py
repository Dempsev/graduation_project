from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BASE_POOL = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_optimization_v1' / 'candidate_pool_optimization_v1.csv'
GA_HISTORY = ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_targetband180_220_overlap_ga_v1' / 'ga_history_v1.csv'
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_active_ga_neighborhood_v1'

PARAM_COLS = ['a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']
FIXED_COLS = ['shift', 'neigs']


def as_float(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').fillna(default).astype(float)


def load_midtrajectory_prototypes() -> pd.DataFrame:
    ga = pd.read_csv(GA_HISTORY)
    for col in ['solve_success', 'contact_valid', 'geometry_valid']:
        ga[col] = pd.to_numeric(ga.get(col), errors='coerce').fillna(0).astype(int)
    ga['active_target_overlap_Hz'] = as_float(ga['active_target_overlap_Hz'])
    valid = ga[
        (ga['solve_success'] > 0)
        & (ga['contact_valid'] > 0)
        & (ga['geometry_valid'] > 0)
        & (ga['active_target_overlap_Hz'] >= 30.0)
        & (ga['active_target_overlap_Hz'] < 39.95)
    ].copy()
    if valid.empty:
        raise RuntimeError('No valid mid-trajectory GA rows found.')

    # Keep representative high-value parameter settings without using the final
    # full-cover answer. Sorting by overlap makes this deterministic.
    valid = valid.sort_values('active_target_overlap_Hz', ascending=False).reset_index(drop=True)
    dedupe_cols = PARAM_COLS
    for col in dedupe_cols:
        valid[col] = as_float(valid[col])
    valid['_param_key'] = valid[dedupe_cols].round(6).astype(str).agg('|'.join, axis=1)
    prototypes = valid.drop_duplicates('_param_key').head(18).copy()
    prototypes['prototype_source'] = 'ga_midtrajectory_top'
    return prototypes


def make_template_rows(prototypes: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for idx, src in prototypes.reset_index(drop=True).iterrows():
        row = {col: float(src[col]) for col in PARAM_COLS}
        row.update({'shift': 200.0, 'neigs': 20.0})
        row['template_id'] = f'ga_mid_top_{idx + 1:02d}'
        row['template_source_sample_id'] = str(src['sample_id'])
        row['template_source_shape_id'] = str(src['shape_id'])
        row['template_source_overlap_Hz'] = float(src['active_target_overlap_Hz'])
        row['template_type'] = 'ga_midtrajectory_direct'
        rows.append(row)

    high = prototypes.copy()
    high = high[[*PARAM_COLS, 'active_target_overlap_Hz']]
    weights = high['active_target_overlap_Hz'].to_numpy(dtype=float)
    weights = weights / weights.sum()
    mean_params = {col: float(np.average(high[col].to_numpy(dtype=float), weights=weights)) for col in PARAM_COLS}
    std_params = {col: float(np.sqrt(np.average((high[col].to_numpy(dtype=float) - mean_params[col]) ** 2, weights=weights))) for col in PARAM_COLS}
    mean_row = {**mean_params, 'shift': 200.0, 'neigs': 20.0}
    mean_row.update({
        'template_id': 'ga_mid_weighted_mean',
        'template_source_sample_id': 'weighted_mean_of_midtrajectory',
        'template_source_shape_id': 'ep206_step33_contour_xy',
        'template_source_overlap_Hz': float(high['active_target_overlap_Hz'].max()),
        'template_type': 'ga_midtrajectory_weighted_mean',
    })
    rows.append(mean_row)

    perturb_cols = ['a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0']
    for col in perturb_cols:
        scale = std_params.get(col, 0.0)
        if scale <= 1e-9:
            continue
        for sign, label in [(-0.6, 'minus'), (0.6, 'plus')]:
            perturbed = dict(mean_params)
            perturbed[col] = float(perturbed[col] + sign * scale)
            perturbed.update({'shift': 200.0, 'neigs': 20.0})
            perturbed.update({
                'template_id': f'ga_mid_mean_{col}_{label}',
                'template_source_sample_id': 'weighted_mean_local_perturbation',
                'template_source_shape_id': 'ep206_step33_contour_xy',
                'template_source_overlap_Hz': float(high['active_target_overlap_Hz'].max()),
                'template_type': 'ga_midtrajectory_mean_perturbation',
            })
            rows.append(perturbed)
    return rows


def clip_params(row: Dict[str, object]) -> Dict[str, object]:
    limits = {
        'a1': (0.35, 0.65),
        'a2': (-0.18, 0.02),
        'b1': (-0.08, 0.08),
        'b2': (-0.02, 0.10),
        'a3': (-0.04, 0.04),
        'b3': (-0.04, 0.04),
        'a4': (-0.03, 0.04),
        'b4': (-0.03, 0.03),
        'a5': (-0.03, 0.03),
        'b5': (-0.02, 0.04),
        'r0': (0.010, 0.015),
    }
    out = dict(row)
    for col, (lo, hi) in limits.items():
        out[col] = float(np.clip(float(out[col]), lo, hi))
    return out


def expand_pool(base: pd.DataFrame, templates: List[Dict[str, object]]) -> pd.DataFrame:
    seed_rows = base.sort_values(['shape_id', 'candidate_id']).drop_duplicates('shape_id').reset_index(drop=True)
    expanded: List[Dict[str, object]] = []
    for _, seed in seed_rows.iterrows():
        for idx, template in enumerate(templates, start=1):
            tpl = clip_params(template)
            row = seed.to_dict()
            shape_id = str(seed['shape_id'])
            row['sample_id'] = f'candidate_pool_active_ga_neighborhood_v1_ng{idx:03d}_{shape_id}'
            row['source_stage'] = 'candidate_pool_active_ga_neighborhood_v1'
            row['source_role'] = 'active_ga_parameter_neighborhood_expansion'
            row['pool_arm'] = 'active_ga_neighborhood'
            row['point_strategy'] = 'active_ga_midtrajectory_parameter_templates_v1'
            row['candidate_id'] = f'ng{idx:03d}'
            row['point_id'] = str(tpl['template_id'])
            row['main_id'] = 'active_ga_midtrajectory_v1'
            row['shape_role'] = 'screening_active_ga_neighborhood'
            for col in PARAM_COLS:
                row[col] = tpl[col]
            for col in FIXED_COLS:
                row[col] = tpl[col]
            row['active_ga_template_id'] = tpl['template_id']
            row['active_ga_template_type'] = tpl['template_type']
            row['active_ga_template_source_sample_id'] = tpl['template_source_sample_id']
            row['active_ga_template_source_shape_id'] = tpl['template_source_shape_id']
            row['active_ga_template_source_overlap_Hz'] = tpl['template_source_overlap_Hz']
            expanded.append(row)
    expanded_df = pd.DataFrame(expanded)
    all_cols = list(dict.fromkeys([*base.columns.tolist(), *expanded_df.columns.tolist()]))
    return pd.concat([base.reindex(columns=all_cols), expanded_df.reindex(columns=all_cols)], ignore_index=True)


def main() -> None:
    base = pd.read_csv(BASE_POOL)
    prototypes = load_midtrajectory_prototypes()
    templates = make_template_rows(prototypes)
    out = expand_pool(base, templates)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / 'candidate_pool_active_ga_neighborhood_v1.csv'
    prototype_csv = OUT_DIR / 'ga_midtrajectory_parameter_prototypes_v1.csv'
    template_csv = OUT_DIR / 'active_ga_parameter_templates_v1.csv'
    info_json = OUT_DIR / 'candidate_pool_active_ga_neighborhood_info_v1.json'

    out.to_csv(out_csv, index=False, encoding='utf-8-sig')
    prototypes.to_csv(prototype_csv, index=False, encoding='utf-8-sig')
    pd.DataFrame(templates).to_csv(template_csv, index=False, encoding='utf-8-sig')

    info = {
        'base_pool': str(BASE_POOL),
        'ga_history': str(GA_HISTORY),
        'out_csv': str(out_csv),
        'rows_base': int(len(base)),
        'unique_shapes': int(base['shape_id'].astype(str).nunique()),
        'templates': int(len(templates)),
        'rows_total': int(len(out)),
        'rows_added': int(len(out) - len(base)),
        'notes': [
            'Expanded candidates are generated from 180-220 Hz GA mid-trajectory parameter templates.',
            'Full-cover GA solutions with active_target_overlap_Hz >= 39.95 are not used as templates.',
            'The pool is intended for ML ranking before any COMSOL validation.',
        ],
    }
    info_json.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[DONE] base rows: {len(base)}')
    print(f'[DONE] templates: {len(templates)}')
    print(f'[DONE] total rows: {len(out)}')
    print(f'[OUT] {out_csv}')


if __name__ == '__main__':
    main()
