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
    PARAMETRIC_CLASSIFIER_FEATURES,
    PARAMETRIC_DIRECTIONAL_FEATURES,
    PARAMETRIC_SEED_DISCOVERY_FEATURES,
    SHAPE_ONLY_FEATURES,
    binary_confusion,
    build_dataloader,
    classification_metrics,
    fit_standardizer,
    parse_group_keys,
    parse_hidden_dims,
    prepare_matrix,
    save_csv_rows,
    save_history_csv,
    save_json,
    save_split_info,
    set_seed,
    split_frame,
    transform_features,
)

DEFAULT_DATASETS = {
    'contact_valid': ROOT / 'data' / 'ml_dataset' / 'v7' / 'tasks' / 'parametric_contact_cls_v7.csv',
    'is_positive_shape': ROOT / 'data' / 'ml_dataset' / 'v7' / 'tasks' / 'parametric_positive_cls_v7.csv',
}

FEATURE_PRESETS = {
    'parametric_core': PARAMETRIC_CLASSIFIER_FEATURES,
    'parametric_directional': PARAMETRIC_DIRECTIONAL_FEATURES,
    'parametric_seed_discovery': PARAMETRIC_SEED_DISCOVERY_FEATURES,
    'shape_only': SHAPE_ONLY_FEATURES,
}

ALLOWED_GROUP_KEYS = ['shape_id', 'shape_family', 'none']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train parameter-aware MLP classifiers for v7 tasks.')
    parser.add_argument('--task', required=True, choices=['contact_valid', 'is_positive_shape'])
    parser.add_argument('--dataset', type=Path, default=None)
    parser.add_argument('--feature-preset', default='parametric_directional', choices=sorted(FEATURE_PRESETS.keys()))
    parser.add_argument('--group-keys', default='shape_id,shape_family')
    parser.add_argument('--run-name', default='')
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
    return parser.parse_args()


def resolve_dataset(args: argparse.Namespace) -> Path:
    return args.dataset if args.dataset is not None else DEFAULT_DATASETS[args.task]


def resolve_run_name(args: argparse.Namespace) -> str:
    if args.run_name:
        return args.run_name
    return f'mlp_{args.task}_{args.feature_preset}_v7_full'


def select_rows(df: pd.DataFrame, task: str) -> pd.DataFrame:
    df = df.copy()
    df = df[np.isfinite(df[task])].copy()
    return df


def predict_proba(model: nn.Module, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(x, dtype=torch.float32)).reshape(-1)
        probs = torch.sigmoid(logits).cpu().numpy()
    return probs


def train_model(model: nn.Module, train_loader, x_val: np.ndarray, y_val: np.ndarray, args: argparse.Namespace) -> tuple[nn.Module, List[Dict[str, float]]]:
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
            'val_accuracy': float(val_metrics['accuracy']),
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


def save_predictions(path: Path, splits: Dict[str, pd.DataFrame], y_true: Dict[str, np.ndarray], y_prob: Dict[str, np.ndarray], task: str, threshold: float) -> None:
    rows: List[Dict[str, object]] = []
    for split_name, frame in splits.items():
        probs = y_prob[split_name]
        truth = y_true[split_name]
        pred = (probs >= threshold).astype(int)
        for idx, (_, row) in enumerate(frame.iterrows()):
            rows.append({
                'split': split_name,
                'sample_id': row['sample_id'],
                'source_stage': row.get('source_stage', ''),
                'selection_source': row.get('selection_source', ''),
                'shape_id': row['shape_id'],
                'shape_family': row['shape_family'],
                'point_id': row.get('point_id', ''),
                'target_name': task,
                'y_true': int(truth[idx]),
                'y_prob': float(probs[idx]),
                'y_pred': int(pred[idx]),
            })
    save_csv_rows(path, ['split', 'sample_id', 'source_stage', 'selection_source', 'shape_id', 'shape_family', 'point_id', 'target_name', 'y_true', 'y_prob', 'y_pred'], rows)


def save_confusion_rows(path: Path, metrics_by_split: Dict[str, Dict[str, float]], y_true: Dict[str, np.ndarray], y_prob: Dict[str, np.ndarray], threshold: float) -> None:
    rows: List[Dict[str, object]] = []
    for split_name, metrics in metrics_by_split.items():
        pred = (y_prob[split_name] >= threshold).astype(int)
        cm = binary_confusion(y_true[split_name], pred)
        rows.append({'split': split_name, **cm, **metrics})
    save_csv_rows(path, ['split', 'tn', 'fp', 'fn', 'tp', 'accuracy', 'precision', 'recall', 'f1', 'balanced_accuracy'], rows)


