from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RESULTS_CSV = (
    ROOT / "data" / "comsol_batch" / "stage4_validation_shape_archetype_targetband_pilot_v1" / "stage4_validation_results.csv"
)
DEFAULT_MANIFEST_CSV = (
    ROOT / "data" / "ml_runs" / "shape_archetype_targetband_pilot_v1" / "validation_manifest_v1" / "shape_archetype_targetband_pilot_manifest_v1.csv"
)
DEFAULT_TBL1_DIR = (
    ROOT / "data" / "comsol_batch" / "stage4_validation_shape_archetype_targetband_pilot_v1" / "tbl1_exports"
)
DEFAULT_OUT_DIR = ROOT / "data" / "analysis" / "shape_archetype_targetband_pilot_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze target-band metrics for archetype pilot validation.")
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS_CSV)
    parser.add_argument("--manifest-csv", type=Path, default=DEFAULT_MANIFEST_CSV)
    parser.add_argument("--tbl1-dir", type=Path, default=DEFAULT_TBL1_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def read_tbl1_numeric(tbl1_path: Path) -> Tuple[pd.Series, pd.Series]:
    tbl = pd.read_csv(tbl1_path, comment="%", header=None)
    if tbl.shape[1] < 3:
        raise RuntimeError(f"Unexpected tbl1 format: {tbl1_path}")
    k_vals = pd.to_numeric(tbl.iloc[:, 0], errors="coerce")
    freq_vals = pd.to_numeric(tbl.iloc[:, -1], errors="coerce")
    valid = k_vals.notna() & freq_vals.notna()
    return k_vals[valid], freq_vals[valid]


def compute_targetband_metrics(tbl1_path: Path, band_low: float, band_high: float) -> Dict[str, float]:
    k_vals, freq_vals = read_tbl1_numeric(tbl1_path)
    if k_vals.empty:
        return {
            "target_gap_is_open": 0,
            "target_gap_overlap_Hz": 0.0,
            "target_gap_cover_ratio": 0.0,
            "target_gap_best_width_Hz": float("nan"),
            "target_gap_lower_edge_Hz": float("nan"),
            "target_gap_upper_edge_Hz": float("nan"),
            "target_gap_center_freq": float("nan"),
            "target_gap_lower_band": float("nan"),
            "target_gap_upper_band": float("nan"),
        }

    frame = pd.DataFrame({"k": k_vals.values, "freq": freq_vals.values})
    grouped = [g.sort_values("freq")["freq"].reset_index(drop=True) for _, g in frame.groupby("k", sort=True)]
    max_bands = max(len(g) for g in grouped)

    best_overlap = 0.0
    best_width = float("-inf")
    best_lower = float("nan")
    best_upper = float("nan")
    best_lower_band = float("nan")
    best_upper_band = float("nan")

    for band_idx in range(max_bands - 1):
        lower_vals = []
        upper_vals = []
        for bands in grouped:
            if len(bands) > band_idx + 1:
                lower_vals.append(float(bands.iloc[band_idx]))
                upper_vals.append(float(bands.iloc[band_idx + 1]))
        if not lower_vals or not upper_vals:
            continue

        lower_edge = max(lower_vals)
        upper_edge = min(upper_vals)
        gap_width = upper_edge - lower_edge
        if gap_width <= 0:
            continue

        overlap = max(0.0, min(upper_edge, band_high) - max(lower_edge, band_low))
        if overlap > best_overlap + 1e-12 or (abs(overlap - best_overlap) <= 1e-12 and gap_width > best_width):
            best_overlap = overlap
            best_width = gap_width
            best_lower = lower_edge
            best_upper = upper_edge
            best_lower_band = band_idx + 1
            best_upper_band = band_idx + 2

    if best_overlap <= 0:
        return {
            "target_gap_is_open": 0,
            "target_gap_overlap_Hz": 0.0,
            "target_gap_cover_ratio": 0.0,
            "target_gap_best_width_Hz": float("nan"),
            "target_gap_lower_edge_Hz": float("nan"),
            "target_gap_upper_edge_Hz": float("nan"),
            "target_gap_center_freq": float("nan"),
            "target_gap_lower_band": float("nan"),
            "target_gap_upper_band": float("nan"),
        }

    return {
        "target_gap_is_open": 1,
        "target_gap_overlap_Hz": best_overlap,
        "target_gap_cover_ratio": best_overlap / max(1e-12, band_high - band_low),
        "target_gap_best_width_Hz": best_width,
        "target_gap_lower_edge_Hz": best_lower,
        "target_gap_upper_edge_Hz": best_upper,
        "target_gap_center_freq": 0.5 * (best_lower + best_upper),
        "target_gap_lower_band": best_lower_band,
        "target_gap_upper_band": best_upper_band,
    }


def classify_role(cover: float, is_open: int) -> str:
    if int(is_open) <= 0:
        return "hard_negative"
    if cover >= 0.50:
        return "target_band_strong"
    if cover >= 0.15:
        return "weak_band_contributor"
    return "near_miss"


def main() -> None:
    args = parse_args()
    results_csv = args.results_csv if args.results_csv.is_absolute() else ROOT / args.results_csv
    manifest_csv = args.manifest_csv if args.manifest_csv.is_absolute() else ROOT / args.manifest_csv
    tbl1_dir = args.tbl1_dir if args.tbl1_dir.is_absolute() else ROOT / args.tbl1_dir
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(results_csv)
    manifest = pd.read_csv(manifest_csv)
    merged = results.merge(
        manifest[
            [
                "validation_id",
                "target_band_tag",
                "target_band_low_Hz",
                "target_band_high_Hz",
                "target_band_center_Hz",
                "target_band_width_Hz",
                "shape_id",
                "shape_family",
                "pilot_archetype_tag",
                "pilot_seed_family",
                "pilot_origin_shape_id",
            ]
        ],
        on="validation_id",
        how="left",
    )

    for base_col in ["shape_id", "shape_family"]:
        if base_col not in merged.columns:
            left_col = f"{base_col}_x"
            right_col = f"{base_col}_y"
            if left_col in merged.columns:
                merged[base_col] = merged[left_col]
            elif right_col in merged.columns:
                merged[base_col] = merged[right_col]

    metric_rows = []
    for row in merged.itertuples(index=False):
        tbl1_path = tbl1_dir / f"{row.sample_id}_tbl1.csv"
        metrics = compute_targetband_metrics(
            tbl1_path,
            float(row.target_band_low_Hz),
            float(row.target_band_high_Hz),
        )
        metrics["validation_id"] = row.validation_id
        metric_rows.append(metrics)
    metrics_df = pd.DataFrame(metric_rows)
    merged = merged.merge(metrics_df, on="validation_id", how="left")
    merged["actual_role"] = [
        classify_role(float(c or 0.0), int(o or 0))
        for c, o in zip(merged["target_gap_cover_ratio"].fillna(0.0), merged["target_gap_is_open"].fillna(0))
    ]

    merged.to_csv(out_dir / "shape_archetype_targetband_pilot_merged_v1.csv", index=False, encoding="utf-8-sig")

    arm_summary = (
        merged.groupby(["target_band_tag", "pilot_archetype_tag"], as_index=False)
        .agg(
            rows_total=("validation_id", "count"),
            solve_success_count=("solve_success", "sum"),
            mean_target_gap_cover_ratio=("target_gap_cover_ratio", "mean"),
            median_target_gap_cover_ratio=("target_gap_cover_ratio", "median"),
            best_target_gap_cover_ratio=("target_gap_cover_ratio", "max"),
            strong_count=("actual_role", lambda s: int((s == "target_band_strong").sum())),
            weak_count=("actual_role", lambda s: int((s == "weak_band_contributor").sum())),
            near_miss_count=("actual_role", lambda s: int((s == "near_miss").sum())),
        )
        .sort_values(["target_band_tag", "best_target_gap_cover_ratio"], ascending=[True, False])
    )
    arm_summary.to_csv(out_dir / "shape_archetype_targetband_pilot_arm_summary_v1.csv", index=False, encoding="utf-8-sig")

    shape_summary = (
        merged.sort_values(
            ["shape_id", "target_gap_cover_ratio", "target_gap_overlap_Hz", "target_gap_best_width_Hz"],
            ascending=[True, False, False, False],
        )
        .groupby("shape_id", as_index=False)
        .head(1)
        .loc[
            :,
            [
                "shape_id",
                "shape_family",
                "pilot_archetype_tag",
                "pilot_seed_family",
                "target_band_tag",
                "target_gap_cover_ratio",
                "target_gap_overlap_Hz",
                "target_gap_lower_edge_Hz",
                "target_gap_upper_edge_Hz",
                "target_gap_lower_band",
                "target_gap_upper_band",
                "actual_role",
                "gap34_gain_Hz",
            ],
        ]
        .rename(columns={"target_band_tag": "best_band_tag", "actual_role": "best_band_role"})
        .sort_values(["target_gap_cover_ratio", "target_gap_overlap_Hz"], ascending=[False, False])
    )
    shape_summary.to_csv(out_dir / "shape_archetype_targetband_pilot_shape_summary_v1.csv", index=False, encoding="utf-8-sig")

    band_summary = (
        shape_summary.groupby("best_band_tag", as_index=False)
        .agg(
            shape_count=("shape_id", "count"),
            strong_count=("best_band_role", lambda s: int((s == "target_band_strong").sum())),
            weak_count=("best_band_role", lambda s: int((s == "weak_band_contributor").sum())),
            near_miss_count=("best_band_role", lambda s: int((s == "near_miss").sum())),
            mean_best_cover_ratio=("target_gap_cover_ratio", "mean"),
            best_cover_ratio_max=("target_gap_cover_ratio", "max"),
        )
        .sort_values("best_band_tag")
    )
    band_summary.to_csv(out_dir / "shape_archetype_targetband_pilot_best_band_summary_v1.csv", index=False, encoding="utf-8-sig")

    top_row = shape_summary.iloc[0].to_dict() if not shape_summary.empty else {}
    summary = {
        "results_csv": str(results_csv),
        "manifest_csv": str(manifest_csv),
        "tbl1_dir": str(tbl1_dir),
        "rows": int(len(merged)),
        "shape_count": int(shape_summary["shape_id"].nunique()) if not shape_summary.empty else 0,
        "strong_count": int((shape_summary["best_band_role"] == "target_band_strong").sum()) if not shape_summary.empty else 0,
        "weak_count": int((shape_summary["best_band_role"] == "weak_band_contributor").sum()) if not shape_summary.empty else 0,
        "near_miss_count": int((shape_summary["best_band_role"] == "near_miss").sum()) if not shape_summary.empty else 0,
        "top_shape": top_row,
    }
    (out_dir / "shape_archetype_targetband_pilot_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] shape archetype target-band pilot analysis complete")
    print(f"[OUT] {out_dir}")
    if top_row:
        print(
            "[TOP] {shape} best_band={band} role={role} cover={cover:.4f} overlap={overlap:.2f}Hz".format(
                shape=top_row.get("shape_id", ""),
                band=top_row.get("best_band_tag", ""),
                role=top_row.get("best_band_role", ""),
                cover=float(top_row.get("target_gap_cover_ratio", 0.0) or 0.0),
                overlap=float(top_row.get("target_gap_overlap_Hz", 0.0) or 0.0),
            )
        )


if __name__ == "__main__":
    main()
