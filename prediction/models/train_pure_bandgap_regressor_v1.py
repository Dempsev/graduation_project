from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stage3_training.ml_common import (
    MLP,
    build_dataloader,
    fit_standardizer,
    fit_target_standardizer,
    inverse_target,
    parse_group_keys,
    parse_hidden_dims,
    prepare_matrix,
    regression_metrics,
    save_csv_rows,
    save_history_csv,
    save_json,
    save_split_info,
    set_seed,
    split_frame,
    transform_features,
    transform_target,
)
from shared.features.prediction import ALLOWED_GROUP_KEYS, PREDICTION_FEATURE_PRESETS
from shared.objectives.prediction import PURE_REGRESSION_TARGET_CHOICES
from shared.splits.prediction import split_external_stage_holdout

DEFAULT_DATASET = ROOT / 'data' / 'pure_prediction' / 'v1' / 'pure_bandgap_regression_v1.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'pure_prediction_runs'
FEATURE_PRESETS = PREDICTION_FEATURE_PRESETS
TARGET_CHOICES = PURE_REGRESSION_TARGET_CHOICES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train a pure-prediction MLP regressor for bandgap targets.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--feature-preset', default='pure_structural_extended', choices=sorted(FEATURE_PRESETS.keys()))
    parser.add_argument('--target', default='gap34_Hz', choices=TARGET_CHOICES)
    parser.add_argument('--split-mode', default='grouped', choices=['grouped', 'stage_holdout'])
    parser.add_argument('--group-keys', default='shape_id,shape_family')
    parser.add_argument('--validation-group-key', default='shape_family', choices=ALLOWED_GROUP_KEYS)
    parser.add_argument('--test-stage-prefixes', default='stage4_validation')
    parser.add_argument('--run-name', default='pure_gap34_predictor_v1')
    parser.add_argument('--loss', default='huber', choices=['mse', 'huber'])
    parser.add_argument('--epochs', type=int, default=600)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--hidden-dims', default='128,64')
    parser.add_argument('--dropout', type=float, default=0.0)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight-decay', type=float, default=1e-5)
    parser.add_argument('--patience', type=int, default=80)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--train-ratio', type=float, default=0.7)
    parser.add_argument('--val-ratio', type=float, default=0.15)
    return parser.parse_args()


def select_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    work = df.copy()
    work = work[np.isfinite(work[target])].copy()
    return work


def build_loss(loss_name: str) -> nn.Module:
    if loss_name == 'huber':
        # Pure fixed-gap labels contain large-magnitude failures; Huber is less sensitive than MSE.
        return nn.SmoothL1Loss(beta=1.0)
    return nn.MSELoss()


