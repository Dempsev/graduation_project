from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]

WEAK_BANDS = ["band180_220", "band200_240", "band220_260", "band240_280"]
TOP_K = 20
RANDOM_REPEATS = 500
SEED = 20260421


def load_dataset() -> pd.DataFrame:
    path = (
        ROOT
        / "data"
        / "prediction_targetband_param_v1"
        / "v1"
        / "windows_dense_v8_truth_plus_exploratory_aug_v1"
        / "targetband_parametric_v1.csv"
    )
    df = pd.read_csv(path)
    return df[df["target_band_tag"].isin(WEAK_BANDS)].copy()


def load_predictions() -> pd.DataFrame:
    cls_path = (
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cls_rf_dense_v8_cmp_v1"
        / "stratified_group_kfold"
        / "predictions.csv"
    )
    reg_path = (
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cover_hgb_dense_v8_cmp_v1"
        / "stratified_group_kfold"
        / "predictions.csv"
    )
    cls = pd.read_csv(cls_path)
    reg = pd.read_csv(reg_path)
    reg = (
        reg[["param_sample_id", "target_band_tag", "y_pred"]]
        .rename(columns={"y_pred": "cover_pred"})
        .groupby(["param_sample_id", "target_band_tag"], as_index=False)
        .mean(numeric_only=True)
    )

    merged = cls.merge(
        reg,
        on=["param_sample_id", "target_band_tag"],
        how="left",
    )
    merged["y_prob"] = pd.to_numeric(merged["y_prob"], errors="coerce").fillna(0.0)
    merged["cover_pred"] = pd.to_numeric(merged["cover_pred"], errors="coerce").fillna(0.0).clip(lower=0.0)
    # For the direct shortlist-value experiment, the stable front-end is the classifier probability.
    merged["predictor_score"] = merged["y_prob"]
    return merged[
        [
            "param_sample_id",
            "design_id",
            "shape_id",
            "shape_family",
            "target_band_tag",
            "y_prob",
            "cover_pred",
            "predictor_score",
        ]
    ].copy()


def compute_generic_scores(df: pd.DataFrame) -> pd.DataFrame:
    thesis = df[df["target_band_tag"].isin(WEAK_BANDS)].copy()
    generic = (
        thesis.groupby("design_id", as_index=False)
        .agg(
            generic_mean_cover=("target_gap_cover_ratio", "mean"),
            generic_best_cover=("target_gap_cover_ratio", "max"),
            generic_positive_count=("target_gap_is_open", "sum"),
        )
    )
    return generic


def shortlist_metrics(sub: pd.DataFrame, shortlist_label: str, band_tag: str) -> dict:
    sub = sub.copy()
    return {
        "target_band_tag": band_tag,
        "shortlist_label": shortlist_label,
        "k": int(len(sub)),
        "mean_true_cover_ratio": float(sub["target_gap_cover_ratio"].mean()),
        "mean_true_overlap_Hz": float(sub["target_gap_overlap_Hz"].mean()),
        "open_hit_count": int((sub["target_gap_is_open"] > 0).sum()),
        "strong_hit_count": int((sub["target_gap_cover_ratio"] >= 0.5).sum()),
        "best_true_cover_ratio": float(sub["target_gap_cover_ratio"].max()),
        "best_true_overlap_Hz": float(sub["target_gap_overlap_Hz"].max()),
        "family_diversity": int(sub["shape_family"].nunique()),
    }


def random_baseline_metrics(pool: pd.DataFrame, band_tag: str, rng: np.random.Generator) -> tuple[dict, pd.DataFrame]:
    records = []
    for _ in range(RANDOM_REPEATS):
        pick = pool.sample(n=min(TOP_K, len(pool)), replace=False, random_state=int(rng.integers(0, 2**31 - 1)))
        records.append(shortlist_metrics(pick, "random20", band_tag))
    frame = pd.DataFrame(records)
    summary = {
        "target_band_tag": band_tag,
        "shortlist_label": "random20_mean",
        "k": TOP_K,
        "mean_true_cover_ratio": float(frame["mean_true_cover_ratio"].mean()),
        "mean_true_overlap_Hz": float(frame["mean_true_overlap_Hz"].mean()),
        "open_hit_count": float(frame["open_hit_count"].mean()),
        "strong_hit_count": float(frame["strong_hit_count"].mean()),
        "best_true_cover_ratio": float(frame["best_true_cover_ratio"].mean()),
        "best_true_overlap_Hz": float(frame["best_true_overlap_Hz"].mean()),
        "family_diversity": float(frame["family_diversity"].mean()),
        "std_mean_true_cover_ratio": float(frame["mean_true_cover_ratio"].std()),
        "std_mean_true_overlap_Hz": float(frame["mean_true_overlap_Hz"].std()),
        "std_open_hit_count": float(frame["open_hit_count"].std()),
        "std_strong_hit_count": float(frame["strong_hit_count"].std()),
    }
    return summary, frame


