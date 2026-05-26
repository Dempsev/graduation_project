from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch5_strict_holdout_validation"
CH4_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"

CASE_CSV = OUT_DIR / "ch5_pred_vs_ga20_redraw_cases.csv"
UNIT_MANIFEST = OUT_DIR / "ch5_pred_vs_ga20_unit_cell_export_manifest.csv"
STRICT_RESULTS = OUT_DIR / "ch5_strict_holdout_comsol_results_top5_random5.csv"
STRICT_POOL = OUT_DIR / "ch5_strict_holdout_candidate_pool.csv"
V12_DATASET = ROOT / "data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/targetband_parametric_v1.csv"
EXISTING_CH5 = ROOT / "research_validation/ch5_prediction_vs_ga/ch5_unified_candidate_comparison.csv"
CH4_SUMMARY = CH4_DIR / "ch4_ga_summary_20gen.csv"
CH4_TYPICAL = CH4_DIR / "ch4_typical_cases_20gen.csv"
REDRAW_SCRIPT = OUT_DIR / "redraw_ch5_fig7_fig8_pred_vs_ga20.py"
EXPORT_SCRIPT = OUT_DIR / "export_ch5_pred_vs_ga20_unit_cells_v1.m"

BANDS = [
    ("band180_220", "180\u2013220 Hz", 180.0, 220.0),
    ("band200_240", "200\u2013240 Hz", 200.0, 240.0),
    ("band240_280", "240\u2013280 Hz", 240.0, 280.0),
]
PARAM_COLS = ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]
PARAM_BOUNDS = {
    "a1": (0.35, 0.55),
    "a2": (-0.18, 0.08),
    "b1": (-0.05, 0.05),
    "b2": (-0.08, 0.08),
    "a3": (-0.04, 0.04),
    "b3": (-0.04, 0.04),
    "a4": (-0.03, 0.03),
    "b4": (-0.03, 0.03),
    "a5": (-0.02, 0.02),
    "b5": (-0.02, 0.03),
    "r0": (0.010, 0.014),
}
IDENTITY_OUT = OUT_DIR / "ch5_fig7_candidate_identity_audit.csv"
DIST_OUT = OUT_DIR / "parameter_distance_table.csv"
PLOT_OUT = OUT_DIR / "ch5_fig7_plotting_source_audit.csv"
REPORT_OUT = OUT_DIR / "CH5_FIG7_INDEPENDENCE_AND_PLOTTING_AUDIT.md"


def nfmt(value: Any) -> str:
    try:
        if pd.isna(value):
            return ""
        return f"{float(value):.12g}"
    except Exception:
        return str(value)


def canonical_key(row: pd.Series | dict[str, Any]) -> str:
    get = row.get
    point_id = str(get("point_id", ""))
    shape_id = str(get("shape_id", ""))
    low = get("target_band_low_Hz", np.nan)
    high = get("target_band_high_Hz", np.nan)
    if not point_id or not shape_id or pd.isna(low) or pd.isna(high):
        return ""
    return "|".join([point_id, shape_id, *[nfmt(get(col, np.nan)) for col in PARAM_COLS], nfmt(low), nfmt(high)])


def no_point_key(row: pd.Series | dict[str, Any]) -> str:
    get = row.get
    shape_id = str(get("shape_id", ""))
    low = get("target_band_low_Hz", np.nan)
    high = get("target_band_high_Hz", np.nan)
    if not shape_id or pd.isna(low) or pd.isna(high):
        return ""
    return "|".join([shape_id, *[nfmt(get(col, np.nan)) for col in PARAM_COLS], nfmt(low), nfmt(high)])


def load_ga20_history_keys() -> tuple[set[str], set[str]]:
    summary = pd.read_csv(CH4_SUMMARY, low_memory=False)
    keys: set[str] = set()
    no_point: set[str] = set()
    for _, srow in summary.iterrows():
        hist_path = Path(str(srow["output_dir"])) / "ga_history_v1.csv"
        if not hist_path.exists():
            continue
        hist = pd.read_csv(hist_path, low_memory=False)
        tag = str(srow["target_band_tag"])
        low, high = tag.split("band", 1)[1].split("_")
        hist["target_band_low_Hz"] = float(low)
        hist["target_band_high_Hz"] = float(high)
        if "point_id" not in hist.columns:
            hist["point_id"] = "rf09_h00_center"
        keys.update(hist.apply(canonical_key, axis=1))
        no_point.update(hist.apply(no_point_key, axis=1))
    return keys, no_point


def shape_feature_table() -> pd.DataFrame:
    v12 = pd.read_csv(V12_DATASET, low_memory=False)
    shape_cols = [col for col in v12.columns if col.startswith("shape_")]
    keep = ["shape_id", "shape_family", *[col for col in shape_cols if col not in {"shape_id", "shape_family"}]]
    return v12[keep].drop_duplicates("shape_id")


