from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SOURCE_MANIFEST = (
    ROOT
    / "data"
    / "ml_runs"
    / "snake_based_archetype_targetband_pilot_v1"
    / "validation_manifest_v1"
    / "snake_based_archetype_targetband_manifest_v1.csv"
)
SOURCE_RESULTS = (
    ROOT
    / "data"
    / "comsol_batch"
    / "stage4_validation_snake_based_archetype_targetband_pilot_v1"
    / "stage4_validation_results.csv"
)
OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "snake_based_archetype_targetband_missing_patch_v1"
    / "validation_manifest_v1"
)
OUT_MANIFEST = OUT_DIR / "snake_based_archetype_targetband_missing_manifest_v1.csv"
OUT_SUMMARY = OUT_DIR / "snake_based_archetype_targetband_missing_manifest_summary_v1.json"


def main() -> None:
    manifest = pd.read_csv(SOURCE_MANIFEST)
    results = pd.read_csv(SOURCE_RESULTS)

    missing = manifest.loc[~manifest["validation_id"].isin(results["validation_id"])].copy()
    missing = missing.sort_values(["rank_within_source", "validation_id"]).reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing.to_csv(OUT_MANIFEST, index=False, encoding="utf-8-sig")

    summary = {
        "source_manifest_csv": str(SOURCE_MANIFEST),
        "source_results_csv": str(SOURCE_RESULTS),
        "out_manifest_csv": str(OUT_MANIFEST),
        "missing_rows": int(len(missing)),
        "target_bands": sorted(missing["target_band_tag"].dropna().astype(str).unique().tolist()),
        "pilot_archetype_counts": {
            str(k): int(v) for k, v in missing["pilot_archetype_tag"].value_counts().sort_index().items()
        },
        "shape_ids": missing["shape_id"].dropna().astype(str).unique().tolist(),
        "validation_ids": missing["validation_id"].dropna().astype(str).tolist(),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[DONE] wrote missing-only manifest: {OUT_MANIFEST}")
    print(f"[ROWS] {len(missing)}")


if __name__ == "__main__":
    main()
