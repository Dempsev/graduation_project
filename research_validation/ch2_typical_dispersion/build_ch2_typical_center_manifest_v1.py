"""Select distinct typical target-band centers for Chapter 2.6.

This reuses the current thesis COMSOL-in-loop GA histories, but keeps the
old local-perturbation plan: a1 +/- 0.01, a2 +/- 0.01, b2 +/- 0.01, r0 +/- 0.0008.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch2_typical_dispersion"
DATA_DIR = ROOT / "data" / "research_validation" / "ch2_typical_dispersion"

BANDS = [
    ("band180_220", 180.0, 220.0),
    ("band200_240", 200.0, 240.0),
    ("band220_260", 220.0, 260.0),
    ("band240_280", 240.0, 280.0),
]

PERTURB_PLAN = {
    "a1": 0.01,
    "a2": 0.01,
    "b2": 0.01,
    "r0": 0.0008,
}


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes"})


def load_ga_history() -> pd.DataFrame:
    frames = []
    for path in sorted((ROOT / "data" / "comsol_batch").glob("comsol_in_loop_thesis_*_overlap_ga_v1/ga_history_v1.csv")):
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        frame["source_history_csv"] = str(path)
        frame["source_run"] = path.parent.name
        frames.append(frame)
    if not frames:
        raise RuntimeError("No thesis GA history files were found.")
    df = pd.concat(frames, ignore_index=True, sort=False)
    for col in ["geometry_valid", "contact_valid", "solve_success"]:
        df[col] = as_bool(df[col]) if col in df.columns else False
    numeric_cols = [
        "active_target_cover_ratio",
        "active_target_overlap_Hz",
        "gap34_Hz",
        "gap34_rel",
        "gap34_lower_edge_Hz",
        "gap34_upper_edge_Hz",
        "a1",
        "a2",
        "b1",
        "b2",
        "a3",
        "b3",
        "a4",
        "b4",
        "a5",
        "b5",
        "r0",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def select_centers(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df["geometry_valid"] & df["contact_valid"] & df["solve_success"]].copy()
    selected = []
    used_shapes: set[str] = set()
    for band_tag, low, high in BANDS:
        sub = valid[valid["active_band_tag"].astype(str) == band_tag].copy()
        if sub.empty:
            raise RuntimeError(f"No valid rows found for {band_tag}.")
        sub = sub.sort_values(
            ["active_target_cover_ratio", "active_target_overlap_Hz", "gap34_Hz"],
            ascending=False,
        )
        chosen = None
        for _, row in sub.iterrows():
            shape_id = str(row["shape_id"])
            if shape_id not in used_shapes:
                chosen = row.copy()
                break
        if chosen is None:
            chosen = sub.iloc[0].copy()
        used_shapes.add(str(chosen["shape_id"]))
        chosen["case_id"] = f"{band_tag}_{str(chosen['shape_id']).replace('_step', '').split('_contour')[0]}"
        chosen["target_band_tag"] = band_tag
        chosen["target_band_low_Hz"] = low
        chosen["target_band_high_Hz"] = high
        selected.append(chosen)
    return pd.DataFrame(selected)


def build_manifest(centers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, center in centers.iterrows():
        base = center.to_dict()
        variants = [("center", "", 0.0)]
        for param, delta in PERTURB_PLAN.items():
            variants.append((f"{param}_plus", param, delta))
            variants.append((f"{param}_minus", param, -delta))
        for variant, param, delta in variants:
            row = {
                "case_id": base["case_id"],
                "variant": variant,
                "target_band_tag": base["target_band_tag"],
                "target_band_low_Hz": base["target_band_low_Hz"],
                "target_band_high_Hz": base["target_band_high_Hz"],
                "source_sample_id": base["sample_id"],
                "source_history_csv": base["source_history_csv"],
                "structure_id": base["shape_id"],
                "shape_id": base["shape_id"],
                "shape_family": base.get("shape_family", str(base["shape_id"]).split("_")[0]),
                "shape_file": str(ROOT / "data" / "shape_contours" / f"{base['shape_id']}.csv"),
                "main_id": base.get("main_id", "rf09"),
                "point_id": base.get("point_id", "rf09_h00_center"),
                "perturb_param": param,
                "perturb_direction": "center" if not param else ("plus" if delta > 0 else "minus"),
                "perturb_value": delta,
            }
            for name in ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]:
                row[name] = float(base.get(name, 0.0))
            if param:
                row[param] = row[param] + delta
            for name in [
                "active_target_cover_ratio",
                "active_target_overlap_Hz",
                "gap34_Hz",
                "gap34_rel",
                "gap34_lower_edge_Hz",
                "gap34_upper_edge_Hz",
            ]:
                row[f"center_{name}"] = float(base.get(name, float("nan")))
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = load_ga_history()
    centers = select_centers(history)
    manifest = build_manifest(centers)

    centers_csv = DATA_DIR / "ch2_typical_center_cases_v1.csv"
    manifest_csv = DATA_DIR / "ch2_typical_local_perturb_manifest_v1.csv"
    summary_json = DATA_DIR / "ch2_typical_manifest_summary_v1.json"
    centers.to_csv(centers_csv, index=False, encoding="utf-8-sig")
    manifest.to_csv(manifest_csv, index=False, encoding="utf-8-sig")

    summary = {
        "centers_csv": str(centers_csv),
        "manifest_csv": str(manifest_csv),
        "bands": BANDS,
        "perturb_plan": PERTURB_PLAN,
        "selection_policy": "top valid current thesis GA row per target band, with duplicate shape_id avoided when possible",
        "selected_cases": centers[
            [
                "case_id",
                "target_band_tag",
                "shape_id",
                "sample_id",
                "active_target_cover_ratio",
                "active_target_overlap_Hz",
                "gap34_lower_edge_Hz",
                "gap34_upper_edge_Hz",
            ]
        ].to_dict(orient="records"),
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
