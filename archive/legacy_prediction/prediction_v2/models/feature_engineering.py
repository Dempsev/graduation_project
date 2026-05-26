from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from shared.features.prediction import PREDICTION_FEATURE_PRESETS

BASE_FEATURE_SET_NAME = 'pure_structural_extended'
ENRICHED_FEATURE_SET_NAME = 'pure_structural_enriched_v2'


def build_enriched_prediction_frame(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    work = df.copy()
    base_features = list(PREDICTION_FEATURE_PRESETS[BASE_FEATURE_SET_NAME])

    derived_features: List[str] = []
    energy_cols: List[str] = []

    for order in range(1, 6):
        a_col = f'a{order}'
        b_col = f'b{order}'
        a = pd.to_numeric(work.get(a_col), errors='coerce').fillna(0.0)
        b = pd.to_numeric(work.get(b_col), errors='coerce').fillna(0.0)

        amp_col = f'h{order}_amp'
        energy_col = f'h{order}_energy'
        abs_a_col = f'h{order}_abs_a'
        abs_b_col = f'h{order}_abs_b'

        work[amp_col] = np.sqrt(a * a + b * b)
        work[energy_col] = work[amp_col] ** 2
        work[abs_a_col] = np.abs(a)
        work[abs_b_col] = np.abs(b)

        derived_features.extend([amp_col, abs_a_col, abs_b_col])
        energy_cols.append(energy_col)

    work['harmonic_energy_total'] = work[energy_cols].sum(axis=1)
    derived_features.append('harmonic_energy_total')

    harmonic_energy_slope = np.zeros(len(work), dtype=float)
    for order in range(1, 6):
        ratio_col = f'h{order}_energy_ratio'
        work[ratio_col] = work[f'h{order}_energy'] / (work['harmonic_energy_total'] + 1e-9)
        derived_features.append(ratio_col)
        harmonic_energy_slope = harmonic_energy_slope + order * work[ratio_col].to_numpy(dtype=float)
    work['harmonic_energy_slope'] = harmonic_energy_slope
    derived_features.append('harmonic_energy_slope')

    bbox_area = pd.to_numeric(work.get('shape_bbox_width'), errors='coerce') * pd.to_numeric(work.get('shape_bbox_height'), errors='coerce')
    work['bbox_fill_v2'] = pd.to_numeric(work.get('shape_area'), errors='coerce') / bbox_area.replace(0, np.nan)
    work['perimeter_area_ratio_v2'] = pd.to_numeric(work.get('shape_perimeter'), errors='coerce') / (pd.to_numeric(work.get('shape_area'), errors='coerce') + 1e-9)
    work['radius_span_v2'] = pd.to_numeric(work.get('shape_max_radius'), errors='coerce') - pd.to_numeric(work.get('shape_min_radius'), errors='coerce')
    work['edge_span_proxy_v2'] = pd.to_numeric(work.get('shape_edge_std'), errors='coerce') / (pd.to_numeric(work.get('shape_edge_mean'), errors='coerce') + 1e-9)
    derived_features.extend(['bbox_fill_v2', 'perimeter_area_ratio_v2', 'radius_span_v2', 'edge_span_proxy_v2'])

    feature_sets = {
        BASE_FEATURE_SET_NAME: base_features,
        ENRICHED_FEATURE_SET_NAME: [*base_features, *derived_features],
    }
    return work, feature_sets
