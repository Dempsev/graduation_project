from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]

SOURCE_CSV = (
    ROOT
    / "data"
    / "ml_runs"
    / "targetband_seed_scoring_v11_12gen_freeze_multiband_neighborhood_v1"
    / "band180_220"
    / "targetband_seed_top_candidates.csv"
)
OUT_DIR = (
    ROOT
    / "data"
    / "ml_runs"
    / "targetband180_220_predictor_top6_v11_12gen_freeze_v1"
    / "validation_manifest_v1"
)
CONTRACT_PATH = ROOT / "shared" / "contracts" / "stage4_validation_manifest_contract_v1.json"

TARGET_BAND_TAG = "band180_220"
TARGET_BAND_LABEL = "180-220 Hz"
TOTAL_K = 6
MAX_PER_SHAPE = 2


def first_present(row: pd.Series, names: list[str], default=None):
    for name in names:
        if name in row.index and pd.notna(row[name]):
            return row[name]
    return default


def normalize_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes"}


def select_diverse_topk(df: pd.DataFrame) -> pd.DataFrame:
    sort_cols = ["target_gap_overlap_pred_Hz", "targetband_score", "target_open_prob"]
    for col in sort_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    ranked = df.sort_values(sort_cols, ascending=False).reset_index(drop=True)

    selected = []
    shape_counts: dict[str, int] = {}
    for _, row in ranked.iterrows():
        shape_id = str(row["shape_id"])
        if shape_counts.get(shape_id, 0) >= MAX_PER_SHAPE:
            continue
        selected.append(row)
        shape_counts[shape_id] = shape_counts.get(shape_id, 0) + 1
        if len(selected) >= TOTAL_K:
            break

    if len(selected) < TOTAL_K:
        raise RuntimeError(f"Only selected {len(selected)} candidates, expected {TOTAL_K}")
    return pd.DataFrame(selected).reset_index(drop=True)


def build_row(rank: int, source: pd.Series) -> dict:
    row = source.to_dict()
    row["validation_id"] = f"tb180p6v11_{rank:03d}"
    row["selection_source"] = "predictor_top6_180_220_v11_12gen_freeze_v1"
    row["selection_label"] = f"predictor_top6_{TARGET_BAND_LABEL.replace(' ', '')}"
    row["rank_within_source"] = rank
    row["rank_cascade"] = float("nan")
    row["rank_surrogate"] = float("nan")
    row["sample_id"] = str(source["sample_id"])
    row["candidate_id"] = f"tb180p6v11_{rank:03d}_{source['shape_id']}"
    row["target_band_tag"] = TARGET_BAND_TAG

    row["positive_prob"] = first_present(source, ["target_open_prob", "positive_prob"], float("nan"))
    row["surrogate_pred_gap34_gain_Hz"] = first_present(source, ["target_gap_overlap_pred_Hz"], float("nan"))
    row["class_score"] = first_present(source, ["target_open_prob"], float("nan"))
    row["cascade_score"] = first_present(source, ["targetband_score"], float("nan"))
    row["positive_gate"] = normalize_bool(first_present(source, ["target_open_gate"], False))
    row["reg_positive_gate"] = normalize_bool(first_present(source, ["targetband_gate"], False))
    row["cascade_gate"] = normalize_bool(first_present(source, ["targetband_gate"], False))
    row["surrogate_objective_name"] = "target_gap_overlap_pred_Hz"
    row["surrogate_prediction_column"] = "target_gap_overlap_pred_Hz"
    row["surrogate_pred_objective_value"] = first_present(source, ["target_gap_overlap_pred_Hz"], float("nan"))
    return row


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    ordered_columns = contract["ordered_columns"]

    top = pd.read_csv(SOURCE_CSV)
    selected = select_diverse_topk(top)
    rows = [build_row(rank, row) for rank, (_, row) in enumerate(selected.iterrows(), start=1)]

    manifest = pd.DataFrame(rows)
    for col in ordered_columns:
        if col not in manifest.columns:
            manifest[col] = ""
    manifest = manifest[ordered_columns]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "targetband180_220_predictor_top6_v11_12gen_freeze_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    selected_path = OUT_DIR / "targetband180_220_predictor_top6_v11_12gen_freeze_selected_candidates_v1.csv"
    selected.to_csv(selected_path, index=False, encoding="utf-8-sig")

    summary = {
        "source_csv": str(SOURCE_CSV),
        "manifest_rows": int(len(manifest)),
        "target_band": TARGET_BAND_LABEL,
        "target_band_tag": TARGET_BAND_TAG,
        "selection": "Top-6 predicted candidates for 180-220 Hz with max two candidates per shape_id",
        "total_k": TOTAL_K,
        "max_per_shape": MAX_PER_SHAPE,
        "manifest_csv": str(manifest_path),
        "selected_candidates_csv": str(selected_path),
    }
    (OUT_DIR / "targetband180_220_predictor_top6_v11_12gen_freeze_manifest_summary_v1.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(manifest_path)
    print(selected[["shape_id", "point_id", "target_gap_overlap_pred_Hz", "targetband_score", "target_open_prob"]])


if __name__ == "__main__":
    main()