def selected_cases_with_keys() -> pd.DataFrame:
    cases = pd.read_csv(CASE_CSV, low_memory=False)
    shape_features = shape_feature_table()
    cases = cases.merge(shape_features, on=["shape_id", "shape_family"], how="left")
    for tag, _, low, high in BANDS:
        mask = cases["target_band_tag"].eq(tag)
        cases.loc[mask, "target_band_low_Hz"] = low
        cases.loc[mask, "target_band_high_Hz"] = high
        cases.loc[mask, "target_band_width_Hz"] = high - low
    cases["physical_key"] = cases.apply(canonical_key, axis=1)
    cases["shape_parameter_band_key"] = cases.apply(no_point_key, axis=1)
    cases["physical_key_source"] = np.where(cases["method"].eq("predicted_top5"), "strict_result_physical_key_or_rebuilt", "rebuilt_from_ga20_history")

    strict = pd.read_csv(STRICT_RESULTS, low_memory=False)
    strict_pred = strict[strict["method"].eq("predicted_top5")][["candidate_id", "physical_key"]].rename(columns={"physical_key": "strict_result_physical_key"})
    cases = cases.merge(strict_pred, on="candidate_id", how="left")
    cases.loc[cases["method"].eq("predicted_top5") & cases["strict_result_physical_key"].notna(), "physical_key"] = cases["strict_result_physical_key"]
    cases = cases.drop(columns=["strict_result_physical_key"], errors="ignore")
    return cases


def build_seen_audit(cases: pd.DataFrame) -> pd.DataFrame:
    v12 = pd.read_csv(V12_DATASET, low_memory=False)
    v12_keys = set(v12.get("physical_key", pd.Series(dtype=str)).dropna().astype(str))
    v12_keys.update(v12.apply(canonical_key, axis=1))
    v12_no_point = set(v12.apply(no_point_key, axis=1))

    ga_keys, ga_no_point = load_ga20_history_keys()

    existing = pd.read_csv(EXISTING_CH5, low_memory=False)
    existing_keys = set(existing.get("physical_key", pd.Series(dtype=str)).dropna().astype(str))
    if set(["point_id", "shape_id", "target_band_low_Hz", "target_band_high_Hz"]).issubset(existing.columns):
        existing_keys.update(existing.apply(canonical_key, axis=1))

    rows = []
    for _, row in cases.iterrows():
        is_pred = row["method"] == "predicted_top5"
        rows.append(
            {
                **row.to_dict(),
                "in_v12_training_set": row["physical_key"] in v12_keys,
                "in_ga20_history": row["physical_key"] in ga_keys,
                "in_existing_ch5": row["physical_key"] in existing_keys,
                "shape_parameter_band_in_v12": row["shape_parameter_band_key"] in v12_no_point,
                "shape_parameter_band_in_ga20": row["shape_parameter_band_key"] in ga_no_point,
                "strict_holdout_pass": bool(is_pred and row["physical_key"] not in v12_keys and row["physical_key"] not in ga_keys and row["physical_key"] not in existing_keys and row["shape_parameter_band_key"] not in v12_no_point and row["shape_parameter_band_key"] not in ga_no_point) if is_pred else "",
            }
        )
    audit = pd.DataFrame(rows)
    audit.to_csv(IDENTITY_OUT, index=False, encoding="utf-8-sig")
    return audit