def train_model(
    model: nn.Module,
    train_loader,
    x_val: np.ndarray,
    y_val_scaled: np.ndarray,
    y_val_raw: np.ndarray,
    args: argparse.Namespace,
    y_mean: float,
    y_std: float,
) -> tuple[nn.Module, List[Dict[str, float]]]:
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = build_loss(args.loss)

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
            val_pred = inverse_target(val_pred_scaled.cpu().numpy(), y_mean, y_std)
        val_rmse = regression_metrics(y_val_raw, val_pred)['rmse']
        history.append({
            'epoch': epoch,
            'train_loss': float(np.mean(train_losses)) if train_losses else math.nan,
            'val_loss': val_loss,
            'val_rmse': float(val_rmse),
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


def predict(model: nn.Module, x: np.ndarray, y_mean: float, y_std: float) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        pred_scaled = model(torch.tensor(x, dtype=torch.float32)).cpu().numpy().reshape(-1)
    return inverse_target(pred_scaled, y_mean, y_std)


def save_predictions(path: Path, splits: Dict[str, pd.DataFrame], y_true: Dict[str, np.ndarray], y_pred: Dict[str, np.ndarray], target_col: str) -> None:
    rows: List[Dict[str, object]] = []
    for split_name, frame in splits.items():
        truth = y_true[split_name]
        pred = y_pred[split_name]
        for idx, (_, row) in enumerate(frame.iterrows()):
            rows.append({
                'split': split_name,
                'sample_id': row['sample_id'],
                'source_stage': row['source_stage'],
                'shape_id': row['shape_id'],
                'shape_family': row['shape_family'],
                'point_id': row.get('point_id', ''),
                'target_name': target_col,
                'y_true': float(truth[idx]),
                'y_pred': float(pred[idx]),
                'abs_error': float(abs(truth[idx] - pred[idx])),
            })
    save_csv_rows(
        path,
        ['split', 'sample_id', 'source_stage', 'shape_id', 'shape_family', 'point_id', 'target_name', 'y_true', 'y_pred', 'abs_error'],
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


def save_plot(path: Path, history: List[Dict[str, float]], y_true: np.ndarray, y_pred: np.ndarray, metrics: Dict[str, float], target_col: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot([row['epoch'] for row in history], [row['train_loss'] for row in history], label='train_loss')
    axes[0].plot([row['epoch'] for row in history], [row['val_loss'] for row in history], label='val_loss')
    axes[0].set_title('Training Curve')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Scaled regression loss')
    axes[0].legend()

    axes[1].scatter(y_true, y_pred, s=18, alpha=0.8)
    line_min = min(np.min(y_true), np.min(y_pred))
    line_max = max(np.max(y_true), np.max(y_pred))
    axes[1].plot([line_min, line_max], [line_min, line_max], 'r--', linewidth=1)
    axes[1].set_title(f'Test Prediction: {target_col}')
    axes[1].set_xlabel('True')
    axes[1].set_ylabel('Predicted')
    axes[1].text(
        0.03,
        0.97,
        f"MAE={metrics['mae']:.3f}\nRMSE={metrics['rmse']:.3f}\nR2={metrics['r2']:.3f}",
        transform=axes[1].transAxes,
        va='top',
    )

    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_checkpoint(
    path: Path,
    model: nn.Module,
    x_train: np.ndarray,
    x_mean: np.ndarray,
    x_std: np.ndarray,
    hidden_dims: List[int],
    args: argparse.Namespace,
    feature_cols: List[str],
    y_mean: float,
    y_std: float,
    split_mode: str,
) -> None:
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_dim': int(x_train.shape[1]),
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'feature_cols': feature_cols,
        'x_mean': x_mean.tolist(),
        'x_std': x_std.tolist(),
        'y_mean': y_mean,
        'y_std': y_std,
        'target': args.target,
        'branch_type': 'pure_prediction',
        'split_mode': split_mode,
        'loss': args.loss,
    }, path)


def train_one_split(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    args: argparse.Namespace,
    split_dir: Path,
    split_label: str,
    hidden_dims: List[int],
) -> Dict[str, float]:
    for split_name, frame in [('train', train_df), ('val', val_df), ('test', test_df)]:
        if frame.empty:
            raise RuntimeError(f'{split_name} split is empty for {split_label}.')

    x_train_raw, y_train_raw = prepare_matrix(train_df, feature_cols, args.target)
    x_val_raw, y_val_raw = prepare_matrix(val_df, feature_cols, args.target)
    x_test_raw, y_test_raw = prepare_matrix(test_df, feature_cols, args.target)

    x_mean, x_std = fit_standardizer(x_train_raw)
    x_train = transform_features(x_train_raw, x_mean, x_std)
    x_val = transform_features(x_val_raw, x_mean, x_std)
    x_test = transform_features(x_test_raw, x_mean, x_std)

    y_mean, y_std = fit_target_standardizer(y_train_raw)
    y_train = transform_target(y_train_raw, y_mean, y_std)
    y_val = transform_target(y_val_raw, y_mean, y_std)

    split_dir.mkdir(parents=True, exist_ok=True)

    model = MLP(input_dim=x_train.shape[1], hidden_dims=hidden_dims, output_dim=1, dropout=args.dropout)
    train_loader = build_dataloader(x_train, y_train, args.batch_size, shuffle=True)
    model, history = train_model(model, train_loader, x_val, y_val, y_val_raw, args, y_mean, y_std)

    pred_train = predict(model, x_train, y_mean, y_std)
    pred_val = predict(model, x_val, y_mean, y_std)
    pred_test = predict(model, x_test, y_mean, y_std)

    metrics = {
        'train': regression_metrics(y_train_raw, pred_train),
        'val': regression_metrics(y_val_raw, pred_val),
        'test': regression_metrics(y_test_raw, pred_test),
    }

    save_checkpoint(split_dir / 'model.pt', model, x_train, x_mean, x_std, hidden_dims, args, feature_cols, y_mean, y_std, args.split_mode)
    save_history_csv(split_dir / 'train_history.csv', history)
    save_predictions(
        split_dir / 'predictions.csv',
        {'train': train_df, 'val': val_df, 'test': test_df},
        {'train': y_train_raw, 'val': y_val_raw, 'test': y_test_raw},
        {'train': pred_train, 'val': pred_val, 'test': pred_test},
        args.target,
    )
    save_stage_metrics(split_dir / 'test_metrics_by_stage.csv', test_df, y_test_raw, pred_test)
    save_plot(split_dir / 'training_summary.png', history, y_test_raw, pred_test, metrics['test'], args.target)
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
        'loss': args.loss,
        'branch_type': 'pure_prediction',
    })
    save_json(split_dir / 'metrics.json', metrics)
    return metrics['test']


def train_for_group(df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace, run_root: Path, group_key: str, hidden_dims: List[int]) -> Dict[str, float]:
    train_df, val_df, test_df = split_frame(df, group_key, args.seed, args.train_ratio, args.val_ratio)
    split_dir = run_root / group_key
    return train_one_split(train_df, val_df, test_df, feature_cols, args, split_dir, group_key, hidden_dims)


def train_stage_holdout(df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace, run_root: Path, hidden_dims: List[int]) -> Dict[str, float]:
    test_stage_prefixes = [part.strip() for part in args.test_stage_prefixes.split(',') if part.strip()]
    train_pool, test_df = split_external_stage_holdout(df, test_stage_prefixes)

    pool_total = args.train_ratio + args.val_ratio
    train_ratio_within_pool = args.train_ratio / pool_total
    val_ratio_within_pool = args.val_ratio / pool_total
    train_df, val_df, _ = split_frame(train_pool, args.validation_group_key, args.seed, train_ratio_within_pool, val_ratio_within_pool)

    split_dir = run_root / 'external_stage_holdout'
    split_label = f'external_stage_holdout::{args.validation_group_key}'
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
        raise RuntimeError('No usable feature columns found for pure prediction regressor.')

    run_root = DEFAULT_OUT_ROOT / args.run_name
    run_root.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Dict[str, float]] = {}
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
        'branch_type': 'pure_prediction',
        'loss': args.loss,
    })

    print('[DONE] pure prediction regressor training complete')
    print(f'[RUN] {run_root}')
    for split_name, metrics in summary.items():
        print(f"[TEST:{split_name}] mae={metrics['mae']:.4f} rmse={metrics['rmse']:.4f} r2={metrics['r2']:.4f}")


if __name__ == '__main__':
    main()
