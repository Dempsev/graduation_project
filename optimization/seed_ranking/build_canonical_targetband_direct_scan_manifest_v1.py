from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_targetband_param_v1.tools.build_canonical_local_robustness_manifest_v1 import (
    CANONICAL_CASES,
    STAGE4_COMPAT_DEFAULTS,
    numeric,
    select_center_rows,
)

DEFAULT_HISTORY_CSV = (
    ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_best_candidates_v1.csv"
)
DEFAULT_OUT_DIR = (
    ROOT / "data" / "ml_runs" / "canonical_targetband_direct_scan_v1" / "validation_manifest_v1"
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

# A single direct-scan package centered on the hardest validated weak-band case.
# The recipes deliberately combine:
# - physics-guided direction: a1_plus (observed best in actual local robustness)
# - robustness-aware direction: tiny r0_minus pullback away from the dangerous r0_plus side
# - multi-objective companions: b2_plus / a2_minus to compare cover-vs-stability tradeoffs
DIRECT_SCAN_RECIPES = [
    ("center", {}, "baseline_center"),
    ("a1_plus_half", {"a1": 0.005}, "physics_guided_a1_plus"),
    ("a1_plus_full", {"a1": 0.010}, "physics_guided_a1_plus"),
    ("a1_plus_full_r0_minus_small", {"a1": 0.010, "r0": -0.00020}, "robustness_aware"),
    ("a1_plus_full_b2_plus_small", {"a1": 0.010, "b2": 0.0040}, "multiobjective_balance"),
    ("a1_plus_full_a2_minus_small", {"a1": 0.010, "a2": -0.0040}, "multiobjective_balance"),
    (
        "a1_plus_full_b2_plus_small_r0_minus_small",
        {"a1": 0.010, "b2": 0.0040, "r0": -0.00020},
        "robustness_aware",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a focused real-COMSOL direct local scan manifest around a canonical target-band case."
    )
    parser.add_argument("--history-csv", type=Path, default=DEFAULT_HISTORY_CSV)
    parser.add_argument("--case-id", default="band240_280_ep253")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def resolve_case(case_id: str) -> Dict[str, object]:
    for case in CANONICAL_CASES:
        if str(case["case_id"]) == str(case_id):
            return case
    raise ValueError(f"Unknown canonical case id: {case_id}")


def clip_param(name: str, value: float) -> float:
    if name not in GLOBAL_BOUNDS:
        return float(value)
    lo, hi = GLOBAL_BOUNDS[name]
    return float(max(lo, min(hi, value)))


def build_row(center: pd.Series, case: Dict[str, object], variant_label: str, deltas: Dict[str, float], preferred_direction: str, rank: int) -> Dict[str, object]:
    out = center.to_dict()
    for field in ["a1", "a2", "b1", "b2", "r0", "a3", "b3", "a4", "b4", "a5", "b5"]:
        out[field] = numeric(out[field])
    for field, delta in deltas.items():
        out[field] = clip_param(field, float(out[field]) + float(delta))

    case_id = str(case["case_id"])
    out["validation_id"] = f"{case_id}__directscan__{rank:02d}"
    out["selection_source"] = "canonical_targetband_direct_scan_v1"
    out["selection_label"] = f"{case_id}__directscan"
    out["rank_within_source"] = rank
    out["canonical_case_id"] = case_id
    out["canonical_variant"] = variant_label
    out["target_band_tag"] = case["target_band_tag"]
    out["target_band_low_Hz"] = case["target_band_low_Hz"]
    out["target_band_high_Hz"] = case["target_band_high_Hz"]
    out["target_band_center_Hz"] = 0.5 * (case["target_band_low_Hz"] + case["target_band_high_Hz"])
    out["target_band_width_Hz"] = case["target_band_high_Hz"] - case["target_band_low_Hz"]
    out["selection_priority"] = rank
    out["pool_arm"] = "canonical_targetband_direct_scan"
    out["point_strategy"] = "canonical_targetband_direct_scan_v1"
    out["target_rule"] = "canonical_targetband_direct_scan_v1"
    out["step_window"] = "direct_local_scan"
    out["seed_shape_id"] = out["shape_id"]
    out["seed_family"] = out["shape_family"]
    out["seed_tier"] = "canonical_case_center"
    out["seed_source"] = "band_supplement_exploratory_v2"
    out["is_seed_shape"] = variant_label == "center"
    out["step_num"] = rank
    out["step_offset"] = rank - 1
    out["step_distance"] = ""
    out["family_prior_source"] = "canonical_case_freeze_v1"
    out["seed_prior_source"] = "canonical_case_freeze_v1"
    out["preferred_direction"] = preferred_direction
    out["allowed_offsets"] = json.dumps(deltas, ensure_ascii=False, sort_keys=True)
    out["v5_reference_validation_id"] = ""
    out["v5_reference_gain_Hz"] = pd.NA
    out["stage1_reference_sample_id"] = ""
    out["stage1_reference_fourier_id"] = ""
    out["stage1_reference_gap_Hz"] = pd.NA
    out["stage1_reference_gap_gain_Hz"] = pd.NA
    out["stage1_reference_contact_length"] = pd.NA
    out["stage1_reference_candidate_tier"] = ""
    out["direct_scan_group"] = preferred_direction
    out["delta_a1"] = float(out["a1"]) - float(numeric(center["a1"]))
    out["delta_a2"] = float(out["a2"]) - float(numeric(center["a2"]))
    out["delta_b2"] = float(out["b2"]) - float(numeric(center["b2"]))
    out["delta_r0"] = float(out["r0"]) - float(numeric(center["r0"]))

    for key, value in STAGE4_COMPAT_DEFAULTS.items():
        out[key] = value
    return out


def main() -> None:
    args = parse_args()
    history_csv = args.history_csv if args.history_csv.is_absolute() else ROOT / args.history_csv
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    history = pd.read_csv(history_csv)
    case = resolve_case(str(args.case_id).strip())
    selected_lookup = {str(item["case"]["case_id"]): item["row"] for item in select_center_rows(history)}
    if str(case["case_id"]) not in selected_lookup:
        raise RuntimeError(f"No canonical center found for {case['case_id']}")
    center = selected_lookup[str(case["case_id"])]

    rows: List[Dict[str, object]] = []
    for rank, (variant_label, deltas, preferred_direction) in enumerate(DIRECT_SCAN_RECIPES, start=1):
        rows.append(build_row(center, case, variant_label, deltas, preferred_direction, rank))

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "canonical_targetband_direct_scan_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "history_csv": str(history_csv),
        "canonical_case_id": str(case["case_id"]),
        "target_band_tag": str(case["target_band_tag"]),
        "shape_id": str(center["shape_id"]),
        "shape_family": str(center["shape_family"]),
        "center_sample_id": str(center["sample_id"]),
        "manifest_rows": int(len(manifest)),
        "recipes": [
            {
                "variant_label": label,
                "deltas": deltas,
                "preferred_direction": direction,
            }
            for label, deltas, direction in DIRECT_SCAN_RECIPES
        ],
    }
    (out_dir / "canonical_targetband_direct_scan_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] canonical target-band direct scan manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[CASE] {case['case_id']} rows={len(manifest)}")


if __name__ == "__main__":
    main()
