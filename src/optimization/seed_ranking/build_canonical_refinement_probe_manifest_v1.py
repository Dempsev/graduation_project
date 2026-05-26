from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]

DEFAULT_SOURCE_MANIFEST = (
    ROOT
    / "data"
    / "ml_runs"
    / "canonical_targetband_refinement_v1_allcases"
    / "validation_manifest_v1"
    / "canonical_targetband_refinement_validation_manifest_v1.csv"
)
DEFAULT_OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "canonical_targetband_refinement_ep248_probe_v1"
    / "validation_manifest_v1"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a compact stage4 validation manifest for a selected canonical refinement probe case."
    )
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--case-id", default="band180_220_ep248")
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_manifest = args.source_manifest if args.source_manifest.is_absolute() else ROOT / args.source_manifest
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir

    if not source_manifest.exists():
        raise FileNotFoundError(source_manifest)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(source_manifest)
    if df.empty:
        raise RuntimeError("Source refinement validation manifest is empty.")

    case_id = str(args.case_id).strip()
    subset = df[df["canonical_case_id"].astype(str) == case_id].copy()
    if subset.empty:
        raise RuntimeError(f"No rows found for canonical_case_id={case_id}")

    ranked = subset.sort_values(
        [
            "rank_within_source",
            "fitness",
            "targetband_score",
            "target_gap_cover_ratio_pred",
            "target_gap_overlap_pred_Hz",
        ],
        ascending=[True, False, False, False, False],
    ).copy()
    selected = ranked.head(max(1, int(args.top_k))).copy()
    selected["selection_source"] = "canonical_targetband_refinement_ep248_probe_v1"
    selected["selection_label"] = "canonical_targetband_refinement_ep248_probe_v1"
    selected["rank_within_source"] = range(1, len(selected) + 1)

    manifest_path = out_dir / "canonical_targetband_refinement_ep248_probe_manifest_v1.csv"
    summary_path = out_dir / "canonical_targetband_refinement_ep248_probe_manifest_summary_v1.json"
    selected.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "source_manifest": str(source_manifest),
        "canonical_case_id": case_id,
        "manifest_rows": int(len(selected)),
        "top_k": int(args.top_k),
        "target_band_tag": str(selected["target_band_tag"].iloc[0]) if "target_band_tag" in selected.columns else "",
        "shape_id": str(selected["shape_id"].iloc[0]) if "shape_id" in selected.columns else "",
        "shape_family": str(selected["shape_family"].iloc[0]) if "shape_family" in selected.columns else "",
        "best_predicted_cover_ratio": float(pd.to_numeric(selected["target_gap_cover_ratio_pred"], errors="coerce").max()),
        "best_predicted_overlap_Hz": float(pd.to_numeric(selected["target_gap_overlap_pred_Hz"], errors="coerce").max()),
        "validation_ids": selected["validation_id"].astype(str).tolist(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[DONE] canonical refinement probe manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[CASE] {case_id} rows={len(selected)} top_k={int(args.top_k)}")


if __name__ == "__main__":
    main()
