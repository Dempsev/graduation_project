from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_real_value(x: object) -> float:
    if pd.isna(x):
        return np.nan
    s = str(x).strip().replace("i", "j")
    try:
        return float(np.real(complex(s)))
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return np.nan


def load_tbl1(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        header=None,
        comment="%",
        sep=r"\s*,\s*|\s+",
        engine="python",
        names=["k", "a1", "eigfreq", "freq"],
    )
    df["k"] = pd.to_numeric(df["k"], errors="coerce")
    df["a1"] = pd.to_numeric(df["a1"], errors="coerce")
    df["freq_real"] = df["freq"].apply(parse_real_value)
    df = df.dropna(subset=["k", "a1", "freq_real"]).copy()
    df = df.sort_values(["a1", "k", "freq_real"]).copy()
    df["band_index"] = df.groupby(["a1", "k"]).cumcount() + 1
    return df


def plot_one_a1(df: pd.DataFrame, a1: float, out_path: Path) -> None:
    sub = df[np.isclose(df["a1"], a1)].copy()
    if sub.empty:
        raise ValueError(f"a1={a1} not found in data")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for _, g in sub.groupby("band_index"):
        g = g.sort_values("k")
        ax.plot(g["k"], g["freq_real"], color="black", linewidth=1.0)

    ax.set_xlim(0, 3)
    ax.set_xlabel("k")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(f"{out_path.stem}  a1={a1:g}")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def plot_all_a1(df: pd.DataFrame, out_path: Path) -> None:
    a1_values = sorted(df["a1"].unique())
    fig, axes = plt.subplots(len(a1_values), 1, figsize=(7, 3.4 * len(a1_values)), sharex=True)
    if len(a1_values) == 1:
        axes = [axes]

    for ax, a1 in zip(axes, a1_values):
        sub = df[np.isclose(df["a1"], a1)].copy()
        for _, g in sub.groupby("band_index"):
            g = g.sort_values("k")
            ax.plot(g["k"], g["freq_real"], color="black", linewidth=0.9)
        ax.set_title(f"a1={a1:g}")
        ax.set_ylabel("Frequency (Hz)")
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlim(0, 3)
    axes[-1].set_xlabel("k")
    fig.tight_layout()
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python postprocess/plot_tbl1_band.py <tbl1.csv> [a1]")

    csv_path = Path(sys.argv[1]).resolve()
    a1_filter = float(sys.argv[2]) if len(sys.argv) >= 3 else None

    df = load_tbl1(csv_path)
    repo_root = Path(__file__).resolve().parents[1]
    default_out_dir = repo_root / "data" / "post_out" / "manual_band_plots"
    if len(csv_path.parents) >= 3 and csv_path.parents[2].name == "data":
        out_dir = csv_path.parents[2] / "post_out" / "manual_band_plots"
    else:
        out_dir = default_out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = csv_path.stem.replace("_tbl1", "")
    plot_all_a1(df, out_dir / f"{stem}_bands_all_a1.png")

    if a1_filter is not None:
        plot_one_a1(df, a1_filter, out_dir / f"{stem}_a1_{a1_filter:g}.png")

    print(out_dir)


if __name__ == "__main__":
    main()
