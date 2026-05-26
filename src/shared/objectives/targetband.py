from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Dict, List


TARGETBAND_FIELDS = [
    'target_band_low_Hz',
    'target_band_high_Hz',
    'target_gap_is_open',
    'target_gap_overlap_Hz',
    'target_gap_cover_ratio',
    'target_gap_best_width_Hz',
    'target_gap_lower_edge_Hz',
    'target_gap_upper_edge_Hz',
    'target_gap_center_freq',
    'target_gap_lower_band',
    'target_gap_upper_band',
]


def empty_targetband_metrics(band_low: float, band_high: float) -> Dict[str, float]:
    metrics = {field: math.nan for field in TARGETBAND_FIELDS}
    metrics['target_band_low_Hz'] = float(band_low)
    metrics['target_band_high_Hz'] = float(band_high)
    metrics['target_gap_is_open'] = 0.0
    metrics['target_gap_overlap_Hz'] = 0.0
    metrics['target_gap_cover_ratio'] = 0.0
    return metrics


def derive_band_tag(band_low: float, band_high: float) -> str:
    return f'band{int(round(float(band_low)))}_{int(round(float(band_high)))}'


def _to_complex_real(text: str) -> float:
    cleaned = str(text).strip()
    if not cleaned:
        return math.nan
    try:
        return float(cleaned)
    except Exception:
        pass
    try:
        return float(complex(cleaned.replace('i', 'j')).real)
    except Exception:
        return math.nan


def _load_tbl1_series(tbl1_csv: Path) -> tuple[List[float], List[float]]:
    k_vals: List[float] = []
    freq_vals: List[float] = []
    with tbl1_csv.open('r', encoding='utf-8-sig') as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith('%'):
                continue
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:
                continue
            try:
                k_val = float(parts[0])
            except Exception:
                continue
            freq_val = _to_complex_real(parts[-1])
            if math.isfinite(freq_val):
                k_vals.append(k_val)
                freq_vals.append(freq_val)
    return k_vals, freq_vals


def compute_targetband_metrics_from_tbl1(tbl1_csv: Path, band_low: float, band_high: float) -> Dict[str, float]:
    metrics = empty_targetband_metrics(band_low, band_high)
    if not tbl1_csv.exists():
        return metrics

    k_vals, freq_vals = _load_tbl1_series(tbl1_csv)
    if not k_vals:
        return metrics

    unique_k = sorted(set(k_vals))
    bands_by_k: List[List[float]] = []
    max_bands = 0
    for k_val in unique_k:
        bands = sorted(freq_vals[idx] for idx, kv in enumerate(k_vals) if kv == k_val)
        bands_by_k.append(bands)
        max_bands = max(max_bands, len(bands))

    best_overlap = 0.0
    best_width = -math.inf
    best_lower = math.nan
    best_upper = math.nan
    best_lb = math.nan
    best_ub = math.nan

    for band_idx in range(max_bands - 1):
        lower: List[float] = []
        upper: List[float] = []
        for bands in bands_by_k:
            if len(bands) > band_idx + 1:
                lower.append(bands[band_idx])
                upper.append(bands[band_idx + 1])
        if not lower or not upper:
            continue
        lower_edge = max(lower)
        upper_edge = min(upper)
        gap_width = upper_edge - lower_edge
        if not math.isfinite(gap_width) or gap_width <= 0:
            continue
        overlap = max(0.0, min(upper_edge, band_high) - max(lower_edge, band_low))
        if overlap > best_overlap + 1e-12 or (abs(overlap - best_overlap) <= 1e-12 and gap_width > best_width):
            best_overlap = overlap
            best_width = gap_width
            best_lower = lower_edge
            best_upper = upper_edge
            best_lb = float(band_idx + 1)
            best_ub = float(band_idx + 2)

    if best_overlap <= 0.0:
        return metrics

    metrics['target_gap_is_open'] = 1.0
    metrics['target_gap_overlap_Hz'] = float(best_overlap)
    metrics['target_gap_cover_ratio'] = float(best_overlap / max(1e-12, band_high - band_low))
    metrics['target_gap_best_width_Hz'] = float(best_width)
    metrics['target_gap_lower_edge_Hz'] = float(best_lower)
    metrics['target_gap_upper_edge_Hz'] = float(best_upper)
    metrics['target_gap_center_freq'] = float(0.5 * (best_lower + best_upper))
    metrics['target_gap_lower_band'] = float(best_lb)
    metrics['target_gap_upper_band'] = float(best_ub)
    return metrics
