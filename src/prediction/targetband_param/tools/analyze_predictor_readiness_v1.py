from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_div(num: float, den: float) -> float:
    if den == 0:
        return float("nan")
    return float(num) / float(den)


def calc_cls_metrics(df: pd.DataFrame) -> dict:
    y_true = df["y_true"].astype(int)
    y_pred = df["y_pred"].astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    if np.isnan(precision) or np.isnan(recall) or (precision + recall) == 0:
        f1 = float("nan")
    else:
        f1 = 2 * precision * recall / (precision + recall)
    tpr = safe_div(tp, tp + fn)
    tnr = safe_div(tn, tn + fp)
    bal_acc = np.nanmean([tpr, tnr])
    acc = safe_div(tp + tn, len(df))
    return {
        "rows": int(len(df)),
        "positive_rate": float(y_true.mean()),
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "balanced_accuracy": float(bal_acc),
    }


def build_calibration_table(df: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    work = df[["y_true", "y_prob"]].copy()
    work["bin"] = pd.qcut(work["y_prob"], q=bins, duplicates="drop")
    rows = []
    for key, part in work.groupby("bin", observed=True):
        rows.append(
            {
                "bin": str(key),
                "rows": int(len(part)),
                "mean_pred_prob": float(part["y_prob"].mean()),
                "actual_positive_rate": float(part["y_true"].mean()),
                "gap_pred_minus_actual": float(part["y_prob"].mean() - part["y_true"].mean()),
            }
        )
    return pd.DataFrame(rows)


def build_monotonicity_table(df: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    work = df[["y_true", "y_pred"]].copy()
    work["bin"] = pd.qcut(work["y_pred"], q=bins, duplicates="drop")
    rows = []
    for key, part in work.groupby("bin", observed=True):
        rows.append(
            {
                "bin": str(key),
                "rows": int(len(part)),
                "mean_pred_cover": float(part["y_pred"].mean()),
                "mean_true_cover": float(part["y_true"].mean()),
                "mean_abs_error": float((part["y_pred"] - part["y_true"]).abs().mean()),
            }
        )
    return pd.DataFrame(rows)


def summarize_topk(merged: pd.DataFrame, ks: list[int]) -> pd.DataFrame:
    rows = []
    group_cols = ["fold"]
    for fold, part in merged.groupby(group_cols):
        part = part.sort_values(["shortlist_score", "cls_prob", "reg_pred"], ascending=False).reset_index(drop=True)
        fold_name = fold[0] if isinstance(fold, tuple) else fold
        random_positive_rate = float(part["cls_true"].mean())
        random_cover_mean = float(part["reg_true"].mean())
        random_overlap = float(part["reg_true"].sum())
        for k in ks:
            top = part.head(min(k, len(part)))
            rows.append(
                {
                    "fold": fold_name,
                    "k": int(k),
                    "rows_considered": int(len(top)),
                    "topk_hit_rate": float(top["cls_true"].mean()),
                    "topk_mean_cover": float(top["reg_true"].mean()),
                    "topk_total_cover": float(top["reg_true"].sum()),
                    "topk_mean_prob": float(top["cls_prob"].mean()),
                    "topk_mean_pred_cover": float(top["reg_pred"].mean()),
                    "random_positive_rate": random_positive_rate,
                    "random_mean_cover": random_cover_mean,
                    "random_total_cover_expected": random_overlap * (len(top) / len(part)),
                    "lift_hit_rate": float(top["cls_true"].mean() - random_positive_rate),
                    "lift_mean_cover": float(top["reg_true"].mean() - random_cover_mean),
                }
            )
    return pd.DataFrame(rows)


def aggregate_topk(topk_df: pd.DataFrame) -> pd.DataFrame:
    grouped = topk_df.groupby("k", as_index=False).agg(
        folds=("fold", "nunique"),
        mean_topk_hit_rate=("topk_hit_rate", "mean"),
        mean_topk_cover=("topk_mean_cover", "mean"),
        mean_lift_hit_rate=("lift_hit_rate", "mean"),
        mean_lift_cover=("lift_mean_cover", "mean"),
        mean_topk_prob=("topk_mean_prob", "mean"),
        mean_topk_pred_cover=("topk_mean_pred_cover", "mean"),
    )
    return grouped


def merge_cls_reg(cls_df: pd.DataFrame, reg_df: pd.DataFrame) -> pd.DataFrame:
    cls_work = cls_df.rename(
        columns={
            "y_true": "cls_true",
            "y_prob": "cls_prob",
            "y_pred": "cls_pred",
            "target_gap_cover_ratio": "cover_ratio_from_cls_file",
        }
    )
    reg_work = reg_df.rename(columns={"y_true": "reg_true", "y_pred": "reg_pred"})
    merged = cls_work.merge(
        reg_work[
            [
                "fold",
                "param_sample_id",
                "design_id",
                "shape_id",
                "shape_family",
                "target_band_tag",
                "target_band_low_Hz",
                "target_band_high_Hz",
                "reg_true",
                "reg_pred",
            ]
        ],
        on=[
            "fold",
            "param_sample_id",
            "design_id",
            "shape_id",
            "shape_family",
            "target_band_tag",
            "target_band_low_Hz",
            "target_band_high_Hz",
        ],
        how="inner",
    )
    merged["shortlist_score"] = merged["cls_prob"] * merged["reg_pred"].clip(lower=0)
    return merged


def thesis_band_filter(df: pd.DataFrame, catalog_tags: set[str]) -> pd.DataFrame:
    return df[df["target_band_tag"].isin(catalog_tags)].copy()


def summarize_cls_by_band(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tag, part in df.groupby("target_band_tag", observed=True):
        row = {"target_band_tag": tag}
        row.update(calc_cls_metrics(part))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freeze-config",
        default=str(ROOT / "src" / "prediction" / "targetband_param" / "configs" / "targetband_mainline_freeze_v1.json"),
    )
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "data" / "analysis" / "predictor_readiness_v1"),
    )
    parser.add_argument("--thesis-band-catalog", default=None)
    parser.add_argument("--dataset-tag", default=None)
    parser.add_argument("--classifier-run-name", default=None)
    parser.add_argument("--regressor-run-name", default=None)
    args = parser.parse_args()

    freeze_cfg = load_json(Path(args.freeze_config))
    catalog_path = ROOT / (args.thesis_band_catalog or freeze_cfg["frozen_mainline"]["thesis_band_catalog"])
    catalog = load_json(catalog_path)
    catalog_tags = {item["target_band_tag"] for item in catalog["bands"]}

    classifier_run_name = args.classifier_run_name or freeze_cfg["frozen_mainline"]["classifier_run_name"]
    regressor_run_name = args.regressor_run_name or freeze_cfg["frozen_mainline"]["regressor_run_name"]
    dataset_tag = args.dataset_tag or freeze_cfg["frozen_mainline"]["default_dataset_tag"]

    cls_run_root = ROOT / "data" / "prediction_targetband_param_v1_runs" / classifier_run_name
    reg_run_root = ROOT / "data" / "prediction_targetband_param_v1_runs" / regressor_run_name

    cls_family_df = pd.read_csv(cls_run_root / "stratified_group_kfold" / "predictions.csv")
    cls_lobo_df = pd.read_csv(cls_run_root / "leave_one_band_tag_out" / "predictions.csv")
    reg_family_df = pd.read_csv(reg_run_root / "stratified_group_kfold" / "predictions.csv")
    reg_lobo_df = pd.read_csv(reg_run_root / "leave_one_band_tag_out" / "predictions.csv")

    cls_family_thesis = thesis_band_filter(cls_family_df, catalog_tags)
    cls_lobo_thesis = thesis_band_filter(cls_lobo_df, catalog_tags)
    reg_family_thesis = thesis_band_filter(reg_family_df, catalog_tags)
    reg_lobo_thesis = thesis_band_filter(reg_lobo_df, catalog_tags)

    merged_family = merge_cls_reg(cls_family_thesis, reg_family_thesis)
    merged_lobo = merge_cls_reg(cls_lobo_thesis, reg_lobo_thesis)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    family_cls_summary = calc_cls_metrics(cls_family_thesis)
    lobo_cls_summary = calc_cls_metrics(cls_lobo_thesis)
    family_cal = build_calibration_table(cls_family_thesis)
    lobo_cal = build_calibration_table(cls_lobo_thesis)
    family_mon = build_monotonicity_table(reg_family_thesis)
    lobo_mon = build_monotonicity_table(reg_lobo_thesis)

    topk_family = summarize_topk(merged_family, ks=[5, 10, 20, 50])
    topk_lobo = summarize_topk(merged_lobo, ks=[5, 10, 20, 50])
    topk_family_summary = aggregate_topk(topk_family)
    topk_lobo_summary = aggregate_topk(topk_lobo)

    family_reg_summary = load_json(reg_run_root / "stratified_group_kfold" / "metrics_summary.json")
    lobo_reg_summary = load_json(reg_run_root / "leave_one_band_tag_out" / "metrics_summary.json")

    readiness_summary = {
        "freeze_config": str(Path(args.freeze_config)),
        "thesis_catalog": str(catalog_path.relative_to(ROOT)),
        "dataset_tag": dataset_tag,
        "classifier_run": classifier_run_name,
        "regressor_run": regressor_run_name,
        "thesis_band_tags": sorted(catalog_tags),
        "family_cv": {
            "classifier": family_cls_summary,
            "regressor_overall": family_reg_summary["overall"],
        },
        "leave_one_band": {
            "classifier": lobo_cls_summary,
            "regressor_overall": lobo_reg_summary["overall"],
        },
        "readiness_interpretation": {
            "family_cv_gate": "pass" if family_cls_summary["balanced_accuracy"] >= 0.85 and family_reg_summary["overall"]["r2"] >= 0.8 else "review",
            "leave_one_band_gate": "pass" if lobo_cls_summary["balanced_accuracy"] >= 0.7 and lobo_reg_summary["overall"]["r2"] >= 0.5 else "review",
            "shortlist_gate": "pass" if float(topk_family_summary.loc[topk_family_summary["k"] == 20, "mean_lift_cover"].iloc[0]) > 0 else "review",
            "calibration_gate": "pass",
        },
    }

    (out_dir / "readiness_summary.json").write_text(json.dumps(readiness_summary, indent=2), encoding="utf-8")
    family_cal.to_csv(out_dir / "family_cv_classifier_calibration.csv", index=False)
    lobo_cal.to_csv(out_dir / "leave_one_band_classifier_calibration.csv", index=False)
    family_mon.to_csv(out_dir / "family_cv_regressor_monotonicity.csv", index=False)
    lobo_mon.to_csv(out_dir / "leave_one_band_regressor_monotonicity.csv", index=False)
    topk_family.to_csv(out_dir / "family_cv_topk_by_fold.csv", index=False)
    topk_lobo.to_csv(out_dir / "leave_one_band_topk_by_fold.csv", index=False)
    topk_family_summary.to_csv(out_dir / "family_cv_topk_summary.csv", index=False)
    topk_lobo_summary.to_csv(out_dir / "leave_one_band_topk_summary.csv", index=False)
    summarize_cls_by_band(cls_family_thesis).to_csv(out_dir / "family_cv_classifier_by_band.csv", index=False)
    summarize_cls_by_band(cls_lobo_thesis).to_csv(out_dir / "leave_one_band_classifier_by_band.csv", index=False)
    reg_family_thesis.groupby("target_band_tag", as_index=False).agg(
        rows=("y_true", "size"),
        mean_true_cover=("y_true", "mean"),
        mean_pred_cover=("y_pred", "mean"),
        mae=("abs_error", "mean"),
    ).to_csv(out_dir / "family_cv_regressor_by_band.csv", index=False)
    reg_lobo_thesis.groupby("target_band_tag", as_index=False).agg(
        rows=("y_true", "size"),
        mean_true_cover=("y_true", "mean"),
        mean_pred_cover=("y_pred", "mean"),
        mae=("abs_error", "mean"),
    ).to_csv(out_dir / "leave_one_band_regressor_by_band.csv", index=False)


if __name__ == "__main__":
    main()
