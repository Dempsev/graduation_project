from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_CATALOG = (
    ROOT / "data" / "snake_based_archetype_expansion_pilot_v1" / "analysis" / "snake_based_archetype_pilot_catalog_v1.csv"
)
DEFAULT_SOURCE_STAGE4_SUMMARY = (
    ROOT / "data" / "analysis" / "snake_based_archetype_targetband_pilot_v1" / "snake_based_archetype_targetband_pilot_shape_summary_v1.csv"
)
DEFAULT_OUT_DIR = ROOT / "data" / "snake_based_bilobe_contact_aware_pilot_v1" / "analysis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bilobe-only, contact-aware snake shortlist.")
    parser.add_argument("--source-catalog", type=Path, default=DEFAULT_SOURCE_CATALOG)
    parser.add_argument("--source-stage4-shape-summary", type=Path, default=DEFAULT_SOURCE_STAGE4_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--top-k", type=int, default=16)
    return parser.parse_args()


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def gaussian_pref(x: float, mu: float, sigma: float) -> float:
    if sigma <= 1e-12:
        return 1.0 if abs(x - mu) <= 1e-12 else 0.0
    z = (x - mu) / sigma
    return math.exp(-0.5 * z * z)


def load_stage4_priors(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=["shape_id", "any_contact_valid", "any_solve_success", "best_target_gap_cover_ratio", "best_band_tag", "best_band_role"]
        )
    df = pd.read_csv(path)
    cols = [c for c in ["shape_id", "contact_valid", "solve_success", "target_gap_cover_ratio", "best_band_tag", "best_band_role"] if c in df.columns]
    if not cols:
        return pd.DataFrame(
            columns=["shape_id", "any_contact_valid", "any_solve_success", "best_target_gap_cover_ratio", "best_band_tag", "best_band_role"]
        )
    df = df[cols].copy()
    if "contact_valid" not in df.columns:
        df["contact_valid"] = 0
    if "solve_success" not in df.columns:
        df["solve_success"] = 0
    if "target_gap_cover_ratio" not in df.columns:
        df["target_gap_cover_ratio"] = 0.0
    priors = (
        df.groupby("shape_id", as_index=False)
        .agg(
            any_contact_valid=("contact_valid", "max"),
            any_solve_success=("solve_success", "max"),
            best_target_gap_cover_ratio=("target_gap_cover_ratio", "max"),
            best_band_tag=("best_band_tag", "first") if "best_band_tag" in df.columns else ("shape_id", "first"),
            best_band_role=("best_band_role", "first") if "best_band_role" in df.columns else ("shape_id", "first"),
        )
    )
    return priors


def compute_contact_aware_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    successful = out.loc[out["any_contact_valid"] > 0].copy()
    if successful.empty:
        area_mu = float(out["area"].median())
        area_sigma = float(max(out["area"].std(ddof=0), 2.5e-06))
    else:
        area_mu = float(successful["area"].median())
        area_sigma = float(max(successful["area"].std(ddof=0), 2.5e-06))

    out["min_dim"] = out[["width", "height"]].min(axis=1)
    out["area_pref"] = out["area"].map(lambda v: gaussian_pref(float(v), area_mu, area_sigma))
    out["compact_pref"] = out["compactness"].map(lambda v: clamp01((float(v) - 0.60) / 0.25))
    out["aspect_pref"] = out["aspect_ratio"].map(
        lambda v: 1.0 if 0.5 <= float(v) <= 2.0 else math.exp(-abs(math.log(max(float(v), 1e-12))))
    )
    out["min_dim_pref"] = out["min_dim"].map(lambda v: clamp01((float(v) - 0.0030) / 0.0015))
    out["neck_health_pref"] = out["neck_score"].map(lambda v: clamp01((2.2 - float(v)) / 1.6))

    out["history_bonus"] = (
        1.0
        + 0.35 * out["any_contact_valid"].fillna(0).astype(float)
        + 0.20 * out["any_solve_success"].fillna(0).astype(float)
        + 0.35 * out["best_target_gap_cover_ratio"].fillna(0.0).astype(float)
    )

    out["reject_tiny"] = (out["min_dim"] < 0.0028) | (out["area"] < 1.10e-05)
    out["reject_sliver"] = (out["aspect_ratio"] < 0.45) | (out["aspect_ratio"] > 2.25)
    out["reject_loose"] = out["compactness"] < 0.50
    out["reject_fragile"] = out["neck_score"] > 2.25
    out["rejected"] = out[["reject_tiny", "reject_sliver", "reject_loose", "reject_fragile"]].any(axis=1)

    out["contact_aware_bilobe_score"] = (
        out["bilobe_candidate_score"].fillna(0.0).astype(float)
        * (0.20 + 0.80 * out["area_pref"])
        * (0.25 + 0.75 * out["compact_pref"])
        * (0.25 + 0.75 * out["aspect_pref"])
        * (0.25 + 0.75 * out["min_dim_pref"])
        * (0.25 + 0.75 * out["neck_health_pref"])
        * out["history_bonus"]
    )
    out.loc[out["rejected"], "contact_aware_bilobe_score"] *= 0.15

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
        reject_reason.append(",".join(reasons))
    out["reject_reason"] = reject_reason

    return out


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog = pd.read_csv(args.source_catalog)
    catalog = catalog.loc[catalog["priority_archetype"] == "bilobe"].copy()

    priors = load_stage4_priors(args.source_stage4_shape_summary)
    merged = catalog.merge(priors, on="shape_id", how="left")
    for col in ["any_contact_valid", "any_solve_success"]:
        if col not in merged.columns:
            merged[col] = 0
        merged[col] = merged[col].fillna(0).astype(int)
    if "best_target_gap_cover_ratio" not in merged.columns:
        merged["best_target_gap_cover_ratio"] = 0.0
    merged["best_target_gap_cover_ratio"] = merged["best_target_gap_cover_ratio"].fillna(0.0)

    scored = compute_contact_aware_scores(merged)
    scored = scored.sort_values(
        ["contact_aware_bilobe_score", "best_target_gap_cover_ratio", "bilobe_candidate_score"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    scored.to_csv(out_dir / "bilobe_contact_aware_catalog_v1.csv", index=False, encoding="utf-8-sig")

    shortlist = scored.loc[~scored["rejected"]].head(args.top_k).copy()
    shortlist["shortlist_rank"] = range(1, len(shortlist) + 1)
    shortlist.to_csv(out_dir / "bilobe_contact_aware_shortlist_v1.csv", index=False, encoding="utf-8-sig")

    whitelist = {
        "shape_ids": shortlist["shape_id"].astype(str).tolist(),
        "top_k": int(args.top_k),
        "source_catalog": str(args.source_catalog),
        "source_stage4_shape_summary": str(args.source_stage4_shape_summary),
    }
    (out_dir / "bilobe_contact_aware_whitelist_v1.json").write_text(
        json.dumps(whitelist, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "source_catalog": str(args.source_catalog),
        "source_stage4_shape_summary": str(args.source_stage4_shape_summary),
        "bilobe_candidates_total": int(len(scored)),
        "rejected_count": int(scored["rejected"].sum()),
        "kept_count": int((~scored["rejected"]).sum()),
        "top_k": int(args.top_k),
        "top_shape_ids": shortlist["shape_id"].astype(str).tolist(),
        "contact_history_positive_count": int((scored["any_contact_valid"] > 0).sum()),
    }
    (out_dir / "bilobe_contact_aware_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] bilobe-only contact-aware snake pilot shortlist built")
    print(f"[OUT] {out_dir}")
    print(f"[KEPT] {(~scored['rejected']).sum()} / {len(scored)}")
    print(f"[TOP] {', '.join(shortlist['shape_id'].astype(str).head(5).tolist())}")


if __name__ == "__main__":
    main()
