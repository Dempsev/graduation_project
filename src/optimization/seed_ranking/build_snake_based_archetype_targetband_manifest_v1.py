from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PILOT_CSV = (
    ROOT
    / "data"
    / "snake_based_archetype_expansion_pilot_v1"
    / "analysis"
    / "snake_based_archetype_pilot_top_by_type_v1.csv"
)
DEFAULT_THESIS_CATALOG = ROOT / "prediction_targetband_param_v1" / "configs" / "thesis_band_catalog_v2.json"
DEFAULT_OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "snake_based_archetype_targetband_pilot_v1"
    / "validation_manifest_v1"
)

TARGET_BANDS = ["band200_240", "band220_260", "band240_280"]
TOP_PER_TYPE = 4

STAGE4_COMPAT_DEFAULTS = {
    "contact_prob": 1.0,
    "positive_prob": 1.0,
    "surrogate_pred_gap34_gain_Hz": 0.0,
    "class_score": 1.0,
    "cascade_score": 1.0,
    "contact_gate": True,
    "positive_gate": True,
    "reg_positive_gate": True,
    "cascade_gate": True,
    "rank_cascade": pd.NA,
    "rank_surrogate": pd.NA,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build target-band screening manifest for snake-based archetype pilot.")
    parser.add_argument("--pilot-csv", type=Path, default=DEFAULT_PILOT_CSV)
    parser.add_argument("--thesis-catalog", type=Path, default=DEFAULT_THESIS_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_target_bands(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bands = [band for band in payload.get("bands", []) if str(band.get("target_band_tag")) in TARGET_BANDS]
    if len(bands) != len(TARGET_BANDS):
        raise RuntimeError(f"Expected target bands {TARGET_BANDS}, found {[b.get('target_band_tag') for b in bands]}")
    return bands


def select_candidates(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["priority_score"] = pd.to_numeric(work["priority_score"], errors="coerce").fillna(-1e18)
    work["compactness"] = pd.to_numeric(work["compactness"], errors="coerce").fillna(0.0)
    work["aspect_ratio"] = pd.to_numeric(work["aspect_ratio"], errors="coerce").fillna(1.0)
    selected = (
        work.sort_values(
            ["priority_archetype", "priority_score", "compactness"],
            ascending=[True, False, False],
        )
        .groupby("priority_archetype", as_index=False)
        .head(TOP_PER_TYPE)
        .reset_index(drop=True)
    )
    return selected


def build_manifest_row(row: pd.Series, band: Dict[str, object], rank: int) -> Dict[str, object]:
    shape_id = str(row["shape_id"])
    archetype_tag = str(row["priority_archetype"])
    band_tag = str(band["target_band_tag"])
    band_low = float(band["band_low_Hz"])
    band_high = float(band["band_high_Hz"])
    point_id = "snake_pilot_center_fixed_v1"

    out = row.to_dict()
    out["sample_id"] = f"stage4_validation_snake_based_archetype_targetband_pilot_v1_{band_tag}_{shape_id}"
    out["validation_id"] = f"{band_tag}__{shape_id}__center"
    out["selection_source"] = "snake_based_archetype_targetband_pilot_v1"
    out["selection_label"] = f"{band_tag}__{archetype_tag}__snake_pilot"
    out["rank_within_source"] = rank
    out["target_band_tag"] = band_tag
    out["target_band_low_Hz"] = band_low
    out["target_band_high_Hz"] = band_high
    out["target_band_center_Hz"] = 0.5 * (band_low + band_high)
    out["target_band_width_Hz"] = band_high - band_low
    out["selection_priority"] = rank
    out["pool_arm"] = "snake_based_archetype_targetband_pilot"
    out["point_strategy"] = "snake_pilot_center_only"
    out["target_rule"] = "snake_based_archetype_targetband_pilot_v1"
    out["step_window"] = "snake_pilot_center"
    out["seed_shape_id"] = shape_id
    out["seed_family"] = str(shape_id).split("_", 1)[0]
    out["seed_tier"] = "snake_archetype_representative"
    out["seed_source"] = "snake_based_archetype_expansion_pilot_v1"
    out["is_seed_shape"] = True
    out["step_num"] = pd.NA
    out["step_offset"] = pd.NA
    out["step_distance"] = pd.NA
    out["family_prior_source"] = "snake_based_archetype_expansion_pilot_v1"
    out["seed_prior_source"] = "snake_based_archetype_expansion_pilot_v1"
    out["preferred_direction"] = ""
    out["allowed_offsets"] = ""
    out["candidate_id"] = shape_id
    out["main_id"] = point_id
    out["point_id"] = point_id
    out["shape_id"] = shape_id
    out["shape_family"] = str(shape_id).split("_", 1)[0]
    out["shape_role"] = "snake_archetype_pilot"
    out["pilot_archetype_tag"] = archetype_tag
    out["pilot_origin_shape_id"] = shape_id
    out["pilot_priority_score"] = float(pd.to_numeric([row["priority_score"]], errors="coerce")[0])

    # Fixed baseline point for natural shape comparison.
    out["a1"] = 0.45
    out["a2"] = 0.0
    out["b1"] = 0.0
    out["b2"] = 0.0
    out["a3"] = 0.0
    out["b3"] = 0.0
    out["a4"] = 0.0
    out["b4"] = 0.0
    out["a5"] = 0.0
    out["b5"] = 0.0
    out["r0"] = 0.012

    for key, value in STAGE4_COMPAT_DEFAULTS.items():
        out[key] = value
    return out


def main() -> None:
    args = parse_args()
    pilot_csv = args.pilot_csv if args.pilot_csv.is_absolute() else ROOT / args.pilot_csv
    thesis_catalog = args.thesis_catalog if args.thesis_catalog.is_absolute() else ROOT / args.thesis_catalog
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pilot_df = pd.read_csv(pilot_csv)
    bands = load_target_bands(thesis_catalog)
    selected = select_candidates(pilot_df)

    rows: List[Dict[str, object]] = []
    rank = 1
    for _, row in selected.iterrows():
        for band in bands:
            rows.append(build_manifest_row(row, band, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "snake_based_archetype_targetband_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    selected.to_csv(
        out_dir / "snake_based_archetype_targetband_representatives_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "pilot_csv": str(pilot_csv),
        "representative_shape_count": int(len(selected)),
        "top_per_type": TOP_PER_TYPE,
        "target_band_count": int(len(bands)),
        "manifest_rows": int(len(manifest)),
        "target_bands": [str(b["target_band_tag"]) for b in bands],
        "priority_counts": selected["priority_archetype"].value_counts().to_dict(),
    }
    (out_dir / "snake_based_archetype_targetband_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] snake-based archetype target-band manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[REPRESENTATIVES] {len(selected)} shapes")
    print(f"[ROWS] {len(manifest)}")


if __name__ == "__main__":
    main()