def main() -> None:
    out_dir = ROOT / "data" / "analysis" / "weak_band_shortlist_value_v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset()
    preds = load_predictions()
    generic = compute_generic_scores(dataset)

    merged = dataset.merge(
        preds,
        on=["param_sample_id", "design_id", "shape_id", "shape_family", "target_band_tag"],
        how="left",
    ).merge(generic, on="design_id", how="left")
    merged["predictor_score"] = pd.to_numeric(merged["predictor_score"], errors="coerce").fillna(0.0)
    merged["y_prob"] = pd.to_numeric(merged["y_prob"], errors="coerce").fillna(0.0)
    merged["cover_pred"] = pd.to_numeric(merged["cover_pred"], errors="coerce").fillna(0.0)

    rng = np.random.default_rng(SEED)
    summary_rows: list[dict] = []
    shortlist_rows: list[dict] = []
    random_frames: list[pd.DataFrame] = []

    for band_tag in WEAK_BANDS:
        pool = merged[merged["target_band_tag"] == band_tag].copy()
        pool = pool.sort_values(["design_id"]).reset_index(drop=True)

        predictor_top = pool.sort_values(
            ["predictor_score", "y_prob", "cover_pred"],
            ascending=False,
        ).head(TOP_K).copy()
        predictor_top["shortlist_label"] = "predictor_top20"

        generic_top = pool.sort_values(
            ["generic_mean_cover", "generic_best_cover", "generic_positive_count"],
            ascending=False,
        ).head(TOP_K).copy()
        generic_top["shortlist_label"] = "generic_unconditional_top20"

        rand_summary, rand_dist = random_baseline_metrics(pool, band_tag, rng)
        rand_dist["target_band_tag"] = band_tag

        summary_rows.append(shortlist_metrics(predictor_top, "predictor_top20", band_tag))
        summary_rows.append(shortlist_metrics(generic_top, "generic_unconditional_top20", band_tag))
        summary_rows.append(rand_summary)

        shortlist_rows.append(
            predictor_top[
                [
                    "target_band_tag",
                    "shortlist_label",
                    "design_id",
                    "shape_id",
                    "shape_family",
                    "predictor_score",
                    "y_prob",
                    "cover_pred",
                    "target_gap_cover_ratio",
                    "target_gap_overlap_Hz",
                ]
            ].copy()
        )
        shortlist_rows.append(
            generic_top[
                [
                    "target_band_tag",
                    "shortlist_label",
                    "design_id",
                    "shape_id",
                    "shape_family",
                    "generic_mean_cover",
                    "generic_best_cover",
                    "generic_positive_count",
                    "target_gap_cover_ratio",
                    "target_gap_overlap_Hz",
                ]
            ].copy()
        )
        random_frames.append(rand_dist)

    summary = pd.DataFrame(summary_rows)

    baseline = summary[summary["shortlist_label"] == "random20_mean"][
        ["target_band_tag", "mean_true_cover_ratio", "mean_true_overlap_Hz", "open_hit_count", "strong_hit_count"]
    ].rename(
        columns={
            "mean_true_cover_ratio": "random_mean_cover",
            "mean_true_overlap_Hz": "random_mean_overlap",
            "open_hit_count": "random_open_hits",
            "strong_hit_count": "random_strong_hits",
        }
    )

    enriched = summary.merge(baseline, on="target_band_tag", how="left")
    enriched["cover_lift_vs_random"] = enriched["mean_true_cover_ratio"] - enriched["random_mean_cover"]
    enriched["overlap_lift_vs_random"] = enriched["mean_true_overlap_Hz"] - enriched["random_mean_overlap"]
    enriched["open_hit_lift_vs_random"] = enriched["open_hit_count"] - enriched["random_open_hits"]
    enriched["strong_hit_lift_vs_random"] = enriched["strong_hit_count"] - enriched["random_strong_hits"]

    enriched.to_csv(out_dir / "weak_band_shortlist_summary_v1.csv", index=False, encoding="utf-8-sig")
    pd.concat(shortlist_rows, ignore_index=True).to_csv(
        out_dir / "weak_band_shortlist_candidates_v1.csv", index=False, encoding="utf-8-sig"
    )
    pd.concat(random_frames, ignore_index=True).to_csv(
        out_dir / "weak_band_random20_distribution_v1.csv", index=False, encoding="utf-8-sig"
    )

    info = {
        "weak_bands": WEAK_BANDS,
        "top_k": TOP_K,
        "random_repeats": RANDOM_REPEATS,
        "predictor_score_definition": "RF classifier probability only; this experiment isolates the shortlist-engine value of the predictor front-end.",
        "generic_baseline_definition": "Band-unconditional top20 ranked by each design's mean true cover across the tracked weak-band catalog.",
        "random_baseline_definition": "Mean over repeated random draws of 20 candidates from the same band-specific pool.",
    }
    (out_dir / "weak_band_shortlist_info_v1.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
