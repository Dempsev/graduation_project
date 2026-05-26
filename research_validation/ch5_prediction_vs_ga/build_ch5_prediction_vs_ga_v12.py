from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

import joblib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from prediction_v3.models.feature_engineering import build_tail_prediction_frame
OUT_DIR = ROOT / "research_validation" / "ch5_prediction_vs_ga"
FIG_DIR = OUT_DIR / "figures"

V12_DATASET = ROOT / "data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/targetband_parametric_v1.csv"
FINAL_MODEL = ROOT / "data/prediction_targetband_param_v1_runs/param_targetband_final_hgb_dense_v12_all_history_ga20_clean_v1/final_predictor_bundle.joblib"
READINESS_DIR = ROOT / "data/analysis/predictor_readiness_v12_all_history_ga20_clean_v1"
CLS_DIR = ROOT / "data/prediction_targetband_param_v1_runs/param_targetband_cls_hgb_dense_v12_all_history_ga20_clean_v1/stratified_group_kfold"
COVER_DIR = ROOT / "data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v12_all_history_ga20_clean_v1/stratified_group_kfold"

CH4_SUMMARY = ROOT / "research_validation/ch4_ga_real_optimization/ch4_ga_summary_20gen.csv"
CH4_TYPICAL = ROOT / "research_validation/ch4_ga_real_optimization/ch4_typical_cases_20gen.csv"
CH4_REPORT = ROOT / "research_validation/ch4_ga_real_optimization/CH4_GA_REAL_OPTIMIZATION_REPORT_20GEN.md"

BANDS = [
    ("band140_180", "140–180 Hz", 140.0, 180.0),
    ("band160_200", "160–200 Hz", 160.0, 200.0),
    ("band180_220", "180–220 Hz", 180.0, 220.0),
    ("band200_240", "200–240 Hz", 200.0, 240.0),
    ("band220_260", "220–260 Hz", 220.0, 260.0),
    ("band240_280", "240–280 Hz", 240.0, 280.0),
]
BAND_ORDER = [b[0] for b in BANDS]
BAND_LABEL = {b[0]: b[1] for b in BANDS}
BAND_LOW = {b[0]: b[2] for b in BANDS}
BAND_HIGH = {b[0]: b[3] for b in BANDS}

PARAM_COLS = ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]
TOPK_VALUES = [5, 10, 20, 40]

PALETTE = {
    "predicted_topk": "#4E79A7",
    "random": "#F28E2B",
    "real_ga": "#59A14F",
    "strict": "#1F4E79",
    "seen_training": "#B07AA1",
    "seen_ga": "#E15759",
    "independent": "#76B7B2",
    "grid": "#E6E6E6",
    "text": "#222222",
}


def configure_fonts() -> str:
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
            "axes.edgecolor": PALETTE["text"],
            "axes.labelcolor": PALETTE["text"],
            "text.color": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
        }
    )
    return font_name


def nfmt(value: Any) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.12g}"


