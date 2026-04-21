from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

TARGET_BANDS = {
    "band180_220": (180.0, 220.0),
    "band200_240": (200.0, 240.0),
    "band220_260": (220.0, 260.0),
    "band240_280": (240.0, 280.0),
}


def overlap_and_cover(lower: float | None, upper: float | None, low: float, high: float) -> tuple[float, float]:
    if lower is None or upper is None:
        return 0.0, 0.0
    if pd.isna(lower) or pd.isna(upper):
        return 0.0, 0.0
    overlap = max(0.0, min(float(upper), high) - max(float(lower), low))
    cover = overlap / (high - low)
    return overlap, cover


def generic_dataset_rows() -> list[dict]:
    path = ROOT / "data" / "prediction_targetband_param_v1" / "v1" / "windows_dense_v8_truth_plus_exploratory_aug_v1" / "targetband_parametric_v1.csv"
    df = pd.read_csv(path)
    rows = []
    for band_tag, (low, high) in TARGET_BANDS.items():
        sub = df[df["target_band_tag"] == band_tag].copy()
        rows.append(
            {
                "target_band_tag": band_tag,
                "line_id": "generic_dataset_prior_v8",
                "line_role": "generic/random-like unconditional baseline",
                "evidence_type": "truth-distribution prior",
                "evaluated_count": int(len(sub)),
                "solve_success_count": int(len(sub)),
                "open_count": int((sub["target_gap_cover_ratio"] > 0).sum()),
                "real_open_rate": float((sub["target_gap_cover_ratio"] > 0).mean()),
                "mean_overlap_Hz": float(sub["target_gap_overlap_Hz"].mean()) if "target_gap_overlap_Hz" in sub.columns else float((sub["target_gap_cover_ratio"] * (high - low)).mean()),
                "mean_cover_ratio": float(sub["target_gap_cover_ratio"].mean()),
                "best_overlap_Hz": float((sub["target_gap_cover_ratio"] * (high - low)).max()),
                "best_cover_ratio": float(sub["target_gap_cover_ratio"].max()),
                "best_shape_id": str(sub.sort_values("target_gap_cover_ratio", ascending=False).iloc[0]["shape_id"]),
                "family_diversity": int(sub.loc[sub["target_gap_cover_ratio"] > 0, "shape_family"].nunique()),
                "budget_proxy": int(len(sub)),
                "notes": "Reference prior from the current v8 truth distribution, not a dedicated real-search run.",
            }
        )
    return rows


def summary_csv_rows(path: Path, line_id: str, line_role: str, notes: str) -> list[dict]:
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        band_tag = str(r["band_tag"])
        rows.append(
            {
                "target_band_tag": band_tag,
                "line_id": line_id,
                "line_role": line_role,
                "evidence_type": "real-search summary",
                "evaluated_count": int(r["evaluated_count"]),
                "solve_success_count": int(r["evaluated_count"]),
                "open_count": int(r["open_count"]),
                "real_open_rate": float(r["open_count"]) / float(r["evaluated_count"]) if float(r["evaluated_count"]) > 0 else 0.0,
                "mean_overlap_Hz": None,
                "mean_cover_ratio": None,
                "best_overlap_Hz": float(r["best_overlap_Hz"]),
                "best_cover_ratio": float(r["best_cover_ratio"]),
                "best_shape_id": str(r["best_shape_id"]),
                "family_diversity": None,
                "budget_proxy": int(r["evaluated_count"]),
                "notes": notes,
            }
        )
    return rows


def validation_rows(path: Path, line_id: str, line_role: str, selection_label: str, band_tag: str) -> list[dict]:
    low, high = TARGET_BANDS[band_tag]
    df = pd.read_csv(path)
    valid = df[(df["solve_success"] == 1) & (df["geometry_valid"] == 1) & (df["contact_valid"] == 1)].copy()
    if selection_label:
        valid = valid[valid["selection_label"] == selection_label].copy()
    if valid.empty:
        return []
    overlaps = []
    covers = []
    for _, r in valid.iterrows():
        overlap, cover = overlap_and_cover(r["gap34_lower_edge_Hz"], r["gap34_upper_edge_Hz"], low, high)
        overlaps.append(overlap)
        covers.append(cover)
    valid["target_overlap_Hz"] = overlaps
    valid["target_cover_ratio"] = covers
    best = valid.sort_values(["target_cover_ratio", "target_overlap_Hz", "gap34_gain_Hz"], ascending=False).iloc[0]
    return [
        {
            "target_band_tag": band_tag,
            "line_id": line_id,
            "line_role": line_role,
            "evidence_type": "real-validation subset",
            "evaluated_count": int(len(df if not selection_label else df[df["selection_label"] == selection_label])),
            "solve_success_count": int(len(valid)),
            "open_count": int((valid["target_cover_ratio"] > 0).sum()),
            "real_open_rate": float((valid["target_cover_ratio"] > 0).mean()),
            "mean_overlap_Hz": float(valid["target_overlap_Hz"].mean()),
            "mean_cover_ratio": float(valid["target_cover_ratio"].mean()),
            "best_overlap_Hz": float(best["target_overlap_Hz"]),
            "best_cover_ratio": float(best["target_cover_ratio"]),
            "best_shape_id": str(best["shape_id"]),
            "family_diversity": int(valid.loc[valid["target_cover_ratio"] > 0, "shape_family"].nunique()),
            "budget_proxy": int(len(df if not selection_label else df[df["selection_label"] == selection_label])),
            "notes": f"Validated subset for {selection_label}" if selection_label else "Validated subset",
        }
    ]


