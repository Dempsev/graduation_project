from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_CATALOG = (
    ROOT / "data" / "snake_based_archetype_expansion_pilot_v1" / "analysis" / "snake_based_archetype_pilot_catalog_v1.csv"
)
DEFAULT_SOURCE_STAGE4_SUMMARY = (
    ROOT / "data" / "analysis" / "snake_based_archetype_targetband_pilot_v1" / "snake_based_archetype_targetband_pilot_shape_summary_v1.csv"
)
DEFAULT_SOURCE_BCATP_SUMMARY = (
    ROOT / "data" / "analysis" / "bilobe_contact_aware_targetband_pilot_v1" / "snake_based_archetype_targetband_pilot_shape_summary_v1.csv"
)
DEFAULT_OUT_ROOT = ROOT / "data" / "snake_based_bilobe_contact_aware_pilot_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a stricter, frozen bilobe-only contact-aware snake shortlist.")
    parser.add_argument("--source-catalog", type=Path, default=DEFAULT_SOURCE_CATALOG)
    parser.add_argument("--source-stage4-shape-summary", type=Path, default=DEFAULT_SOURCE_STAGE4_SUMMARY)
    parser.add_argument("--source-bcatp-shape-summary", type=Path, default=DEFAULT_SOURCE_BCATP_SUMMARY)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--top-k", type=int, default=6)
    return parser.parse_args()


def load_priors(*paths: Path) -> pd.DataFrame:
    frames = []
    for path in paths:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        cols = [c for c in ["shape_id", "contact_valid", "solve_success", "target_gap_cover_ratio", "best_band_tag", "best_band_role"] if c in df.columns]
        if not cols:
            continue
        df = df[cols].copy()
        if "contact_valid" not in df.columns:
            df["contact_valid"] = 0
        if "solve_success" not in df.columns:
            df["solve_success"] = 0
        if "target_gap_cover_ratio" not in df.columns:
            df["target_gap_cover_ratio"] = 0.0
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["shape_id", "any_contact_valid", "any_solve_success", "best_target_gap_cover_ratio"])
    all_df = pd.concat(frames, ignore_index=True)
    return (
        all_df.groupby("shape_id", as_index=False)
        .agg(
            any_contact_valid=("contact_valid", "max"),
            any_solve_success=("solve_success", "max"),
            best_target_gap_cover_ratio=("target_gap_cover_ratio", "max"),
            best_band_tag=("best_band_tag", "first") if "best_band_tag" in all_df.columns else ("shape_id", "first"),
            best_band_role=("best_band_role", "first") if "best_band_role" in all_df.columns else ("shape_id", "first"),
        )
    )


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["min_dim"] = out[["width", "height"]].min(axis=1)
    out["history_contact"] = out["any_contact_valid"].fillna(0).astype(int)
    out["history_solve"] = out["any_solve_success"].fillna(0).astype(int)
    out["history_cover"] = out["best_target_gap_cover_ratio"].fillna(0.0).astype(float)

    out["reject_tiny"] = (out["min_dim"] < 0.0030) | (out["area"] < 1.20e-05)
    out["reject_sliver"] = (out["aspect_ratio"] < 0.50) | (out["aspect_ratio"] > 2.05)
    out["reject_loose"] = out["compactness"] < 0.72
    out["reject_fragile"] = out["neck_score"] > 1.65
    out["reject_no_history"] = False
    out["rejected"] = out[["reject_tiny", "reject_sliver", "reject_loose", "reject_fragile"]].any(axis=1)

    out["history_bonus"] = 1.0 + 0.80 * out["history_contact"] + 0.30 * out["history_solve"] + 1.20 * out["history_cover"]
    out["history_penalty"] = 1.0
    no_history_mask = (out["history_contact"] <= 0) & (out["history_cover"] <= 0.0)
    out.loc[no_history_mask, "history_penalty"] = 0.35
    out["geometry_pref"] = (
        out["compactness"].map(lambda v: clamp01((float(v) - 0.72) / 0.18))
        * out["aspect_ratio"].map(lambda v: 1.0 if 0.6 <= float(v) <= 1.8 else 0.2)
        * out["min_dim"].map(lambda v: clamp01((float(v) - 0.0031) / 0.0014))
        * out["neck_score"].map(lambda v: clamp01((1.8 - float(v)) / 1.0))
    )
    out["contact_aware_bilobe_score_v2"] = (
        out["bilobe_candidate_score"].fillna(0.0).astype(float)
        * out["geometry_pref"]
        * out["history_bonus"]
        * out["history_penalty"]
    )
    out.loc[out["rejected"], "contact_aware_bilobe_score_v2"] *= 0.05

    reject_reason = []
    for row in out.itertuples(index=False):
        reasons = []
        if row.reject_tiny:
            reasons.append("tiny")
        if row.reject_sliver:
            reasons.append("sliver")
        if row.reject_loose:
            reasons.append("loose")
        if row.reject_fragile:
            reasons.append("fragile")
        if row.reject_no_history:
            reasons.append("no_history")
        reject_reason.append(",".join(reasons))
    out["reject_reason"] = reject_reason
    return out


