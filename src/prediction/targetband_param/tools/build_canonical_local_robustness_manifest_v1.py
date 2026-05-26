from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]

DEFAULT_HISTORY_CSV = (
    ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_best_candidates_v1.csv"
)
DEFAULT_OUT_DIR = ROOT / "data" / "ml_runs" / "canonical_inverse_design_local_robustness_v1" / "validation_manifest_v1"


CANONICAL_CASES = [
    {
        "case_id": "band200_240_ep193",
        "target_band_tag": "band200_240",
        "target_band_low_Hz": 200.0,
        "target_band_high_Hz": 240.0,
        "shape_id": "ep193_step51_contour_xy",
        "archive_band_tag": "band200_240",
        "selection_mode": "max_fitness",
        "expected_shape_family": "ep193",
    },
    {
        "case_id": "band220_260_ep253",
        "target_band_tag": "band220_260",
        "target_band_low_Hz": 220.0,
        "target_band_high_Hz": 260.0,
        "shape_id": "ep253_step54_contour_xy",
        "archive_band_tag": "band220_260",
        "selection_mode": "max_fitness",
        "expected_shape_family": "ep253",
    },
    {
        "case_id": "band240_280_ep253",
        "target_band_tag": "band240_280",
        "target_band_low_Hz": 240.0,
        "target_band_high_Hz": 280.0,
        "shape_id": "ep253_step54_contour_xy",
        "archive_band_tag": "band240_280",
        "selection_mode": "max_archive_cover",
        "expected_shape_family": "ep253",
    },
    {
        "case_id": "band180_220_ep248",
        "target_band_tag": "band180_220",
        "target_band_low_Hz": 180.0,
        "target_band_high_Hz": 220.0,
        "shape_id": "ep248_step27_contour_xy",
        "archive_band_tag": "band180_220",
        "selection_mode": "max_archive_cover",
        "expected_shape_family": "ep248",
    },
]