def save_plot(path: Path, history: List[Dict[str, float]], test_true: np.ndarray, test_prob: np.ndarray, metrics: Dict[str, float], threshold: float, task: str) -> None:
    test_pred = (test_prob >= threshold).astype(int)
    cm = binary_confusion(test_true, test_pred)
    mat = np.array([[cm['tn'], cm['fp']], [cm['fn'], cm['tp']]], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot([row['epoch'] for row in history], [row['train_loss'] for row in history], label='train_loss')
    axes[0].plot([row['epoch'] for row in history], [row['val_loss'] for row in history], label='val_loss')
    axes[0].set_title('Training Curve')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('BCE loss')
    axes[0].legend()

    im = axes[1].imshow(mat, cmap='Blues')
    axes[1].set_xticks([0, 1], labels=['Pred 0', 'Pred 1'])
    axes[1].set_yticks([0, 1], labels=['True 0', 'True 1'])
    axes[1].set_title(f'Test Confusion: {task}')
    for i in range(2):
        for j in range(2):
            axes[1].text(j, i, int(mat[i, j]), ha='center', va='center', color='black')
    axes[1].text(
        1.15,
        0.95,
        f"Acc={metrics['accuracy']:.3f}\nPrec={metrics['precision']:.3f}\nRecall={metrics['recall']:.3f}\nF1={metrics['f1']:.3f}\nBalAcc={metrics['balanced_accuracy']:.3f}",
        transform=axes[1].transAxes,
        va='top',
    )
    fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def train_for_group(df: pd.DataFrame, feature_cols: List[str], args: argparse.Namespace, run_root: Path, group_key: str, hidden_dims: List[int]) -> Dict[str, float]:
    train_df, val_df, test_df = split_frame(df, group_key, args.seed, args.train_ratio, args.val_ratio)
    for split_name, frame in [('train', train_df), ('val', val_df), ('test', test_df)]:
        if frame.empty:
            raise RuntimeError(f'{args.task} split {split_name} is empty for group key {group_key}.')

    x_train_raw, y_train = prepare_matrix(train_df, feature_cols, args.task)
    x_val_raw, y_val = prepare_matrix(val_df, feature_cols, args.task)
    x_test_raw, y_test = prepare_matrix(test_df, feature_cols, args.task)

    x_mean, x_std = fit_standardizer(x_train_raw)
    x_train = transform_features(x_train_raw, x_mean, x_std)
    x_val = transform_features(x_val_raw, x_mean, x_std)
    x_test = transform_features(x_test_raw, x_mean, x_std)

    split_dir = run_root / group_key
    split_dir.mkdir(parents=True, exist_ok=True)

    model = MLP(input_dim=x_train.shape[1], hidden_dims=hidden_dims, output_dim=1, dropout=args.dropout)
    train_loader = build_dataloader(x_train, y_train, args.batch_size, shuffle=True)
    model, history = train_model(model, train_loader, x_val, y_val, args)

    prob_train = predict_proba(model, x_train)
    prob_val = predict_proba(model, x_val)
    prob_test = predict_proba(model, x_test)

    metrics = {
        'train': classification_metrics(y_train, prob_train, threshold=args.threshold),
        'val': classification_metrics(y_val, prob_val, threshold=args.threshold),
        'test': classification_metrics(y_test, prob_test, threshold=args.threshold),
    }

    torch.save({
        'model_state_dict': model.state_dict(),
        'input_dim': int(x_train.shape[1]),
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'feature_cols': feature_cols,
        'x_mean': x_mean.tolist(),
        'x_std': x_std.tolist(),
        'task': args.task,
        'threshold': args.threshold,
    }, split_dir / 'model.pt')

    save_history_csv(split_dir / 'train_history.csv', history)
    save_predictions(
        split_dir / 'predictions.csv',
        {'train': train_df, 'val': val_df, 'test': test_df},
        {'train': y_train, 'val': y_val, 'test': y_test},
        {'train': prob_train, 'val': prob_val, 'test': prob_test},
        args.task,
        args.threshold,
    )
    save_confusion_rows(split_dir / 'confusion_matrix.csv', metrics, {'train': y_train, 'val': y_val, 'test': y_test}, {'train': prob_train, 'val': prob_val, 'test': prob_test}, args.threshold)
    save_plot(split_dir / 'training_summary.png', history, y_test, prob_test, metrics['test'], args.threshold, args.task)
    save_split_info(split_dir / 'split_info.json', group_key, train_df, val_df, test_df)
    save_json(split_dir / 'config.json', {
        'dataset': str(resolve_dataset(args)),
        'task': args.task,
        'feature_preset': args.feature_preset,
        'group_key': group_key,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'hidden_dims': hidden_dims,
        'dropout': args.dropout,
        'lr': args.lr,
        'weight_decay': args.weight_decay,
        'patience': args.patience,
        'seed': args.seed,
        'threshold': args.threshold,
        'feature_cols': feature_cols,
    })
    save_json(split_dir / 'metrics.json', metrics)
    return metrics['test']


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    dataset_path = resolve_dataset(args)
    run_name = resolve_run_name(args)
    hidden_dims = parse_hidden_dims(args.hidden_dims)
    group_keys = parse_group_keys(args.group_keys, ALLOWED_GROUP_KEYS)

    df = pd.read_csv(dataset_path)
    df = select_rows(df, args.task)
    if df.empty:
        raise RuntimeError(f'No rows remain for task {args.task}.')

    preset_cols = FEATURE_PRESETS[args.feature_preset]
    feature_cols = [col for col in preset_cols if col in df.columns]
    missing = [col for col in preset_cols if col not in df.columns]
    if missing:
        print(f'[WARN] missing features ignored: {missing}')
    if not feature_cols:
        raise RuntimeError('No usable feature columns found for classifier.')

    run_root = DEFAULT_OUT_ROOT / run_name
    run_root.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Dict[str, float]] = {}
    for group_key in group_keys:
        summary[group_key] = train_for_group(df, feature_cols, args, run_root, group_key, hidden_dims)

    save_json(run_root / 'metrics_by_group.json', summary)
    save_json(run_root / 'run_config.json', {
        'dataset': str(dataset_path),
        'task': args.task,
        'feature_preset': args.feature_preset,
        'group_keys': group_keys,
        'run_name': run_name,
        'feature_cols': feature_cols,
    })

    print('[DONE] parameter-aware classifier training complete')
    print(f'[RUN] {run_root}')
    for group_key in group_keys:
        metrics = summary[group_key]
        print(f"[TEST:{group_key}] acc={metrics['accuracy']:.4f} prec={metrics['precision']:.4f} recall={metrics['recall']:.4f} f1={metrics['f1']:.4f} bal_acc={metrics['balanced_accuracy']:.4f}")


if __name__ == '__main__':
    main()