def freeze_contours(shortlist: pd.DataFrame, frozen_dir: Path) -> pd.DataFrame:
    frozen_dir.mkdir(parents=True, exist_ok=True)
    frozen_paths = []
    for row in shortlist.itertuples(index=False):
        src = Path(str(row.shape_csv))
        dst = frozen_dir / f"{row.shape_id}.csv"
        shutil.copy2(src, dst)
        frozen_paths.append(str(dst))
    out = shortlist.copy()
    out["frozen_shape_csv"] = frozen_paths
    return out


def main() -> None:
    args = parse_args()
    out_root = args.out_root if args.out_root.is_absolute() else ROOT / args.out_root
    analysis_dir = out_root / "analysis"
    frozen_dir = out_root / "frozen_shape_contours"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    catalog = pd.read_csv(args.source_catalog)
    catalog = catalog.loc[catalog["priority_archetype"] == "bilobe"].copy()
    priors = load_priors(args.source_stage4_shape_summary, args.source_bcatp_shape_summary)
    merged = catalog.merge(priors, on="shape_id", how="left")
    for col in ["any_contact_valid", "any_solve_success"]:
        if col not in merged.columns:
            merged[col] = 0
    if "best_target_gap_cover_ratio" not in merged.columns:
        merged["best_target_gap_cover_ratio"] = 0.0
    merged["any_contact_valid"] = merged["any_contact_valid"].fillna(0).astype(int)
    merged["any_solve_success"] = merged["any_solve_success"].fillna(0).astype(int)
    merged["best_target_gap_cover_ratio"] = merged["best_target_gap_cover_ratio"].fillna(0.0)

    scored = compute_scores(merged)
    scored = scored.sort_values(
        ["contact_aware_bilobe_score_v2", "best_target_gap_cover_ratio", "bilobe_candidate_score"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    scored.to_csv(analysis_dir / "bilobe_contact_aware_catalog_v2.csv", index=False, encoding="utf-8-sig")

    shortlist = scored.loc[~scored["rejected"]].head(args.top_k).copy()
    shortlist["shortlist_rank"] = range(1, len(shortlist) + 1)
    shortlist = freeze_contours(shortlist, frozen_dir)
    shortlist.to_csv(analysis_dir / "bilobe_contact_aware_shortlist_v2.csv", index=False, encoding="utf-8-sig")

    whitelist = {
        "shape_ids": shortlist["shape_id"].astype(str).tolist(),
        "top_k": int(args.top_k),
        "frozen_shape_dir": str(frozen_dir),
    }
    (analysis_dir / "bilobe_contact_aware_whitelist_v2.json").write_text(
        json.dumps(whitelist, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "source_catalog": str(args.source_catalog),
        "source_stage4_shape_summary": str(args.source_stage4_shape_summary),
        "source_bcatp_shape_summary": str(args.source_bcatp_shape_summary),
        "bilobe_candidates_total": int(len(scored)),
        "rejected_count": int(scored["rejected"].sum()),
        "kept_count": int((~scored["rejected"]).sum()),
        "top_k": int(args.top_k),
        "top_shape_ids": shortlist["shape_id"].astype(str).tolist(),
        "frozen_shape_dir": str(frozen_dir),
    }
    (analysis_dir / "bilobe_contact_aware_summary_v2.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] bilobe-only contact-aware snake pilot v2 shortlist built")
    print(f"[OUT] {analysis_dir}")
    print(f"[FROZEN] {frozen_dir}")
    print(f"[KEPT] {(~scored['rejected']).sum()} / {len(scored)}")
    print(f"[TOP] {', '.join(shortlist['shape_id'].astype(str).tolist())}")


if __name__ == "__main__":
    main()
