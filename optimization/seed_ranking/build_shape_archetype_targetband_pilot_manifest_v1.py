from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_targetband_param_v1.tools.build_canonical_local_robustness_manifest_v1 import (  # noqa: E402
    STAGE4_COMPAT_DEFAULTS,
)


DEFAULT_STAGE1_RESULTS = (
    ROOT / "data" / "comsol_batch" / "stage1_shape_archetype_pilot_v1" / "stage1_screening_results.csv"
)
DEFAULT_PILOT_CATALOG = (
    ROOT / "data" / "analysis" / "shape_archetype_pilot_v1" / "shape_archetype_pilot_catalog_v1.csv"
)
DEFAULT_THESIS_CATALOG = ROOT / "prediction_targetband_param_v1" / "configs" / "thesis_band_catalog_v2.json"
DEFAULT_OUT_DIR = (
    ROOT / "data" / "ml_runs" / "shape_archetype_targetband_pilot_v1" / "validation_manifest_v1"
)

TARGET_BANDS = ["band200_240", "band220_260", "band240_280"]
ARCHETYPE_TITLE = {
    "pas": "asym",
    "pne": "neck",
    "pbi": "bilobe",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a target-band pilot manifest from hand-made archetype shapes."
    )
    parser.add_argument("--stage1-results", type=Path, default=DEFAULT_STAGE1_RESULTS)
    parser.add_argument("--pilot-catalog", type=Path, default=DEFAULT_PILOT_CATALOG)
    parser.add_argument("--thesis-catalog", type=Path, default=DEFAULT_THESIS_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_target_bands(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bands = [band for band in payload.get("bands", []) if str(band.get("target_band_tag")) in TARGET_BANDS]
    if len(bands) != len(TARGET_BANDS):
        raise RuntimeError(f"Expected target bands {TARGET_BANDS}, found {[b.get('target_band_tag') for b in bands]}")
    return bands


def parse_shape_family_tokens(shape_id: str) -> Dict[str, str]:
    family = str(shape_id).split("_", 1)[0]
    prefix = family[:3]
    seed_suffix = family[3:]
    seed_family = f"ep{seed_suffix}"
    if prefix not in ARCHETYPE_TITLE:
        raise RuntimeError(f"Unsupported pilot family prefix in shape_id={shape_id}")
    return {
        "shape_family": family,
        "archetype_prefix": prefix,
        "archetype_tag": ARCHETYPE_TITLE[prefix],
        "seed_family": seed_family,
    }


def select_representatives(stage1_df: pd.DataFrame, pilot_catalog: pd.DataFrame) -> pd.DataFrame:
    work = stage1_df.copy()
    parsed = work["shape_id"].astype(str).map(parse_shape_family_tokens).apply(pd.Series)
    work = pd.concat([work, parsed], axis=1)
    work["gap_gain_Hz_num"] = pd.to_numeric(work["gap_gain_Hz"], errors="coerce").fillna(-1e18)
    work["gap_target_Hz_num"] = pd.to_numeric(work["gap_target_Hz"], errors="coerce").fillna(-1e18)

    keep_cols = ["shape_id", "shape_family", "archetype_tag", "seed_family"]
    meta = pilot_catalog[keep_cols].drop_duplicates()
    work = work.merge(meta, on=["shape_id", "shape_family", "archetype_tag", "seed_family"], how="left")

    reps = (
        work.sort_values(
            ["seed_family", "archetype_tag", "gap_gain_Hz_num", "gap_target_Hz_num", "shape_id"],
            ascending=[True, True, False, False, True],
        )
        .groupby(["seed_family", "archetype_tag"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    return reps


def build_manifest_row(
    row: pd.Series,
    band: Dict[str, object],
    rank: int,
) -> Dict[str, object]:
    shape_id = str(row["shape_id"])
    shape_family = str(row["shape_family"])
    archetype_tag = str(row["archetype_tag"])
    seed_family = str(row["seed_family"])
    band_tag = str(band["target_band_tag"])
    band_low = float(band["band_low_Hz"])
    band_high = float(band["band_high_Hz"])
    point_id = "pilot_center_fixed_v1"

    out: Dict[str, object] = row.to_dict()
    out["validation_id"] = f"{band_tag}__{shape_family}__center"
    out["selection_source"] = "shape_archetype_targetband_pilot_v1"
    out["selection_label"] = f"{band_tag}__{archetype_tag}__pilot"
    out["rank_within_source"] = rank
    out["target_band_tag"] = band_tag
    out["target_band_low_Hz"] = band_low
    out["target_band_high_Hz"] = band_high
    out["target_band_center_Hz"] = 0.5 * (band_low + band_high)
    out["target_band_width_Hz"] = band_high - band_low
    out["selection_priority"] = rank
    out["pool_arm"] = "shape_archetype_targetband_pilot"
    out["point_strategy"] = "pilot_center_only"
    out["target_rule"] = "shape_archetype_targetband_pilot_v1"
    out["step_window"] = "pilot_center"
    out["seed_shape_id"] = shape_id
    out["seed_family"] = seed_family
    out["seed_tier"] = "pilot_archetype_representative"
    out["seed_source"] = "stage1_shape_archetype_pilot_v1"
    out["is_seed_shape"] = True
    out["step_num"] = pd.NA
    out["step_offset"] = pd.NA
    out["step_distance"] = pd.NA
    out["family_prior_source"] = "shape_archetype_pilot_v1"
    out["seed_prior_source"] = "shape_archetype_pilot_v1"
    out["preferred_direction"] = ""
    out["allowed_offsets"] = ""
    out["candidate_id"] = shape_id
    out["main_id"] = point_id
    out["point_id"] = point_id
    out["shape_role"] = "pilot_archetype"
    out["sample_id"] = str(row["sample_id"])
    out["stage1_reference_sample_id"] = str(row["sample_id"])
    out["stage1_reference_fourier_id"] = str(row["fourier_id"])
    out["stage1_reference_gap_Hz"] = float(pd.to_numeric([row["gap_target_Hz"]], errors="coerce")[0])
    out["stage1_reference_gap_gain_Hz"] = float(pd.to_numeric([row["gap_gain_Hz"]], errors="coerce")[0])
    out["stage1_reference_contact_length"] = float(pd.to_numeric([row["contact_length"]], errors="coerce")[0])
    out["stage1_reference_candidate_tier"] = str(row.get("candidate_tier", ""))
    out["v5_reference_validation_id"] = ""
    out["v5_reference_gain_Hz"] = pd.NA
    out["pilot_archetype_tag"] = archetype_tag
    out["pilot_seed_family"] = seed_family
    out["pilot_origin_shape_id"] = shape_id

    for field in ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]:
        raw = row[field] if field in row.index else 0.0
        out[field] = float(pd.to_numeric([raw], errors="coerce")[0])

    for key, value in STAGE4_COMPAT_DEFAULTS.items():
        out[key] = value
    return out


def main() -> None:
    args = parse_args()
    stage1_results = args.stage1_results if args.stage1_results.is_absolute() else ROOT / args.stage1_results
    pilot_catalog_path = args.pilot_catalog if args.pilot_catalog.is_absolute() else ROOT / args.pilot_catalog
    thesis_catalog = args.thesis_catalog if args.thesis_catalog.is_absolute() else ROOT / args.thesis_catalog
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    stage1_df = pd.read_csv(stage1_results)
    pilot_catalog = pd.read_csv(pilot_catalog_path)
    if "candidate_tier" not in stage1_df.columns:
        stage1_df["candidate_tier"] = ""
    reps = select_representatives(stage1_df, pilot_catalog)
    bands = load_target_bands(thesis_catalog)

    rows: List[Dict[str, object]] = []
    rank = 1
    for _, rep in reps.iterrows():
        for band in bands:
            rows.append(build_manifest_row(rep, band, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "shape_archetype_targetband_pilot_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    rep_cols = [
        "shape_id",
        "shape_family",
        "archetype_tag",
        "seed_family",
        "sample_id",
        "gap_target_Hz",
        "gap_gain_Hz",
        "contact_length",
        "n_domains",
        "candidate_tier",
    ]
    reps[rep_cols].to_csv(
        out_dir / "shape_archetype_targetband_pilot_representatives_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "stage1_results": str(stage1_results),
        "pilot_catalog": str(pilot_catalog_path),
        "representative_shape_count": int(len(reps)),
        "target_band_count": int(len(bands)),
        "manifest_rows": int(len(manifest)),
        "selection_rule": "best stage1 gap_gain_Hz per seed_family x archetype_tag",
        "target_bands": [str(b["target_band_tag"]) for b in bands],
        "representatives": reps[rep_cols].to_dict(orient="records"),
    }
    (out_dir / "shape_archetype_targetband_pilot_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] shape archetype target-band pilot manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[REPRESENTATIVES] {len(reps)} shapes")
    print(f"[ROWS] {len(manifest)}")


if __name__ == "__main__":
    main()
