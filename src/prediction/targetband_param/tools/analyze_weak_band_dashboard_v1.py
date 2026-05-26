from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
WEAK_BANDS = ["band180_220", "band200_240", "band220_260", "band240_280"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_topk_per_band(cls_df: pd.DataFrame, reg_df: pd.DataFrame, ks: list[int]) -> pd.DataFrame:
    cls = cls_df.rename(columns={"y_true": "cls_true", "y_prob": "cls_prob"})
    reg = reg_df.rename(columns={"y_true": "reg_true", "y_pred": "reg_pred"})
    merged = cls.merge(
        reg[
            [
                "fold",
                "param_sample_id",
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
            "target_band_tag",
            "target_band_low_Hz",
            "target_band_high_Hz",
        ],
        how="inner",
    )
    merged["shortlist_score"] = merged["cls_prob"] * merged["reg_pred"].clip(lower=0)

    rows = []
    for band_tag, part in merged.groupby("target_band_tag", observed=True):
        part = part.sort_values(["shortlist_score", "cls_prob", "reg_pred"], ascending=False).reset_index(drop=True)
        random_cover = float(part["reg_true"].mean())
        random_positive_rate = float(part["cls_true"].mean())
        for k in ks:
            top = part.head(min(k, len(part)))
            rows.append(
                {
                    "target_band_tag": band_tag,
                    "k": int(k),
                    "rows_considered": int(len(top)),
                    "topk_hit_rate": float(top["cls_true"].mean()),
                    "topk_mean_cover": float(top["reg_true"].mean()),
                    "topk_mean_pred_cover": float(top["reg_pred"].mean()),
                    "topk_mean_prob": float(top["cls_prob"].mean()),
                    "random_positive_rate": random_positive_rate,
                    "random_mean_cover": random_cover,
                    "lift_hit_rate": float(top["cls_true"].mean() - random_positive_rate),
                    "lift_mean_cover": float(top["reg_true"].mean() - random_cover),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    out_dir = ROOT / "data" / "analysis" / "weak_band_dashboard_v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Coverage side
    coverage_path = ROOT / "data" / "analysis" / "targetband_band_coverage_v1" / "thesis_band_catalog_v2_after_exploratory_v2" / "band_coverage_summary_v1.csv"
    coverage = pd.read_csv(coverage_path)
    coverage = coverage[coverage["target_band_tag"].isin(WEAK_BANDS)].copy()
    coverage = coverage.rename(
        columns={
            "target_band_tag": "band_tag",
            "positive_rows": "coverage_positive_rows",
            "positive_families": "coverage_positive_families",
            "cover_ratio_mean_positive": "coverage_mean_positive_cover_ratio",
            "supplement_deficiency_score": "coverage_deficiency_score",
        }
    )

    # Shortlist side
    cls_family = pd.read_csv(ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cls_rf_dense_v8_cmp_v1" / "stratified_group_kfold" / "predictions.csv")
    reg_family = pd.read_csv(ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cover_hgb_dense_v8_cmp_v1" / "stratified_group_kfold" / "predictions.csv")
    cls_lobo = pd.read_csv(ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cls_rf_dense_v8_cmp_v1" / "leave_one_band_tag_out" / "predictions.csv")
    reg_lobo = pd.read_csv(ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cover_hgb_dense_v8_cmp_v1" / "leave_one_band_tag_out" / "predictions.csv")

    cls_family = cls_family[cls_family["target_band_tag"].isin(WEAK_BANDS)].copy()
    reg_family = reg_family[reg_family["target_band_tag"].isin(WEAK_BANDS)].copy()
    cls_lobo = cls_lobo[cls_lobo["target_band_tag"].isin(WEAK_BANDS)].copy()
    reg_lobo = reg_lobo[reg_lobo["target_band_tag"].isin(WEAK_BANDS)].copy()

    topk_family = summarize_topk_per_band(cls_family, reg_family, ks=[5, 10, 20])
    topk_lobo = summarize_topk_per_band(cls_lobo, reg_lobo, ks=[5, 10, 20])
    topk_family["eval_mode"] = "family_cv"
    topk_lobo["eval_mode"] = "leave_one_band"
    topk_all = pd.concat([topk_family, topk_lobo], ignore_index=True)

    focus_topk = topk_all[topk_all["k"] == 20].copy()
    focus_topk = focus_topk.rename(columns={"target_band_tag": "band_tag"})

    # Inverse-design usefulness side
    ladder = pd.read_csv(ROOT / "data" / "analysis" / "targetband_baseline_ladder_v1" / "canonical_band_comparison_v1.csv")
    ladder = ladder[ladder["target_band_tag"].isin(WEAK_BANDS)].copy()

    mainline = ladder[ladder["line_id"] == "band_supplement_exploratory_v2"].copy()
    mainline = mainline.rename(
        columns={
            "target_band_tag": "band_tag",
            "real_open_rate": "mainline_real_open_rate",
            "best_overlap_Hz": "mainline_best_overlap_Hz",
            "best_cover_ratio": "mainline_best_cover_ratio",
            "best_shape_id": "mainline_best_shape_id",
            "family_diversity": "mainline_family_diversity",
            "budget_proxy": "mainline_budget_proxy",
        }
    )

    conservative = ladder[ladder["line_id"] == "band_supplement_ga_v1"].copy()
    conservative = conservative.rename(
        columns={
            "target_band_tag": "band_tag",
            "best_overlap_Hz": "conservative_best_overlap_Hz",
            "best_cover_ratio": "conservative_best_cover_ratio",
            "best_shape_id": "conservative_best_shape_id",
        }
    )

    catalog = ladder[ladder["line_id"] == "band_catalog_real_ga_v1"].copy()
    catalog = catalog.rename(
        columns={
            "target_band_tag": "band_tag",
            "best_overlap_Hz": "catalog_best_overlap_Hz",
            "best_cover_ratio": "catalog_best_cover_ratio",
            "best_shape_id": "catalog_best_shape_id",
        }
    )

    dashboard = coverage[
        [
            "band_tag",
            "target_band_low_Hz",
            "target_band_high_Hz",
            "coverage_positive_rows",
            "coverage_positive_families",
            "coverage_mean_positive_cover_ratio",
            "coverage_deficiency_score",
        ]
    ].merge(
        focus_topk[focus_topk["eval_mode"] == "family_cv"][
            ["band_tag", "topk_hit_rate", "topk_mean_cover", "lift_mean_cover", "topk_mean_prob", "topk_mean_pred_cover"]
        ].rename(
            columns={
                "topk_hit_rate": "family_cv_top20_hit_rate",
                "topk_mean_cover": "family_cv_top20_mean_cover",
                "lift_mean_cover": "family_cv_top20_cover_lift",
                "topk_mean_prob": "family_cv_top20_mean_prob",
                "topk_mean_pred_cover": "family_cv_top20_mean_pred_cover",
            }
        ),
        on="band_tag",
        how="left",
    ).merge(
        focus_topk[focus_topk["eval_mode"] == "leave_one_band"][
            ["band_tag", "topk_hit_rate", "topk_mean_cover", "lift_mean_cover", "topk_mean_prob", "topk_mean_pred_cover"]
        ].rename(
            columns={
                "topk_hit_rate": "lobo_top20_hit_rate",
                "topk_mean_cover": "lobo_top20_mean_cover",
                "lift_mean_cover": "lobo_top20_cover_lift",
                "topk_mean_prob": "lobo_top20_mean_prob",
                "topk_mean_pred_cover": "lobo_top20_mean_pred_cover",
            }
        ),
        on="band_tag",
        how="left",
    ).merge(
        mainline[
            [
                "band_tag",
                "mainline_real_open_rate",
                "mainline_best_overlap_Hz",
                "mainline_best_cover_ratio",
                "mainline_best_shape_id",
                "mainline_family_diversity",
                "mainline_budget_proxy",
            ]
        ],
        on="band_tag",
        how="left",
    ).merge(
        conservative[["band_tag", "conservative_best_overlap_Hz", "conservative_best_cover_ratio", "conservative_best_shape_id"]],
        on="band_tag",
        how="left",
    ).merge(
        catalog[["band_tag", "catalog_best_overlap_Hz", "catalog_best_cover_ratio", "catalog_best_shape_id"]],
        on="band_tag",
        how="left",
    )

    dashboard["delta_cover_vs_conservative"] = dashboard["mainline_best_cover_ratio"] - dashboard["conservative_best_cover_ratio"]
    dashboard["delta_overlap_vs_conservative"] = dashboard["mainline_best_overlap_Hz"] - dashboard["conservative_best_overlap_Hz"]
    dashboard["delta_cover_vs_catalog"] = dashboard["mainline_best_cover_ratio"] - dashboard["catalog_best_cover_ratio"]
    dashboard["delta_overlap_vs_catalog"] = dashboard["mainline_best_overlap_Hz"] - dashboard["catalog_best_overlap_Hz"]

    dashboard.to_csv(out_dir / "weak_band_dashboard_summary_v1.csv", index=False, encoding="utf-8-sig")
    topk_all.to_csv(out_dir / "weak_band_topk_diagnostics_v1.csv", index=False, encoding="utf-8-sig")

    rank = dashboard.sort_values(
        [
            "coverage_deficiency_score",
            "delta_cover_vs_conservative",
        ],
        ascending=[False, False],
    ).reset_index(drop=True)
    rank.insert(0, "tracking_priority_rank", range(1, len(rank) + 1))
    rank.to_csv(out_dir / "weak_band_tracking_priority_v1.csv", index=False, encoding="utf-8-sig")

    info = {
        "weak_bands": WEAK_BANDS,
        "definition": {
            "coverage_positive_rows": "Number of positive truth rows currently available for the band.",
            "coverage_positive_families": "Number of families with positive truth in the band.",
            "coverage_mean_positive_cover_ratio": "Mean cover ratio among positive truth rows.",
            "family_cv_top20_mean_cover": "Top-20 shortlist quality under family-CV.",
            "lobo_top20_mean_cover": "Top-20 shortlist quality under leave-one-band evaluation.",
            "mainline_best_cover_ratio": "Best real inverse-design result from exploratory v2.",
            "delta_cover_vs_conservative": "Mainline cover advantage over conservative supplement baseline.",
            "delta_cover_vs_catalog": "Mainline cover advantage over old band-catalog real GA baseline."
        },
        "notes": [
            "This dashboard is the standing weak-band tracking panel for the frozen target-band mainline.",
            "The local predictor-guided GA validation line is only directly validated on band180_220, so it is not part of the unified weak-band dashboard table.",
            "Weak-band progress should be read jointly from coverage, shortlist quality, and final inverse-design usefulness."
        ],
    }
    (out_dir / "weak_band_dashboard_info_v1.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
