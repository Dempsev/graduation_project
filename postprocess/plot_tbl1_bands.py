from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from .tbl1_post_utils import infer_manual_plot_dir, load_tbl1_data, model_name_from_path
except ImportError:
    from tbl1_post_utils import infer_manual_plot_dir, load_tbl1_data, model_name_from_path


def apply_k_path_ticks(ax: plt.Axes) -> None:
    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])


def plot_one_param_value(df: pd.DataFrame, param_name: str, param_value: float, out_path: Path) -> None:
    sub = df[np.isclose(df[param_name], param_value)].copy()
    if sub.empty:
        raise ValueError(f"{param_name}={param_value} not found in data")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for _, group in sub.groupby("band_index"):
        group = group.sort_values("k")
        ax.plot(group["k"], group["freq_real"], color="black", linewidth=1.0)

    apply_k_path_ticks(ax)
    ax.set_xlabel("k")
    ax.set_ylabel("Frequency (Hz)")
    if param_name == "case":
        ax.set_title(out_path.stem)
    else:
        ax.set_title(f"{out_path.stem}  {param_name}={param_value:g}")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def plot_all_param_values(df: pd.DataFrame, param_name: str, out_path: Path) -> None:
    param_values = sorted(df[param_name].unique())
    fig, axes = plt.subplots(len(param_values), 1, figsize=(7, 3.4 * len(param_values)), sharex=True)
    if len(param_values) == 1:
        axes = [axes]

    for ax, param_value in zip(axes, param_values):
        sub = df[np.isclose(df[param_name], param_value)].copy()
        for _, group in sub.groupby("band_index"):
            group = group.sort_values("k")
            ax.plot(group["k"], group["freq_real"], color="black", linewidth=0.9)
        if param_name == "case":
            ax.set_title(out_path.stem)
        else:
            ax.set_title(f"{param_name}={param_value:g}")
        ax.set_ylabel("Frequency (Hz)")
        ax.grid(True, alpha=0.25)

    apply_k_path_ticks(axes[-1])
    axes[-1].set_xlabel("k")
    fig.tight_layout()
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot one COMSOL tbl1 band diagram.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("param_value", nargs="?", type=float, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = args.csv_path.resolve()
    param_value_filter = args.param_value

    df, param_name = load_tbl1_data(csv_path)
    if df.empty:
        raise RuntimeError(f"no valid rows found in {csv_path}")

    out_dir = args.out_dir.resolve() if args.out_dir is not None else infer_manual_plot_dir(csv_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = model_name_from_path(csv_path)
    plot_all_param_values(df, param_name, out_dir / f"{stem}_bands_all_{param_name}.png")

    if param_value_filter is not None:
        plot_one_param_value(
            df,
            param_name,
            param_value_filter,
            out_dir / f"{stem}_{param_name}_{param_value_filter:g}.png",
        )

    print(out_dir)


if __name__ == "__main__":
    main()
