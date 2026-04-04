from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stage3_training.ml_common import (
    MLP,
    binary_confusion,
    build_dataloader,
    classification_metrics,
    fit_standardizer,
    parse_group_keys,
    parse_hidden_dims,
    regression_metrics,
    save_csv_rows,
    save_history_csv,
    save_json,
    save_split_info,
    set_seed,
    split_frame,
    transform_features,
)
from shared.features.prediction import ALLOWED_GROUP_KEYS, PREDICTION_FEATURE_PRESETS
from shared.objectives.prediction import PURE_WIDTH_TARGET_CHOICES
from shared.splits.prediction import split_external_stage_holdout

DEFAULT_DATASET = ROOT / 'data' / 'pure_prediction' / 'v1' / 'pure_bandgap_regression_v1.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'pure_prediction_runs'
FEATURE_PRESETS = PREDICTION_FEATURE_PRESETS
WIDTH_TARGET_CHOICES = PURE_WIDTH_TARGET_CHOICES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a two-stage pure prediction model: gap-open classifier + positive-width regressor.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--feature-preset', default='pure_structural_extended', choices=sorted(FEATURE_PRESETS.keys()))
    parser.add_argument('--target', default='gap34_width_Hz', choices=WIDTH_TARGET_CHOICES)
    parser.add_argument('--split-mode', default='grouped', choices=['grouped', 'stage_holdout'])
    parser.add_argument('--group-keys', default='shape_id,shape_family')
    parser.add_argument('--validation-group-key', default='shape_family', choices=ALLOWED_GROUP_KEYS)
    parser.add_argument('--test-stage-prefixes', default='stage4_validation')
    parser.add_argument('--run-name', default='pure_gap34width_twostage_v1')
    parser.add_argument('--epochs', type=int, default=500)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--hidden-dims', default='128,64')
    parser.add_argument('--dropout', type=float, default=0.0)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight-decay', type=float, default=1e-5)
    parser.add_argument('--patience', type=int, default=80)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--train-ratio', type=float, default=0.7)
    parser.add_argument('--val-ratio', type=float, default=0.15)
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--target-transform', default='log1p', choices=['none', 'log1p'])
    return parser.parse_args()


def select_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    work = df.copy()
    work = work[np.isfinite(work[target])].copy()
    work['gap_open_target'] = (pd.to_numeric(work[target], errors='coerce') > 1e-12).astype(int)
    return work


def transform_positive_target(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == 'log1p':
        return np.log1p(y)
    return y


def inverse_positive_target(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == 'log1p':
        return np.expm1(y)
    return y


def train_classifier(model: nn.Module, train_loader, x_val: np.ndarray, y_val: np.ndarray, args: argparse.Namespace) -> Tuple[nn.Module, List[Dict[str, float]]]:
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    train_targets = train_loader.dataset.tensors[1].numpy()
    train_pos = float(np.sum(train_targets == 1.0))
    train_neg = float(len(train_targets) - train_pos)
    pos_weight = torch.tensor([train_neg / train_pos], dtype=torch.float32) if train_pos > 0 else torch.tensor([1.0], dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    x_val_t = torch.tensor(x_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.float32)
    best_state = None
    best_val_f1 = -math.inf
    best_val_loss = math.inf
    patience_left = args.patience
    history: List[Dict[str, float]] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses: List[float] = []
        for xb, yb in train_loader:
            optimizer.zero_grad()
            logits = model(xb).reshape(-1)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))

        model.eval()
        with torch.no_grad():
            val_logits = model(x_val_t).reshape(-1)
            val_loss = float(criterion(val_logits, y_val_t).item())
            val_prob = torch.sigmoid(val_logits).cpu().numpy()
        val_metrics = classification_metrics(y_val, val_prob, threshold=args.threshold)
        history.append({
            'epoch': epoch,
            'train_loss': float(np.mean(train_losses)) if train_losses else math.nan,
            'val_loss': val_loss,
            'val_f1': float(val_metrics['f1']),
            'val_balanced_accuracy': float(val_metrics['balanced_accuracy']),
        })

        improved = (val_metrics['f1'] > best_val_f1 + 1e-6) or (
            abs(val_metrics['f1'] - best_val_f1) <= 1e-6 and val_loss < best_val_loss
        )
        if improved:
            best_val_f1 = float(val_metrics['f1'])
            best_val_loss = val_loss
            best_state = {key: value.cpu().clone() for key, value in model.state_dict().items()}
            patience_left = args.patience
        else:
            patience_left -= 1
            if patience_left <= 0:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, history


def train_regressor(
    model: nn.Module,
    train_loader,
    x_val: np.ndarray,
    y_val_scaled: np.ndarray,
    y_val_raw: np.ndarray,
    y_mean: float,
    y_std: float,
    args: argparse.Namespace,
) -> Tuple[nn.Module, List[Dict[str, float]]]:
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = nn.SmoothL1Loss(beta=1.0)

    x_val_t = torch.tensor(x_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val_scaled, dtype=torch.float32)
    best_state = None
    best_val_rmse = math.inf
    patience_left = args.patience
    history: List[Dict[str, float]] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses: List[float] = []
        for xb, yb in train_loader:
            optimizer.zero_grad()
            pred = model(xb).reshape(-1)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))

        model.eval()
        with torch.no_grad():
            val_pred_scaled = model(x_val_t).reshape(-1)
            val_loss = float(criterion(val_pred_scaled, y_val_t).item())
            val_pred = inverse_positive_target(val_pred_scaled.cpu().numpy() * y_std + y_mean, args.target_transform)
        val_rmse = regression_metrics(y_val_raw, val_pred)['rmse']
        history.append({
            'epoch': epoch,
            'train_loss': float(np.mean(train_losses)) if train_losses else math.nan,
            'val_loss': val_loss,
            'val_rmse_positive_only': float(val_rmse),
        })
        if val_rmse < best_val_rmse:
            best_val_rmse = float(val_rmse)
            best_state = {key: value.cpu().clone() for key, value in model.state_dict().items()}
            patience_left = args.patience
        else:
            patience_left -= 1
            if patience_left <= 0:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, history


