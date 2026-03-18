from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / 'data' / 'ml_dataset' / 'v1' / 'mlp_gap34_regression_v1.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'ml_runs'

DEFAULT_FEATURES = [
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5',
    'r0', 'shift', 'neigs', 'contact_length', 'n_domains',
    'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height',
    'shape_bbox_aspect_ratio', 'shape_centroid_x', 'shape_centroid_y', 'shape_point_count'
]

PRESETS = {
    'post_stage1': {'stages': ['stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine']},
    'all': {'stages': None},
    'harmonics_focus': {'stages': ['stage2_harmonics', 'stage2_harmonics_refine']},
    'low_order_focus': {'stages': ['stage2', 'stage2_refine']},
}


@dataclass
class SplitData:
    name: str
    frame: pd.DataFrame
    x: np.ndarray
    y: np.ndarray


class MLPRegressor(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: Sequence[int], dropout: float = 0.0):
        super().__init__()
        layers: List[nn.Module] = []
        prev = input_dim
        for hidden in hidden_dims:
            layers.append(nn.Linear(prev, hidden))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev = hidden
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train first-pass MLP regressor for metamaterial dataset.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--preset', choices=sorted(PRESETS.keys()), default='post_stage1')
    parser.add_argument('--target', default='gap34_gain_Hz', choices=['gap34_gain_Hz', 'gap34_Hz', 'gap34_rel', 'gap34_gain_rel'])
    parser.add_argument('--group-key', default='shape_id', choices=['shape_id', 'shape_family', 'source_stage', 'none'])
    parser.add_argument('--run-name', default='mlp_gap34_gain_post_stage1_v1')
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
    parser.add_argument('--positive-only', action='store_true')
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def parse_hidden_dims(text: str) -> List[int]:
    dims = [int(part.strip()) for part in text.split(',') if part.strip()]
    if not dims:
        raise ValueError('hidden dims must not be empty')
    return dims


def select_rows(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    df = df.copy()
    preset = PRESETS[args.preset]
    stages = preset['stages']
    if stages is not None:
        df = df[df['source_stage'].isin(stages)].copy()
    df = df[np.isfinite(df[args.target])].copy()
    if args.positive_only:
        if args.target == 'gap34_gain_Hz':
            df = df[df['gap34_gain_Hz'] > 0].copy()
        elif args.target == 'gap34_Hz':
            df = df[df['gap34_Hz'] > 0].copy()
    return df


def split_frame(df: pd.DataFrame, group_key: str, seed: int, train_ratio: float, val_ratio: float) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    if group_key == 'none':
        idx = np.arange(len(df))
        rng.shuffle(idx)
        train_end = int(len(idx) * train_ratio)
        val_end = int(len(idx) * (train_ratio + val_ratio))
        return df.iloc[idx[:train_end]].copy(), df.iloc[idx[train_end:val_end]].copy(), df.iloc[idx[val_end:]].copy()

    groups = df[group_key].astype(str).fillna('')
    unique_groups = groups.unique().tolist()
    rng.shuffle(unique_groups)
    n_total = len(unique_groups)
    n_train = max(1, int(round(n_total * train_ratio)))
    n_val = max(1, int(round(n_total * val_ratio)))
    if n_train + n_val >= n_total:
        n_val = max(1, n_total - n_train - 1)
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
    stds = np.where((np.isfinite(stds)) & (stds > 0), stds, 1.0)
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


def build_dataloader(x: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool) -> DataLoader:
    ds = TensorDataset(torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    denom = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - np.sum((y_true - y_pred) ** 2) / denom) if denom > 0 else math.nan
    return {'mae': mae, 'rmse': rmse, 'r2': r2}


def train_model(model: nn.Module, train_loader: DataLoader, x_val: np.ndarray, y_val: np.ndarray, args: argparse.Namespace, out_dir: Path, y_mean: float, y_std: float) -> Tuple[nn.Module, List[Dict[str, float]]]:
    device = torch.device('cpu')
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = nn.MSELoss()

    x_val_t = torch.tensor(x_val, dtype=torch.float32, device=device)
    y_val_t = torch.tensor(y_val, dtype=torch.float32, device=device)

    best_state = None
    best_val_rmse = math.inf
    patience_left = args.patience
    history: List[Dict[str, float]] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses = []
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))

        model.eval()
        with torch.no_grad():
            val_pred = model(x_val_t)
            val_loss = float(criterion(val_pred, y_val_t).item())
            val_pred_np = inverse_target(val_pred.cpu().numpy(), y_mean, y_std)
            val_true_np = inverse_target(y_val, y_mean, y_std)
            val_rmse = regression_metrics(val_true_np, val_pred_np)['rmse']

        history.append({
            'epoch': epoch,
            'train_loss': float(np.mean(train_losses)) if train_losses else math.nan,
            'val_loss': val_loss,
            'val_rmse': val_rmse,
        })

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
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
        pred = model(torch.tensor(x, dtype=torch.float32)).cpu().numpy()
    return inverse_target(pred, y_mean, y_std)


def save_history(path: Path, history: List[Dict[str, float]]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['epoch', 'train_loss', 'val_loss', 'val_rmse'])
        writer.writeheader()
        writer.writerows(history)