def best_candidate_family_diversity(path: Path) -> dict[str, int]:
    df = pd.read_csv(path)
    family_counts = {}
    band_col = "band_tag" if "band_tag" in df.columns else "archive_band_tag" if "archive_band_tag" in df.columns else None
    if band_col is None:
        return family_counts
    for band_tag, part in df.groupby(band_col):
        family_counts[str(band_tag)] = int(part["shape_family"].nunique()) if "shape_family" in part.columns else int(part["best_shape_family"].nunique())
    return family_counts


def main() -> None:
    out_dir = ROOT / "data" / "analysis" / "targetband_baseline_ladder_v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    rows.extend(generic_dataset_rows())
    rows.extend(
        summary_csv_rows(
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_catalog_ga_v1" / "ga_band_catalog_summary_v1.csv",
            "band_catalog_real_ga_v1",
            "old band-catalog real GA baseline",
            "Old target-band real global-search baseline under the pre-shape-aware setup.",
        )
    )
    rows.extend(
        summary_csv_rows(
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_ga_v1" / "ga_band_catalog_summary_v1.csv",
            "band_supplement_ga_v1",
            "old conservative supplement baseline",
            "Weak-band-oriented but still conservative search box.",
        )
    )
    rows.extend(
        summary_csv_rows(
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_summary_v1.csv",
            "band_supplement_exploratory_v2",
            "predictor-guided / shape-aware / exploratory mainline",
            "Current strongest weak-band inverse-design line with band-aware shape pool and novelty avoidance.",
        )
    )
    rows.extend(
        validation_rows(
            ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_v1" / "stage4_validation_results.csv",
            "targetband_local_ga_v1_probe",
            "old predictor-guided local GA validation (probe)",
            "targetband_180_220_top_6_per_shape_2",
            "band180_220",
        )
    )
    rows.extend(
        validation_rows(
            ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_results.csv",
            "targetband_local_ga_v1_top6",
            "old predictor-guided local GA validation (top6)",
            "targetband_180_220_top_6_per_shape_1",
            "band180_220",
        )
    )

    frame = pd.DataFrame(rows)

    # Fill family diversity for real-search summaries from best-candidate exports when possible.
    fam_maps = {
        "band_catalog_real_ga_v1": best_candidate_family_diversity(
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_catalog_ga_v1" / "ga_band_catalog_best_candidates_v1.csv"
        ),
        "band_supplement_ga_v1": best_candidate_family_diversity(
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_ga_v1" / "ga_band_catalog_best_candidates_v1.csv"
        ),
        "band_supplement_exploratory_v2": best_candidate_family_diversity(
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_best_candidates_v1.csv"
        ),
    }
    for idx, row in frame.iterrows():
        if pd.isna(row["family_diversity"]) and row["line_id"] in fam_maps:
            frame.at[idx, "family_diversity"] = fam_maps[row["line_id"]].get(row["target_band_tag"])

    frame.to_csv(out_dir / "baseline_ladder_summary_v1.csv", index=False, encoding="utf-8-sig")

    canonical = frame[frame["target_band_tag"].isin(list(TARGET_BANDS.keys()))].copy()
    canonical.to_csv(out_dir / "canonical_band_comparison_v1.csv", index=False, encoding="utf-8-sig")

    summary = {
        "target_bands": list(TARGET_BANDS.keys()),
        "line_ids": sorted(frame["line_id"].unique().tolist()),
        "notes": [
            "Not every line is available for every band. The local GA validation line is currently only real-validated for band180_220.",
            "The generic dataset prior is a truth-distribution baseline rather than a dedicated random real-search run.",
            "Real-search lines report true search summaries; validation lines report actual validated subsets.",
        ],
    }
    (out_dir / "baseline_ladder_info_v1.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