def predict_classifier_proba(model: nn.Module, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(x, dtype=torch.float32)).reshape(-1)
        return torch.sigmoid(logits).cpu().numpy()


def predict_positive_width(model: nn.Module, x: np.ndarray, y_mean: float, y_std: float, transform_mode: str) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        pred_scaled = model(torch.tensor(x, dtype=torch.float32)).reshape(-1).cpu().numpy()
    pred_transformed = pred_scaled * y_std + y_mean
    pred_raw = inverse_positive_target(pred_transformed, transform_mode)
    return np.clip(pred_raw, 0.0, None)


def split_frames(df: pd.DataFrame, args: argparse.Namespace, group_key: str | None = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    if args.split_mode == 'grouped':
        assert group_key is not None
        train_df, val_df, test_df = split_frame(df, group_key, args.seed, args.train_ratio, args.val_ratio)
        return train_df, val_df, test_df, group_key

    test_stage_prefixes = [part.strip() for part in args.test_stage_prefixes.split(',') if part.strip()]
    train_pool, test_df = split_external_stage_holdout(df, test_stage_prefixes)
    pool_total = args.train_ratio + args.val_ratio
    train_ratio_within_pool = args.train_ratio / pool_total
    val_ratio_within_pool = args.val_ratio / pool_total
    train_df, val_df, _ = split_frame(train_pool, args.validation_group_key, args.seed, train_ratio_within_pool, val_ratio_within_pool)
    return train_df, val_df, test_df, f'external_stage_holdout::{args.validation_group_key}'


def save_prediction_rows(
    path: Path,
    splits: Dict[str, pd.DataFrame],
    open_truth: Dict[str, np.ndarray],
    width_truth: Dict[str, np.ndarray],
    open_prob: Dict[str, np.ndarray],
    width_positive_pred: Dict[str, np.ndarray],
    expected_width_pred: Dict[str, np.ndarray],
    threshold: float,
) -> None:
    rows: List[Dict[str, object]] = []
    for split_name, frame in splits.items():
        probs = open_prob[split_name]
        truth_open = open_truth[split_name]
        truth_width = width_truth[split_name]
        pos_pred = width_positive_pred[split_name]
        exp_pred = expected_width_pred[split_name]
        pred_open = (probs >= threshold).astype(int)
        for idx, (_, row) in enumerate(frame.iterrows()):
            rows.append({
                'split': split_name,
                'sample_id': row['sample_id'],
                'source_stage': row['source_stage'],
                'shape_id': row['shape_id'],
                'shape_family': row['shape_family'],
                'point_id': row.get('point_id', ''),
                'gap_open_true': int(truth_open[idx]),
                'gap_open_prob': float(probs[idx]),
                'gap_open_pred': int(pred_open[idx]),
                'width_true': float(truth_width[idx]),
                'width_positive_pred': float(pos_pred[idx]),
                'width_expected_pred': float(exp_pred[idx]),
                'abs_error_expected': float(abs(truth_width[idx] - exp_pred[idx])),
            })
    save_csv_rows(
        path,
        ['split', 'sample_id', 'source_stage', 'shape_id', 'shape_family', 'point_id', 'gap_open_true', 'gap_open_prob',
         'gap_open_pred', 'width_true', 'width_positive_pred', 'width_expected_pred', 'abs_error_expected'],
        rows,
    )


def save_stage_metrics(path: Path, frame: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    rows: List[Dict[str, object]] = []
    work = frame.reset_index(drop=True).copy()
    work['y_true'] = y_true
    work['y_pred'] = y_pred
    for stage_name, subset in work.groupby('source_stage'):
        metrics = regression_metrics(subset['y_true'].to_numpy(dtype=float), subset['y_pred'].to_numpy(dtype=float))
        rows.append({
            'source_stage': stage_name,
            'rows': int(len(subset)),
            'mae': float(metrics['mae']),
            'rmse': float(metrics['rmse']),
            'r2': float(metrics['r2']),
        })
    save_csv_rows(path, ['source_stage', 'rows', 'mae', 'rmse', 'r2'], rows)


def save_plot(path: Path, classifier_history: List[Dict[str, float]], reg_history: List[Dict[str, float]], y_true: np.ndarray, y_pred: np.ndarray, metrics: Dict[str, float], target_col: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    axes[0].plot([row['epoch'] for row in classifier_history], [row['train_loss'] for row in classifier_history], label='train_loss')
    axes[0].plot([row['epoch'] for row in classifier_history], [row['val_loss'] for row in classifier_history], label='val_loss')
    axes[0].set_title('Gap-Open Classifier')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('BCE loss')
    axes[0].legend()

    axes[1].plot([row['epoch'] for row in reg_history], [row['train_loss'] for row in reg_history], label='train_loss')
    axes[1].plot([row['epoch'] for row in reg_history], [row['val_loss'] for row in reg_history], label='val_loss')
    axes[1].set_title('Positive-Width Regressor')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Huber loss')
    axes[1].legend()

    axes[2].scatter(y_true, y_pred, s=18, alpha=0.8)
    line_min = min(np.min(y_true), np.min(y_pred))
    line_max = max(np.max(y_true), np.max(y_pred))
    axes[2].plot([line_min, line_max], [line_min, line_max], 'r--', linewidth=1)
    axes[2].set_title(f'Expected Width Prediction: {target_col}')
    axes[2].set_xlabel('True')
    axes[2].set_ylabel('Predicted')
    axes[2].text(
        0.03,
        0.97,
        f"MAE={metrics['mae']:.3f}\nRMSE={metrics['rmse']:.3f}\nR2={metrics['r2']:.3f}",
        transform=axes[2].transAxes,
        va='top',
    )

    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def train_one_split(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    args: argparse.Namespace,
    split_dir: Path,
    split_label: str,
    hidden_dims: List[int],
) -> Dict[str, object]:
    for split_name, frame in [('train', train_df), ('val', val_df), ('test', test_df)]:
        if frame.empty:
            raise RuntimeError(f'{split_name} split is empty for {split_label}.')

    x_train_raw = train_df.loc[:, feature_cols].astype(float).to_numpy()
    x_val_raw = val_df.loc[:, feature_cols].astype(float).to_numpy()
    x_test_raw = test_df.loc[:, feature_cols].astype(float).to_numpy()

    y_open_train = train_df['gap_open_target'].astype(float).to_numpy()
    y_open_val = val_df['gap_open_target'].astype(float).to_numpy()
    y_open_test = test_df['gap_open_target'].astype(float).to_numpy()

    y_width_train = train_df[args.target].astype(float).to_numpy()
    y_width_val = val_df[args.target].astype(float).to_numpy()
    y_width_test = test_df[args.target].astype(float).to_numpy()

    positive_train = train_df[train_df['gap_open_target'] == 1].copy()
    positive_val = val_df[val_df['gap_open_target'] == 1].copy()
    positive_test = test_df[test_df['gap_open_target'] == 1].copy()
    if positive_train.empty or positive_val.empty or positive_test.empty:
        raise RuntimeError(f'Positive-width subset is empty for {split_label}.')

    x_mean, x_std = fit_standardizer(x_train_raw)
    x_train = transform_features(x_train_raw, x_mean, x_std)
    x_val = transform_features(x_val_raw, x_mean, x_std)
    x_test = transform_features(x_test_raw, x_mean, x_std)

    x_train_pos = transform_features(positive_train.loc[:, feature_cols].astype(float).to_numpy(), x_mean, x_std)
    x_val_pos = transform_features(positive_val.loc[:, feature_cols].astype(float).to_numpy(), x_mean, x_std)
    x_test_pos = transform_features(positive_test.loc[:, feature_cols].astype(float).to_numpy(), x_mean, x_std)

    y_width_train_pos_raw = positive_train[args.target].astype(float).to_numpy()
    y_width_val_pos_raw = positive_val[args.target].astype(float).to_numpy()
    y_width_test_pos_raw = positive_test[args.target].astype(float).to_numpy()
    y_width_train_pos_trans = transform_positive_target(y_width_train_pos_raw, args.target_transform)
    y_width_val_pos_trans = transform_positive_target(y_width_val_pos_raw, args.target_transform)

    y_mean = float(np.mean(y_width_train_pos_trans))
    y_std = float(np.std(y_width_train_pos_trans))
    if not math.isfinite(y_std) or y_std <= 0:
        y_std = 1.0
    y_train_scaled = (y_width_train_pos_trans - y_mean) / y_std
    y_val_scaled = (y_width_val_pos_trans - y_mean) / y_std

    split_dir.mkdir(parents=True, exist_ok=True)

    clf_model = MLP(input_dim=x_train.shape[1], hidden_dims=hidden_dims, output_dim=1, dropout=args.dropout)
    clf_loader = build_dataloader(x_train, y_open_train, args.batch_size, shuffle=True)
    clf_model, clf_history = train_classifier(clf_model, clf_loader, x_val, y_open_val, args)

    reg_model = MLP(input_dim=x_train.shape[1], hidden_dims=hidden_dims, output_dim=1, dropout=args.dropout)
    reg_loader = build_dataloader(x_train_pos, y_train_scaled, args.batch_size, shuffle=True)
    reg_model, reg_history = train_regressor(reg_model, reg_loader, x_val_pos, y_val_scaled, y_width_val_pos_raw, y_mean, y_std, args)

    open_prob = {
        'train': predict_classifier_proba(clf_model, x_train),
        'val': predict_classifier_proba(clf_model, x_val),
        'test': predict_classifier_proba(clf_model, x_test),
    }
    width_positive_pred = {
        'train': predict_positive_width(reg_model, x_train, y_mean, y_std, args.target_transform),
        'val': predict_positive_width(reg_model, x_val, y_mean, y_std, args.target_transform),
        'test': predict_positive_width(reg_model, x_test, y_mean, y_std, args.target_transform),
    }
    expected_width_pred = {
        split: open_prob[split] * width_positive_pred[split]
        for split in ['train', 'val', 'test']
    }

    clf_metrics = {
        'train': classification_metrics(y_open_train, open_prob['train'], threshold=args.threshold),
        'val': classification_metrics(y_open_val, open_prob['val'], threshold=args.threshold),
        'test': classification_metrics(y_open_test, open_prob['test'], threshold=args.threshold),
    }
    width_metrics = {
        'train_expected': regression_metrics(y_width_train, expected_width_pred['train']),
        'val_expected': regression_metrics(y_width_val, expected_width_pred['val']),
        'test_expected': regression_metrics(y_width_test, expected_width_pred['test']),
        'train_positive_only': regression_metrics(y_width_train_pos_raw, width_positive_pred['train'][y_open_train > 0.5]),
        'val_positive_only': regression_metrics(y_width_val_pos_raw, width_positive_pred['val'][y_open_val > 0.5]),
        'test_positive_only': regression_metrics(y_width_test_pos_raw, width_positive_pred['test'][y_open_test > 0.5]),
    }

    torch.save({
        'model_state_dict': clf_model.state_dict(),
        'input_dim': int(x_train.shape[1]),
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'feature_cols': feature_cols,
        'x_mean': x_mean.tolist(),
        'x_std': x_std.tolist(),
        'task': 'gap_open_classifier',
        'target': args.target,
        'threshold': args.threshold,
    }, split_dir / 'classifier_model.pt')
    torch.save({
        'model_state_dict': reg_model.state_dict(),
        'input_dim': int(x_train.shape[1]),
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'feature_cols': feature_cols,
        'x_mean': x_mean.tolist(),
        'x_std': x_std.tolist(),
        'task': 'positive_width_regressor',
        'target': args.target,
        'target_transform': args.target_transform,
        'y_mean': y_mean,
        'y_std': y_std,
    }, split_dir / 'regressor_model.pt')

    save_history_csv(split_dir / 'classifier_history.csv', clf_history)
    save_history_csv(split_dir / 'regressor_history.csv', reg_history)
    save_prediction_rows(
        split_dir / 'predictions.csv',
        {'train': train_df, 'val': val_df, 'test': test_df},
        {'train': y_open_train, 'val': y_open_val, 'test': y_open_test},
        {'train': y_width_train, 'val': y_width_val, 'test': y_width_test},
        open_prob,
        width_positive_pred,
        expected_width_pred,
        args.threshold,
    )
    save_stage_metrics(split_dir / 'test_expected_metrics_by_stage.csv', test_df, y_width_test, expected_width_pred['test'])
    save_plot(split_dir / 'training_summary.png', clf_history, reg_history, y_width_test, expected_width_pred['test'], width_metrics['test_expected'], args.target)
    split_info_group_key = split_label if split_label in ALLOWED_GROUP_KEYS else args.validation_group_key
    save_split_info(split_dir / 'split_info.json', split_info_group_key, train_df, val_df, test_df)
    save_json(split_dir / 'config.json', {
        'dataset': str(args.dataset),
        'feature_preset': args.feature_preset,
        'target': args.target,
        'split_mode': args.split_mode,
        'split_label': split_label,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'lr': args.lr,
        'weight_decay': args.weight_decay,
        'patience': args.patience,
        'seed': args.seed,
        'feature_cols': feature_cols,
        'threshold': args.threshold,
        'target_transform': args.target_transform,
        'branch_type': 'pure_prediction_twostage',
    })
    save_json(split_dir / 'metrics.json', {
        'classification': clf_metrics,
        'regression': width_metrics,
    })

    return {
        'classification_test': clf_metrics['test'],
        'regression_test_expected': width_metrics['test_expected'],
        'regression_test_positive_only': width_metrics['test_positive_only'],
    }


def train_for_group(df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace, run_root: Path, group_key: str, hidden_dims: List[int]) -> Dict[str, object]:
    train_df, val_df, test_df, split_label = split_frames(df, args, group_key=group_key)
    split_dir = run_root / group_key
    return train_one_split(train_df, val_df, test_df, feature_cols, args, split_dir, split_label, hidden_dims)


def train_stage_holdout(df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace, run_root: Path, hidden_dims: List[int]) -> Dict[str, object]:
    train_df, val_df, test_df, split_label = split_frames(df, args)
    split_dir = run_root / 'external_stage_holdout'
    return train_one_split(train_df, val_df, test_df, feature_cols, args, split_dir, split_label, hidden_dims)


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    hidden_dims = parse_hidden_dims(args.hidden_dims)
    group_keys = parse_group_keys(args.group_keys, ALLOWED_GROUP_KEYS)

    df = pd.read_csv(args.dataset)
    df = select_rows(df, args.target)
    if df.empty:
        raise RuntimeError('No rows remain after target filtering.')

    preset_cols = FEATURE_PRESETS[args.feature_preset]
    feature_cols = [col for col in preset_cols if col in df.columns]
    missing = [col for col in preset_cols if col not in df.columns]
    if missing:
        print(f'[WARN] missing features ignored: {missing}')
    if not feature_cols:
        raise RuntimeError('No usable feature columns found for pure prediction two-stage model.')

    run_root = DEFAULT_OUT_ROOT / args.run_name
    run_root.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Dict[str, object]] = {}
    if args.split_mode == 'grouped':
        for group_key in group_keys:
            summary[group_key] = train_for_group(df, feature_cols, args, run_root, group_key, hidden_dims)
    else:
        summary['external_stage_holdout'] = train_stage_holdout(df, feature_cols, args, run_root, hidden_dims)

    save_json(run_root / 'metrics_by_group.json', summary)
    save_json(run_root / 'run_config.json', {
        'dataset': str(args.dataset),
        'feature_preset': args.feature_preset,
        'target': args.target,
        'split_mode': args.split_mode,
        'group_keys': group_keys,
        'validation_group_key': args.validation_group_key,
        'test_stage_prefixes': args.test_stage_prefixes,
        'run_name': args.run_name,
        'feature_cols': feature_cols,
        'threshold': args.threshold,
        'target_transform': args.target_transform,
        'branch_type': 'pure_prediction_twostage',
    })

    print('[DONE] pure prediction two-stage training complete')
    print(f'[RUN] {run_root}')
    for split_name, metrics in summary.items():
        cls = metrics['classification_test']
        reg = metrics['regression_test_expected']
        pos = metrics['regression_test_positive_only']
        print(
            f"[TEST:{split_name}] cls_f1={cls['f1']:.4f} cls_bal_acc={cls['balanced_accuracy']:.4f} "
            f"exp_mae={reg['mae']:.4f} exp_rmse={reg['rmse']:.4f} exp_r2={reg['r2']:.4f} "
            f"pos_mae={pos['mae']:.4f} pos_rmse={pos['rmse']:.4f} pos_r2={pos['r2']:.4f}"
        )


if __name__ == '__main__':
    main()