PERTURB_PLAN = {
    "a1": 0.01,
    "a2": 0.01,
    "b2": 0.01,
    "r0": 0.0008,
}


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
    parser = argparse.ArgumentParser(description="Build a local-neighborhood robustness manifest around canonical target-band cases.")
    parser.add_argument("--history-csv", type=Path, default=DEFAULT_HISTORY_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def select_center_rows(history: pd.DataFrame) -> list[dict]:
    selected: list[dict] = []
    for case in CANONICAL_CASES:
        sub = history[
            (history["shape_id"].astype(str) == case["shape_id"])
            & (history["archive_band_tag"].astype(str) == case["archive_band_tag"])
        ].copy()
        if sub.empty:
            raise RuntimeError(f"No matching history rows found for canonical case {case['case_id']}")
        if case["selection_mode"] == "max_fitness":
            sub["fitness_num"] = pd.to_numeric(sub["fitness"], errors="coerce").fillna(-1e18)
            chosen = sub.sort_values(["fitness_num", "archive_cover_ratio", "archive_overlap_Hz"], ascending=False).iloc[0]
        else:
            sub["archive_cover_ratio_num"] = pd.to_numeric(sub["archive_cover_ratio"], errors="coerce").fillna(-1e18)
            sub["archive_overlap_Hz_num"] = pd.to_numeric(sub["archive_overlap_Hz"], errors="coerce").fillna(-1e18)
            chosen = sub.sort_values(["archive_cover_ratio_num", "archive_overlap_Hz_num", "fitness"], ascending=False).iloc[0]
        selected.append({"case": case, "row": chosen})
    return selected


def perturb_specs(case_id: str) -> Iterable[tuple[str, dict[str, float]]]:
    yield "center", {}
    for field, delta in PERTURB_PLAN.items():
        yield f"{field}_plus", {field: delta}
        yield f"{field}_minus", {field: -delta}


def numeric(v: object) -> float:
    return float(pd.to_numeric([v], errors="coerce")[0])


def build_row(center: pd.Series, case: dict, variant_label: str, deltas: dict[str, float], rank: int) -> dict:
    out = center.to_dict()
    for field in ["a1", "a2", "b1", "b2", "r0", "a3", "b3", "a4", "b4", "a5", "b5"]:
        out[field] = numeric(out[field])
    for field, delta in deltas.items():
        out[field] = float(out[field]) + float(delta)

    out["validation_id"] = f"{case['case_id']}__{variant_label}"
    out["selection_source"] = "canonical_local_robustness_v1"
    out["selection_label"] = f"{case['case_id']}__local_neighborhood"
    out["rank_within_source"] = rank
    out["canonical_case_id"] = case["case_id"]
    out["canonical_variant"] = variant_label
    out["target_band_tag"] = case["target_band_tag"]
    out["target_band_low_Hz"] = case["target_band_low_Hz"]
    out["target_band_high_Hz"] = case["target_band_high_Hz"]
    out["target_band_center_Hz"] = 0.5 * (case["target_band_low_Hz"] + case["target_band_high_Hz"])
    out["target_band_width_Hz"] = case["target_band_high_Hz"] - case["target_band_low_Hz"]
    out["selection_priority"] = rank
    out["pool_arm"] = "canonical_local_robustness"
    out["point_strategy"] = "canonical_local_neighborhood"
    out["target_rule"] = "canonical_local_robustness"
    out["step_window"] = "local_robustness"
    out["seed_shape_id"] = out["shape_id"]
    out["seed_family"] = out["shape_family"]
    out["seed_tier"] = "canonical_case_center"
    out["seed_source"] = "band_supplement_exploratory_v2"
    out["is_seed_shape"] = True
    out["step_num"] = pd.NA
    out["step_offset"] = pd.NA
    out["step_distance"] = pd.NA
    out["family_prior_source"] = "canonical_case_freeze_v1"
    out["seed_prior_source"] = "canonical_case_freeze_v1"
    out["preferred_direction"] = ""
    out["allowed_offsets"] = ""
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
    history_csv = args.history_csv if args.history_csv.is_absolute() else ROOT / args.history_csv
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    history = pd.read_csv(history_csv)
    selected = select_center_rows(history)

    rows: list[dict] = []
    center_summary: list[dict] = []
    rank = 1
    for item in selected:
        case = item["case"]
        row = item["row"]
        center_summary.append(
            {
                "canonical_case_id": case["case_id"],
                "target_band_tag": case["target_band_tag"],
                "shape_id": row["shape_id"],
                "shape_family": row["shape_family"],
                "sample_id": row["sample_id"],
                "generation": int(numeric(row["generation"])),
                "individual_index": int(numeric(row["individual_index"])),
                "archive_cover_ratio": float(numeric(row["archive_cover_ratio"])),
                "archive_overlap_Hz": float(numeric(row["archive_overlap_Hz"])),
                "gap34_lower_edge_Hz": float(numeric(row["gap34_lower_edge_Hz"])),
                "gap34_upper_edge_Hz": float(numeric(row["gap34_upper_edge_Hz"])),
                "a1": float(numeric(row["a1"])),
                "a2": float(numeric(row["a2"])),
                "b2": float(numeric(row["b2"])),
                "r0": float(numeric(row["r0"])),
            }
        )
        for variant_label, deltas in perturb_specs(case["case_id"]):
            rows.append(build_row(row, case, variant_label, deltas, rank))
            rank += 1

    manifest = pd.DataFrame(rows)
    manifest_path = out_dir / "canonical_local_robustness_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    center_df = pd.DataFrame(center_summary)
    center_path = out_dir / "canonical_local_robustness_centers_v1.csv"
    center_df.to_csv(center_path, index=False, encoding="utf-8-sig")

    summary = {
        "history_csv": str(history_csv),
        "manifest_rows": int(len(manifest)),
        "canonical_case_count": int(len(center_df)),
        "variants_per_case": int(len(PERTURB_PLAN) * 2 + 1),
        "perturb_plan": PERTURB_PLAN,
        "cases": center_summary,
    }
    (out_dir / "canonical_local_robustness_manifest_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] canonical local robustness manifest built")
    print(f"[OUT] {manifest_path}")
    print(f"[CASES] {len(center_df)} cases, {len(manifest)} rows")


if __name__ == "__main__":
    main()
