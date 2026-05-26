from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SHORTLIST_CSV = (
    ROOT
    / "data"
    / "snake_based_bilobe_contact_aware_pilot_v2"
    / "analysis"
    / "bilobe_contact_aware_shortlist_v2.csv"
)
DEFAULT_THESIS_CATALOG = ROOT / "prediction_targetband_param_v1" / "configs" / "thesis_band_catalog_v2.json"
DEFAULT_OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "bilobe_contact_aware_targetband_pilot_v2"
    / "validation_manifest_v1"
)
TARGET_BANDS = ["band200_240", "band220_260", "band240_280"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build target-band manifest for bilobe-only contact-aware snake shortlist v2.")
    parser.add_argument("--shortlist-csv", type=Path, default=DEFAULT_SHORTLIST_CSV)
    parser.add_argument("--thesis-catalog", type=Path, default=DEFAULT_THESIS_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_target_bands(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bands = [band for band in payload.get("bands", []) if str(band.get("target_band_tag")) in TARGET_BANDS]
    return bands


def build_manifest_row(row: pd.Series, band: Dict[str, object], rank: int) -> Dict[str, object]:
    shape_id = str(row["shape_id"])
    band_tag = str(band["target_band_tag"])
    band_low = float(band["band_low_Hz"])
    band_high = float(band["band_high_Hz"])
    point_id = "bilobe_contact_aware_center_v2"

    out = row.to_dict()
    out["sample_id"] = f"stage4_validation_bilobe_contact_aware_targetband_pilot_v2_{band_tag}_{shape_id}"
    out["validation_id"] = f"{band_tag}__{shape_id}__center"
    out["selection_source"] = "bilobe_contact_aware_targetband_pilot_v2"
    out["selection_label"] = f"{band_tag}__bilobe__contact_aware_v2"
    out["rank_within_source"] = rank
    out["target_band_tag"] = band_tag
    out["target_band_low_Hz"] = band_low
    out["target_band_high_Hz"] = band_high
    out["target_band_center_Hz"] = 0.5 * (band_low + band_high)
    out["target_band_width_Hz"] = band_high - band_low
    out["selection_priority"] = rank
    out["pool_arm"] = "bilobe_contact_aware_targetband_pilot_v2"
    out["point_strategy"] = "bilobe_contact_aware_center_only_v2"
    out["target_rule"] = "bilobe_contact_aware_targetband_pilot_v2"
    out["step_window"] = "bilobe_contact_aware_center_v2"
    out["seed_shape_id"] = shape_id
    out["seed_family"] = str(shape_id).split("_", 1)[0]
    out["seed_tier"] = "bilobe_contact_aware_representative_v2"
    out["seed_source"] = "snake_based_bilobe_contact_aware_pilot_v2"
    out["is_seed_shape"] = True
    out["step_num"] = pd.NA
    out["step_offset"] = pd.NA
    out["step_distance"] = pd.NA
    out["family_prior_source"] = "snake_based_bilobe_contact_aware_pilot_v2"
    out["seed_prior_source"] = "snake_based_bilobe_contact_aware_pilot_v2"
    out["preferred_direction"] = ""
    out["allowed_offsets"] = ""
    out["candidate_id"] = shape_id
    out["main_id"] = point_id
    out["point_id"] = point_id
    out["shape_family"] = str(shape_id).split("_", 1)[0]
    out["shape_role"] = "snake_bilobe_contact_aware_pilot_v2"
    out["pilot_archetype_tag"] = "bilobe"
    out["pilot_origin_shape_id"] = shape_id
    out["pilot_priority_score"] = float(pd.to_numeric([row["contact_aware_bilobe_score_v2"]], errors="coerce")[0])
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
    out["contact_prob"] = 1.0
    out["positive_prob"] = 1.0
    out["surrogate_pred_gap34_gain_Hz"] = 0.0
    out["class_score"] = 1.0
    out["cascade_score"] = 1.0
    out["contact_gate"] = True
    out["positive_gate"] = True
    out["reg_positive_gate"] = True
    out["cascade_gate"] = True
    out["rank_cascade"] = pd.NA
    out["rank_surrogate"] = pd.NA
    return out


def main() -> None:
    args = parse_args()
    shortlist_df = pd.read_csv(args.shortlist_csv)
    bands = load_target_bands(args.thesis_catalog)
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    rank = 1
    for _, row in shortlist_df.iterrows():
        for band in bands:
            rows.append(build_manifest_row(row, band, rank))
            rank += 1
    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "bilobe_contact_aware_targetband_manifest_v2.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")
    shortlist_df.to_csv(out_dir / "bilobe_contact_aware_targetband_representatives_v2.csv", index=False, encoding="utf-8-sig")
    summary = {
        "shortlist_csv": str(args.shortlist_csv),
        "representative_shape_count": int(len(shortlist_df)),
        "target_band_count": int(len(bands)),
        "manifest_rows": int(len(manifest)),
    }
    (out_dir / "bilobe_contact_aware_targetband_manifest_summary_v2.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[DONE] {manifest_path}")


if __name__ == "__main__":
    main()
