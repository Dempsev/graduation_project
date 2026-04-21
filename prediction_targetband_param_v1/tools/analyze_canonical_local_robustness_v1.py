from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_CSV = ROOT / "data" / "ml_runs" / "canonical_inverse_design_local_robustness_v1" / "validation_manifest_v1" / "canonical_local_robustness_manifest_v1.csv"
RESULTS_CSV = ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_local_robustness_v1" / "stage4_validation_results.csv"
OUT_DIR = ROOT / "data" / "analysis" / "canonical_local_robustness_v1"


def overlap_and_cover(lower: float | None, upper: float | None, low: float, high: float) -> tuple[float, float]:
    if pd.isna(lower) or pd.isna(upper):
        return 0.0, 0.0
    overlap = max(0.0, min(float(upper), high) - max(float(lower), low))
    return overlap, overlap / (high - low)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(MANIFEST_CSV)
    results = pd.read_csv(RESULTS_CSV)

    merged = results.merge(
        manifest[
            [
                "validation_id",
                "canonical_case_id",
                "canonical_variant",
                "target_band_tag",
                "target_band_low_Hz",
                "target_band_high_Hz",
                "a1",
                "a2",
                "b2",
                "r0",
            ]
        ],
        on="validation_id",
        how="left",
    )

    overlaps = []
    covers = []
    for _, row in merged.iterrows():
        overlap, cover = overlap_and_cover(
            row.get("gap34_lower_edge_Hz"),
            row.get("gap34_upper_edge_Hz"),
            float(row["target_band_low_Hz"]),
            float(row["target_band_high_Hz"]),
        )
        overlaps.append(overlap)
        covers.append(cover)
    merged["target_overlap_Hz_actual"] = overlaps
    merged["target_cover_ratio_actual"] = covers

    merged.to_csv(OUT_DIR / "canonical_local_robustness_merged_v1.csv", index=False, encoding="utf-8-sig")

    case_rows = []
    variant_rows = []
    for case_id, sub in merged.groupby("canonical_case_id"):
        center = sub[sub["canonical_variant"] == "center"].copy()
        center_cover = float(center["target_cover_ratio_actual"].iloc[0]) if not center.empty else 0.0
        center_overlap = float(center["target_overlap_Hz_actual"].iloc[0]) if not center.empty else 0.0
        center_lower = float(center["gap34_lower_edge_Hz"].iloc[0]) if not center.empty else float("nan")
        center_upper = float(center["gap34_upper_edge_Hz"].iloc[0]) if not center.empty else float("nan")

        pert = sub[sub["canonical_variant"] != "center"].copy()
        if pert.empty:
            continue

        pert["cover_delta_vs_center"] = pert["target_cover_ratio_actual"] - center_cover
        pert["overlap_delta_vs_center_Hz"] = pert["target_overlap_Hz_actual"] - center_overlap
        pert["lower_edge_shift_Hz"] = pert["gap34_lower_edge_Hz"] - center_lower
        pert["upper_edge_shift_Hz"] = pert["gap34_upper_edge_Hz"] - center_upper
        pert["cover_ge_90pct_center"] = pert["target_cover_ratio_actual"] >= 0.9 * center_cover if center_cover > 0 else False
        pert["cover_ge_80pct_center"] = pert["target_cover_ratio_actual"] >= 0.8 * center_cover if center_cover > 0 else False

        variant_rows.append(pert)

        case_rows.append(
            {
                "canonical_case_id": case_id,
                "target_band_tag": str(sub["target_band_tag"].iloc[0]),
                "shape_id": str(sub["shape_id"].iloc[0]),
                "center_cover_ratio": center_cover,
                "center_overlap_Hz": center_overlap,
                "center_gap34_lower_edge_Hz": center_lower,
                "center_gap34_upper_edge_Hz": center_upper,
                "variant_count": int(len(pert)),
                "mean_variant_cover_ratio": float(pert["target_cover_ratio_actual"].mean()),
                "min_variant_cover_ratio": float(pert["target_cover_ratio_actual"].min()),
                "max_variant_cover_ratio": float(pert["target_cover_ratio_actual"].max()),
                "variants_ge_90pct_center": int(pert["cover_ge_90pct_center"].sum()),
                "variants_ge_80pct_center": int(pert["cover_ge_80pct_center"].sum()),
                "mean_abs_lower_edge_shift_Hz": float(pert["lower_edge_shift_Hz"].abs().mean()),
                "mean_abs_upper_edge_shift_Hz": float(pert["upper_edge_shift_Hz"].abs().mean()),
                "max_abs_lower_edge_shift_Hz": float(pert["lower_edge_shift_Hz"].abs().max()),
                "max_abs_upper_edge_shift_Hz": float(pert["upper_edge_shift_Hz"].abs().max()),
            }
        )

    case_df = pd.DataFrame(case_rows)
    case_df.to_csv(OUT_DIR / "canonical_local_robustness_case_summary_v1.csv", index=False, encoding="utf-8-sig")

    if variant_rows:
        pd.concat(variant_rows, ignore_index=True).to_csv(
            OUT_DIR / "canonical_local_robustness_variant_summary_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

    info = {
        "manifest_csv": str(MANIFEST_CSV),
        "results_csv": str(RESULTS_CSV),
        "notes": [
            "Center vs local perturbation robustness is evaluated per canonical case.",
            "Perturbation quality is summarized relative to the center candidate within the same target band.",
            "A robust local basin is indicated by high variant retention of target cover and small gap-edge drift.",
        ],
    }
    (OUT_DIR / "canonical_local_robustness_info_v1.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
