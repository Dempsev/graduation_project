"""Build Chapter 2.6 summary CSVs and README from COMSOL local perturbation results."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = ROOT / "research_validation" / "ch2_typical_dispersion"
DATA_DIR = ROOT / "data" / "research_validation" / "ch2_typical_dispersion"


def main() -> None:
    results_csv = DATA_DIR / "ch2_typical_local_perturb_results_v1.csv"
    if not results_csv.is_file():
        raise FileNotFoundError(results_csv)
    df = pd.read_csv(results_csv)
    for col in [
        "cover_ratio",
        "target_overlap_Hz",
        "band_lower_Hz",
        "band_upper_Hz",
        "gap34_Hz",
        "gap34_rel",
        "solve_success",
        "contact_valid",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    case_rows = []
    perturb_rows = []
    variant_order = ["a1_plus", "a1_minus", "a2_plus", "a2_minus", "b2_plus", "b2_minus", "r0_plus", "r0_minus"]
    for case_id, sub in df.groupby("case_id", sort=False):
        center = sub[sub["variant"] == "center"].iloc[0]
        variants = sub[sub["variant"] != "center"].copy()
        center_cover = float(center["cover_ratio"])
        center_lower = float(center["band_lower_Hz"])
        center_upper = float(center["band_upper_Hz"])
        target_band = f"{int(center['target_band_low_Hz'])}-{int(center['target_band_high_Hz'])}"
        case_rows.append(
            {
                "case_id": case_id,
                "target_band": target_band,
                "target_band_tag": center["target_band"],
                "structure_id": center["structure_id"],
                "center_cover_ratio": center_cover,
                "center_band_interval_Hz": f"{center_lower:.3f}-{center_upper:.3f}",
                "center_band_lower_Hz": center_lower,
                "center_band_upper_Hz": center_upper,
                "target_overlap_Hz": float(center["target_overlap_Hz"]),
                "gap34_Hz": float(center["gap34_Hz"]),
                "gap34_rel": float(center["gap34_rel"]),
                "note": "中心结构" if center_cover >= 0.5 else "目标频带覆盖较低，用于说明高频段覆盖困难",
            }
        )
        perturb_rows.append(
            {
                "case_id": case_id,
                "center_cover_ratio": center_cover,
                "mean_variant_cover_ratio": float(variants["cover_ratio"].mean()),
                "min_variant_cover_ratio": float(variants["cover_ratio"].min()),
                "variants_ge_90pct_center": int((variants["cover_ratio"] >= 0.9 * center_cover).sum()) if center_cover > 0 else 0,
                "variants_ge_80pct_center": int((variants["cover_ratio"] >= 0.8 * center_cover).sum()) if center_cover > 0 else 0,
                "mean_lower_edge_shift_Hz": float((variants["band_lower_Hz"] - center_lower).mean()),
                "mean_upper_edge_shift_Hz": float((variants["band_upper_Hz"] - center_upper).mean()),
                "mean_abs_lower_edge_shift_Hz": float((variants["band_lower_Hz"] - center_lower).abs().mean()),
                "mean_abs_upper_edge_shift_Hz": float((variants["band_upper_Hz"] - center_upper).abs().mean()),
                "variant_count": int(len(variants)),
                "success_variant_count": int((variants["solve_success"] == 1).sum()),
            }
        )

    case_df = pd.DataFrame(case_rows)
    robust_df = pd.DataFrame(perturb_rows)
    case_csv = DATA_DIR / "ch2_typical_dispersion_case_summary.csv"
    robust_csv = DATA_DIR / "ch2_local_robustness_stats.csv"
    variant_csv = DATA_DIR / "ch2_local_perturb_variant_results.csv"
    case_df.to_csv(case_csv, index=False, encoding="utf-8-sig")
    robust_df.to_csv(robust_csv, index=False, encoding="utf-8-sig")
    df.to_csv(variant_csv, index=False, encoding="utf-8-sig")

    summary = {
        "case_summary_csv": str(case_csv),
        "robustness_stats_csv": str(robust_csv),
        "variant_results_csv": str(variant_csv),
        "variant_order": variant_order,
        "case_count": int(len(case_df)),
        "variant_count": int(len(df)),
        "success_count": int((df["solve_success"] == 1).sum()),
    }
    (DATA_DIR / "ch2_typical_dispersion_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    readme = f"""# Chapter 2.6 Typical Dispersion And Local Perturbation Analysis

This folder contains the reusable scripts for thesis section 2.6.

## Reproduction

1. Build current typical-case manifest:
   `D:\\python312\\python.exe research_validation/ch2_typical_dispersion/build_ch2_typical_center_manifest_v1.py`

2. Run COMSOL truth evaluations through a shared COMSOL MATLAB engine:
   `D:\\python312\\python.exe research_validation/ch2_typical_dispersion/run_ch2_typical_local_perturb_via_engine_v1.py --start 1 --max-count 0`

3. Build summary tables:
   `D:\\python312\\python.exe research_validation/ch2_typical_dispersion/build_ch2_typical_stats_v1.py`

4. Export figures:
   `D:\\python312\\python.exe research_validation/ch2_typical_dispersion/export_ch2_typical_figures_via_engine_v1.py`

## Outputs

- Case summary: `{case_csv}`
- Robustness statistics: `{robust_csv}`
- Variant results: `{variant_csv}`
- Raw COMSOL tbl1 exports: `{DATA_DIR / 'tbl1_exports'}`

The local perturbation plan reuses the old thesis setup: a1 +/- 0.01,
a2 +/- 0.01, b2 +/- 0.01, and r0 +/- 0.0008.
"""
    (WORK_DIR / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
