from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def plot_bandgap_summary(case_df: pd.DataFrame, fig_dir: Path) -> None:
    for param_name, group in case_df.groupby("param_name"):
        g = group.sort_values("param_value")

        plt.figure()
        plt.plot(g["param_value"], g["max_gap_Hz"], marker="o")
        plt.xlabel(param_name)
        plt.ylabel("Bandgap width (Hz)")
        plt.title(f"Bandgap width vs {param_name}")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(fig_dir / f"bandgap_width_vs_{param_name}.png", dpi=300)
        plt.close()

        plt.figure()
        plt.plot(g["param_value"], g["gap_lower_edge_Hz"], marker="o", label="Lower edge")
        plt.plot(g["param_value"], g["gap_upper_edge_Hz"], marker="o", label="Upper edge")
        plt.xlabel(param_name)
        plt.ylabel("Frequency (Hz)")
        plt.title(f"Bandgap edges vs {param_name}")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / f"bandgap_edges_vs_{param_name}.png", dpi=300)
        plt.close()


def plot_band_diagrams(out_dir: Path) -> int:
    bands_dir = out_dir / "bands_by_case"
    if not bands_dir.is_dir():
        return 0

    band_fig_dir = out_dir / "plots" / "bands_by_case"
    band_fig_dir.mkdir(parents=True, exist_ok=True)

    plotted = 0
    for csv_path in sorted(bands_dir.glob("bands_*.csv")):
        df = pd.read_csv(csv_path)
        if df.empty or "k" not in df.columns:
            continue

        band_cols = [c for c in df.columns if c.startswith("band")]
        if not band_cols:
            continue

        plt.figure(figsize=(6.4, 4.8))
        x = pd.to_numeric(df["k"], errors="coerce")
        for col in band_cols:
            y = pd.to_numeric(df[col], errors="coerce")
            plt.plot(x, y, color="black", linewidth=0.8, alpha=0.95)

        title = csv_path.stem.removeprefix("bands_")
        plt.xlabel("k")
        plt.ylabel("Frequency (Hz)")
        plt.title(title)
        if x.notna().any():
            xmin = float(x.min())
            xmax = float(x.max())
            if xmin <= 0.0 + 1e-9 and xmax >= 3.0 - 1e-9:
                plt.xlim(0, 3)
                plt.xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])
                plt.axvline(1, color="0.8", linewidth=0.8)
                plt.axvline(2, color="0.8", linewidth=0.8)
        plt.grid(True, alpha=0.25)
        plt.tight_layout()
        plt.savefig(band_fig_dir / f"{csv_path.stem}.png", dpi=300)
        plt.close()
        plotted += 1

    return plotted


def main() -> None:
    out_dir = project_root() / "data" / "post_out"
    case_path = out_dir / "bandgap_by_case.csv"
    if not case_path.is_file():
        raise FileNotFoundError(f"summary file not found: {case_path}")

    df = pd.read_csv(case_path)
    if df.empty:
        raise RuntimeError("bandgap_by_case.csv is empty")

    fig_dir = out_dir / "plots"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plot_bandgap_summary(df, fig_dir)
    band_count = plot_band_diagrams(out_dir)

    print(f"[DONE] summary plots written to: {fig_dir}")
    print(f"[DONE] band diagrams written: {band_count}")


if __name__ == "__main__":
    main()
