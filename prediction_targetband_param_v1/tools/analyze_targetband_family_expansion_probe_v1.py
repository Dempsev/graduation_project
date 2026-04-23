from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_CSV = (
    ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_family_expansion_probe_v1" / "stage4_validation_results.csv"
)
DEFAULT_MANIFEST_CSV = (
    ROOT / "data" / "ml_runs" / "targetband_family_expansion_probe_v1" / "validation_manifest_v1" / "targetband_family_expansion_probe_manifest_v1.csv"
)
DEFAULT_OUT_DIR = ROOT / "data" / "analysis" / "targetband_family_expansion_probe_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze weak-band family expansion probe results.")
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS_CSV)
    parser.add_argument("--manifest-csv", type=Path, default=DEFAULT_MANIFEST_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([pd.NA] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def compute_target_overlap(lower: pd.Series, upper: pd.Series, band_low: pd.Series, band_high: pd.Series) -> pd.Series:
    return (pd.concat([upper, band_high], axis=1).min(axis=1) - pd.concat([lower, band_low], axis=1).max(axis=1)).clip(lower=0.0)


def classify_role(cover: float, is_open: int) -> str:
    if int(is_open) > 0:
        if cover >= 0.50:
            return "target_band_strong"
        if cover >= 0.15:
            return "weak_band_contributor"
        return "near_miss"
    return "hard_negative"


def main() -> None:
    args = parse_args()
    results_csv = args.results_csv if args.results_csv.is_absolute() else ROOT / args.results_csv
    manifest_csv = args.manifest_csv if args.manifest_csv.is_absolute() else ROOT / args.manifest_csv
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not results_csv.exists():
        raise FileNotFoundError(results_csv)
    if not manifest_csv.exists():
        raise FileNotFoundError(manifest_csv)

    results = pd.read_csv(results_csv)
    manifest = pd.read_csv(manifest_csv)
    merged = results.merge(
        manifest[
            [
                "validation_id",
                "target_band_tag",
                "shape_family",
                "shape_id",
                "family_probe_variant",
                "preferred_direction",
                "seed_shape_role",
                "seed_base_cover_ratio",
                "seed_base_overlap_Hz",
                "delta_a1",
                "delta_a2",
                "delta_b2",
                "delta_r0",
                "target_band_low_Hz",
                "target_band_high_Hz",
            ]
        ],
        on="validation_id",
        how="left",
    )

    if "shape_family" not in merged.columns:
        if "shape_family_x" in merged.columns:
            merged["shape_family"] = merged["shape_family_x"]
        elif "shape_family_y" in merged.columns:
            merged["shape_family"] = merged["shape_family_y"]
    if "shape_id" not in merged.columns:
        if "shape_id_x" in merged.columns:
            merged["shape_id"] = merged["shape_id_x"]
        elif "shape_id_y" in merged.columns:
            merged["shape_id"] = merged["shape_id_y"]

    lower = numeric_series(merged, "gap34_lower_edge_Hz")
    upper = numeric_series(merged, "gap34_upper_edge_Hz")
    band_low = numeric_series(merged, "target_band_low_Hz")
    band_high = numeric_series(merged, "target_band_high_Hz")
    merged["target_overlap_Hz_actual"] = compute_target_overlap(lower, upper, band_low, band_high)
    merged["target_cover_ratio_actual"] = merged["target_overlap_Hz_actual"] / (band_high - band_low).clip(lower=1e-12)
    merged["target_edge_mismatch_Hz"] = (lower - band_low).abs() + (upper - band_high).abs()
    is_open_actual = (numeric_series(merged, "target_overlap_Hz_actual").fillna(0.0) > 0).astype(int)
    merged["actual_role"] = [
        classify_role(float(c or 0.0), int(o or 0))
        for c, o in zip(
            numeric_series(merged, "target_cover_ratio_actual").fillna(0.0),
            is_open_actual,
        )
    ]

    merged.to_csv(out_dir / "targetband_family_expansion_probe_merged_v1.csv", index=False, encoding="utf-8-sig")

    family_rows = []
    for (band_tag, family), subset in merged.groupby(["target_band_tag", "shape_family"], sort=True):
        subset = subset.sort_values(
            ["target_cover_ratio_actual", "target_overlap_Hz_actual", "gap34_gain_Hz"],
            ascending=[False, False, False],
        ).copy()
        base = subset[subset["family_probe_variant"] == "center"].iloc[0]
        best = subset.iloc[0]
        family_rows.append(
            {
                "target_band_tag": str(band_tag),
                "shape_family": str(family),
                "shape_id": str(best.get("shape_id", "")),
                "seed_shape_role": str(base.get("seed_shape_role", "")),
                "base_variant": str(base.get("family_probe_variant", "")),
                "base_cover_ratio_actual": float(base.get("target_cover_ratio_actual", 0.0) or 0.0),
                "base_overlap_Hz_actual": float(base.get("target_overlap_Hz_actual", 0.0) or 0.0),
                "base_actual_role": str(base.get("actual_role", "")),
                "best_validation_id": str(best.get("validation_id", "")),
                "best_variant": str(best.get("family_probe_variant", "")),
                "best_preferred_direction": str(best.get("preferred_direction", "")),
                "best_cover_ratio_actual": float(best.get("target_cover_ratio_actual", 0.0) or 0.0),
                "best_overlap_Hz_actual": float(best.get("target_overlap_Hz_actual", 0.0) or 0.0),
                "best_actual_role": str(best.get("actual_role", "")),
                "best_gap34_gain_Hz": float(best.get("gap34_gain_Hz", 0.0) or 0.0),
                "cover_gain_vs_base": float((best.get("target_cover_ratio_actual", 0.0) or 0.0) - (base.get("target_cover_ratio_actual", 0.0) or 0.0)),
                "overlap_gain_vs_base_Hz": float((best.get("target_overlap_Hz_actual", 0.0) or 0.0) - (base.get("target_overlap_Hz_actual", 0.0) or 0.0)),
                "promoted_to_weak_contributor": int((base.get("target_cover_ratio_actual", 0.0) or 0.0) < 0.15 and (best.get("target_cover_ratio_actual", 0.0) or 0.0) >= 0.15),
                "promoted_to_target_band_strong": int((base.get("target_cover_ratio_actual", 0.0) or 0.0) < 0.50 and (best.get("target_cover_ratio_actual", 0.0) or 0.0) >= 0.50),
            }
        )

    family_summary = pd.DataFrame(family_rows).sort_values(
        ["target_band_tag", "best_cover_ratio_actual", "cover_gain_vs_base", "shape_family"],
        ascending=[True, False, False, True],
    )
    family_summary.to_csv(out_dir / "targetband_family_expansion_probe_family_summary_v1.csv", index=False, encoding="utf-8-sig")

    band_summary = (
        family_summary.groupby("target_band_tag", as_index=False)
        .agg(
            family_count=("shape_family", "count"),
            promoted_to_weak_contributor=("promoted_to_weak_contributor", "sum"),
            promoted_to_target_band_strong=("promoted_to_target_band_strong", "sum"),
            best_cover_ratio_actual_max=("best_cover_ratio_actual", "max"),
            mean_cover_gain_vs_base=("cover_gain_vs_base", "mean"),
            mean_overlap_gain_vs_base_Hz=("overlap_gain_vs_base_Hz", "mean"),
        )
        .sort_values("target_band_tag")
    )
    band_summary.to_csv(out_dir / "targetband_family_expansion_probe_band_summary_v1.csv", index=False, encoding="utf-8-sig")

    top = family_summary.sort_values(
        ["promoted_to_target_band_strong", "promoted_to_weak_contributor", "best_cover_ratio_actual", "cover_gain_vs_base"],
        ascending=[False, False, False, False],
    ).iloc[0].to_dict() if not family_summary.empty else {}
    summary: Dict[str, object] = {
        "results_csv": str(results_csv),
        "manifest_csv": str(manifest_csv),
        "rows": int(len(merged)),
        "family_target_count": int(len(family_summary)),
        "promoted_to_weak_contributor": int(family_summary["promoted_to_weak_contributor"].sum()) if not family_summary.empty else 0,
        "promoted_to_target_band_strong": int(family_summary["promoted_to_target_band_strong"].sum()) if not family_summary.empty else 0,
        "top_family_target": top,
    }
    (out_dir / "targetband_family_expansion_probe_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] target-band family expansion probe analysis complete")
    print(f"[OUT] {out_dir}")
    if top:
        print(
            "[TOP] {band} {family} best={variant} cover={cover:.4f} gain={gain:.4f}".format(
                band=top.get("target_band_tag", ""),
                family=top.get("shape_family", ""),
                variant=top.get("best_variant", ""),
                cover=float(top.get("best_cover_ratio_actual", 0.0) or 0.0),
                gain=float(top.get("cover_gain_vs_base", 0.0) or 0.0),
            )
        )


if __name__ == "__main__":
    main()
