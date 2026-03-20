from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn

from ml_common import (
    DEFAULT_OUT_ROOT,
    ROOT,
    MLP,
    SURROGATE_CORE_FEATURES,
    SURROGATE_DIRECTIONAL_FEATURES,
    SURROGATE_GEO_EXTRA_FEATURES,
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
    save_regression_stage_metrics,
    save_split_info,
    set_seed,
    split_frame,
    transform_features,
    transform_target,
)

DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v6' / 'tasks' / 'surrogate_regression_core_v6.csv'
ALLOWED_GROUP_KEYS = ['shape_id', 'shape_family', 'none']
FEATURE_PRESETS = {
    'surrogate_core': SURROGATE_CORE_FEATURES,
    'surrogate_geo_augmented': [*SURROGATE_CORE_FEATURES, *SURROGATE_GEO_EXTRA_FEATURES],
    'surrogate_directional': SURROGATE_DIRECTIONAL_FEATURES,
    'surrogate_directional_geo_augmented': [*SURROGATE_DIRECTIONAL_FEATURES, *SURROGATE_GEO_EXTRA_FEATURES],
}
TARGET_CHOICES = ['gap34_gain_Hz', 'gap34_Hz', 'gap34_rel', 'gap34_gain_rel']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train cleaned surrogate MLP regressor for v6 datasets.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--feature-preset', default='surrogate_directional', choices=sorted(FEATURE_PRESETS.keys()))
    parser.add_argument('--target', default='gap34_gain_Hz', choices=TARGET_CHOICES)
    parser.add_argument('--group-keys', default='shape_id,shape_family')
    parser.add_argument('--run-name', default='mlp_gap34_gain_surrogate_v6_full')
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
    df = df.copy()
    df = df[np.isfinite(df[target])].copy()
    return df


def train_model(model: nn.Module, train_loader, x_val: np.ndarray, y_val_scaled: np.ndarray, y_val_raw: np.ndarray, args: argparse.Namespace, y_mean: float, y_std: float) -> tuple[nn.Module, List[Dict[str, float]]]:
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = nn.MSELoss()

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
                'target_name': target_col,
                'y_true': float(truth[idx]),
                'y_pred': float(pred[idx]),
                'abs_error': float(abs(truth[idx] - pred[idx])),
            })
    save_csv_rows(path, ['split', 'sample_id', 'source_stage', 'shape_id', 'shape_family', 'target_name', 'y_true', 'y_pred', 'abs_error'], rows)


def save_plot(path: Path, history: List[Dict[str, float]], y_true: np.ndarray, y_pred: np.ndarray, metrics: Dict[str, float], target_col: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot([row['epoch'] for row in history], [row['train_loss'] for row in history], label='train_loss')
    axes[0].plot([row['epoch'] for row in history], [row['val_loss'] for row in history], label='val_loss')
    axes[0].set_title('Training Curve')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('MSE (scaled)')
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


def train_for_group(df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace, run_root: Path, group_key: str, hidden_dims: List[int]) -> Dict[str, float]:
    train_df, val_df, test_df = split_frame(df, group_key, args.seed, args.train_ratio, args.val_ratio)
    for split_name, frame in [('train', train_df), ('val', val_df), ('test', test_df)]:
        if frame.empty:
            raise RuntimeError(f'{split_name} split is empty for group key {group_key}.')

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

    split_dir = run_root / group_key
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
    }, split_dir / 'model.pt')

    save_history_csv(split_dir / 'train_history.csv', history)
    save_predictions(
        split_dir / 'predictions.csv',
        {'train': train_df, 'val': val_df, 'test': test_df},
        {'train': y_train_raw, 'val': y_val_raw, 'test': y_test_raw},
        {'train': pred_train, 'val': pred_val, 'test': pred_test},
        args.target,
    )
    save_regression_stage_metrics(split_dir / 'test_metrics_by_stage.csv', test_df, y_test_raw, pred_test)
    save_plot(split_dir / 'training_summary.png', history, y_test_raw, pred_test, metrics['test'], args.target)
    save_split_info(split_dir / 'split_info.json', group_key, train_df, val_df, test_df)
    save_json(split_dir / 'config.json', {
        'dataset': str(args.dataset),
        'feature_preset': args.feature_preset,
        'target': args.target,
        'group_key': group_key,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'lr': args.lr,
        'weight_decay': args.weight_decay,
        'patience': args.patience,
        'seed': args.seed,
        'feature_cols': feature_cols,
    })
    save_json(split_dir / 'metrics.json', metrics)
    return metrics['test']


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
        raise RuntimeError('No usable feature columns found for regressor v5.')

    run_root = DEFAULT_OUT_ROOT / args.run_name
    run_root.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Dict[str, float]] = {}
    for group_key in group_keys:
        summary[group_key] = train_for_group(df, feature_cols, args, run_root, group_key, hidden_dims)

    save_json(run_root / 'metrics_by_group.json', summary)
    save_json(run_root / 'run_config.json', {
        'dataset': str(args.dataset),
        'feature_preset': args.feature_preset,
        'target': args.target,
        'group_keys': group_keys,
        'run_name': args.run_name,
        'feature_cols': feature_cols,
    })

    print('[DONE] cleaned surrogate MLP training complete')
    print(f'[RUN] {run_root}')
    for group_key in group_keys:
        metrics = summary[group_key]
        print(f"[TEST:{group_key}] mae={metrics['mae']:.4f} rmse={metrics['rmse']:.4f} r2={metrics['r2']:.4f}")


if __name__ == '__main__':
    main()