def save_predictions(path: Path, splits: Sequence[SplitData], preds: Dict[str, np.ndarray], target_col: str) -> None:
    rows = []
    for split in splits:
        pred = preds[split.name]
        for i, (_, row) in enumerate(split.frame.iterrows()):
            rows.append({
                'split': split.name,
                'sample_id': row['sample_id'],
                'source_stage': row['source_stage'],
                'shape_id': row['shape_id'],
                'shape_family': row['shape_family'],
                'target_name': target_col,
                'y_true': float(split.y[i]),
                'y_pred': float(pred[i]),
                'abs_error': float(abs(split.y[i] - pred[i])),
            })
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['split', 'sample_id', 'source_stage', 'shape_id', 'shape_family', 'target_name', 'y_true', 'y_pred', 'abs_error'])
        writer.writeheader()
        writer.writerows(rows)


def save_stage_metrics(path: Path, test_frame: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    rows = []
    work = test_frame.copy()
    work['_y_true'] = y_true
    work['_y_pred'] = y_pred
    for stage, sub in work.groupby('source_stage'):
        metrics = regression_metrics(sub['_y_true'].to_numpy(), sub['_y_pred'].to_numpy())
        rows.append({'source_stage': stage, 'rows': len(sub), **metrics})
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['source_stage', 'rows', 'mae', 'rmse', 'r2'])
        writer.writeheader()
        writer.writerows(rows)


def save_plot(path: Path, history: List[Dict[str, float]], y_true: np.ndarray, y_pred: np.ndarray, metrics: Dict[str, float], target_col: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot([h['epoch'] for h in history], [h['train_loss'] for h in history], label='train_loss')
    axes[0].plot([h['epoch'] for h in history], [h['val_loss'] for h in history], label='val_loss')
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
    axes[1].text(0.03, 0.97, f"MAE={metrics['mae']:.3f}\nRMSE={metrics['rmse']:.3f}\nR2={metrics['r2']:.3f}", transform=axes[1].transAxes, va='top')

    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    hidden_dims = parse_hidden_dims(args.hidden_dims)

    df = pd.read_csv(args.dataset)
    df = select_rows(df, args)
    if df.empty:
        raise RuntimeError('No rows remain after preset/target filtering.')

    feature_cols = [col for col in DEFAULT_FEATURES if col in df.columns]
    missing = [col for col in DEFAULT_FEATURES if col not in df.columns]
    if missing:
        print(f'[WARN] missing features ignored: {missing}')
    if not feature_cols:
        raise RuntimeError('No usable feature columns found.')

    train_df, val_df, test_df = split_frame(df, args.group_key, args.seed, args.train_ratio, args.val_ratio)
    for name, frame in [('train', train_df), ('val', val_df), ('test', test_df)]:
        if frame.empty:
            raise RuntimeError(f'{name} split is empty; adjust split settings or group key.')

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
    y_test = transform_target(y_test_raw, y_mean, y_std)

    out_dir = DEFAULT_OUT_ROOT / args.run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    model = MLPRegressor(input_dim=x_train.shape[1], hidden_dims=hidden_dims, dropout=args.dropout)
    train_loader = build_dataloader(x_train, y_train, args.batch_size, shuffle=True)
    model, history = train_model(model, train_loader, x_val, y_val, args, out_dir, y_mean, y_std)

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
        'input_dim': x_train.shape[1],
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'feature_cols': feature_cols,
        'x_mean': x_mean.tolist(),
        'x_std': x_std.tolist(),
        'y_mean': y_mean,
        'y_std': y_std,
        'target': args.target,
    }, out_dir / 'model.pt')

    save_history(out_dir / 'train_history.csv', history)
    save_predictions(
        out_dir / 'predictions.csv',
        [SplitData('train', train_df, x_train, y_train_raw), SplitData('val', val_df, x_val, y_val_raw), SplitData('test', test_df, x_test, y_test_raw)],
        {'train': pred_train, 'val': pred_val, 'test': pred_test},
        args.target,
    )
    save_stage_metrics(out_dir / 'test_metrics_by_stage.csv', test_df, y_test_raw, pred_test)
    save_plot(out_dir / 'training_summary.png', history, y_test_raw, pred_test, metrics['test'], args.target)

    split_info = {
        'train_rows': len(train_df), 'val_rows': len(val_df), 'test_rows': len(test_df),
        'train_groups': sorted(train_df[args.group_key].astype(str).unique().tolist()) if args.group_key != 'none' else [],
        'val_groups': sorted(val_df[args.group_key].astype(str).unique().tolist()) if args.group_key != 'none' else [],
        'test_groups': sorted(test_df[args.group_key].astype(str).unique().tolist()) if args.group_key != 'none' else [],
    }
    (out_dir / 'split_info.json').write_text(json.dumps(split_info, indent=2, ensure_ascii=False), encoding='utf-8')

    config = {
        'dataset': str(args.dataset),
        'preset': args.preset,
        'target': args.target,
        'group_key': args.group_key,
        'run_name': args.run_name,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'lr': args.lr,
        'weight_decay': args.weight_decay,
        'patience': args.patience,
        'seed': args.seed,
        'positive_only': args.positive_only,
        'feature_cols': feature_cols,
    }
    (out_dir / 'config.json').write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
    (out_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] first-pass MLP training complete')
    print(f'[RUN] {out_dir}')
    print(f"[TRAIN] rows={len(train_df)} mae={metrics['train']['mae']:.4f} rmse={metrics['train']['rmse']:.4f} r2={metrics['train']['r2']:.4f}")
    print(f"[VAL] rows={len(val_df)} mae={metrics['val']['mae']:.4f} rmse={metrics['val']['rmse']:.4f} r2={metrics['val']['r2']:.4f}")
    print(f"[TEST] rows={len(test_df)} mae={metrics['test']['mae']:.4f} rmse={metrics['test']['rmse']:.4f} r2={metrics['test']['r2']:.4f}")


if __name__ == '__main__':
    main()
