from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SHORTLIST_CSV = (
    ROOT
    / "data"
    / "snake_based_bilobe_contact_aware_pilot_v2"
    / "analysis"
    / "bilobe_contact_aware_catalog_v2.csv"
)
THESIS_CATALOG = ROOT / "prediction_targetband_param_v1" / "configs" / "thesis_band_catalog_v2.json"
FROZEN_DIR = ROOT / "data" / "snake_based_bilobe_contact_aware_pilot_v2" / "frozen_shape_contours"
OUT_DIR = ROOT / "data" / "ml_runs" / "ep17_bilobe_family_targetband_probe_v1" / "validation_manifest_v1"

TARGET_BANDS = ["band200_240", "band220_260", "band240_280"]
EP17_SHAPES = [
    "ep17_step156_contour_xy",
    "ep17_step180_contour_xy",
    "ep17_step129_contour_xy",
    "ep17_step72_contour_xy",
]


def load_target_bands(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [band for band in payload.get("bands", []) if str(band.get("target_band_tag")) in TARGET_BANDS]


def build_manifest_row(row: pd.Series, band: Dict[str, object], rank: int) -> Dict[str, object]:
    shape_id = str(row["shape_id"])
    band_tag = str(band["target_band_tag"])
    band_low = float(band["band_low_Hz"])
    band_high = float(band["band_high_Hz"])
    point_id = "ep17_bilobe_family_center_v1"

    out = row.to_dict()
    out["sample_id"] = f"stage4_validation_ep17_bilobe_family_targetband_probe_v1_{band_tag}_{shape_id}"
    out["validation_id"] = f"{band_tag}__{shape_id}__center"
    out["selection_source"] = "ep17_bilobe_family_targetband_probe_v1"
    out["selection_label"] = f"{band_tag}__ep17_bilobe_family"
    out["rank_within_source"] = rank
    out["target_band_tag"] = band_tag
    out["target_band_low_Hz"] = band_low
    out["target_band_high_Hz"] = band_high
    out["target_band_center_Hz"] = 0.5 * (band_low + band_high)
    out["target_band_width_Hz"] = band_high - band_low
    out["selection_priority"] = rank
    out["pool_arm"] = "ep17_bilobe_family_targetband_probe"
    out["point_strategy"] = "ep17_bilobe_family_center_only"
    out["target_rule"] = "ep17_bilobe_family_targetband_probe_v1"
    out["step_window"] = "ep17_bilobe_family_center"
    out["seed_shape_id"] = shape_id
    out["seed_family"] = "ep17"
    out["seed_tier"] = "ep17_bilobe_family_member"
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
    out["shape_family"] = "ep17"
    out["shape_role"] = "ep17_bilobe_family_probe"
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
    df = pd.read_csv(SHORTLIST_CSV)
    df = df.loc[df["shape_id"].isin(EP17_SHAPES)].copy()
    bands = load_target_bands(THESIS_CATALOG)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    rank = 1
    for shape_id in EP17_SHAPES:
        row = df.loc[df["shape_id"] == shape_id]
        if row.empty:
            continue
        series = row.iloc[0]
        for band in bands:
            rows.append(build_manifest_row(series, band, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = OUT_DIR / "ep17_bilobe_family_targetband_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")
    df.to_csv(OUT_DIR / "ep17_bilobe_family_representatives_v1.csv", index=False, encoding="utf-8-sig")
    summary = {
        "shape_count": int(len(df)),
        "target_band_count": int(len(bands)),
        "manifest_rows": int(len(manifest)),
        "frozen_shape_dir": str(FROZEN_DIR),
        "shape_ids": df["shape_id"].astype(str).tolist(),
    }
    (OUT_DIR / "ep17_bilobe_family_targetband_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[DONE] {manifest_path}")


if __name__ == "__main__":
    main()
