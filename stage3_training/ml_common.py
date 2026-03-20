from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = ROOT / 'data' / 'ml_runs'

SHAPE_ONLY_FEATURES = [
    'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height',
    'shape_bbox_aspect_ratio', 'shape_centroid_x', 'shape_centroid_y', 'shape_point_count',
]

DIRECTIONAL_CONTEXT_FEATURES = [
    'shape_step', 'has_seed_context', 'seed_step', 'step_num', 'step_offset', 'step_distance',
    'step_direction_sign', 'is_seed_shape', 'preferred_direction_sign',
    'matches_preferred_direction', 'within_directional_window',
]

STAGE1_REFERENCE_NUMERIC_FEATURES = [
    'has_stage1_reference',
    'stage1_reference_contact_valid',
    'stage1_reference_solve_success',
    'stage1_reference_is_positive_shape',
    'stage1_reference_gap_Hz',
    'stage1_reference_gap_gain_Hz',
    'stage1_reference_contact_length',
    'stage1_reference_candidate_tier_rank',
]

SURROGATE_CORE_FEATURES = [
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0',
    *SHAPE_ONLY_FEATURES,
]

PARAMETRIC_CLASSIFIER_FEATURES = [
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0',
    *SHAPE_ONLY_FEATURES,
]

PARAMETRIC_DIRECTIONAL_FEATURES = [
    *PARAMETRIC_CLASSIFIER_FEATURES,
    *DIRECTIONAL_CONTEXT_FEATURES,
]

PARAMETRIC_SEED_DISCOVERY_FEATURES = [
    *PARAMETRIC_DIRECTIONAL_FEATURES,
    *STAGE1_REFERENCE_NUMERIC_FEATURES,
]

SURROGATE_DIRECTIONAL_FEATURES = [
    *SURROGATE_CORE_FEATURES,
    *DIRECTIONAL_CONTEXT_FEATURES,
]

SURROGATE_SEED_DISCOVERY_FEATURES = [
    *SURROGATE_DIRECTIONAL_FEATURES,
    *STAGE1_REFERENCE_NUMERIC_FEATURES,
]

SURROGATE_GEO_EXTRA_FEATURES = ['contact_length', 'n_domains']


class MLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: Sequence[int], output_dim: int = 1, dropout: float = 0.0):
        super().__init__()
        layers: List[nn.Module] = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, output_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def parse_hidden_dims(text: str) -> List[int]:
    dims = [int(part.strip()) for part in text.split(',') if part.strip()]
    if not dims:
        raise ValueError('hidden dims must not be empty')
    return dims


def parse_group_keys(text: str, allowed: Sequence[str]) -> List[str]:
    allowed_set = set(allowed)
    keys = [part.strip() for part in text.split(',') if part.strip()]
    if not keys:
        raise ValueError('group keys must not be empty')
    invalid = [key for key in keys if key not in allowed_set]
    if invalid:
        raise ValueError(f'invalid group keys: {invalid}; allowed={sorted(allowed_set)}')
    return keys


def split_frame(df: pd.DataFrame, group_key: str, seed: int, train_ratio: float, val_ratio: float) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    if group_key == 'none':
        idx = np.arange(len(df))
        rng.shuffle(idx)
        train_end = max(1, int(len(idx) * train_ratio))
        val_end = max(train_end + 1, int(len(idx) * (train_ratio + val_ratio)))
        val_end = min(val_end, len(idx) - 1)
        return df.iloc[idx[:train_end]].copy(), df.iloc[idx[train_end:val_end]].copy(), df.iloc[idx[val_end:]].copy()

    groups = df[group_key].astype(str).fillna('')
    unique_groups = groups.unique().tolist()
    if len(unique_groups) < 3:
        return split_frame(df, 'none', seed, train_ratio, val_ratio)

    rng.shuffle(unique_groups)
    n_total = len(unique_groups)
    n_train = max(1, int(round(n_total * train_ratio)))
    n_val = max(1, int(round(n_total * val_ratio)))
    if n_train + n_val >= n_total:
        n_val = max(1, n_total - n_train - 1)
    if n_train + n_val >= n_total:
        n_train = max(1, n_total - n_val - 1)

    train_groups = set(unique_groups[:n_train])
    val_groups = set(unique_groups[n_train:n_train + n_val])
    test_groups = set(unique_groups[n_train + n_val:])
    if not test_groups:
        moved = val_groups.pop() if val_groups else train_groups.pop()
        test_groups.add(moved)

    train_df = df[groups.isin(train_groups)].copy()
    val_df = df[groups.isin(val_groups)].copy()
    test_df = df[groups.isin(test_groups)].copy()
    return train_df, val_df, test_df


