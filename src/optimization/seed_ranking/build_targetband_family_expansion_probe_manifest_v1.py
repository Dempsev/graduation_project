from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_targetband_param_v1.tools.build_canonical_local_robustness_manifest_v1 import (  # noqa: E402
    CANONICAL_CASES,
    STAGE4_COMPAT_DEFAULTS,
    numeric,
    select_center_rows,
)
from prediction_targetband_param_v1.tools.build_targetband_shape_atlas_v1 import (  # noqa: E402
    DEFAULT_CATALOG,
    DEFAULT_V7_INFO,
    iter_band_source_specs,
    load_band_rows,
    load_catalog,
    load_v7_source_tags,
)

DEFAULT_HISTORY_CSV = (
    ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_best_candidates_v1.csv"
)
DEFAULT_OUT_DIR = (
    ROOT / "data" / "ml_runs" / "targetband_family_expansion_probe_v1" / "validation_manifest_v1"
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

PROBE_FAMILIES: List[Dict[str, object]] = [
    {"target_band_tag": "band240_280", "shape_family": "ep183", "priority": 1},
    {"target_band_tag": "band240_280", "shape_family": "ep195", "priority": 2},
    {"target_band_tag": "band240_280", "shape_family": "ep205", "priority": 3},
    {"target_band_tag": "band240_280", "shape_family": "ep252", "priority": 4},
    {"target_band_tag": "band240_280", "shape_family": "ep253", "priority": 5},
    {"target_band_tag": "band220_260", "shape_family": "ep206", "priority": 6},
    {"target_band_tag": "band220_260", "shape_family": "ep248", "priority": 7},
    {"target_band_tag": "band200_240", "shape_family": "ep36", "priority": 8},
    {"target_band_tag": "band200_240", "shape_family": "ep130", "priority": 9},
    {"target_band_tag": "band200_240", "shape_family": "ep193", "priority": 10},
]

PROBE_RECIPES: List[Tuple[str, Dict[str, float], str]] = [
    ("center", {}, "seed_baseline"),
    ("a1_plus", {"a1": 0.0080}, "known_favorable"),
    ("a1_minus", {"a1": -0.0080}, "direction_check"),
    ("a2_minus", {"a2": -0.0040}, "known_favorable"),
    ("a2_plus", {"a2": 0.0040}, "direction_check"),
    ("b2_plus", {"b2": 0.0040}, "known_favorable"),
    ("b2_minus", {"b2": -0.0040}, "direction_check"),
    ("r0_minus_small", {"r0": -0.00020}, "radius_probe"),
    ("r0_plus_tiny", {"r0": 0.00012}, "failure_boundary"),
    ("a1_plus_a2_minus", {"a1": 0.0080, "a2": -0.0040}, "near_miss_correction"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a first-batch weak-band family expansion probe manifest."
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--v7-info", type=Path, default=DEFAULT_V7_INFO)
    parser.add_argument("--history-csv", type=Path, default=DEFAULT_HISTORY_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def clip_param(name: str, value: float) -> float:
    if name not in GLOBAL_BOUNDS:
        return float(value)
    lo, hi = GLOBAL_BOUNDS[name]
    return float(max(lo, min(hi, value)))


def classify_role(best_cover: float, positive_count: int) -> str:
    if positive_count > 0:
        if best_cover >= 0.50:
            return "target_band_strong"
        if best_cover >= 0.15:
            return "weak_band_contributor"
        return "near_miss"
    return "hard_negative"


def build_canonical_lookup(history_csv: Path) -> Dict[Tuple[str, str], pd.Series]:
    history = pd.read_csv(history_csv)
    selected_lookup = {}
    for item in select_center_rows(history):
        case = item["case"]
        row = item["row"]
        selected_lookup[(str(case["target_band_tag"]), str(row["shape_family"]))] = row
    return selected_lookup


def select_best_family_row(rows: pd.DataFrame, family: str) -> pd.Series:
    subset = rows[rows["shape_family"].astype(str) == str(family)].copy()
    if subset.empty:
        raise RuntimeError(f"No rows found for family={family}")
    subset["target_gap_cover_ratio_num"] = pd.to_numeric(subset["target_gap_cover_ratio"], errors="coerce").fillna(-1.0)
    subset["target_gap_overlap_Hz_num"] = pd.to_numeric(subset["target_gap_overlap_Hz"], errors="coerce").fillna(-1.0)
    subset["solve_success_num"] = pd.to_numeric(subset["solve_success"], errors="coerce").fillna(0.0)
    subset["training_ready_num"] = pd.to_numeric(subset["is_training_ready"], errors="coerce").fillna(0.0)
    chosen = subset.sort_values(
        ["target_gap_cover_ratio_num", "target_gap_overlap_Hz_num", "solve_success_num", "training_ready_num", "shape_id", "sample_id"],
        ascending=[False, False, False, False, True, True],
    ).iloc[0]
    return chosen


def build_seed_lookup(catalog: List[Dict[str, object]], v7_tags: List[str], canonical_lookup: Dict[Tuple[str, str], pd.Series]) -> Dict[Tuple[str, str], Dict[str, object]]:
    by_band_specs = {str(band["target_band_tag"]): (band, specs) for band, specs in iter_band_source_specs(catalog, v7_tags)}
    seed_lookup: Dict[Tuple[str, str], Dict[str, object]] = {}

    for item in PROBE_FAMILIES:
        band_tag = str(item["target_band_tag"])
        family = str(item["shape_family"])
        band_meta, specs = by_band_specs[band_tag]
        key = (band_tag, family)
        if key in canonical_lookup:
            row = canonical_lookup[key]
            source = "canonical_center"
            shape_role = "target_band_strong"
            base_cover = float(numeric(row.get("archive_cover_ratio", 0.0)))
            base_overlap = float(numeric(row.get("archive_overlap_Hz", 0.0)))
        else:
            rows = load_band_rows(specs, band_tag)
            row = select_best_family_row(rows, family)
            source = "atlas_best_row"
            base_cover = float(numeric(row.get("target_gap_cover_ratio", 0.0)))
            base_overlap = float(numeric(row.get("target_gap_overlap_Hz", 0.0)))
            positive_count = int(numeric(row.get("target_gap_is_open", 0)))
            shape_role = classify_role(base_cover, positive_count)

        seed_lookup[key] = {
            "band_meta": band_meta,
            "row": row,
            "seed_source": source,
            "seed_shape_role": shape_role,
            "seed_base_cover_ratio": base_cover,
            "seed_base_overlap_Hz": base_overlap,
        }
    return seed_lookup


def build_manifest_row(
    item: Dict[str, object],
    seed_info: Dict[str, object],
    variant_label: str,
    deltas: Dict[str, float],
    preferred_direction: str,
    rank: int,
) -> Dict[str, object]:
    center = seed_info["row"]
    band_meta = seed_info["band_meta"]
    out = center.to_dict()
    for field in ["a1", "a2", "b1", "b2", "r0", "a3", "b3", "a4", "b4", "a5", "b5"]:
        out[field] = numeric(out[field])
    for field, delta in deltas.items():
        out[field] = clip_param(field, float(out[field]) + float(delta))

    band_tag = str(item["target_band_tag"])
    family = str(item["shape_family"])
    out["validation_id"] = f"{band_tag}__{family}__{variant_label}"
    out["selection_source"] = "targetband_family_expansion_probe_v1"
    out["selection_label"] = f"{band_tag}__{family}__family_probe"
    out["rank_within_source"] = rank
    out["target_band_tag"] = band_tag
    out["target_band_low_Hz"] = float(band_meta["band_low_Hz"])
    out["target_band_high_Hz"] = float(band_meta["band_high_Hz"])
    out["target_band_center_Hz"] = 0.5 * (float(band_meta["band_low_Hz"]) + float(band_meta["band_high_Hz"]))
    out["target_band_width_Hz"] = float(band_meta["band_high_Hz"]) - float(band_meta["band_low_Hz"])
    out["selection_priority"] = int(item["priority"])
    out["pool_arm"] = "targetband_family_expansion_probe"
    out["point_strategy"] = "family_directed_probe"
    out["target_rule"] = "weak_band_family_expansion_v1"
    out["step_window"] = "family_expansion_probe"
    out["seed_shape_id"] = out["shape_id"]
    out["seed_family"] = family
    out["seed_tier"] = "family_seed_center"
    out["seed_source"] = str(seed_info["seed_source"])
    out["is_seed_shape"] = variant_label == "center"
    out["step_num"] = rank
    out["step_offset"] = rank - 1
    out["step_distance"] = ""
    out["family_prior_source"] = "targetband_shape_atlas_v1"
    out["seed_prior_source"] = "targetband_shape_atlas_v1"
    out["preferred_direction"] = preferred_direction
    out["allowed_offsets"] = json.dumps(deltas, ensure_ascii=False, sort_keys=True)
    out["family_probe_group"] = band_tag
    out["family_probe_variant"] = variant_label
    out["family_probe_priority"] = int(item["priority"])
    out["seed_shape_role"] = str(seed_info["seed_shape_role"])
    out["seed_base_cover_ratio"] = float(seed_info["seed_base_cover_ratio"])
    out["seed_base_overlap_Hz"] = float(seed_info["seed_base_overlap_Hz"])
    out["delta_a1"] = float(out["a1"]) - float(numeric(center["a1"]))
    out["delta_a2"] = float(out["a2"]) - float(numeric(center["a2"]))
    out["delta_b2"] = float(out["b2"]) - float(numeric(center["b2"]))
    out["delta_r0"] = float(out["r0"]) - float(numeric(center["r0"]))

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
    catalog = load_catalog(args.catalog)
    v7_tags = load_v7_source_tags(args.v7_info)
    history_csv = args.history_csv if args.history_csv.is_absolute() else ROOT / args.history_csv
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    canonical_lookup = build_canonical_lookup(history_csv)
    seed_lookup = build_seed_lookup(catalog, v7_tags, canonical_lookup)

    rows: List[Dict[str, object]] = []
    seed_summary: List[Dict[str, object]] = []
    rank = 1
    for item in PROBE_FAMILIES:
        key = (str(item["target_band_tag"]), str(item["shape_family"]))
        seed_info = seed_lookup[key]
        seed_row = seed_info["row"]
        seed_summary.append(
            {
                "target_band_tag": key[0],
                "shape_family": key[1],
                "shape_id": str(seed_row["shape_id"]),
                "sample_id": str(seed_row["sample_id"]),
                "seed_source": str(seed_info["seed_source"]),
                "seed_shape_role": str(seed_info["seed_shape_role"]),
                "seed_base_cover_ratio": float(seed_info["seed_base_cover_ratio"]),
                "seed_base_overlap_Hz": float(seed_info["seed_base_overlap_Hz"]),
                "a1": float(numeric(seed_row["a1"])),
                "a2": float(numeric(seed_row["a2"])),
                "b2": float(numeric(seed_row["b2"])),
                "r0": float(numeric(seed_row["r0"])),
            }
        )
        for variant_label, deltas, preferred_direction in PROBE_RECIPES:
            rows.append(build_manifest_row(item, seed_info, variant_label, deltas, preferred_direction, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "targetband_family_expansion_probe_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    seed_df = pd.DataFrame(seed_summary)
    seed_df.to_csv(out_dir / "targetband_family_expansion_probe_seeds_v1.csv", index=False, encoding="utf-8-sig")

    summary = {
        "history_csv": str(history_csv),
        "manifest_rows": int(len(manifest)),
        "family_target_count": int(len(seed_df)),
        "variants_per_family_target": int(len(PROBE_RECIPES)),
        "probe_families": PROBE_FAMILIES,
        "probe_recipes": [
            {"variant_label": label, "deltas": deltas, "preferred_direction": direction}
            for label, deltas, direction in PROBE_RECIPES
        ],
        "seeds": seed_summary,
        "canonical_lookup_keys": [f"{band}::{family}" for band, family in sorted(canonical_lookup.keys())],
    }
    (out_dir / "targetband_family_expansion_probe_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] target-band family expansion probe manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[FAMILIES] {len(seed_df)} family-targets, {len(manifest)} rows")


if __name__ == "__main__":
    main()
