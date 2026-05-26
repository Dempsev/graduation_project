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
    / "snake_based_bilobe_contact_aware_pilot_v1"
    / "analysis"
    / "bilobe_contact_aware_shortlist_v1.csv"
)
DEFAULT_THESIS_CATALOG = ROOT / "prediction_targetband_param_v1" / "configs" / "thesis_band_catalog_v2.json"
DEFAULT_OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "bilobe_contact_aware_targetband_pilot_v1"
    / "validation_manifest_v1"
)

TARGET_BANDS = ["band200_240", "band220_260", "band240_280"]
TOP_K = 8

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
    parser = argparse.ArgumentParser(description="Build target-band manifest for bilobe-only contact-aware snake shortlist.")
    parser.add_argument("--shortlist-csv", type=Path, default=DEFAULT_SHORTLIST_CSV)
    parser.add_argument("--thesis-catalog", type=Path, default=DEFAULT_THESIS_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    return parser.parse_args()


def load_target_bands(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bands = [band for band in payload.get("bands", []) if str(band.get("target_band_tag")) in TARGET_BANDS]
    if len(bands) != len(TARGET_BANDS):
        raise RuntimeError(f"Expected target bands {TARGET_BANDS}, found {[b.get('target_band_tag') for b in bands]}")
    return bands


def select_candidates(df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    work = df.copy()
    work["contact_aware_bilobe_score"] = pd.to_numeric(work["contact_aware_bilobe_score"], errors="coerce").fillna(-1e18)
    work["best_target_gap_cover_ratio"] = pd.to_numeric(work["best_target_gap_cover_ratio"], errors="coerce").fillna(0.0)
    work["bilobe_candidate_score"] = pd.to_numeric(work["bilobe_candidate_score"], errors="coerce").fillna(0.0)
    if "rejected" in work.columns:
        work = work.loc[~work["rejected"].astype(str).str.lower().eq("true")].copy()
    selected = (
        work.sort_values(
            ["contact_aware_bilobe_score", "best_target_gap_cover_ratio", "bilobe_candidate_score"],
            ascending=[False, False, False],
        )
        .head(top_k)
        .reset_index(drop=True)
    )
    return selected


def build_manifest_row(row: pd.Series, band: Dict[str, object], rank: int) -> Dict[str, object]:
    shape_id = str(row["shape_id"])
    band_tag = str(band["target_band_tag"])
    band_low = float(band["band_low_Hz"])
    band_high = float(band["band_high_Hz"])
    point_id = "bilobe_contact_aware_center_v1"

    out = row.to_dict()
    out["sample_id"] = f"stage4_validation_bilobe_contact_aware_targetband_pilot_v1_{band_tag}_{shape_id}"
    out["validation_id"] = f"{band_tag}__{shape_id}__center"
    out["selection_source"] = "bilobe_contact_aware_targetband_pilot_v1"
    out["selection_label"] = f"{band_tag}__bilobe__contact_aware"
    out["rank_within_source"] = rank
    out["target_band_tag"] = band_tag
    out["target_band_low_Hz"] = band_low
    out["target_band_high_Hz"] = band_high
    out["target_band_center_Hz"] = 0.5 * (band_low + band_high)
    out["target_band_width_Hz"] = band_high - band_low
    out["selection_priority"] = rank
    out["pool_arm"] = "bilobe_contact_aware_targetband_pilot"
    out["point_strategy"] = "bilobe_contact_aware_center_only"
    out["target_rule"] = "bilobe_contact_aware_targetband_pilot_v1"
    out["step_window"] = "bilobe_contact_aware_center"
    out["seed_shape_id"] = shape_id
    out["seed_family"] = str(shape_id).split("_", 1)[0]
    out["seed_tier"] = "bilobe_contact_aware_representative"
    out["seed_source"] = "snake_based_bilobe_contact_aware_pilot_v1"
    out["is_seed_shape"] = True
    out["step_num"] = pd.NA
    out["step_offset"] = pd.NA
    out["step_distance"] = pd.NA
    out["family_prior_source"] = "snake_based_bilobe_contact_aware_pilot_v1"
    out["seed_prior_source"] = "snake_based_bilobe_contact_aware_pilot_v1"
    out["preferred_direction"] = ""
    out["allowed_offsets"] = ""
    out["candidate_id"] = shape_id
    out["main_id"] = point_id
    out["point_id"] = point_id
    out["shape_family"] = str(shape_id).split("_", 1)[0]
    out["shape_role"] = "snake_bilobe_contact_aware_pilot"
    out["pilot_archetype_tag"] = "bilobe"
    out["pilot_origin_shape_id"] = shape_id
    out["pilot_priority_score"] = float(pd.to_numeric([row["contact_aware_bilobe_score"]], errors="coerce")[0])

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
    shortlist_csv = args.shortlist_csv if args.shortlist_csv.is_absolute() else ROOT / args.shortlist_csv
    thesis_catalog = args.thesis_catalog if args.thesis_catalog.is_absolute() else ROOT / args.thesis_catalog
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    shortlist_df = pd.read_csv(shortlist_csv)
    bands = load_target_bands(thesis_catalog)
    selected = select_candidates(shortlist_df, args.top_k)

    rows: List[Dict[str, object]] = []
    rank = 1
    for _, row in selected.iterrows():
        for band in bands:
            rows.append(build_manifest_row(row, band, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "bilobe_contact_aware_targetband_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    selected.to_csv(
        out_dir / "bilobe_contact_aware_targetband_representatives_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "shortlist_csv": str(shortlist_csv),
        "representative_shape_count": int(len(selected)),
        "top_k": int(args.top_k),
        "target_band_count": int(len(bands)),
        "manifest_rows": int(len(manifest)),
        "target_bands": [str(b["target_band_tag"]) for b in bands],
    }
    (out_dir / "bilobe_contact_aware_targetband_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] bilobe-only contact-aware target-band manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[REPRESENTATIVES] {len(selected)} shapes")
    print(f"[ROWS] {len(manifest)}")


if __name__ == "__main__":
    main()
