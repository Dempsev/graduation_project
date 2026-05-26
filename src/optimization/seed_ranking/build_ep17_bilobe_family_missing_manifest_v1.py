from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SOURCE_MANIFEST = (
    ROOT
    / "data"
    / "ml_runs"
    / "ep17_bilobe_family_targetband_probe_v1"
    / "validation_manifest_v1"
    / "ep17_bilobe_family_targetband_manifest_v1.csv"
)
SOURCE_RESULTS = (
    ROOT
    / "data"
    / "comsol_batch"
    / "stage4_validation_ep17_bilobe_family_targetband_probe_v1"
    / "stage4_validation_results.csv"
)
SOURCE_CONTOURS = ROOT / "data" / "snake_based_archetype_expansion_pilot_v1" / "shape_contours"
FROZEN_DIR = ROOT / "data" / "snake_based_bilobe_contact_aware_pilot_v2" / "frozen_shape_contours"
OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "ep17_bilobe_family_targetband_missing_patch_v1"
    / "validation_manifest_v1"
)


def main() -> None:
    manifest = pd.read_csv(SOURCE_MANIFEST)
    results = pd.read_csv(SOURCE_RESULTS)
    missing = manifest.loc[~manifest["validation_id"].isin(results["validation_id"])].copy()

    # Also include rows that failed only because frozen CSV was missing.
    csv_missing_ids = results.loc[results["error_message"].fillna("").astype(str) == "csv_not_found", "validation_id"]
    if not csv_missing_ids.empty:
        missing = pd.concat([missing, manifest.loc[manifest["validation_id"].isin(csv_missing_ids)]], ignore_index=True)
        missing = missing.drop_duplicates(subset=["validation_id"]).reset_index(drop=True)

    # Ensure the missing family member contours are frozen before rerun.
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    for shape_id in missing["shape_id"].dropna().astype(str).unique():
        src = SOURCE_CONTOURS / f"{shape_id}.csv"
        dst = FROZEN_DIR / f"{shape_id}.csv"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "ep17_bilobe_family_missing_manifest_v1.csv"
    summary_path = OUT_DIR / "ep17_bilobe_family_missing_manifest_summary_v1.json"
    missing.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "missing_rows": int(len(missing)),
        "shape_ids": missing["shape_id"].dropna().astype(str).unique().tolist(),
        "target_bands": sorted(missing["target_band_tag"].dropna().astype(str).unique().tolist()),
        "frozen_shape_dir": str(FROZEN_DIR),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] {manifest_path}")


if __name__ == "__main__":
    main()
