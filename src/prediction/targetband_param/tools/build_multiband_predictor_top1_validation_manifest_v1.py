from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]

BANDS = [
    ("band140_180", "140-180 Hz"),
    ("band160_200", "160-200 Hz"),
    ("band180_220", "180-220 Hz"),
    ("band200_240", "200-240 Hz"),
    ("band220_260", "220-260 Hz"),
    ("band240_280", "240-280 Hz"),
]

SOURCE_DIR = ROOT / "data" / "ml_runs" / "targetband_seed_scoring_v10_multiband_neighborhood_v1"
OUT_DIR = ROOT / "data" / "ml_runs" / "targetband_multiband_predictor_top1_v1" / "validation_manifest_v1"
CONTRACT_PATH = ROOT / "shared" / "contracts" / "stage4_validation_manifest_contract_v1.json"


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


def build_row(band_tag: str, band_label: str, rank: int, source: pd.Series) -> dict:
    row = source.to_dict()
    row["validation_id"] = f"mbpred{rank:03d}"
    row["selection_source"] = "predictor_top1_multiband_v10_v1"
    row["selection_label"] = f"predictor_top1_{band_label.replace(' ', '')}"
    row["rank_within_source"] = rank
    row["rank_cascade"] = float("nan")
    row["rank_surrogate"] = float("nan")
    row["sample_id"] = str(source["sample_id"])
    row["candidate_id"] = f"mbpred_{band_tag}_top1"
    row["target_band_tag"] = band_tag

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
    rows = []

    for rank, (band_tag, band_label) in enumerate(BANDS, start=1):
        top_path = SOURCE_DIR / band_tag / "targetband_seed_top_candidates.csv"
        if not top_path.is_file():
            raise FileNotFoundError(top_path)
        top = pd.read_csv(top_path)
        for col in ["target_gap_overlap_pred_Hz", "targetband_score", "target_open_prob"]:
            if col in top.columns:
                top[col] = pd.to_numeric(top[col], errors="coerce")
        top = top.sort_values(
            ["target_gap_overlap_pred_Hz", "targetband_score", "target_open_prob"],
            ascending=False,
        )
        rows.append(build_row(band_tag, band_label, rank, top.iloc[0]))

    manifest = pd.DataFrame(rows)
    for col in ordered_columns:
        if col not in manifest.columns:
            manifest[col] = ""
    manifest = manifest[ordered_columns]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "targetband_multiband_predictor_top1_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "source_dir": str(SOURCE_DIR),
        "manifest_rows": int(len(manifest)),
        "selection": "top-1 candidate per thesis target band, sorted by predicted target overlap",
        "bands": [{"band_tag": tag, "band_label": label} for tag, label in BANDS],
        "manifest_csv": str(manifest_path),
    }
    (OUT_DIR / "targetband_multiband_predictor_top1_manifest_summary_v1.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
