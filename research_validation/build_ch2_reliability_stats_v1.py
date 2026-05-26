"""Build Chapter 2 reliability statistics from existing COAD batch outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "research_validation" / "ch2_mesh_reliability_v1"


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes"})


def load_history_frames() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in sorted((ROOT / "data" / "comsol_batch").glob("comsol_in_loop_thesis_*_overlap_ga_v1/ga_history_v1.csv")):
        try:
            frame = pd.read_csv(path)
        except Exception:
            continue
        if frame.empty:
            continue
        frame["source_csv"] = str(path)
        frame["source_run"] = path.parent.name
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False)
    for col in ["geometry_valid", "contact_valid", "has_tiny_fragments", "solve_success"]:
        if col in df.columns:
            df[col] = as_bool(df[col])
        else:
            df[col] = False
    if "error_message" not in df.columns:
        df["error_message"] = ""
    df["error_message"] = df["error_message"].fillna("").astype(str)
    return df


def classify_failures(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    if total == 0:
        return pd.DataFrame(columns=["check_item", "failure_count", "ratio_percent", "handling"])

    geometry_invalid = (~df["geometry_valid"]).sum()
    contact_invalid = (df["geometry_valid"] & ~df["contact_valid"]).sum()
    solve_failed = (df["geometry_valid"] & df["contact_valid"] & ~df["solve_success"]).sum()
    success = (df["geometry_valid"] & df["contact_valid"] & df["solve_success"]).sum()

    error_text = df["error_message"].str.lower()
    mesh_failed = (
        df["geometry_valid"]
        & df["contact_valid"]
        & ~df["solve_success"]
        & error_text.str.contains("mesh|网格", regex=True)
    ).sum()
    eig_failed = (
        df["geometry_valid"]
        & df["contact_valid"]
        & ~df["solve_success"]
        & error_text.str.contains("eig|eigen|conver|特征|收敛", regex=True)
    ).sum()
    result_incomplete = (
        df["geometry_valid"]
        & df["contact_valid"]
        & ~df["solve_success"]
        & error_text.str.contains("missingtbl1|tbl1|emptydata|result|结果", regex=True)
    ).sum()
    tiny_fragments = df.get("has_tiny_fragments", pd.Series(False, index=df.index)).sum()
    non_contact = error_text.str.contains("no_contact|contact", regex=True).sum()

    rows = [
        ("总候选样本", total, 100.0, "作为统计基数"),
        ("几何无效", geometry_invalid, geometry_invalid / total * 100, "剔除，不进入频散求解"),
        ("接触无效", contact_invalid, contact_invalid / total * 100, "剔除或记录为局部扰动未接触"),
        ("网格生成失败", mesh_failed, mesh_failed / total * 100, "记录失败原因，必要时调整几何或网格"),
        ("特征频率求解失败", eig_failed, eig_failed / total * 100, "记录为 solve_failed，不参与带隙统计"),
        ("结果不完整", result_incomplete, result_incomplete / total * 100, "缺失 tbl1 或频率表为空时剔除"),
        ("其他求解失败", max(int(solve_failed - mesh_failed - eig_failed - result_incomplete), 0), max(int(solve_failed - mesh_failed - eig_failed - result_incomplete), 0) / total * 100, "保留 error_message 供追溯"),
        ("成功求解", success, success / total * 100, "进入带隙、覆盖率和优化统计"),
        ("碎片域记录", tiny_fragments, tiny_fragments / total * 100, "作为几何异常子类追踪"),
        ("局部扰动未接触记录", non_contact, non_contact / total * 100, "作为接触异常子类追踪"),
    ]
    return pd.DataFrame(rows, columns=["check_item", "failure_count", "ratio_percent", "handling"])


def build_error_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["error_message", "count"])
    failed = df[df["error_message"].str.len() > 0].copy()
    if failed.empty:
        return pd.DataFrame(columns=["error_message", "count"])
    return (
        failed.groupby("error_message", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "error_message"], ascending=[False, True])
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_history_frames()
    stats = classify_failures(df)
    breakdown = build_error_breakdown(df)

    raw_csv = OUT_DIR / "reliability_raw_history_rows_v1.csv"
    stats_csv = OUT_DIR / "batch_reliability_stats_v1.csv"
    breakdown_csv = OUT_DIR / "batch_failure_reason_breakdown_v1.csv"
    summary_json = OUT_DIR / "batch_reliability_summary_v1.json"

    df.to_csv(raw_csv, index=False, encoding="utf-8-sig")
    stats.to_csv(stats_csv, index=False, encoding="utf-8-sig")
    breakdown.to_csv(breakdown_csv, index=False, encoding="utf-8-sig")

    payload = {
        "raw_history_rows_csv": str(raw_csv),
        "stats_csv": str(stats_csv),
        "failure_reason_breakdown_csv": str(breakdown_csv),
        "source_runs": sorted(df["source_run"].dropna().unique().tolist()) if not df.empty else [],
        "total_rows": int(len(df)),
    }
    summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
