from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch5_strict_holdout_validation"
FIG_DIR = OUT_DIR / "figures"
UNIT_EXPORT_DIR = FIG_DIR / "unit_cell_redraw_exports"
CH4_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"

STRICT_RESULTS = OUT_DIR / "ch5_strict_holdout_comsol_results_top5_random5.csv"
CH4_TYPICAL = CH4_DIR / "ch4_typical_cases_20gen.csv"
CH4_SUMMARY = CH4_DIR / "ch4_ga_summary_20gen.csv"
CASE_CSV = OUT_DIR / "ch5_pred_vs_ga20_redraw_cases.csv"
UNIT_MANIFEST = OUT_DIR / "ch5_pred_vs_ga20_unit_cell_export_manifest.csv"
CHECKLIST = OUT_DIR / "CH5_FIGURE_REDRAW_CHECKLIST.md"

BANDS = [
    ("band180_220", "180\u2013220 Hz", 180.0, 220.0),
    ("band200_240", "200\u2013240 Hz", 200.0, 240.0),
    ("band240_280", "240\u2013280 Hz", 240.0, 280.0),
]
BAND_LABEL = {tag: label for tag, label, _, _ in BANDS}
BAND_LOW = {tag: low for tag, _, low, _ in BANDS}
BAND_HIGH = {tag: high for tag, _, _, high in BANDS}
PARAM_COLS = ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]


