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
    STAGE4_COMPAT_DEFAULTS,
    numeric,
)

DEFAULT_BASE_CSV = (
    ROOT / "data" / "analysis" / "targetband_family_expansion_probe_round2_v1" / "targetband_family_expansion_probe_round2_merged_v1.csv"
)
DEFAULT_OUT_DIR = (
    ROOT / "data" / "ml_runs" / "targetband_family_expansion_probe_round3_v1" / "validation_manifest_v1"
)

KEEP_TARGETS: List[Tuple[str, str]] = [
    ("band200_240", "ep130"),
    ("band240_280", "ep195"),
    ("band240_280", "ep253"),
]

RECIPES_BY_FAMILY: Dict[Tuple[str, str], List[Tuple[str, Dict[str, float], str]]] = {
    ("band200_240", "ep130"): [
        ("round3_center", {}, "round3_center"),
        ("r0_plus_ultra", {"r0": 0.00003}, "radius_followup"),
        ("r0_plus_ultra_a1_plus_tiny", {"r0": 0.00003, "a1": 0.0010}, "coupled_followup"),
        ("r0_plus_ultra_a2_plus_tiny", {"r0": 0.00003, "a2": 0.0010}, "coupled_followup"),
        ("a1_plus_tiny", {"a1": 0.0010}, "direction_followup"),
        ("a2_plus_tiny", {"a2": 0.0010}, "direction_followup"),
    ],
    ("band240_280", "ep195"): [
        ("round3_center", {}, "round3_center"),
        ("a1_plus_tinier", {"a1": 0.0010}, "direction_followup"),
        ("a2_minus_tinier", {"a2": -0.0010}, "direction_followup"),
        ("a1_plus_tinier_a2_minus_tinier", {"a1": 0.0010, "a2": -0.0010}, "coupled_followup"),
        ("b2_plus_tinier", {"b2": 0.0010}, "direction_followup"),
        ("a1_plus_tinier_b2_plus_tinier", {"a1": 0.0010, "b2": 0.0010}, "coupled_followup"),
    ],
    ("band240_280", "ep253"): [
        ("round3_center", {}, "round3_center"),
        ("a1_plus_tinier", {"a1": 0.0010}, "direction_followup"),
        ("a2_minus_tinier", {"a2": -0.0010}, "direction_followup"),
        ("a1_plus_tinier_a2_minus_tinier", {"a1": 0.0010, "a2": -0.0010}, "coupled_followup"),
        ("b2_plus_tinier", {"b2": 0.0010}, "direction_followup"),
        ("a1_plus_tinier_b2_plus_tinier", {"a1": 0.0010, "b2": 0.0010}, "coupled_followup"),
    ],
}

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build round-3 family-expansion probe manifest.")
    parser.add_argument("--base-csv", type=Path, default=DEFAULT_BASE_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def clip_param(name: str, value: float) -> float:
    if name not in GLOBAL_BOUNDS:
        return float(value)
    lo, hi = GLOBAL_BOUNDS[name]
    return float(max(lo, min(hi, value)))


def select_best_rows(df: pd.DataFrame) -> List[Dict[str, object]]:
    picked: List[Dict[str, object]] = []
    for band_tag, family in KEEP_TARGETS:
        subset = df[(df["target_band_tag"] == band_tag) & (df["shape_family"] == family)].copy()
        if subset.empty:
            raise RuntimeError(f"Missing prior probe rows for {band_tag}/{family}")
        subset = subset.sort_values(
            ["target_cover_ratio_actual", "target_overlap_Hz_actual", "gap34_gain_Hz"],
            ascending=[False, False, False],
        )
        picked.append(subset.iloc[0].to_dict())
    return picked


def build_row(seed: Dict[str, object], variant_label: str, deltas: Dict[str, float], preferred_direction: str, rank: int) -> Dict[str, object]:
    out = dict(seed)
    for field in ["a1", "a2", "b1", "b2", "r0", "a3", "b3", "a4", "b4", "a5", "b5"]:
        out[field] = numeric(out[field])
    base_a1 = float(out["a1"])
    base_a2 = float(out["a2"])
    base_b2 = float(out["b2"])
    base_r0 = float(out["r0"])
    for field, delta in deltas.items():
        out[field] = clip_param(field, float(out[field]) + float(delta))

    band_tag = str(out["target_band_tag"])
    family = str(out["shape_family"])
    out["validation_id"] = f"{band_tag}__{family}__round3__{rank:02d}"
    out["selection_source"] = "targetband_family_expansion_probe_round3_v1"
    out["selection_label"] = f"{band_tag}__{family}__family_probe_round3"
    out["rank_within_source"] = rank
    out["pool_arm"] = "targetband_family_expansion_probe_round3"
    out["point_strategy"] = "family_directed_probe_round3"
    out["target_rule"] = "weak_band_family_expansion_round3_v1"
    out["step_window"] = "family_expansion_probe_round3"
    out["is_seed_shape"] = variant_label == "round3_center"
    out["step_num"] = rank
    out["step_offset"] = rank - 1
    out["step_distance"] = ""
    out["preferred_direction"] = preferred_direction
    out["allowed_offsets"] = json.dumps(deltas, ensure_ascii=False, sort_keys=True)
    out["family_probe_variant"] = variant_label
    out["seed_shape_role"] = str(out.get("actual_role", out.get("seed_shape_role", "")))
    out["seed_base_cover_ratio"] = float(out.get("target_cover_ratio_actual", 0.0) or 0.0)
    out["seed_base_overlap_Hz"] = float(out.get("target_overlap_Hz_actual", 0.0) or 0.0)
    out["round3_parent_validation_id"] = str(seed.get("validation_id", ""))
    out["round3_parent_variant"] = str(seed.get("family_probe_variant", ""))
    out["delta_a1"] = float(out["a1"]) - base_a1
    out["delta_a2"] = float(out["a2"]) - base_a2
    out["delta_b2"] = float(out["b2"]) - base_b2
    out["delta_r0"] = float(out["r0"]) - base_r0

    for key, value in STAGE4_COMPAT_DEFAULTS.items():
        out[key] = value
    return out


def main() -> None:
    args = parse_args()
    base_csv = args.base_csv if args.base_csv.is_absolute() else ROOT / args.base_csv
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    prior = pd.read_csv(base_csv)
    best_rows = select_best_rows(prior)

    rows: List[Dict[str, object]] = []
    seed_summary: List[Dict[str, object]] = []
    rank = 1
    for best in best_rows:
        key = (str(best["target_band_tag"]), str(best["shape_family"]))
        recipes = RECIPES_BY_FAMILY[key]
        seed_summary.append(
            {
                "target_band_tag": key[0],
                "shape_family": key[1],
                "shape_id": str(best["shape_id"]),
                "base_validation_id": str(best["validation_id"]),
                "base_best_variant": str(best.get("family_probe_variant", "")),
                "target_cover_ratio_actual": float(best.get("target_cover_ratio_actual", 0.0) or 0.0),
                "target_overlap_Hz_actual": float(best.get("target_overlap_Hz_actual", 0.0) or 0.0),
                "a1": float(numeric(best["a1"])),
                "a2": float(numeric(best["a2"])),
                "b2": float(numeric(best["b2"])),
                "r0": float(numeric(best["r0"])),
            }
        )
        for variant_label, deltas, preferred_direction in recipes:
            rows.append(build_row(best, variant_label, deltas, preferred_direction, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "targetband_family_expansion_probe_round3_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(seed_summary).to_csv(
        out_dir / "targetband_family_expansion_probe_round3_seeds_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "base_csv": str(base_csv),
        "manifest_rows": int(len(manifest)),
        "family_target_count": int(len(seed_summary)),
        "keep_targets": [{"target_band_tag": b, "shape_family": f} for b, f in KEEP_TARGETS],
        "recipes_by_family": {
            f"{band}::{family}": [
                {"variant_label": label, "deltas": deltas, "preferred_direction": direction}
                for label, deltas, direction in RECIPES_BY_FAMILY[(band, family)]
            ]
            for band, family in KEEP_TARGETS
        },
        "seeds": seed_summary,
    }
    (out_dir / "targetband_family_expansion_probe_round3_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] target-band family expansion probe round3 manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[FAMILIES] {len(seed_summary)} family-targets, {len(manifest)} rows")


if __name__ == "__main__":
    main()