def canonical_key(row: pd.Series | Dict[str, Any]) -> str:
    get = row.get if isinstance(row, dict) else row.get
    point_id = str(get("point_id", ""))
    shape_id = str(get("shape_id", ""))
    low = get("target_band_low_Hz", np.nan)
    high = get("target_band_high_Hz", np.nan)
    parts = [point_id, shape_id, *[nfmt(get(c, np.nan)) for c in PARAM_COLS], nfmt(low), nfmt(high)]
    if not point_id or not shape_id or pd.isna(low) or pd.isna(high):
        return ""
    return "|".join(parts)


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def md_table(df: pd.DataFrame, path: Path, max_rows: int | None = None) -> None:
    show = df.copy()
    if max_rows is not None and len(show) > max_rows:
        show = show.head(max_rows)
    lines = []
    cols = list(show.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in show.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if pd.isna(value):
                text = ""
            elif isinstance(value, float):
                text = f"{value:.6g}"
            else:
                text = str(value)
            values.append(text.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    if max_rows is not None and len(df) > max_rows:
        lines.append("")
        lines.append(f"> 仅预览前 {max_rows} 行，完整结果见同名 CSV。")
    path.write_text("\n".join(lines), encoding="utf-8")


def save_all(fig: plt.Figure, stem: str) -> Dict[str, str]:
    paths: Dict[str, str] = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths[ext] = str(path)
    plt.close(fig)
    return paths


def style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_linewidth(0.8)
        ax.spines[side].set_color(PALETTE["text"])


def load_and_score_v12() -> tuple[pd.DataFrame, set[str], pd.DataFrame]:
    df = pd.read_csv(V12_DATASET)
    df = df[df["target_band_tag"].isin(BAND_ORDER)].copy()
    df["target_band"] = df["target_band_tag"].map(BAND_LABEL)
    df["physical_key_canonical"] = df.apply(canonical_key, axis=1)

    bundle = joblib.load(FINAL_MODEL)
    scored, _ = build_tail_prediction_frame(df)
    feature_cols = bundle["feature_cols"]
    X = scored.reindex(columns=feature_cols)
    fill_values = pd.Series(bundle.get("fill_values", {}))
    X = X.fillna(fill_values).fillna(0)
    scored["predicted_open_prob"] = bundle["classifier"].predict_proba(X)[:, 1]
    scored["predicted_cover_ratio"] = np.clip(bundle["regressor"].predict(X), 0, 1)
    scored["predicted_overlap_Hz"] = scored["predicted_cover_ratio"] * scored["target_band_width_Hz"]
    scored["predicted_score"] = scored["predicted_open_prob"] * scored["predicted_cover_ratio"]
    return scored, set(scored["physical_key_canonical"].dropna()), df


def load_ga20_history() -> tuple[pd.DataFrame, set[str]]:
    summary = pd.read_csv(CH4_SUMMARY)
    frames: list[pd.DataFrame] = []
    for _, srow in summary.iterrows():
        hist_path = Path(srow["output_dir"]) / "ga_history_v1.csv"
        if not hist_path.exists():
            continue
        hist = pd.read_csv(hist_path)
        hist["target_band"] = srow["target_band"]
        hist["target_band_tag"] = srow["target_band_tag"]
        hist["target_band_low_Hz"] = BAND_LOW[srow["target_band_tag"]]
        hist["target_band_high_Hz"] = BAND_HIGH[srow["target_band_tag"]]
        hist["target_band_width_Hz"] = hist["target_band_high_Hz"] - hist["target_band_low_Hz"]
        hist["evaluation_index"] = np.arange(1, len(hist) + 1)
        hist["source_file"] = str(hist_path)
        frames.append(hist)
    ga = pd.concat(frames, ignore_index=True)
    ga["physical_key_canonical"] = ga.apply(canonical_key, axis=1)
    return ga, set(ga["physical_key_canonical"].dropna())


def select_predicted_and_random(scored: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred_frames: list[pd.DataFrame] = []
    rand_frames: list[pd.DataFrame] = []
    for tag in BAND_ORDER:
        band_df = scored[scored["target_band_tag"] == tag].copy()
        pred = band_df.sort_values(["predicted_score", "predicted_cover_ratio", "predicted_open_prob"], ascending=False).head(40).copy()
        pred["rank_in_method"] = np.arange(1, len(pred) + 1)
        pred_frames.append(pred)

        rand = band_df.sample(n=min(40, len(band_df)), random_state=20260519 + BAND_ORDER.index(tag)).copy()
        rand["rank_in_method"] = np.arange(1, len(rand) + 1)
        rand_frames.append(rand)
    return pd.concat(pred_frames, ignore_index=True), pd.concat(rand_frames, ignore_index=True)


def leakage_tag(row: pd.Series) -> str:
    if not row.get("physical_key", ""):
        return "missing_physical_key"
    if bool(row.get("duplicated_across_methods", False)):
        return "duplicated_across_methods"
    if bool(row.get("in_v12_training_set", False)):
        return "seen_in_training"
    if bool(row.get("in_ga20_history", False)):
        return "seen_in_ga20"
    return "independent_candidate"


def normalize_candidate_rows(
    df: pd.DataFrame,
    method: str,
    source_file: str,
    v12_keys: set[str],
    ga_keys: set[str],
    predicted_keys: set[str],
    random_keys: set[str],
) -> pd.DataFrame:
    work = df.copy()
    work["method"] = method
    work["source_file"] = source_file
    work["target_band"] = work["target_band_tag"].map(BAND_LABEL).fillna(work.get("target_band", ""))
    work["target_band_width_Hz"] = pd.to_numeric(work["target_band_high_Hz"], errors="coerce") - pd.to_numeric(work["target_band_low_Hz"], errors="coerce")
    if "physical_key_canonical" not in work:
        work["physical_key_canonical"] = work.apply(canonical_key, axis=1)
    work["physical_key"] = work["physical_key_canonical"]
    work["in_v12_training_set"] = work["physical_key"].isin(v12_keys)
    work["in_ga20_history"] = work["physical_key"].isin(ga_keys)
    work["in_predicted_topk"] = work["physical_key"].isin(predicted_keys)
    work["in_random"] = work["physical_key"].isin(random_keys)
    work["duplicated_across_methods"] = work["in_predicted_topk"] & work["in_random"]
    work["leakage_tag"] = work.apply(leakage_tag, axis=1)
    return work


def build_unified(pred: pd.DataFrame, rand: pd.DataFrame, ga: pd.DataFrame, v12_keys: set[str], ga_keys: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    predicted_keys = set(pred["physical_key_canonical"].dropna())
    random_keys = set(rand["physical_key_canonical"].dropna())

    pred_norm = normalize_candidate_rows(pred, "predicted_topk", str(FINAL_MODEL), v12_keys, ga_keys, predicted_keys, random_keys)
    rand_norm = normalize_candidate_rows(rand, "random", str(V12_DATASET), v12_keys, ga_keys, predicted_keys, random_keys)
    ga_norm = normalize_candidate_rows(ga, "real_ga", "ch4_ga_history_v1.csv", v12_keys, ga_keys, predicted_keys, random_keys)

    def map_truth(work: pd.DataFrame) -> pd.DataFrame:
        work = work.copy()
        work["true_gap_lower_Hz"] = work.get("target_gap_lower_edge_Hz", np.nan)
        work["true_gap_upper_Hz"] = work.get("target_gap_upper_edge_Hz", np.nan)
        work["true_overlap_Hz"] = work.get("target_gap_overlap_Hz", np.nan)
        work["true_cover_ratio"] = work.get("target_gap_cover_ratio", np.nan)
        if "active_target_overlap_Hz" in work:
            work["true_gap_lower_Hz"] = work.get("active_target_lower_edge_Hz", work["true_gap_lower_Hz"])
            work["true_gap_upper_Hz"] = work.get("active_target_upper_edge_Hz", work["true_gap_upper_Hz"])
            work["true_overlap_Hz"] = work.get("active_target_overlap_Hz", work["true_overlap_Hz"])
            work["true_cover_ratio"] = work.get("active_target_cover_ratio", work["true_cover_ratio"])
        missing_overlap = pd.to_numeric(work["true_overlap_Hz"], errors="coerce").isna()
        work.loc[missing_overlap, "true_overlap_Hz"] = pd.to_numeric(work.loc[missing_overlap, "true_cover_ratio"], errors="coerce") * pd.to_numeric(work.loc[missing_overlap, "target_band_width_Hz"], errors="coerce")
        work["active_open"] = pd.to_numeric(work["true_overlap_Hz"], errors="coerce").fillna(0) > 0
        return work

    pred_norm = map_truth(pred_norm)
    rand_norm = map_truth(rand_norm)
    ga_norm = map_truth(ga_norm)

    for work in [pred_norm, rand_norm]:
        work["evaluation_scope"] = "engineering_screening"
        work["verification_budget_index"] = work["rank_in_method"]
        work["generation"] = np.nan
        work["evaluation_index"] = np.nan

    ga_norm["evaluation_scope"] = "real_ga_reference"
    ga_norm["rank_in_method"] = ga_norm["evaluation_index"]
    ga_norm["verification_budget_index"] = ga_norm["evaluation_index"]
    for col in ["predicted_open_prob", "predicted_cover_ratio", "predicted_overlap_Hz", "predicted_score"]:
        if col not in ga_norm:
            ga_norm[col] = np.nan

    strict = pd.concat([pred_norm, rand_norm], ignore_index=True)
    strict = strict[(~strict["in_v12_training_set"]) & (~strict["in_ga20_history"])].copy()
    strict["evaluation_scope"] = "strict_holdout"

    unified = pd.concat([pred_norm, rand_norm, strict, ga_norm], ignore_index=True, sort=False)

    out_cols = [
        "target_band", "target_band_low_Hz", "target_band_high_Hz", "target_band_width_Hz",
        "method", "evaluation_scope", "source_file", "candidate_id", "point_id", "shape_id", "shape_family",
        "physical_key", "rank_in_method", "verification_budget_index", "generation", "evaluation_index",
        "predicted_open_prob", "predicted_cover_ratio", "predicted_overlap_Hz", "predicted_score",
        "true_gap_lower_Hz", "true_gap_upper_Hz", "true_overlap_Hz", "true_cover_ratio", "active_open",
        "geometry_valid", "contact_valid", "solve_success", "leakage_tag", "note",
    ]
    for col in out_cols:
        if col not in unified:
            unified[col] = ""
    unified["note"] = unified["note"].fillna("")
    unified.loc[unified["method"].isin(["predicted_topk", "random"]) & unified["in_v12_training_set"], "note"] = "候选来自 v12 数据集，属于 engineering_screening 口径，不作为独立 holdout 证据。"
    unified.loc[unified["method"].eq("real_ga"), "note"] = "第4章20代真实COMSOL-GA历史评价记录。"

    audit_cols = [
        "target_band", "method", "candidate_id", "physical_key", "in_v12_training_set", "in_ga20_history",
        "in_predicted_topk", "in_random", "leakage_tag", "note",
    ]
    audit = pd.concat([pred_norm, rand_norm, ga_norm], ignore_index=True, sort=False)
    if "note" not in audit:
        audit["note"] = ""
    audit["note"] = audit["note"].fillna("")
    audit = audit[audit_cols].copy()
    return unified[out_cols], audit


def summarize_topk(unified: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope in ["engineering_screening", "strict_holdout"]:
        scope_df = unified[(unified["evaluation_scope"] == scope) & (unified["method"] == "predicted_topk")].copy()
        for tag in BAND_ORDER:
            bdf = scope_df[scope_df["target_band"] == BAND_LABEL[tag]].sort_values("rank_in_method")
            for k in TOPK_VALUES:
                sub = bdf.head(k).copy()
                n = len(sub)
                note = ""
                if n == 0 and scope == "strict_holdout":
                    note = "strict_holdout 无独立候选；v12候选均已见于训练集或GA20历史。"
                success = sub["solve_success"].replace("", np.nan) if "solve_success" in sub else pd.Series(dtype=float)
                solve_success = pd.to_numeric(success, errors="coerce")
                n_solve = int(solve_success.fillna(1).sum()) if n else 0
                active = sub["active_open"].astype(bool) if n else pd.Series(dtype=bool)
                best_idx = pd.to_numeric(sub["true_cover_ratio"], errors="coerce").idxmax() if n and pd.to_numeric(sub["true_cover_ratio"], errors="coerce").notna().any() else None
                best = sub.loc[best_idx] if best_idx is not None else pd.Series(dtype=object)
                corr_cover = np.nan
                corr_overlap = np.nan
                if n >= 3:
                    corr_cover = sub[["predicted_cover_ratio", "true_cover_ratio"]].corr(method="spearman").iloc[0, 1]
                    corr_overlap = sub[["predicted_overlap_Hz", "true_overlap_Hz"]].corr(method="spearman").iloc[0, 1]
                rows.append({
                    "target_band": BAND_LABEL[tag],
                    "evaluation_scope": scope,
                    "k": k,
                    "n_candidates": n,
                    "n_independent_candidates": int((sub["leakage_tag"] == "independent_candidate").sum()) if n else 0,
                    "n_seen_in_training": int(sub["in_v12_training_set"].sum()) if "in_v12_training_set" in sub else n,
                    "n_seen_in_ga20": int(sub["in_ga20_history"].sum()) if "in_ga20_history" in sub else 0,
                    "n_solve_success": n_solve,
                    "solve_success_rate": n_solve / n if n else np.nan,
                    "n_active": int(active.sum()) if n else 0,
                    "active_rate": float(active.mean()) if n else np.nan,
                    "best_true_cover_ratio": pd.to_numeric(sub["true_cover_ratio"], errors="coerce").max() if n else np.nan,
                    "mean_true_cover_ratio": pd.to_numeric(sub["true_cover_ratio"], errors="coerce").mean() if n else np.nan,
                    "median_true_cover_ratio": pd.to_numeric(sub["true_cover_ratio"], errors="coerce").median() if n else np.nan,
                    "best_true_overlap_Hz": pd.to_numeric(sub["true_overlap_Hz"], errors="coerce").max() if n else np.nan,
                    "mean_true_overlap_Hz": pd.to_numeric(sub["true_overlap_Hz"], errors="coerce").mean() if n else np.nan,
                    "median_true_overlap_Hz": pd.to_numeric(sub["true_overlap_Hz"], errors="coerce").median() if n else np.nan,
                    "best_candidate_id": best.get("candidate_id", "") if len(best) else "",
                    "best_rank": best.get("rank_in_method", np.nan) if len(best) else np.nan,
                    "best_predicted_open_prob": best.get("predicted_open_prob", np.nan) if len(best) else np.nan,
                    "best_predicted_cover_ratio": best.get("predicted_cover_ratio", np.nan) if len(best) else np.nan,
                    "best_predicted_overlap_Hz": best.get("predicted_overlap_Hz", np.nan) if len(best) else np.nan,
                    "best_predicted_score": best.get("predicted_score", np.nan) if len(best) else np.nan,
                    "spearman_rank_corr_pred_cover": corr_cover,
                    "spearman_rank_corr_pred_overlap": corr_overlap,
                    "note": note,
                })
    return pd.DataFrame(rows)


def best_by_method(unified: pd.DataFrame, k: int = 40) -> pd.DataFrame:
    frames = []
    for method, scope in [("predicted_topk", "engineering_screening"), ("random", "engineering_screening"), ("real_ga", "real_ga_reference")]:
        df = unified[(unified["method"] == method) & (unified["evaluation_scope"] == scope)].copy()
        if method != "real_ga":
            df = df[pd.to_numeric(df["rank_in_method"], errors="coerce") <= k]
        agg = df.groupby("target_band", as_index=False).agg(
            best_true_overlap_Hz=("true_overlap_Hz", "max"),
            best_true_cover_ratio=("true_cover_ratio", "max"),
            active_rate=("active_open", "mean"),
        )
        agg["method"] = method
        frames.append(agg)
    return pd.concat(frames, ignore_index=True)


def draw_figures(unified: pd.DataFrame, topk: pd.DataFrame, audit: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    outputs: Dict[str, Dict[str, str]] = {}

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.axis("off")
    boxes = [
        (0.06, 0.60, "v12最终模型\nHGB分类+覆盖率回归"),
        (0.32, 0.60, "预测Top-k候选\n覆盖率主线排序"),
        (0.58, 0.60, "随机候选\n同字段口径"),
        (0.84, 0.60, "第4章20代\n真实GA基准"),
        (0.32, 0.20, "physical_key\n重叠审计"),
        (0.58, 0.20, "COMSOL真值字段映射\ntrue_cover/true_overlap"),
    ]
    for x, y, text in boxes:
        ax.text(x, y, text, ha="center", va="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.35", facecolor="#F7F7F7", edgecolor="#555555"))
    for x1, y1, x2, y2 in [(0.17, .60, .24, .60), (.43, .60, .50, .60), (.69, .60, .76, .60), (.32,.50,.32,.31), (.58,.50,.58,.31), (.41,.20,.49,.20)]:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.0, color="#555555"))
    ax.set_title("第5章对比实验流程", fontsize=12)
    outputs["ch5_fig5_1_comparison_workflow"] = save_all(fig, "ch5_fig5_1_comparison_workflow")

    best40 = best_by_method(unified, 40)
    labels = [BAND_LABEL[t] for t in BAND_ORDER]
    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for i, method in enumerate(["predicted_topk", "random"]):
        vals = [best40[(best40["target_band"] == lab) & (best40["method"] == method)]["active_rate"].max() for lab in labels]
        ax.bar(x + (i - .5) * width, vals, width, label=method, color=PALETTE[method], edgecolor="#333333", linewidth=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylim(0, 1.1); ax.set_ylabel("有效率"); ax.set_title("预测Top-k与随机候选有效率对比")
    style_axis(ax); ax.legend()
    outputs["ch5_fig5_2_topk_random_active_rate"] = save_all(fig, "ch5_fig5_2_topk_random_active_rate")

    for metric, stem, title, ylabel in [
        ("best_true_overlap_Hz", "ch5_fig5_3_best_overlap_compare", "最优目标频带重叠宽度对比", "目标频带重叠宽度 / Hz"),
        ("best_true_cover_ratio", "ch5_fig5_4_best_cover_compare", "最优目标频带覆盖率对比", "目标频带覆盖率"),
    ]:
        fig, ax = plt.subplots(figsize=(7.4, 3.8))
        for i, method in enumerate(["predicted_topk", "random", "real_ga"]):
            vals = [best40[(best40["target_band"] == lab) & (best40["method"] == method)][metric].max() for lab in labels]
            ax.bar(x + (i - 1) * width, vals, width, label=method, color=PALETTE[method], edgecolor="#333333", linewidth=0.6)
        ax.set_xticks(x); ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_ylabel(ylabel); ax.set_title(title); style_axis(ax); ax.legend()
        outputs[stem] = save_all(fig, stem)

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6), sharey=True)
    for ax, metric, title in zip(axes, ["best_true_overlap_Hz", "best_true_cover_ratio"], ["按重叠宽度", "按覆盖率"]):
        for tag in BAND_ORDER:
            ga_best = best40[(best40["target_band"] == BAND_LABEL[tag]) & (best40["method"] == "real_ga")][metric].max()
            vals = []
            for k in TOPK_VALUES:
                row = topk[(topk["target_band"] == BAND_LABEL[tag]) & (topk["evaluation_scope"] == "engineering_screening") & (topk["k"] == k)]
                val = row["best_true_overlap_Hz" if "overlap" in metric else "best_true_cover_ratio"].max()
                vals.append(val / ga_best if ga_best and ga_best > 0 else np.nan)
            ax.plot(TOPK_VALUES, vals, marker="o", label=BAND_LABEL[tag])
        ax.axhline(0.8, color="#999999", lw=0.8, ls="--")
        ax.set_title(title); ax.set_xlabel("Top-k预算"); ax.grid(axis="y", color=PALETTE["grid"])
    axes[0].set_ylabel("达到GA最优的比例")
    axes[1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    outputs["ch5_fig5_5_topk_to_ga_ratio"] = save_all(fig, "ch5_fig5_5_topk_to_ga_ratio")

    for metric, stem, title, ylabel in [
        ("true_overlap_Hz", "ch5_fig5_6_budget_best_overlap_curve", "验证预算-历史最优重叠宽度曲线", "历史最优重叠宽度 / Hz"),
        ("true_cover_ratio", "ch5_fig5_7_budget_best_cover_curve", "验证预算-历史最优覆盖率曲线", "历史最优覆盖率"),
    ]:
        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        for method, scope in [("predicted_topk", "engineering_screening"), ("random", "engineering_screening")]:
            df = unified[(unified["method"] == method) & (unified["evaluation_scope"] == scope)].copy()
            df = df.sort_values(["target_band", "rank_in_method"])
            curve = df.groupby("rank_in_method")[metric].max().cummax()
            ax.plot(curve.index, curve.values, marker="o", markersize=3, label=method, color=PALETTE[method])
        ga = unified[(unified["method"] == "real_ga") & (unified["evaluation_scope"] == "real_ga_reference")].copy()
        ga_curve = ga.groupby("evaluation_index")[metric].max().cummax()
        ax.plot(ga_curve.index, ga_curve.values, label="real_ga", color=PALETTE["real_ga"], lw=1.6)
        ax.set_xlabel("验证/评价预算"); ax.set_ylabel(ylabel); ax.set_title(title); style_axis(ax); ax.legend()
        outputs[stem] = save_all(fig, stem)

    leak_summary = audit[audit["method"].isin(["predicted_topk", "random"])].copy()
    leak_summary["category"] = np.select(
        [leak_summary["leakage_tag"].eq("independent_candidate"), leak_summary["in_ga20_history"], leak_summary["in_v12_training_set"]],
        ["独立候选", "GA20已见", "训练集已见"],
        default="其他",
    )
    counts = leak_summary.groupby(["method", "category"]).size().unstack(fill_value=0)
    prop = counts.div(counts.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    bottom = np.zeros(len(prop))
    for cat, color in [("独立候选", PALETTE["independent"]), ("训练集已见", PALETTE["seen_training"]), ("GA20已见", PALETTE["seen_ga"]), ("其他", "#BBBBBB")]:
        vals = prop[cat].values if cat in prop else np.zeros(len(prop))
        ax.bar(prop.index, vals, bottom=bottom, label=cat, color=color, edgecolor="#333333", linewidth=0.5)
        bottom += vals
    ax.set_ylim(0, 1.05); ax.set_ylabel("比例"); ax.set_title("physical_key重叠审计")
    style_axis(ax); ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    outputs["ch5_fig5_8_physical_key_overlap_audit"] = save_all(fig, "ch5_fig5_8_physical_key_overlap_audit")

    outputs.update(draw_case_figures(unified))
    return outputs


def draw_shape(ax: plt.Axes, shape_id: str) -> None:
    path = ROOT / "data/shape_contours" / f"{shape_id}.csv"
    ax.axis("off")
    ax.set_aspect("equal")
    if not path.exists():
        ax.text(0.5, 0.5, "缺少轮廓", ha="center", va="center")
        return
    xy = pd.read_csv(path)
    ax.fill(xy["x"], xy["y"], color="#9DB4C0", edgecolor="#333333", linewidth=0.8, alpha=0.9)
    pad = max(xy["x"].max() - xy["x"].min(), xy["y"].max() - xy["y"].min()) * 0.2
    ax.set_xlim(xy["x"].min() - pad, xy["x"].max() + pad)
    ax.set_ylim(xy["y"].min() - pad, xy["y"].max() + pad)


def draw_case_figures(unified: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    outputs: Dict[str, Dict[str, str]] = {}
    case_bands = ["180–220 Hz", "200–240 Hz", "240–280 Hz"]
    fig, axes = plt.subplots(len(case_bands), 3, figsize=(7.0, 6.0))
    for r, band in enumerate(case_bands):
        for c, method in enumerate(["predicted_topk", "random", "real_ga"]):
            scope = "real_ga_reference" if method == "real_ga" else "engineering_screening"
            df = unified[(unified["target_band"] == band) & (unified["method"] == method) & (unified["evaluation_scope"] == scope)].copy()
            if df.empty:
                axes[r, c].axis("off")
                continue
            idx = pd.to_numeric(df["true_cover_ratio"], errors="coerce").idxmax()
            row = df.loc[idx]
            draw_shape(axes[r, c], row["shape_id"])
            axes[r, c].set_title(f"{band}\n{method}\n{row['shape_id']}", fontsize=7)
    fig.suptitle("典型目标频带结构单胞对比图", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    outputs["ch5_fig5_9_typical_unit_cell_compare"] = save_all(fig, "ch5_fig5_9_typical_unit_cell_compare")

    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.2))
    for ax, tag in zip(axes, ["band180_220", "band200_240", "band240_280"]):
        path = ROOT / f"research_validation/ch4_ga_real_optimization/figures/ch4_fig4_7_dispersion_{tag}.png"
        if path.exists():
            ax.imshow(mpimg.imread(path))
        else:
            ax.text(0.5, 0.5, "缺少频散图", ha="center", va="center")
        ax.axis("off")
        ax.set_title(BAND_LABEL[tag], fontsize=9)
    fig.suptitle("典型目标频带频散曲线与目标频带标注", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    outputs["ch5_fig5_10_typical_dispersion_compare"] = save_all(fig, "ch5_fig5_10_typical_dispersion_compare")

    high = best_by_method(unified, 40)
    high = high[high["target_band"].isin(["220–260 Hz", "240–280 Hz"])]
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    xlabels = ["220–260 Hz", "240–280 Hz"]
    x = np.arange(len(xlabels))
    width = 0.25
    for i, method in enumerate(["predicted_topk", "random", "real_ga"]):
        vals = [high[(high["target_band"] == lab) & (high["method"] == method)]["best_true_cover_ratio"].max() for lab in xlabels]
        ax.bar(x + (i - 1) * width, vals, width, label=method, color=PALETTE[method], edgecolor="#333333", linewidth=0.6)
    ax.set_xticks(x); ax.set_xticklabels(xlabels)
    ax.set_ylabel("最优目标频带覆盖率"); ax.set_title("高频困难频带边界分析")
    style_axis(ax); ax.legend()
    outputs["ch5_fig5_11_highfreq_boundary_analysis"] = save_all(fig, "ch5_fig5_11_highfreq_boundary_analysis")
    return outputs


def write_report(
    unified: pd.DataFrame,
    audit: pd.DataFrame,
    topk: pd.DataFrame,
    outputs: Dict[str, Dict[str, str]],
    terminal: Dict[str, Any],
) -> None:
    strict_counts = terminal["strict_holdout_counts"]
    pred_v12_overlap = terminal["predicted_topk_v12_overlap"]
    pred_ga_overlap = terminal["predicted_topk_ga20_overlap"]
    rand_v12_overlap = terminal["random_v12_overlap"]
    strict_df = pd.DataFrame({"target_band": list(strict_counts.keys()), "strict_holdout_n": list(strict_counts.values())})
    strict_lines = ["| target_band | strict_holdout_n |", "| --- | ---: |"]
    strict_lines.extend([f"| {r.target_band} | {r.strict_holdout_n} |" for r in strict_df.itertuples(index=False)])
    lines = [
        "# 第5章 预测筛选与真实遗传优化对比材料整理报告",
        "",
        "## 5.1 对比实验设置与数据来源",
        "",
        f"第三章最终模型采用 v12 all-history + GA20 clean 数据集，数据文件为 `{V12_DATASET}`，清洗后样本数为 46,754 行；最终模型包为 `{FINAL_MODEL}`。第5章比较对象包括：预测 Top-k 候选、随机候选和第4章20代真实 COMSOL-GA 基准。",
        "",
        "本章统一采用覆盖率主线：分类标签为 `target_gap_is_open`，回归标签为 `target_gap_cover_ratio`，真实重叠宽度为 `target_gap_overlap_Hz`。输出表中统一映射为 `true_cover_ratio` 与 `true_overlap_Hz`。",
        "",
        "## 5.2 数据独立性与 physical_key 重叠审计",
        "",
        f"审计表见 `ch5_physical_key_overlap_audit.csv/md`。预测 Top-k 与 v12 训练集 physical_key 重叠数量为 {pred_v12_overlap}，与 GA20 历史重叠数量为 {pred_ga_overlap}；随机候选与 v12 训练集重叠数量为 {rand_v12_overlap}。",
        "",
        "由于本次 predicted_topk 与 random 均从 v12 已清洗候选池中整理，strict_holdout 口径下独立候选数量不足。第5章主要结果应采用 `engineering_screening` 口径，strict_holdout 仅作为数据独立性审计参考。",
        "",
        "strict_holdout 各频带剩余样本数：",
        "",
        "\n".join(strict_lines),
        "",
        "## 5.3 预测 Top-k 候选筛选结果分析",
        "",
        "Top-k 统计表见 `ch5_topk_validation_summary.csv/md`。在 engineering_screening 口径下，预测候选按照 `predicted_score = predicted_open_prob × predicted_cover_ratio` 排序，并同时报告真实覆盖率与真实重叠宽度。",
        "",
        "## 5.4 随机候选与预测候选对比",
        "",
        "统一候选对比表见 `ch5_unified_candidate_comparison.csv/md`。图5-2比较预测 Top-k 与随机候选有效率，图5-3和图5-4分别比较最优重叠宽度与最优覆盖率。",
        "",
        "## 5.5 预测候选与真实 GA 基准对比",
        "",
        "真实 GA 基准严格采用第4章20代结果，不回退到12代。图5-5给出 Top-k 预算下预测候选达到 GA 最优的比例，分别按重叠宽度和覆盖率计算。",
        "",
        "## 5.6 验证预算效率分析",
        "",
        "图5-6与图5-7分别给出预算-历史最优重叠宽度曲线和预算-历史最优覆盖率曲线。由于 predicted_topk/random 的 v12 真值并非新独立验证，预算效率表述应限定为工程筛选复盘，不宜写成严格泛化验证。",
        "",
        "## 5.7 典型目标频带案例分析",
        "",
        "图5-9整理了 180–220 Hz、200–240 Hz、240–280 Hz 三个典型频带下 predicted_topk、random、real_ga 的最优结构轮廓对比；图5-10引用第4章真实 GA 代表频带频散曲线。",
        "",
        "## 5.8 高频困难频带与方法边界分析",
        "",
        "图5-11显示 220–260 Hz 与 240–280 Hz 在三类方法下的最优覆盖率均明显低于中频段，说明高频困难更可能来自当前结构族与参数空间的可达性限制，而不只是排序模型本身。",
        "",
        "## 5.9 本章小结",
        "",
        "1. v12 最终模型可用于工程筛选排序，但第5章必须显式标注候选是否已见于训练数据或GA20历史。",
        "2. 本章统一采用 `true_cover_ratio` 与 `true_overlap_Hz` 双指标，避免只看重叠宽度造成解释偏差。",
        "3. 第4章20代真实 GA 是本章真实优化基准，不能再使用旧12代结果。",
        "4. strict_holdout 样本不足时，应把其作为审计结果，而不是伪造独立验证结论。",
        "5. 高频目标频带的低覆盖率提示后续应优先扩展结构族或参数化机制。",
        "",
        "## 图件清单",
        "",
    ]
    for stem, paths in outputs.items():
        lines.append(f"- `{stem}`: `{Path(paths['png']).name}`, `{Path(paths['svg']).name}`, `{Path(paths['pdf']).name}`")
    (OUT_DIR / "CH5_PREDICTION_SCREENING_VS_REAL_GA_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def terminal_summary(unified: pd.DataFrame, audit: pd.DataFrame) -> Dict[str, Any]:
    pred = audit[audit["method"] == "predicted_topk"]
    rand = audit[audit["method"] == "random"]
    strict = unified[unified["evaluation_scope"] == "strict_holdout"]
    strict_counts = {BAND_LABEL[tag]: int((strict["target_band"] == BAND_LABEL[tag]).sum()) for tag in BAND_ORDER}
    generated = sorted([p.name for p in OUT_DIR.glob("*") if p.is_file()] + [f"figures/{p.name}" for p in FIG_DIR.glob("*") if p.is_file()])
    return {
        "final_model_exists": FINAL_MODEL.exists(),
        "readiness_dir_exists": READINESS_DIR.exists(),
        "predicted_topk_has_independent_comsol": False,
        "random_has_independent_comsol": False,
        "predicted_topk_v12_overlap": int(pred["in_v12_training_set"].sum()),
        "predicted_topk_ga20_overlap": int(pred["in_ga20_history"].sum()),
        "random_v12_overlap": int(rand["in_v12_training_set"].sum()),
        "random_ga20_overlap": int(rand["in_ga20_history"].sum()),
        "strict_holdout_counts": strict_counts,
        "generated_files": generated,
    }


def main() -> None:
    ensure_dirs()
    font_name = configure_fonts()
    scored, v12_keys, _ = load_and_score_v12()
    ga, ga_keys = load_ga20_history()
    pred, rand = select_predicted_and_random(scored)
    unified, audit = build_unified(pred, rand, ga, v12_keys, ga_keys)
    topk = summarize_topk(unified)

    unified.to_csv(OUT_DIR / "ch5_unified_candidate_comparison.csv", index=False, encoding="utf-8-sig")
    audit.to_csv(OUT_DIR / "ch5_physical_key_overlap_audit.csv", index=False, encoding="utf-8-sig")
    topk.to_csv(OUT_DIR / "ch5_topk_validation_summary.csv", index=False, encoding="utf-8-sig")
    md_table(unified, OUT_DIR / "ch5_unified_candidate_comparison.md", max_rows=80)
    md_table(audit, OUT_DIR / "ch5_physical_key_overlap_audit.md", max_rows=120)
    md_table(topk, OUT_DIR / "ch5_topk_validation_summary.md")

    outputs = draw_figures(unified, topk, audit)
    term = terminal_summary(unified, audit)
    term["font_name"] = font_name
    write_report(unified, audit, topk, outputs, term)
    (OUT_DIR / "CH5_TERMINAL_CHECKLIST_V12.md").write_text(json.dumps(term, ensure_ascii=False, indent=2), encoding="utf-8")

    print("# 第5章 v12 口径材料整理完成")
    print(f"第三章最终模型路径存在: {term['final_model_exists']} -> {FINAL_MODEL}")
    print(f"readiness 目录存在: {term['readiness_dir_exists']} -> {READINESS_DIR}")
    print(f"predicted_topk 候选是否已有独立真实 COMSOL 验证结果: {term['predicted_topk_has_independent_comsol']}")
    print(f"random 候选是否已有独立真实 COMSOL 验证结果: {term['random_has_independent_comsol']}")
    print(f"predicted_topk 与 v12 训练集 physical_key 重叠数量: {term['predicted_topk_v12_overlap']}")
    print(f"predicted_topk 与 GA20 历史 physical_key 重叠数量: {term['predicted_topk_ga20_overlap']}")
    print(f"random 与 v12 训练集 physical_key 重叠数量: {term['random_v12_overlap']}")
    print(f"random 与 GA20 历史 physical_key 重叠数量: {term['random_ga20_overlap']}")
    print("strict_holdout 口径下每个频带剩余样本数量:")
    for band, count in term["strict_holdout_counts"].items():
        print(f"- {band}: {count}")
    print("strict_holdout 样本不足建议: 先从 v12 候选池中剔除训练/GA20 physical_key，生成待验证manifest；优先选择每个频带Top-20预测高分但未见候选，再人工启动短预算COMSOL验证。")
    print("生成文件:")
    for name in term["generated_files"]:
        print(f"- {name}")


if __name__ == "__main__":
    main()
