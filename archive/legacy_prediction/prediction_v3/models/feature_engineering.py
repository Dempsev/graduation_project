from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from shared.features.prediction import PREDICTION_FEATURE_PRESETS

BASE_FEATURE_SET_NAME = 'pure_structural_local_v3'
ENRICHED_FEATURE_SET_NAME = 'pure_structural_tail_v3'

LOCAL_SHAPE_FIELDS = [
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


def build_tail_prediction_frame(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    work = df.copy()
    base_features = [*PREDICTION_FEATURE_PRESETS['pure_structural_extended'], *LOCAL_SHAPE_FIELDS]

    derived_features: List[str] = []
    energy_cols: List[str] = []
    for order in range(1, 6):
        a_col = f'a{order}'
        b_col = f'b{order}'
        a = pd.to_numeric(work.get(a_col), errors='coerce').fillna(0.0)
        b = pd.to_numeric(work.get(b_col), errors='coerce').fillna(0.0)

        amp_col = f'h{order}_amp'
        energy_col = f'h{order}_energy'
        work[amp_col] = np.sqrt(a * a + b * b)
        work[energy_col] = work[amp_col] ** 2
        work[f'h{order}_abs_a'] = np.abs(a)
        work[f'h{order}_abs_b'] = np.abs(b)
        derived_features.extend([amp_col, f'h{order}_abs_a', f'h{order}_abs_b'])
        energy_cols.append(energy_col)

    work['harmonic_energy_total'] = work[energy_cols].sum(axis=1)
    derived_features.append('harmonic_energy_total')
    harmonic_energy_slope = np.zeros(len(work), dtype=float)
    for order in range(1, 6):
        ratio_col = f'h{order}_energy_ratio'
        work[ratio_col] = work[f'h{order}_energy'] / (work['harmonic_energy_total'] + 1e-9)
        harmonic_energy_slope = harmonic_energy_slope + order * work[ratio_col].to_numpy(dtype=float)
        derived_features.append(ratio_col)
    work['harmonic_energy_slope'] = harmonic_energy_slope
    derived_features.append('harmonic_energy_slope')

    major_span = pd.to_numeric(work.get('shape_pca_major_span'), errors='coerce')
    minor_span = pd.to_numeric(work.get('shape_pca_minor_span'), errors='coerce')
    edge_p10 = pd.to_numeric(work.get('shape_edge_p10'), errors='coerce')
    edge_p90 = pd.to_numeric(work.get('shape_edge_p90'), errors='coerce')
    area = pd.to_numeric(work.get('shape_area'), errors='coerce')
    hull_area = pd.to_numeric(work.get('shape_hull_area'), errors='coerce')

    work['shape_neck_ratio_v3'] = edge_p10 / (minor_span + 1e-9)
    work['shape_edge_tail_ratio_v3'] = edge_p90 / (edge_p10 + 1e-9)
    work['shape_solidity_gap_v3'] = 1.0 - pd.to_numeric(work.get('shape_solidity'), errors='coerce')
    work['shape_hull_fill_gap_v3'] = (hull_area - area) / (hull_area + 1e-9)
    work['shape_turn_density_v3'] = pd.to_numeric(work.get('shape_turn_abs_mean'), errors='coerce') / (major_span + 1e-9)
    work['shape_minor_major_gap_v3'] = (major_span - minor_span) / (major_span + 1e-9)
    derived_features.extend([
        'shape_neck_ratio_v3',
        'shape_edge_tail_ratio_v3',
        'shape_solidity_gap_v3',
        'shape_hull_fill_gap_v3',
        'shape_turn_density_v3',
        'shape_minor_major_gap_v3',
    ])

    feature_sets = {
        BASE_FEATURE_SET_NAME: base_features,
        ENRICHED_FEATURE_SET_NAME: [*base_features, *derived_features],
    }
    return work, feature_sets