def prepare_matrix(frame: pd.DataFrame, feature_cols: Sequence[str], target_col: str) -> Tuple[np.ndarray, np.ndarray]:
    x = frame.loc[:, feature_cols].astype(float).to_numpy()
    y = frame.loc[:, target_col].astype(float).to_numpy()
    return x, y


def fit_standardizer(x_train: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    means = np.nanmean(x_train, axis=0)
    stds = np.nanstd(x_train, axis=0)
    means = np.where(np.isfinite(means), means, 0.0)
    stds = np.where(np.isfinite(stds) & (stds > 0), stds, 1.0)
    return means, stds


def transform_features(x: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    filled = np.where(np.isfinite(x), x, means)
    return (filled - means) / stds


def fit_target_standardizer(y_train: np.ndarray) -> Tuple[float, float]:
    mean = float(np.mean(y_train))
    std = float(np.std(y_train))
    if not math.isfinite(std) or std <= 0:
        std = 1.0
    return mean, std


def transform_target(y: np.ndarray, mean: float, std: float) -> np.ndarray:
    return (y - mean) / std


def inverse_target(y_scaled: np.ndarray, mean: float, std: float) -> np.ndarray:
    return y_scaled * std + mean


def build_dataloader(x: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool, target_dtype: torch.dtype = torch.float32) -> DataLoader:
    dataset = TensorDataset(torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=target_dtype))
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    denom = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - np.sum((y_true - y_pred) ** 2) / denom) if denom > 0 else math.nan
    return {'mae': mae, 'rmse': rmse, 'r2': r2}


def binary_confusion(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, int]:
    yt = y_true.astype(int)
    yp = y_pred.astype(int)
    tp = int(np.sum((yt == 1) & (yp == 1)))
    tn = int(np.sum((yt == 0) & (yp == 0)))
    fp = int(np.sum((yt == 0) & (yp == 1)))
    fn = int(np.sum((yt == 1) & (yp == 0)))
    return {'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp}


def classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    y_pred = (y_prob >= threshold).astype(int)
    cm = binary_confusion(y_true, y_pred)
    total = len(y_true)
    accuracy = (cm['tp'] + cm['tn']) / total if total else math.nan
    precision = cm['tp'] / (cm['tp'] + cm['fp']) if (cm['tp'] + cm['fp']) > 0 else 0.0
    recall = cm['tp'] / (cm['tp'] + cm['fn']) if (cm['tp'] + cm['fn']) > 0 else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    tnr = cm['tn'] / (cm['tn'] + cm['fp']) if (cm['tn'] + cm['fp']) > 0 else math.nan
    if math.isfinite(tnr):
        balanced_accuracy = 0.5 * (recall + tnr)
    else:
        balanced_accuracy = recall
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'balanced_accuracy': float(balanced_accuracy),
    }


def save_csv_rows(path: Path, fieldnames: Sequence[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def save_history_csv(path: Path, history: List[Dict[str, float]]) -> None:
    if not history:
        save_csv_rows(path, ['epoch'], [])
        return
    fieldnames = list(history[0].keys())
    save_csv_rows(path, fieldnames, history)


def save_split_info(path: Path, group_key: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    split_info = {
        'group_key': group_key,
        'train_rows': int(len(train_df)),
        'val_rows': int(len(val_df)),
        'test_rows': int(len(test_df)),
        'train_groups': sorted(train_df[group_key].astype(str).unique().tolist()) if group_key != 'none' else [],
        'val_groups': sorted(val_df[group_key].astype(str).unique().tolist()) if group_key != 'none' else [],
        'test_groups': sorted(test_df[group_key].astype(str).unique().tolist()) if group_key != 'none' else [],
    }
    save_json(path, split_info)


def save_regression_stage_metrics(path: Path, test_frame: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    rows: List[Dict[str, object]] = []
    work = test_frame.copy()
    work['_y_true'] = y_true
    work['_y_pred'] = y_pred
    for stage, subset in work.groupby('source_stage'):
        metrics = regression_metrics(subset['_y_true'].to_numpy(), subset['_y_pred'].to_numpy())
        rows.append({'source_stage': stage, 'rows': int(len(subset)), **metrics})
    save_csv_rows(path, ['source_stage', 'rows', 'mae', 'rmse', 'r2'], rows)