def configure_fonts() -> None:
    for path in [Path(r"C:\Windows\Fonts\msyh.ttc"), Path(r"C:\Windows\Fonts\simhei.ttf"), Path(r"C:\Windows\Fonts\simsun.ttc")]:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            break
    else:
        font_name = "DejaVu Sans"
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_name, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": "#222222",
            "axes.labelcolor": "#222222",
            "text.color": "#222222",
            "xtick.color": "#222222",
            "ytick.color": "#222222",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def save_fig(fig: plt.Figure, stem: str) -> dict[str, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths[ext] = path
    plt.close(fig)
    return paths


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes"}


def best_predicted_cases() -> list[dict[str, Any]]:
    strict = pd.read_csv(STRICT_RESULTS, low_memory=False)
    strict = strict[strict["target_band_tag"].isin([tag for tag, *_ in BANDS])].copy()
    strict = strict[strict["method"].eq("predicted_top5")].copy()
    strict["_overlap"] = pd.to_numeric(strict["true_overlap_Hz"], errors="coerce").fillna(-1)
    rows: list[dict[str, Any]] = []
    for tag, label, low, high in BANDS:
        sub = strict[strict["target_band_tag"].eq(tag)].sort_values("_overlap", ascending=False)
        if sub.empty:
            raise FileNotFoundError(f"Missing predicted_top5 strict result for {tag}")
        row = sub.iloc[0].to_dict()
        rows.append(
            {
                "target_band": label,
                "target_band_tag": tag,
                "method": "predicted_top5",
                "candidate_id": str(row["candidate_id"]),
                "sample_id": str(row["candidate_id"]),
                "main_id": "strict_holdout",
                "point_id": str(row.get("point_id", "")),
                "shape_id": str(row["shape_id"]),
                "shape_family": str(row["shape_family"]),
                "shape_file": str(ROOT / "data" / "shape_contours" / f"{row['shape_id']}.csv"),
                "overlap_Hz": float(row["true_overlap_Hz"]),
                "cover_ratio": float(row["true_cover_ratio"]),
                "gap_lower_Hz": row.get("true_gap_lower_Hz", math.nan),
                "gap_upper_Hz": row.get("true_gap_upper_Hz", math.nan),
                "dispersion_tbl1_csv": str(row["tbl1_path"]),
                "geometry_source": "MATLAB/COMSOL redraw from strict_holdout result row",
                **{col: float(row.get(col, 0.0)) for col in PARAM_COLS},
            }
        )
    return rows


def best_ga20_cases() -> list[dict[str, Any]]:
    typical = pd.read_csv(CH4_TYPICAL, low_memory=False)
    summary = pd.read_csv(CH4_SUMMARY, low_memory=False)
    rows: list[dict[str, Any]] = []
    for tag, label, _, _ in BANDS:
        typ = typical[typical["target_band_tag"].eq(tag)]
        if typ.empty:
            raise FileNotFoundError(f"Missing GA20 typical case for {tag}")
        trow = typ.iloc[0]
        srow = summary[summary["target_band_tag"].eq(tag)].iloc[0]
        hist = pd.read_csv(Path(str(srow["output_dir"])) / "ga_history_v1.csv", low_memory=False)
        hrow = hist[hist["sample_id"].astype(str).eq(str(trow["sample_id"]))]
        if hrow.empty:
            hrow = hist.sort_values("active_target_overlap_Hz", ascending=False).head(1)
        hrow = hrow.iloc[0]
        rows.append(
            {
                "target_band": label,
                "target_band_tag": tag,
                "method": "ga20",
                "candidate_id": str(trow["candidate_id"]),
                "sample_id": str(trow["sample_id"]),
                "main_id": str(hrow.get("main_id", "rf09")),
                "point_id": str(hrow.get("point_id", "rf09_h00_center")),
                "shape_id": str(trow["shape_id"]),
                "shape_family": str(trow["shape_family"]),
                "shape_file": str(trow["shape_contour_csv"]),
                "overlap_Hz": float(trow["target_overlap_Hz"]),
                "cover_ratio": float(trow["cover_ratio"]),
                "gap_lower_Hz": float(trow["gap_lower_Hz"]),
                "gap_upper_Hz": float(trow["gap_upper_Hz"]),
                "dispersion_tbl1_csv": str(trow["dispersion_tbl1_csv"]),
                "geometry_source": "MATLAB/COMSOL redraw from GA20 history row",
                **{col: float(hrow.get(col, trow.get(col, 0.0))) for col in PARAM_COLS},
            }
        )
    return rows


def prepare_cases() -> pd.DataFrame:
    rows = []
    pred = {row["target_band_tag"]: row for row in best_predicted_cases()}
    ga = {row["target_band_tag"]: row for row in best_ga20_cases()}
    for tag, *_ in BANDS:
        rows.append(pred[tag])
        rows.append(ga[tag])
    df = pd.DataFrame(rows)
    df.to_csv(CASE_CSV, index=False, encoding="utf-8-sig")
    print(f"[CASES] {CASE_CSV}")
    print(df[["target_band", "method", "candidate_id", "shape_id", "shape_family", "overlap_Hz", "cover_ratio", "dispersion_tbl1_csv"]].to_string(index=False))
    return df


def load_unit_manifest() -> pd.DataFrame:
    if not UNIT_MANIFEST.exists():
        raise FileNotFoundError(f"Missing COMSOL unit-cell export manifest: {UNIT_MANIFEST}")
    manifest = pd.read_csv(UNIT_MANIFEST, low_memory=False)
    failed = manifest[~manifest["status"].astype(str).eq("ok")]
    if not failed.empty:
        raise RuntimeError("Some COMSOL unit-cell exports failed:\n" + failed.to_string(index=False))
    for path in manifest["png_path"]:
        if not Path(str(path)).exists():
            raise FileNotFoundError(f"Missing COMSOL unit-cell PNG: {path}")
    return manifest


def draw_unit_cell_montage(cases: pd.DataFrame, manifest: pd.DataFrame) -> dict[str, Path]:
    configure_fonts()
    fig, axes = plt.subplots(2, 3, figsize=(10.8, 4.7))
    methods = [("predicted_top5", "预测Top5"), ("ga20", "GA20")]
    for c, (tag, label, _, _) in enumerate(BANDS):
        for r, (method, method_cn) in enumerate(methods):
            ax = axes[r, c]
            rec = manifest[(manifest["target_band_tag"].eq(tag)) & (manifest["method"].eq(method))].iloc[0]
            case = cases[(cases["target_band_tag"].eq(tag)) & (cases["method"].eq(method))].iloc[0]
            image = mpimg.imread(str(rec["png_path"]))
            ax.imshow(image)
            ax.axis("off")
            ax.set_title(f"{label} {method_cn}\n{float(case['overlap_Hz']):.2f} Hz", fontsize=10, pad=4)
    fig.subplots_adjust(left=0.03, right=0.985, top=0.92, bottom=0.04, wspace=0.08, hspace=0.26)
    return save_fig(fig, "ch5_strict_fig7_unit_cells_pred_vs_ga20_redraw")


def read_tbl1_lines(path: str | Path) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing dispersion tbl1 CSV: {p}")
    rows: list[tuple[float, float]] = []
    with p.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("%"):
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 3:
                continue
            try:
                k_val = float(parts[0])
                freq = float(complex(parts[-1].replace("i", "j")).real)
            except Exception:
                continue
            if math.isfinite(k_val) and math.isfinite(freq):
                rows.append((k_val, freq))
    if not rows:
        raise ValueError(f"No numeric dispersion rows found: {p}")
    df = pd.DataFrame(rows, columns=["k", "freq"])
    unique_k = sorted(df["k"].unique())
    lines: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    max_bands = max(df.groupby("k").size())
    for band_idx in range(max_bands):
        xs: list[float] = []
        ys: list[float] = []
        for k_val in unique_k:
            freqs = sorted(df.loc[df["k"].eq(k_val), "freq"].tolist())
            if len(freqs) > band_idx:
                xs.append(float(k_val))
                ys.append(float(freqs[band_idx]))
        if len(xs) > 1:
            lines[band_idx + 1] = (np.array(xs), np.array(ys))
    return lines


def plot_dispersion_set(ax: plt.Axes, tbl1_path: str, color: str, label: str, alpha: float, linewidth: float) -> None:
    lines = read_tbl1_lines(tbl1_path)
    first = True
    for _, (x, y) in sorted(lines.items()):
        ax.plot(x, y, color=color, alpha=alpha, linewidth=linewidth, label=label if first else None)
        first = False


def draw_dispersion_compare(cases: pd.DataFrame) -> dict[str, Path]:
    configure_fonts()
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.45), sharey=True)
    pred_color = "#2C7FB8"
    ga_color = "#555555"
    band_color = "#F28E2B"
    for ax, (tag, label, low, high) in zip(axes, BANDS):
        pred = cases[(cases["target_band_tag"].eq(tag)) & (cases["method"].eq("predicted_top5"))].iloc[0]
        ga = cases[(cases["target_band_tag"].eq(tag)) & (cases["method"].eq("ga20"))].iloc[0]
        band_patch = ax.axhspan(low, high, color=band_color, alpha=0.16, label="目标频带", zorder=0)
        plot_dispersion_set(ax, str(ga["dispersion_tbl1_csv"]), ga_color, "GA20", alpha=0.60, linewidth=0.85)
        plot_dispersion_set(ax, str(pred["dispersion_tbl1_csv"]), pred_color, "预测 Top5", alpha=0.88, linewidth=1.10)
        if pd.notna(pred["gap_lower_Hz"]) and pd.notna(pred["gap_upper_Hz"]):
            ax.axhspan(float(pred["gap_lower_Hz"]), float(pred["gap_upper_Hz"]), color="#59A14F", alpha=0.08, zorder=0)
        ax.set_title(label, fontsize=11)
        ax.set_xlabel("波矢参数", fontsize=10)
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, alpha=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=9)
        ax.text(
            0.02,
            0.97,
            f"预测：{float(pred['overlap_Hz']):.2f} Hz / {float(pred['cover_ratio']):.3f}\n"
            f"GA20：{float(ga['overlap_Hz']):.2f} Hz / {float(ga['cover_ratio']):.3f}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8.2,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, pad=2.0),
        )
    axes[0].set_ylabel("频率 / Hz", fontsize=10)
    handles = [
        Line2D([0], [0], color=pred_color, lw=1.5, label="预测 Top5"),
        Line2D([0], [0], color=ga_color, lw=1.5, label="GA20"),
        Patch(facecolor=band_color, alpha=0.16, label="目标频带"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8.8, frameon=True, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(w_pad=1.2, rect=[0, 0.08, 1, 1])
    return save_fig(fig, "ch5_strict_fig8_dispersion_pred_vs_ga20_redraw")


def write_checklist(cases: pd.DataFrame, manifest: pd.DataFrame, unit_paths: dict[str, Path], dispersion_paths: dict[str, Path]) -> None:
    lines = [
        "# 第5章图5-7/图5-8重绘数据检查报告",
        "",
        "## 绘图原则",
        "",
        "- 单胞结构图由 MATLAB/COMSOL 几何生成流程 `export_ch5_pred_vs_ga20_unit_cells_v1.m` 重新导出，Python 仅负责排版。",
        "- 频散曲线均来自真实 COMSOL 导出的 `tbl1` 数据，不使用占位图或简化矩形。",
        "",
        "## 候选与数据路径",
        "",
        "| target_band | method | candidate_id | shape_id | shape_family | overlap_Hz | cover_ratio | geometry_png | dispersion_tbl1_csv | geometry_status | dispersion_exists |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for _, case in cases.iterrows():
        rec = manifest[(manifest["target_band_tag"].eq(case["target_band_tag"])) & (manifest["method"].eq(case["method"]))].iloc[0]
        disp_exists = Path(str(case["dispersion_tbl1_csv"])).exists()
        lines.append(
            f"| {case['target_band']} | {case['method']} | {case['candidate_id']} | {case['shape_id']} | {case['shape_family']} | "
            f"{float(case['overlap_Hz']):.3f} | {float(case['cover_ratio']):.3f} | {rec['png_path']} | {case['dispersion_tbl1_csv']} | {rec['status']} | {disp_exists} |"
        )
    lines.extend([
        "",
        "## MATLAB/COMSOL 单胞导出",
        "",
        f"- 是否成功调用 MATLAB 绘制真实单胞：{bool((manifest['status'].astype(str) == 'ok').all())}",
        f"- COMSOL 单胞导出 manifest：`{UNIT_MANIFEST}`",
        "",
        "## 频散数据检查",
        "",
        f"- 是否成功找到所有频散曲线数据：{all(Path(str(p)).exists() for p in cases['dispersion_tbl1_csv'])}",
        "- 若某个候选缺少几何或频散数据，本报告会在上表中显示 `False` 或 `failed`；本次未使用任何矩形示意或假图顶替。",
        "",
        "## 输出图件",
        "",
    ])
    for name, paths in [("图5-7 单胞结构对比", unit_paths), ("图5-8 频散曲线对比", dispersion_paths)]:
        lines.append(f"- {name}:")
        for ext, path in paths.items():
            lines.append(f"  - {ext}: `{path}`")
    CHECKLIST.write_text("\n".join(lines), encoding="utf-8")


def assemble() -> None:
    cases = pd.read_csv(CASE_CSV, low_memory=False)
    manifest = load_unit_manifest()
    unit_paths = draw_unit_cell_montage(cases, manifest)
    dispersion_paths = draw_dispersion_compare(cases)
    write_checklist(cases, manifest, unit_paths, dispersion_paths)
    print("[UNIT FIGURES]")
    for path in unit_paths.values():
        print(path)
    print("[DISPERSION FIGURES]")
    for path in dispersion_paths.values():
        print(path)
    print(f"[CHECKLIST] {CHECKLIST}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare-cases", "assemble"])
    args = parser.parse_args()
    if args.command == "prepare-cases":
        prepare_cases()
    else:
        assemble()


if __name__ == "__main__":
    main()
