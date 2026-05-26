from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]

BUDGETS = [100, 200, 400, 800]
TARGET_BANDS = ["band180_220", "band200_240", "band220_260", "band240_280"]
LINES = {
    "band_catalog_real_ga_v1": {
        "history_csv": ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_catalog_ga_v1" / "ga_history_v1.csv",
        "line_role": "old band-catalog real GA baseline",
    },
    "band_supplement_ga_v1": {
        "history_csv": ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_ga_v1" / "ga_history_v1.csv",
        "line_role": "old conservative supplement baseline",
    },
    "band_supplement_exploratory_v2": {
        "history_csv": ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_history_v1.csv",
        "line_role": "predictor-guided / shape-aware / exploratory mainline",
    },
}


def load_history(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    df["individual_index"] = pd.to_numeric(df["individual_index"], errors="coerce")
    df["_eval_order"] = range(1, len(df) + 1)
    return df


def summarize_budget_slice(df: pd.DataFrame, line_id: str, line_role: str, budget: int, band_tag: str) -> dict:
    cover_col = f"{band_tag}_cover_ratio"
    overlap_col = f"{band_tag}_overlap_Hz"
    is_open_col = f"{band_tag}_is_open"

    sub = df.iloc[: min(budget, len(df))].copy()
    if sub.empty:
        return {
            "line_id": line_id,
            "line_role": line_role,
            "target_band_tag": band_tag,
            "budget_evaluations": budget,
            "evaluated_count": 0,
            "solve_success_count": 0,
            "open_hit_count": 0,
            "strong_hit_count": 0,
            "best_cover_ratio": 0.0,
            "best_overlap_Hz": 0.0,
            "best_shape_id": None,
            "best_shape_family": None,
            "budget_open_rate": 0.0,
            "budget_strong_rate": 0.0,
        }

    solve_success = pd.to_numeric(sub["solve_success"], errors="coerce").fillna(0).astype(int)
    if cover_col in sub.columns:
        cover = pd.to_numeric(sub[cover_col], errors="coerce").fillna(0.0)
    else:
        cover = pd.Series(0.0, index=sub.index)
    if overlap_col in sub.columns:
        overlap = pd.to_numeric(sub[overlap_col], errors="coerce").fillna(0.0)
    else:
        overlap = pd.Series(0.0, index=sub.index)
    if is_open_col in sub.columns:
        is_open = pd.to_numeric(sub[is_open_col], errors="coerce").fillna(0).astype(int)
    else:
        is_open = pd.Series(0, index=sub.index, dtype=int)
    strong = (cover >= 0.5).astype(int)

    best_idx = cover.idxmax()
    best_row = sub.loc[best_idx]

    return {
        "line_id": line_id,
        "line_role": line_role,
        "target_band_tag": band_tag,
        "budget_evaluations": budget,
        "evaluated_count": int(len(sub)),
        "solve_success_count": int(solve_success.sum()),
        "open_hit_count": int(is_open.sum()),
        "strong_hit_count": int(strong.sum()),
        "best_cover_ratio": float(cover.max()),
        "best_overlap_Hz": float(overlap.loc[best_idx]),
        "best_shape_id": str(best_row["shape_id"]),
        "best_shape_family": str(best_row["shape_family"]),
        "budget_open_rate": float(is_open.mean()),
        "budget_strong_rate": float(strong.mean()),
    }


def build_summary() -> pd.DataFrame:
    rows: list[dict] = []
    for line_id, meta in LINES.items():
        history = load_history(meta["history_csv"])
        for budget in BUDGETS:
            for band_tag in TARGET_BANDS:
                rows.append(summarize_budget_slice(history, line_id, meta["line_role"], budget, band_tag))
    return pd.DataFrame(rows)


def build_best_line_table(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for band_tag in TARGET_BANDS:
        for budget in BUDGETS:
            sub = summary[(summary["target_band_tag"] == band_tag) & (summary["budget_evaluations"] == budget)].copy()
            sub = sub.sort_values(
                ["best_cover_ratio", "best_overlap_Hz", "strong_hit_count", "open_hit_count"],
                ascending=False,
            )
            best = sub.iloc[0]
            rows.append(
                {
                    "target_band_tag": band_tag,
                    "budget_evaluations": budget,
                    "best_line_id": best["line_id"],
                    "best_line_role": best["line_role"],
                    "best_cover_ratio": float(best["best_cover_ratio"]),
                    "best_overlap_Hz": float(best["best_overlap_Hz"]),
                    "best_shape_id": str(best["best_shape_id"]),
                    "best_shape_family": str(best["best_shape_family"]),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    out_dir = ROOT / "data" / "analysis" / "same_budget_baselines_v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = build_summary()
    summary.to_csv(out_dir / "same_budget_summary_v1.csv", index=False, encoding="utf-8-sig")

    best_lines = build_best_line_table(summary)
    best_lines.to_csv(out_dir / "same_budget_best_lines_v1.csv", index=False, encoding="utf-8-sig")

    info = {
        "budgets": BUDGETS,
        "target_bands": TARGET_BANDS,
        "included_lines": list(LINES.keys()),
        "excluded_lines": [
            "generic_dataset_prior_v8",
            "targetband_local_ga_v1_probe",
            "targetband_local_ga_v1_top6",
        ],
        "notes": [
            "Only real-search lines with sequential evaluation histories are included.",
            "Generic dataset prior and local validation subsets are excluded because they do not represent a chronological real-search budget trace.",
            "A strong hit is defined as target-band cover ratio >= 0.5 within the sliced budget.",
        ],
    }
    (out_dir / "same_budget_info_v1.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