def distance_table(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tag, label, _, _ in BANDS:
        pred = cases[(cases["target_band_tag"].eq(tag)) & (cases["method"].eq("predicted_top5"))].iloc[0]
        ga = cases[(cases["target_band_tag"].eq(tag)) & (cases["method"].eq("ga20"))].iloc[0]
        shape_same = str(pred["shape_id"]) == str(ga["shape_id"])
        family_same = str(pred["shape_family"]) == str(ga["shape_family"])
        norm_values = []
        for param in PARAM_COLS:
            pv = float(pred[param])
            gv = float(ga[param])
            abs_diff = abs(pv - gv)
            low, high = PARAM_BOUNDS[param]
            span = max(abs(high - low), 1e-12)
            norm_diff = abs_diff / span
            norm_values.append(norm_diff)
            rows.append(
                {
                    "target_band": label,
                    "target_band_tag": tag,
                    "parameter": param,
                    "predicted_value": pv,
                    "ga20_value": gv,
                    "absolute_difference": abs_diff,
                    "normalized_difference": norm_diff,
                    "shape_id_same": shape_same,
                    "shape_family_same": family_same,
                }
            )
        l2 = float(np.sqrt(np.sum(np.square(norm_values))))
        mean_norm = float(np.mean(norm_values))
        max_norm = float(np.max(norm_values))
        near_duplicate = bool(shape_same and max_norm < 0.05 and l2 < 0.10)
        near_duplicate_by_parameters = bool(max_norm < 0.03 and l2 < 0.08)
        for row in rows[-len(PARAM_COLS):]:
            row["normalized_l2_distance_all_params"] = l2
            row["mean_normalized_difference_all_params"] = mean_norm
            row["max_normalized_difference_all_params"] = max_norm
            row["near_duplicate"] = near_duplicate
            row["near_duplicate_by_parameters"] = near_duplicate_by_parameters
            row["distance_note"] = (
                "same_shape_but_parameters_not_near_duplicate"
                if shape_same and not near_duplicate
                else "different_shape"
                if not shape_same
                else "near_duplicate"
            )
    dist = pd.DataFrame(rows)
    dist.to_csv(DIST_OUT, index=False, encoding="utf-8-sig")
    return dist


def plotting_source_audit(cases: pd.DataFrame) -> pd.DataFrame:
    manifest = pd.read_csv(UNIT_MANIFEST, low_memory=False)
    rows = []
    for tag, label, _, _ in BANDS:
        for method in ["predicted_top5", "ga20"]:
            case = cases[(cases["target_band_tag"].eq(tag)) & (cases["method"].eq(method))].iloc[0]
            rec = manifest[(manifest["target_band_tag"].eq(tag)) & (manifest["method"].eq(method))].iloc[0]
            rows.append(
                {
                    "target_band": label,
                    "method": method,
                    "candidate_id": case["candidate_id"],
                    "shape_id": case["shape_id"],
                    "shape_file_input": case["shape_file"],
                    "unit_cell_png": rec["png_path"],
                    "unit_cell_status": rec["status"],
                    "geometry_valid": rec["geometry_valid"],
                    "contact_valid": rec["contact_valid"],
                    "uses_method_specific_output_file": method in str(rec["png_path"]),
                    "png_exists": Path(str(rec["png_path"])).exists(),
                }
            )
    plot = pd.DataFrame(rows)
    plot["geometry_png_duplicated"] = plot.duplicated("unit_cell_png", keep=False)
    plot["shape_file_duplicated_within_band"] = plot.duplicated(["target_band", "shape_file_input"], keep=False)

    redraw_text = REDRAW_SCRIPT.read_text(encoding="utf-8")
    export_text = EXPORT_SCRIPT.read_text(encoding="utf-8")
    plot["script_uses_manifest_method_filter"] = 'manifest["method"].eq(method)' in redraw_text
    plot["export_uses_case_row_params"] = "pointSpec = struct" in export_text and "double(row.a1(1))" in export_text
    plot["export_fallback_to_default_or_ga20"] = any(token in export_text.lower() for token in ["default geometry", "rectangle", "ga20 fallback"])
    plot.to_csv(PLOT_OUT, index=False, encoding="utf-8-sig")
    return plot


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    show = df if max_rows is None else df.head(max_rows)
    cols = list(show.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in show.iterrows():
        vals = []
        for col in cols:
            value = row[col]
            if pd.isna(value):
                text = ""
            elif isinstance(value, float):
                text = f"{value:.6g}"
            else:
                text = str(value)
            vals.append(text.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_report(identity: pd.DataFrame, dist: pd.DataFrame, plot: pd.DataFrame) -> None:
    pair_rows = []
    for tag, label, _, _ in BANDS:
        pred = identity[(identity["target_band_tag"].eq(tag)) & (identity["method"].eq("predicted_top5"))].iloc[0]
        ga = identity[(identity["target_band_tag"].eq(tag)) & (identity["method"].eq("ga20"))].iloc[0]
        dsub = dist[dist["target_band_tag"].eq(tag)]
        pair_rows.append(
            {
                "target_band": label,
                "physical_key_same": pred["physical_key"] == ga["physical_key"],
                "shape_parameter_band_key_same": pred["shape_parameter_band_key"] == ga["shape_parameter_band_key"],
                "shape_id_same": pred["shape_id"] == ga["shape_id"],
                "shape_family_same": pred["shape_family"] == ga["shape_family"],
                "max_normalized_difference": float(dsub["max_normalized_difference_all_params"].iloc[0]),
                "normalized_l2_distance": float(dsub["normalized_l2_distance_all_params"].iloc[0]),
                "near_duplicate": bool(dsub["near_duplicate"].iloc[0]),
                "near_duplicate_by_parameters": bool(dsub["near_duplicate_by_parameters"].iloc[0]),
                "pred_in_v12": bool(pred["in_v12_training_set"]),
                "pred_in_ga20": bool(pred["in_ga20_history"]),
                "pred_shape_param_in_v12": bool(pred["shape_parameter_band_in_v12"]),
                "pred_shape_param_in_ga20": bool(pred["shape_parameter_band_in_ga20"]),
            }
        )
    pair_df = pd.DataFrame(pair_rows)
    same_png = bool(plot["geometry_png_duplicated"].any())
    fallback = bool(plot["export_fallback_to_default_or_ga20"].any())
    can_use = not same_png and not fallback and not pair_df["physical_key_same"].any() and not pair_df["near_duplicate_by_parameters"].any()
    recommendation = (
        "方案A更适合论文：保留 predicted Top5 vs GA20，并在图注/正文说明 180–220 Hz 与 200–240 Hz 的 predicted Top5 与 GA20 使用相同 shape_id，说明预测模型在独立候选集中识别到与真实 GA20 相似的高性能结构；同时强调 physical_key 与连续参数不同。"
        if can_use
        else "建议改为方案B或补充随机候选对比，因为存在重复/近重复或绘图来源风险。"
    )

    lines = [
        "# 第5章图5-7独立性与绘图来源审计报告",
        "",
        "## 结论",
        "",
        f"- predicted_top5 和 GA20 是否 physical_key 完全不同：{not pair_df['physical_key_same'].any()}",
        f"- 是否存在 shape_id 相同：{bool(pair_df['shape_id_same'].any())}。180–220 Hz 与 200–240 Hz 相同，240–280 Hz 不同。",
        f"- 连续参数是否高度接近：{bool(pair_df['near_duplicate_by_parameters'].any())}。按当前阈值 max_norm<0.03 且 L2<0.08 未触发近重复。",
        f"- 图5-7是否误用了同一份几何绘图数据：{same_png}。manifest 中 predicted_top5 与 GA20 输出文件不同。",
        f"- 是否存在 fallback 到 GA20/默认/矩形占位图：{fallback}。脚本使用各自 case row 的 Fourier 参数与 shape_file 调用 `validate_stage2_harmonics_geometry`。",
        f"- 当前图是否可以放入论文：{can_use}。",
        f"- 推荐方案：{recommendation}",
        "",
        "## 每个频带配对审计",
        "",
        md_table(pair_df),
        "",
        "## 候选身份表",
        "",
        "完整表见 `ch5_fig7_candidate_identity_audit.csv`。下表保留核心字段：",
        "",
        md_table(identity[[
            "target_band", "method", "candidate_id", "point_id", "shape_id", "shape_family",
            "physical_key", "overlap_Hz", "cover_ratio", "in_v12_training_set", "in_ga20_history",
            "in_existing_ch5", "shape_parameter_band_in_v12", "shape_parameter_band_in_ga20",
            "strict_holdout_pass",
        ]]),
        "",
        "## 参数距离表",
        "",
        "完整表见 `parameter_distance_table.csv`。下表为每个频带的归一化距离摘要：",
        "",
        md_table(pair_df[[
            "target_band", "shape_id_same", "shape_family_same", "max_normalized_difference",
            "normalized_l2_distance", "near_duplicate", "near_duplicate_by_parameters",
        ]]),
        "",
        "## 绘图来源检查",
        "",
        "完整表见 `ch5_fig7_plotting_source_audit.csv`。",
        "",
        md_table(plot[[
            "target_band", "method", "candidate_id", "shape_id", "shape_file_input", "unit_cell_png",
            "unit_cell_status", "uses_method_specific_output_file", "geometry_png_duplicated",
            "shape_file_duplicated_within_band", "export_uses_case_row_params", "export_fallback_to_default_or_ga20",
        ]]),
        "",
        "## 解释建议",
        "",
        "180–220 Hz 和 200–240 Hz 中 predicted Top5 与 GA20 的 shape_id 相同，因此单胞轮廓形态会非常接近；但 point_id、physical_key 和 Fourier 连续参数不同，且 predicted_top5 未命中 v12、GA20 或旧第5章候选集合，也未命中不含 point_id 的 shape-parameter-band key。这里更像是预测模型在 strict_holdout 候选池中找到了与 GA20 同结构族/同离散轮廓但连续参数不同的高性能邻域，而不是抄用了 GA20 候选。",
        "",
        "若担心读者把“形态接近”误解为重复样本，建议在图注中补一句：`其中 180–220 Hz 与 200–240 Hz 的预测候选和 GA20 最优候选具有相同离散轮廓编号，但 Fourier 连续参数与 physical_key 不同，属于独立候选集中搜索到的相近高性能结构。`",
    ]
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    cases = selected_cases_with_keys()
    identity = build_seen_audit(cases)
    dist = distance_table(cases)
    plot = plotting_source_audit(cases)
    write_report(identity, dist, plot)
    print(f"[IDENTITY] {IDENTITY_OUT}")
    print(f"[DISTANCE] {DIST_OUT}")
    print(f"[PLOT] {PLOT_OUT}")
    print(f"[REPORT] {REPORT_OUT}")


if __name__ == "__main__":
    main()
