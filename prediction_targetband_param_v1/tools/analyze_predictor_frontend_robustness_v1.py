from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

WEAK_BANDS = ["band180_220", "band200_240", "band220_260", "band240_280"]
THRESHOLDS = [0.3, 0.4, 0.5, 0.6, 0.7]
TOP_K = 20
PERTURB_SIGMA = 0.02
PERTURB_REPEATS = 500
SEED = 20260421


def load_classifier_predictions(split: str) -> pd.DataFrame:
    path = (
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cls_rf_dense_v8_cmp_v1"
        / split
        / "predictions.csv"
    )
    df = pd.read_csv(path)
    df = df[df["target_band_tag"].isin(WEAK_BANDS)].copy()
    df["y_prob"] = pd.to_numeric(df["y_prob"], errors="coerce").fillna(0.0)
    df["target_gap_cover_ratio"] = pd.to_numeric(df["target_gap_cover_ratio"], errors="coerce").fillna(0.0)
    df["target_gap_overlap_Hz"] = df["target_gap_cover_ratio"] * 40.0
    return df


def stable_sort(df: pd.DataFrame, score_col: str) -> pd.DataFrame:
    return df.sort_values(
        [score_col, "target_gap_cover_ratio", "design_id"],
        ascending=[False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def shortlist(df: pd.DataFrame, score_col: str = "y_prob", threshold: float | None = None, top_k: int = TOP_K) -> pd.DataFrame:
    work = df.copy()
    if threshold is not None:
        work = work[work[score_col] >= threshold].copy()
    work = stable_sort(work, score_col)
    return work.head(min(top_k, len(work))).copy()


def shortlist_metrics(sub: pd.DataFrame, band_tag: str, label: str, threshold: float | None = None) -> dict:
    return {
        "target_band_tag": band_tag,
        "label": label,
        "threshold": threshold,
        "pool_count": int(len(sub)) if label == "eligible_pool" else None,
        "shortlist_count": int(len(sub)),
        "mean_true_cover_ratio": float(sub["target_gap_cover_ratio"].mean()) if not sub.empty else 0.0,
        "mean_true_overlap_Hz": float(sub["target_gap_overlap_Hz"].mean()) if not sub.empty else 0.0,
        "open_hit_count": int((sub["target_gap_cover_ratio"] > 0).sum()) if not sub.empty else 0,
        "strong_hit_count": int((sub["target_gap_cover_ratio"] >= 0.5).sum()) if not sub.empty else 0,
        "best_true_cover_ratio": float(sub["target_gap_cover_ratio"].max()) if not sub.empty else 0.0,
        "best_true_overlap_Hz": float(sub["target_gap_overlap_Hz"].max()) if not sub.empty else 0.0,
        "family_diversity": int(sub["shape_family"].nunique()) if not sub.empty else 0,
    }


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def threshold_sensitivity_rows(df: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    summary_rows: list[dict] = []
    pair_rows: list[dict] = []
    for band_tag in WEAK_BANDS:
        band = df[df["target_band_tag"] == band_tag].copy()
        threshold_shortlists: dict[float, pd.DataFrame] = {}
        for thr in THRESHOLDS:
            eligible = band[band["y_prob"] >= thr].copy()
            shortlisted = shortlist(band, threshold=thr)
            row = shortlist_metrics(shortlisted, band_tag, "threshold_shortlist", threshold=thr)
            row["eligible_pool_count"] = int(len(eligible))
            summary_rows.append(row)
            threshold_shortlists[thr] = shortlisted
        for a, b in combinations(THRESHOLDS, 2):
            sa = threshold_shortlists[a]
            sb = threshold_shortlists[b]
            design_a = set(sa["design_id"].tolist())
            design_b = set(sb["design_id"].tolist())
            family_a = set(sa["shape_family"].tolist())
            family_b = set(sb["shape_family"].tolist())
            pair_rows.append(
                {
                    "target_band_tag": band_tag,
                    "threshold_a": a,
                    "threshold_b": b,
                    "design_overlap_count": int(len(design_a & design_b)),
                    "design_jaccard": float(jaccard(design_a, design_b)),
                    "family_overlap_count": int(len(family_a & family_b)),
                    "family_jaccard": float(jaccard(family_a, family_b)),
                }
            )
    return summary_rows, pair_rows


def ranking_stability_rows(family_df: pd.DataFrame, loo_df: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    compare_rows: list[dict] = []
    perturb_rows: list[dict] = []
    rng = np.random.default_rng(SEED)

    for band_tag in WEAK_BANDS:
        fam_band = family_df[family_df["target_band_tag"] == band_tag].copy()
        loo_band = loo_df[loo_df["target_band_tag"] == band_tag].copy()

        fam_top = shortlist(fam_band)
        loo_top = shortlist(loo_band)

        fam_design = set(fam_top["design_id"].tolist())
        loo_design = set(loo_top["design_id"].tolist())
        fam_family = set(fam_top["shape_family"].tolist())
        loo_family = set(loo_top["shape_family"].tolist())

        compare_rows.append(
            {
                "target_band_tag": band_tag,
                "comparison": "family_cv_vs_leave_one_band",
                "design_overlap_count": int(len(fam_design & loo_design)),
                "design_jaccard": float(jaccard(fam_design, loo_design)),
                "family_overlap_count": int(len(fam_family & loo_family)),
                "family_jaccard": float(jaccard(fam_family, loo_family)),
                "family_cv_mean_cover": float(fam_top["target_gap_cover_ratio"].mean()),
                "leave_one_band_mean_cover": float(loo_top["target_gap_cover_ratio"].mean()),
            }
        )

        base_top = fam_top.copy()
        base_design = set(base_top["design_id"].tolist())
        base_family = set(base_top["shape_family"].tolist())
        design_retention: dict[str, int] = {d: 0 for d in base_design}
        family_retention: dict[str, int] = {f: 0 for f in base_family}
        design_jaccards: list[float] = []
        family_jaccards: list[float] = []

        for _ in range(PERTURB_REPEATS):
            pert = fam_band.copy()
            pert["_score"] = (pert["y_prob"] + rng.normal(0.0, PERTURB_SIGMA, size=len(pert))).clip(0.0, 1.0)
            pert_top = shortlist(pert, score_col="_score")
            pert_design = set(pert_top["design_id"].tolist())
            pert_family = set(pert_top["shape_family"].tolist())
            design_jaccards.append(jaccard(base_design, pert_design))
            family_jaccards.append(jaccard(base_family, pert_family))
            for d in base_design & pert_design:
                design_retention[d] += 1
            for f in base_family & pert_family:
                family_retention[f] += 1

        perturb_rows.append(
            {
                "target_band_tag": band_tag,
                "comparison": "family_cv_vs_small_score_perturbation",
                "sigma": PERTURB_SIGMA,
                "repeats": PERTURB_REPEATS,
                "mean_design_jaccard": float(np.mean(design_jaccards)),
                "mean_family_jaccard": float(np.mean(family_jaccards)),
                "min_design_jaccard": float(np.min(design_jaccards)),
                "min_family_jaccard": float(np.min(family_jaccards)),
                "core_design_count_ge_50pct": int(sum(v / PERTURB_REPEATS >= 0.5 for v in design_retention.values())),
                "core_family_count_ge_50pct": int(sum(v / PERTURB_REPEATS >= 0.5 for v in family_retention.values())),
            }
        )

    return compare_rows, perturb_rows


def main() -> None:
    out_dir = ROOT / "data" / "analysis" / "predictor_frontend_robustness_v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    family_df = load_classifier_predictions("stratified_group_kfold")
    loo_df = load_classifier_predictions("leave_one_band_tag_out")

    threshold_rows, threshold_pair_rows = threshold_sensitivity_rows(family_df)
    rank_compare_rows, rank_perturb_rows = ranking_stability_rows(family_df, loo_df)

    pd.DataFrame(threshold_rows).to_csv(
        out_dir / "threshold_sensitivity_summary_v1.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(threshold_pair_rows).to_csv(
        out_dir / "threshold_pairwise_stability_v1.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(rank_compare_rows).to_csv(
        out_dir / "ranking_cross_split_stability_v1.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(rank_perturb_rows).to_csv(
        out_dir / "ranking_perturbation_stability_v1.csv", index=False, encoding="utf-8-sig"
    )

    info = {
        "weak_bands": WEAK_BANDS,
        "thresholds": THRESHOLDS,
        "top_k": TOP_K,
        "perturb_sigma": PERTURB_SIGMA,
        "perturb_repeats": PERTURB_REPEATS,
        "notes": [
            "This robustness package evaluates the predictor front-end only.",
            "Threshold sensitivity is computed on family-CV classifier probabilities.",
            "Ranking stability is evaluated both across family-CV vs leave-one-band and under small score perturbations.",
        ],
    }
    (out_dir / "predictor_frontend_robustness_info_v1.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
