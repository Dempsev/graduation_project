from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RESULTS_CSV = (
    ROOT / "data" / "comsol_batch" / "stage4_validation_canonical_targetband_direct_scan_v1" / "stage4_validation_results.csv"
)
DEFAULT_MANIFEST_CSV = (
    ROOT / "data" / "ml_runs" / "canonical_targetband_direct_scan_v1" / "validation_manifest_v1" / "canonical_targetband_direct_scan_manifest_v1.csv"
)
DEFAULT_OUT_DIR = ROOT / "data" / "analysis" / "canonical_targetband_direct_scan_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze real-COMSOL direct scan results for a canonical target-band case.")
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS_CSV)
    parser.add_argument("--manifest-csv", type=Path, default=DEFAULT_MANIFEST_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df.get(col), errors="coerce")


def compute_target_overlap(lower: pd.Series, upper: pd.Series, band_low: pd.Series, band_high: pd.Series) -> pd.Series:
    return (pd.concat([upper, band_high], axis=1).min(axis=1) - pd.concat([lower, band_low], axis=1).max(axis=1)).clip(lower=0.0)


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
                "canonical_case_id",
                "canonical_variant",
                "target_band_tag",
                "target_band_low_Hz",
                "target_band_high_Hz",
                "preferred_direction",
                "delta_a1",
                "delta_a2",
                "delta_b2",
                "delta_r0",
            ]
        ],
        on="validation_id",
        how="left",
        suffixes=("", "_manifest"),
    )

    lower = numeric_series(merged, "gap34_lower_edge_Hz")
    upper = numeric_series(merged, "gap34_upper_edge_Hz")
    band_low = numeric_series(merged, "target_band_low_Hz")
    band_high = numeric_series(merged, "target_band_high_Hz")
    merged["target_overlap_Hz_actual"] = compute_target_overlap(lower, upper, band_low, band_high)
    merged["target_cover_ratio_actual"] = merged["target_overlap_Hz_actual"] / (band_high - band_low).clip(lower=1e-12)
    merged["target_edge_mismatch_Hz"] = (lower - band_low).abs() + (upper - band_high).abs()
    merged["multiobjective_rank_score"] = (
        0.55 * numeric_series(merged, "target_cover_ratio_actual").fillna(0.0)
        + 0.20 * (1.0 - (numeric_series(merged, "target_edge_mismatch_Hz").fillna(999.0) / 80.0).clip(lower=0.0, upper=1.0))
        + 0.15 * (numeric_series(merged, "gap34_gain_Hz").fillna(0.0) / 20.0).clip(lower=0.0, upper=1.0)
        + 0.10 * (1.0 - (numeric_series(merged, "delta_r0").abs().fillna(0.0) / 0.0008).clip(lower=0.0, upper=1.0))
    )
    ranked = merged.sort_values(
        ["target_cover_ratio_actual", "target_overlap_Hz_actual", "multiobjective_rank_score", "gap34_gain_Hz"],
        ascending=[False, False, False, False],
    ).copy()

    merged.to_csv(out_dir / "canonical_targetband_direct_scan_merged_v1.csv", index=False, encoding="utf-8-sig")
    ranked.to_csv(out_dir / "canonical_targetband_direct_scan_ranked_v1.csv", index=False, encoding="utf-8-sig")

    top = ranked.iloc[0].to_dict() if not ranked.empty else {}
    summary: Dict[str, object] = {
        "results_csv": str(results_csv),
        "manifest_csv": str(manifest_csv),
        "rows": int(len(ranked)),
        "best_validation_id": str(top.get("validation_id", "")),
        "best_variant": str(top.get("canonical_variant", "")),
        "best_target_cover_ratio_actual": float(top.get("target_cover_ratio_actual", 0.0) or 0.0),
        "best_target_overlap_Hz_actual": float(top.get("target_overlap_Hz_actual", 0.0) or 0.0),
        "best_gap34_gain_Hz": float(top.get("gap34_gain_Hz", 0.0) or 0.0),
        "best_multiobjective_rank_score": float(top.get("multiobjective_rank_score", 0.0) or 0.0),
    }
    (out_dir / "canonical_targetband_direct_scan_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] canonical target-band direct scan analysis complete")
    print(f"[OUT] {out_dir}")
    if top:
        print(
            "[BEST] {vid} variant={variant} cover={cover:.4f} overlap={overlap:.4f} gain={gain:.4f}".format(
                vid=top.get("validation_id", ""),
                variant=top.get("canonical_variant", ""),
                cover=float(top.get("target_cover_ratio_actual", 0.0) or 0.0),
                overlap=float(top.get("target_overlap_Hz_actual", 0.0) or 0.0),
                gain=float(top.get("gap34_gain_Hz", 0.0) or 0.0),
            )
        )


if __name__ == "__main__":
    main()
