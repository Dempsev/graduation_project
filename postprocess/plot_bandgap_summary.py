from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

try:
    from .tbl1_post_utils import project_root
except ImportError:
    from tbl1_post_utils import project_root


def apply_k_path_ticks(ax: plt.Axes, x: pd.Series) -> None:
    if not x.notna().any():
        return

    xmin = float(x.min())
    xmax = float(x.max())
    if xmin <= 1e-9 and xmax >= 3.0 - 1e-9:
        ax.set_xlim(0, 3)
        ax.set_xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])
        ax.axvline(1, color="0.8", linewidth=0.8)
        ax.axvline(2, color="0.8", linewidth=0.8)


def plot_bandgap_summary(case_df: pd.DataFrame, fig_dir: Path) -> None:
    for param_name, param_group in case_df.groupby("param_name"):
        if param_group["param_value"].nunique() <= 1:
            continue

        width_fig, width_ax = plt.subplots()
        edge_fig, edge_ax = plt.subplots()

        for model_name, model_group in param_group.groupby("model"):
            g = model_group.sort_values("param_value")
            label = model_name if param_group["model"].nunique() > 1 else None

            width_ax.plot(g["param_value"], g["max_gap_Hz"], marker="o", label=label)
            edge_ax.plot(g["param_value"], g["gap_lower_edge_Hz"], marker="o", label=f"{model_name} lower")
            edge_ax.plot(g["param_value"], g["gap_upper_edge_Hz"], marker="o", linestyle="--", label=f"{model_name} upper")

        width_ax.set_xlabel(param_name)
        width_ax.set_ylabel("Bandgap width (Hz)")
        width_ax.set_title(f"Bandgap width vs {param_name}")
        width_ax.grid(True, alpha=0.3)
        if param_group["model"].nunique() > 1:
            width_ax.legend(fontsize=8)
        width_fig.tight_layout()
        width_fig.savefig(fig_dir / f"bandgap_width_vs_{param_name}.png", dpi=300)
        plt.close(width_fig)

        edge_ax.set_xlabel(param_name)
        edge_ax.set_ylabel("Frequency (Hz)")
        edge_ax.set_title(f"Bandgap edges vs {param_name}")
        edge_ax.grid(True, alpha=0.3)
        edge_ax.legend(fontsize=8)
        edge_fig.tight_layout()
        edge_fig.savefig(fig_dir / f"bandgap_edges_vs_{param_name}.png", dpi=300)
        plt.close(edge_fig)


def format_case_label(row: pd.Series) -> str:
    label = str(row["model"])
    params: list[str] = []
    for name in ("shift_Hz", "neigs", "a1", "b1", "a2", "b2", "a3", "b3"):
        if name not in row.index or pd.isna(row[name]):
            continue
        value = float(row[name])
        if name not in {"shift_Hz", "neigs"} and abs(value) < 1e-12:
            continue
        params.append(f"{name}={value:g}")

    if "notes" in row.index and pd.notna(row["notes"]):
        note = str(row["notes"]).strip()
        if note:
            params.append(note)

    if not params:
        return label
    return label + "\n" + "\n".join(params[:5])


def plot_screening_case_summary(model_df: pd.DataFrame, fig_dir: Path) -> int:
    if model_df.empty:
        return 0

    comparison_df = model_df.sort_values("max_gap_Hz", ascending=False).reset_index(drop=True)
    labels = [format_case_label(row) for _, row in comparison_df.iterrows()]
    x = list(range(len(comparison_df)))

    fig, axes = plt.subplots(2, 1, figsize=(max(10, 1.05 * len(comparison_df)), 8), sharex=True)

    axes[0].bar(x, comparison_df["max_gap_Hz"].fillna(0.0), color="#5B7DB1")
    axes[0].set_ylabel("Bandgap width (Hz)")
    axes[0].set_title("Best bandgap by case")
    axes[0].grid(True, axis="y", alpha=0.3)

    axes[1].bar(x, comparison_df["relative_gap"].fillna(0.0), color="#C97941")
    axes[1].set_ylabel("Relative gap")
    axes[1].set_title("Best relative gap by case")
    axes[1].grid(True, axis="y", alpha=0.3)
    axes[1].set_xticks(x, labels, rotation=25, ha="right")

    fig.tight_layout()
    fig.savefig(fig_dir / "screening_case_comparison.png", dpi=300)
    plt.close(fig)
    return len(comparison_df)


def plot_band_diagrams(out_dir: Path) -> int:
    bands_dir = out_dir / "case_band_tables"
    if not bands_dir.is_dir():
        return 0

    band_fig_dir = out_dir / "plots" / "case_band_diagrams"
    band_fig_dir.mkdir(parents=True, exist_ok=True)

    plotted = 0
    for csv_path in sorted(bands_dir.glob("bands_*.csv")):
        df = pd.read_csv(csv_path)
        if df.empty or "k" not in df.columns:
            continue

        band_cols = [c for c in df.columns if c.startswith("band")]
        if not band_cols:
            continue

        fig, ax = plt.subplots(figsize=(6.4, 4.8))
        x = pd.to_numeric(df["k"], errors="coerce")
        for col in band_cols:
            y = pd.to_numeric(df[col], errors="coerce")
            ax.plot(x, y, color="black", linewidth=0.8, alpha=0.95)

        ax.set_xlabel("k")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title(csv_path.stem.removeprefix("bands_"))
        apply_k_path_ticks(ax, x)
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(band_fig_dir / f"{csv_path.stem}.png", dpi=300)
        plt.close(fig)
        plotted += 1

    return plotted


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot bandgap summaries from postprocess outputs.")
    parser.add_argument("--out-dir", type=Path, default=project_root() / "data" / "postprocess_out")
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    case_path = out_dir / "bandgap_by_case.csv"
    model_path = out_dir / "bandgap_by_model.csv"
    if not case_path.is_file():
        raise FileNotFoundError(f"summary file not found: {case_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"summary file not found: {model_path}")

    df = pd.read_csv(case_path)
    model_df = pd.read_csv(model_path)
    if df.empty:
        raise RuntimeError("bandgap_by_case.csv is empty")
    if model_df.empty:
        raise RuntimeError("bandgap_by_model.csv is empty")

    fig_dir = out_dir / "plots"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plot_bandgap_summary(df, fig_dir)
    comparison_count = plot_screening_case_summary(model_df, fig_dir)
    band_count = plot_band_diagrams(out_dir)

    print(f"[DONE] summary plots written to: {fig_dir}")
    print(f"[DONE] screening cases compared: {comparison_count}")
    print(f"[DONE] band diagrams written: {band_count}")


if __name__ == "__main__":
    main()
