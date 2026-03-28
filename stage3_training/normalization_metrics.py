from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd


DEFAULT_REFERENCE_COLUMNS = (
    'ref_gap34_Hz',
    'stage1_reference_gap_Hz',
    'gap_target_Hz',
)


def first_existing_column(frame: pd.DataFrame, candidates: Sequence[str]) -> str:
    for name in candidates:
        if name in frame.columns:
            return name
    return ''


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors='coerce').astype(float)
    den = pd.to_numeric(denominator, errors='coerce').astype(float)
    out = np.full(len(num), np.nan, dtype=float)
    valid = np.isfinite(num) & np.isfinite(den) & (np.abs(den) > 1e-12)
    out[valid] = num[valid] / den[valid]
    return pd.Series(out, index=numerator.index if hasattr(numerator, 'index') else None, dtype=float)


def zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce').astype(float)
    finite = values[np.isfinite(values)]
    if finite.empty:
        return pd.Series(np.full(len(values), np.nan), index=values.index, dtype=float)
    mean = float(finite.mean())
    std = float(finite.std(ddof=0))
    if not np.isfinite(std) or std <= 1e-12:
        return pd.Series(np.full(len(values), np.nan), index=values.index, dtype=float)
    return (values - mean) / std


def robust_zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce').astype(float)
    finite = values[np.isfinite(values)]
    if finite.empty:
        return pd.Series(np.full(len(values), np.nan), index=values.index, dtype=float)
    median = float(finite.median())
    mad = float(np.nanmedian(np.abs(finite - median)))
    if not np.isfinite(mad) or mad <= 1e-12:
        return pd.Series(np.full(len(values), np.nan), index=values.index, dtype=float)
    return 0.67448975 * (values - median) / mad


def attach_normalization_columns(
    frame: pd.DataFrame,
    prediction_columns: Iterable[str] | None = None,
    reference_candidates: Sequence[str] = DEFAULT_REFERENCE_COLUMNS,
) -> pd.DataFrame:
    out = frame.copy()
    reference_col = first_existing_column(out, reference_candidates)

    metric_columns = [
        'gap34_Hz',
        'gap34_gain_Hz',
        'max_gap_Hz',
        'gap34_rel',
        'gap34_gain_rel',
    ]
    if prediction_columns:
        for col in prediction_columns:
            if col and col in out.columns and col not in metric_columns:
                metric_columns.append(col)

    for col in metric_columns:
        if col not in out.columns:
            continue
        out[col] = pd.to_numeric(out[col], errors='coerce')
        out[f'{col}_zscore'] = zscore(out[col])
        out[f'{col}_robust_zscore'] = robust_zscore(out[col])

        if reference_col:
            out[f'{col}_over_{reference_col}'] = safe_ratio(out[col], out[reference_col])
            out[f'{col}_pct_of_{reference_col}'] = 100.0 * out[f'{col}_over_{reference_col}']

    if reference_col:
        out['_normalization_reference_column'] = reference_col
    else:
        out['_normalization_reference_column'] = ''
    return out

