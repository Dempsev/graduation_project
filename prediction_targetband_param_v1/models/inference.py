from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd

from prediction_v3.dataset.build_pure_prediction_dataset_v3 import PURE_V3_FEATURE_FIELDS, compute_shape_features
from prediction_v3.models.feature_engineering import ENRICHED_FEATURE_SET_NAME, build_tail_prediction_frame
from shared.objectives.targetband import derive_band_tag


BAND_FEATURES = ['target_band_low_Hz', 'target_band_high_Hz', 'target_band_center_Hz', 'target_band_width_Hz']


def _attach_missing_shape_features(df: pd.DataFrame) -> pd.DataFrame:
    missing_cols = [col for col in PURE_V3_FEATURE_FIELDS if col not in df.columns]
    if not missing_cols:
        return df

    work = df.copy()
    cache: Dict[str, Dict[str, float]] = {}
    shape_ids = work.get('shape_id')
    if shape_ids is None:
        for col in missing_cols:
            work[col] = np.nan
        return work

    for shape_id in shape_ids.astype(str):
        if shape_id not in cache:
            cache[shape_id] = compute_shape_features(shape_id)
    for col in missing_cols:
        work[col] = [cache[str(shape_id)].get(col, np.nan) for shape_id in shape_ids.astype(str)]
    return work


def prepare_targetband_inference_frame(
    df: pd.DataFrame,
    band_low: float,
    band_high: float,
    band_tag: str | None = None,
) -> pd.DataFrame:
    work = _attach_missing_shape_features(df)
    work['target_band_low_Hz'] = float(band_low)
    work['target_band_high_Hz'] = float(band_high)
    work['target_band_center_Hz'] = 0.5 * (float(band_low) + float(band_high))
    work['target_band_width_Hz'] = float(band_high) - float(band_low)
    work['target_band_tag'] = str(band_tag or derive_band_tag(band_low, band_high))
    work, _ = build_tail_prediction_frame(work)
    return work


def _resolve_run_root(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _discover_model_paths(run_root: Path) -> List[Path]:
    root = _resolve_run_root(run_root)
    direct = sorted(root.glob('fold_*/model.joblib'))
    if direct:
        return direct
    nested = sorted(root.glob('*/fold_*/model.joblib'))
    if nested:
        return nested
    raise FileNotFoundError(f'No fold model.joblib files found under {run_root}')


def _fit_feature_matrix(frame: pd.DataFrame, feature_cols: List[str], fill_values: Dict[str, float]) -> np.ndarray:
    work = frame.copy()
    for col in feature_cols:
        if col not in work.columns:
            work[col] = float(fill_values.get(col, 0.0))
    work = work.loc[:, feature_cols].apply(pd.to_numeric, errors='coerce').copy()
    work = work.fillna({col: float(fill_values.get(col, 0.0)) for col in feature_cols})
    return work.to_numpy(dtype=float)


def _load_bundles(run_root: Path) -> List[Dict[str, object]]:
    return [joblib.load(path) for path in _discover_model_paths(run_root)]


def predict_targetband_classifier(frame: pd.DataFrame, run_root: Path) -> np.ndarray:
    bundles = _load_bundles(run_root)
    preds: List[np.ndarray] = []
    for bundle in bundles:
        feature_cols = list(bundle['feature_cols'])
        x = _fit_feature_matrix(frame, feature_cols, dict(bundle.get('fill_values', {})))
        model = bundle['model']
        pred = model.predict_proba(x)[:, 1]
        preds.append(np.asarray(pred, dtype=float))
    return np.mean(np.vstack(preds), axis=0)


def predict_targetband_regressor(frame: pd.DataFrame, run_root: Path) -> tuple[np.ndarray, str]:
    bundles = _load_bundles(run_root)
    preds: List[np.ndarray] = []
    target_name = ''
    for bundle in bundles:
        feature_cols = list(bundle['feature_cols'])
        x = _fit_feature_matrix(frame, feature_cols, dict(bundle.get('fill_values', {})))
        model = bundle['model']
        pred = np.asarray(model.predict(x), dtype=float)
        bundle_target = str(bundle.get('target', '')).strip()
        if bundle_target:
            target_name = bundle_target
        target_transform = str(bundle.get('target_transform', 'none')).strip()
        if target_transform == 'log1p':
            pred = np.expm1(pred)
        pred = np.clip(pred, 0.0, None)
        if target_name == 'target_gap_cover_ratio':
            pred = np.clip(pred, 0.0, 1.0)
        preds.append(pred)
    return np.mean(np.vstack(preds), axis=0), target_name


def build_targetband_prediction_frame(
    df: pd.DataFrame,
    band_low: float,
    band_high: float,
    classifier_run_root: Path,
    regressor_run_root: Path,
    band_tag: str | None = None,
) -> pd.DataFrame:
    frame = prepare_targetband_inference_frame(df, band_low, band_high, band_tag=band_tag)
    out = frame.copy()
    out['target_open_prob'] = predict_targetband_classifier(frame, classifier_run_root)
    reg_pred, reg_target = predict_targetband_regressor(frame, regressor_run_root)
    out['target_regression_target'] = reg_target or 'target_gap_cover_ratio'
    if out['target_regression_target'].iloc[0] == 'target_gap_overlap_Hz':
        out['target_gap_overlap_pred_Hz'] = reg_pred
        out['target_gap_cover_ratio_pred'] = reg_pred / np.clip(out['target_band_width_Hz'].to_numpy(dtype=float), 1e-12, None)
    else:
        out['target_gap_cover_ratio_pred'] = reg_pred
        out['target_gap_overlap_pred_Hz'] = reg_pred * out['target_band_width_Hz'].to_numpy(dtype=float)
    out['target_gap_cover_ratio_pred'] = np.clip(out['target_gap_cover_ratio_pred'], 0.0, 1.0)
    out['target_gap_overlap_pred_Hz'] = np.clip(out['target_gap_overlap_pred_Hz'], 0.0, None)
    return out
