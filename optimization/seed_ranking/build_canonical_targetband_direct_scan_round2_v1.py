from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_targetband_param_v1.tools.build_canonical_local_robustness_manifest_v1 import STAGE4_COMPAT_DEFAULTS


DEFAULT_BASE_RESULTS = (
    ROOT / "data" / "analysis" / "canonical_targetband_direct_scan_v1" / "canonical_targetband_direct_scan_ranked_v1.csv"
)
DEFAULT_HISTORY_CSV = (
    ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_best_candidates_v1.csv"
)
DEFAULT_OUT_DIR = (
    ROOT / "data" / "ml_runs" / "canonical_targetband_direct_scan_round2_v1" / "validation_manifest_v1"
)

GLOBAL_BOUNDS: Dict[str, Tuple[float, float]] = {
    "a1": (0.42, 0.58),
    "a2": (-0.24, 0.00),
    "b1": (-0.08, 0.08),
    "b2": (-0.04, 0.12),
    "a3": (-0.06, 0.06),
    "b3": (-0.06, 0.06),
    "a4": (-0.05, 0.05),
    "b4": (-0.05, 0.05),
    "a5": (-0.04, 0.04),
    "b5": (-0.04, 0.04),
    "r0": (0.008, 0.016),
}

# Round-2 is intentionally small and only explores the promising a1/a2/b2 neighborhood.
ROUND2_RECIPES = [
    ("round2_center", {}, "round2_center"),
    ("a1_plus_tiny", {"a1": 0.0020}, "a1_refine"),
    ("a1_minus_tiny", {"a1": -0.0020}, "a1_refine"),
    ("a2_minus_tiny", {"a2": -0.0020}, "a2_refine"),
    ("a2_plus_tiny", {"a2": 0.0020}, "a2_refine"),
    ("b2_plus_tiny", {"b2": 0.0020}, "b2_refine"),
    ("b2_minus_tiny", {"b2": -0.0020}, "b2_refine"),
    ("a1_plus_tiny_a2_minus_tiny", {"a1": 0.0020, "a2": -0.0020}, "coupled_refine"),
    ("a1_plus_tiny_b2_plus_tiny", {"a1": 0.0020, "b2": 0.0020}, "coupled_refine"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a second-round direct local scan manifest around the current best real COMSOL point.")
    parser.add_argument("--base-results", type=Path, default=DEFAULT_BASE_RESULTS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def clip_param(name: str, value: float) -> float:
    if name not in GLOBAL_BOUNDS:
        return float(value)
    lo, hi = GLOBAL_BOUNDS[name]
    return float(max(lo, min(hi, value)))


def base_row_from_best(base_results: Path) -> pd.Series:
    ranked = pd.read_csv(base_results)
    if ranked.empty:
        raise RuntimeError("Base ranked direct-scan results are empty.")
    best = ranked.iloc[0].copy()
    if str(best.get("canonical_case_id", "")) != "band240_280_ep253":
        raise RuntimeError("Round-2 builder currently expects band240_280_ep253 as the best base case.")
    return best


def build_row(best: pd.Series, variant_label: str, deltas: Dict[str, float], preferred_direction: str, rank: int) -> Dict[str, object]:
    out = best.to_dict()
    for field in ["a1", "a2", "b1", "b2", "r0", "a3", "b3", "a4", "b4", "a5", "b5"]:
        out[field] = float(pd.to_numeric([out[field]], errors="coerce")[0])
    for field, delta in deltas.items():
        out[field] = clip_param(field, float(out[field]) + float(delta))

    case_id = str(best["canonical_case_id"])
    out["validation_id"] = f"{case_id}__round2__{rank:02d}"
    out["selection_source"] = "canonical_targetband_direct_scan_round2_v1"
    out["selection_label"] = f"{case_id}__round2"
    out["rank_within_source"] = rank
    out["canonical_variant"] = variant_label
    out["step_window"] = "direct_local_scan_round2"
    out["point_strategy"] = "canonical_targetband_direct_scan_round2_v1"
    out["target_rule"] = "canonical_targetband_direct_scan_round2_v1"
    out["preferred_direction"] = preferred_direction
    out["allowed_offsets"] = json.dumps(deltas, ensure_ascii=False, sort_keys=True)
    out["step_num"] = rank
    out["step_offset"] = rank - 1
    out["direct_scan_group"] = preferred_direction
    out["delta_a1"] = float(out["a1"]) - float(best["a1"])
    out["delta_a2"] = float(out["a2"]) - float(best["a2"])
    out["delta_b2"] = float(out["b2"]) - float(best["b2"])
    out["delta_r0"] = float(out["r0"]) - float(best["r0"])
    out["source_sample_id"] = str(best.get("sample_id", ""))
    out["seed_shape_id"] = str(best.get("shape_id", ""))
    out["seed_family"] = str(best.get("shape_family", ""))
    out["seed_tier"] = "round1_best_real_scan"
    out["seed_source"] = "canonical_targetband_direct_scan_v1"
    out["is_seed_shape"] = variant_label == "round2_center"
    out["family_prior_source"] = "canonical_targetband_direct_scan_v1"
    out["seed_prior_source"] = "canonical_targetband_direct_scan_v1"
    out["v5_reference_validation_id"] = ""
    out["v5_reference_gain_Hz"] = pd.NA
    out["stage1_reference_sample_id"] = ""
    out["stage1_reference_fourier_id"] = ""
    out["stage1_reference_gap_Hz"] = pd.NA
    out["stage1_reference_gap_gain_Hz"] = pd.NA
    out["stage1_reference_contact_length"] = pd.NA
    out["stage1_reference_candidate_tier"] = ""
    for key, value in STAGE4_COMPAT_DEFAULTS.items():
        out[key] = value
    return out


def main() -> None:
    args = parse_args()
    base_results = args.base_results if args.base_results.is_absolute() else ROOT / args.base_results
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    best = base_row_from_best(base_results)
    rows: List[Dict[str, object]] = []
    for rank, (variant_label, deltas, preferred_direction) in enumerate(ROUND2_RECIPES, start=1):
        rows.append(build_row(best, variant_label, deltas, preferred_direction, rank))

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "canonical_targetband_direct_scan_round2_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "base_results": str(base_results),
        "base_validation_id": str(best["validation_id"]),
        "canonical_case_id": str(best["canonical_case_id"]),
        "base_variant": str(best["canonical_variant"]),
        "base_a1": float(best["a1"]),
        "base_a2": float(best["a2"]),
        "base_b2": float(best["b2"]),
        "base_r0": float(best["r0"]),
        "manifest_rows": int(len(manifest)),
        "recipes": [
            {"variant_label": label, "deltas": deltas, "preferred_direction": direction}
            for label, deltas, direction in ROUND2_RECIPES
        ],
    }
    (out_dir / "canonical_targetband_direct_scan_round2_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] canonical target-band direct scan round2 manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[BASE] {best['validation_id']} -> rows={len(manifest)}")


if __name__ == "__main__":
    main()
