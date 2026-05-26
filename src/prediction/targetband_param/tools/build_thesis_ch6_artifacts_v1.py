from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]

CHAPTER_DIR = ROOT / "data" / "analysis" / "thesis_ch6_v1"
FIG_DIR = CHAPTER_DIR / "figures"
TAB_DIR = CHAPTER_DIR / "tables"

WEAK_BANDS = ["band180_220", "band200_240", "band220_260", "band240_280"]
CANONICAL_BANDS = ["band180_220", "band200_240", "band220_260", "band240_280"]
BASELINE_LINES = [
    "generic_dataset_prior_v8",
    "band_supplement_ga_v1",
    "band_catalog_real_ga_v1",
    "band_supplement_exploratory_v2",
]

LINE_LABELS = {
    "generic_dataset_prior_v8": "Generic prior",
    "band_supplement_ga_v1": "Conservative supplement",
    "band_catalog_real_ga_v1": "Old band-catalog GA",
    "band_supplement_exploratory_v2": "Current exploratory mainline",
    "targetband_local_ga_v1_probe": "Local GA probe",
    "targetband_local_ga_v1_top6": "Local GA top6",
}

LINE_COLORS = {
    "generic_dataset_prior_v8": "#9e9e9e",
    "band_supplement_ga_v1": "#8c564b",
    "band_catalog_real_ga_v1": "#1f77b4",
    "band_supplement_exploratory_v2": "#2ca02c",
}

FONT_CANDIDATES = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]


def set_plot_style() -> None:
    plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["axes.titleweight"] = "bold"


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)


def run_step(script_rel: str, *args: str) -> None:
    script = ROOT / script_rel
    cmd = [sys.executable, str(script), *args]
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def fmt(v: object, digits: int = 4) -> str:
    if pd.isna(v):
        return ""
    if isinstance(v, (float, np.floating)):
        return f"{float(v):.{digits}f}"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return str(v)


def df_to_markdown(df: pd.DataFrame, digits: int = 4) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |"]
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        values = [fmt(row[c], digits=digits) for c in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_table(df: pd.DataFrame, stem: str, digits: int = 4) -> Path:
    csv_path = TAB_DIR / f"{stem}.csv"
    md_path = TAB_DIR / f"{stem}.md"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    md_path.write_text(df_to_markdown(df, digits=digits), encoding="utf-8")
    return csv_path


def write_index(entries: list[dict[str, str]]) -> None:
    lines = [
        "# Chapter 6 Artifact Index",
        "",
        "This folder collects the thesis-ready figures and tables for Chapter 6.",
        "",
    ]
    for item in entries:
        lines.append(f"- **{item['name']}**")
        lines.append(f"  - Figure/Table: {item['path']}")
        lines.append(f"  - Note: {item['note']}")
    (CHAPTER_DIR / "chapter6_artifacts_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_bar_labels(ax: plt.Axes, bars: list[plt.Rectangle], digits: int = 3, dy: float = 0.01) -> None:
    for bar in bars:
        h = float(bar.get_height())
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + dy,
            f"{h:.{digits}f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
        )


def generate_coverage_summary() -> Path:
    dataset = ROOT / "data" / "prediction_targetband_param_v1" / "v1" / "windows_dense_v8_truth_plus_exploratory_aug_v1" / "targetband_parametric_v1.csv"
    catalog = ROOT / "src" / "prediction" / "targetband_param" / "configs" / "thesis_band_catalog_v2.json"
    run_step(
        "src/prediction/targetband_param/tools/analyze_band_coverage_v1.py",
        "--dataset",
        str(dataset),
        "--catalog",
        str(catalog),
        "--out-tag",
        "thesis_band_catalog_v2_after_exploratory_v2",
    )
    return ROOT / "data" / "analysis" / "targetband_band_coverage_v1" / "thesis_band_catalog_v2_after_exploratory_v2" / "band_coverage_summary_v1.csv"


def summarize_topk_per_band(cls_df: pd.DataFrame, reg_df: pd.DataFrame, ks: list[int]) -> pd.DataFrame:
    cls = cls_df.rename(columns={"y_true": "cls_true", "y_prob": "cls_prob"}).copy()
    reg = reg_df.rename(columns={"y_true": "reg_true", "y_pred": "reg_pred"}).copy()
    merged = cls.merge(
        reg[
            [
                "fold",
                "param_sample_id",
                "target_band_tag",
                "target_band_low_Hz",
                "target_band_high_Hz",
                "reg_true",
                "reg_pred",
            ]
        ],
        on=["fold", "param_sample_id", "target_band_tag", "target_band_low_Hz", "target_band_high_Hz"],
        how="inner",
    )
    merged["shortlist_score"] = merged["cls_prob"] * merged["reg_pred"].clip(lower=0)

    rows: list[dict] = []
    for band_tag, part in merged.groupby("target_band_tag", observed=True):
        part = part.sort_values(["shortlist_score", "cls_prob", "reg_pred"], ascending=False).reset_index(drop=True)
        random_cover = float(part["reg_true"].mean())
        random_positive_rate = float(part["cls_true"].mean())
        for k in ks:
            top = part.head(min(k, len(part)))
            rows.append(
                {
                    "band_tag": band_tag,
                    "k": int(k),
                    "rows_considered": int(len(top)),
                    "topk_hit_rate": float(top["cls_true"].mean()),
                    "topk_mean_cover": float(top["reg_true"].mean()),
                    "topk_mean_pred_cover": float(top["reg_pred"].mean()),
                    "topk_mean_prob": float(top["cls_prob"].mean()),
                    "random_positive_rate": random_positive_rate,
                    "random_mean_cover": random_cover,
                    "lift_hit_rate": float(top["cls_true"].mean() - random_positive_rate),
                    "lift_mean_cover": float(top["reg_true"].mean() - random_cover),
                }
            )
    return pd.DataFrame(rows)


def build_weak_band_dashboard(coverage: pd.DataFrame) -> pd.DataFrame:
    weak = coverage[coverage["target_band_tag"].isin(WEAK_BANDS)].copy()
    weak = weak.rename(
        columns={
            "target_band_tag": "band_tag",
            "positive_rows": "coverage_positive_rows",
            "positive_families": "coverage_positive_families",
            "cover_ratio_mean_positive": "coverage_mean_positive_cover_ratio",
            "supplement_deficiency_score": "coverage_deficiency_score",
        }
    )

    cls_family = pd.read_csv(
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cls_rf_dense_v8_cmp_v1"
        / "stratified_group_kfold"
        / "predictions.csv"
    )
    reg_family = pd.read_csv(
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cover_hgb_dense_v8_cmp_v1"
        / "stratified_group_kfold"
        / "predictions.csv"
    )
    cls_lobo = pd.read_csv(
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cls_rf_dense_v8_cmp_v1"
        / "leave_one_band_tag_out"
        / "predictions.csv"
    )
    reg_lobo = pd.read_csv(
        ROOT
        / "data"
        / "prediction_targetband_param_v1_runs"
        / "param_targetband_cover_hgb_dense_v8_cmp_v1"
        / "leave_one_band_tag_out"
        / "predictions.csv"
    )

    cls_family = cls_family[cls_family["target_band_tag"].isin(WEAK_BANDS)].copy()
    reg_family = reg_family[reg_family["target_band_tag"].isin(WEAK_BANDS)].copy()
    cls_lobo = cls_lobo[cls_lobo["target_band_tag"].isin(WEAK_BANDS)].copy()
    reg_lobo = reg_lobo[reg_lobo["target_band_tag"].isin(WEAK_BANDS)].copy()

    topk_family = summarize_topk_per_band(cls_family, reg_family, ks=[20])
    topk_lobo = summarize_topk_per_band(cls_lobo, reg_lobo, ks=[20])
    topk_family = topk_family.rename(
        columns={
            "topk_mean_cover": "family_cv_top20_mean_cover",
            "lift_mean_cover": "family_cv_top20_cover_lift",
            "topk_mean_prob": "family_cv_top20_mean_prob",
            "topk_mean_pred_cover": "family_cv_top20_mean_pred_cover",
            "topk_hit_rate": "family_cv_top20_hit_rate",
            "lift_hit_rate": "family_cv_top20_hit_rate_lift",
            "random_mean_cover": "family_cv_random_mean_cover",
        }
    )
    topk_lobo = topk_lobo.rename(
        columns={
            "topk_mean_cover": "lobo_top20_mean_cover",
            "lift_mean_cover": "lobo_top20_cover_lift",
            "topk_mean_prob": "lobo_top20_mean_prob",
            "topk_mean_pred_cover": "lobo_top20_mean_pred_cover",
            "topk_hit_rate": "lobo_top20_hit_rate",
            "lift_hit_rate": "lobo_top20_hit_rate_lift",
            "random_mean_cover": "lobo_random_mean_cover",
        }
    )

    canonical_ref = pd.read_csv(
        ROOT
        / "data"
        / "ml_runs"
        / "canonical_targetband_refinement_v1_allcases"
        / "canonical_targetband_refinement_summary_v1.csv"
    )
    canonical_ref = canonical_ref[canonical_ref["target_band_tag"].isin(WEAK_BANDS)].copy()
    canonical_ref = canonical_ref.rename(
        columns={
            "target_band_tag": "band_tag",
            "best_target_cover_ratio_pred": "canonical_best_target_cover_ratio_pred",
            "best_target_open_prob": "canonical_best_target_open_prob",
            "best_targetband_score": "canonical_best_targetband_score",
        }
    )

    dashboard = weak[
        [
            "band_tag",
            "target_band_low_Hz",
            "target_band_high_Hz",
            "coverage_positive_rows",
            "coverage_positive_families",
            "coverage_mean_positive_cover_ratio",
            "coverage_deficiency_score",
        ]
    ].merge(
        topk_family[
            [
                "band_tag",
                "family_cv_top20_mean_cover",
                "family_cv_top20_cover_lift",
                "family_cv_top20_hit_rate",
                "family_cv_top20_mean_prob",
                "family_cv_top20_mean_pred_cover",
                "family_cv_random_mean_cover",
            ]
        ],
        on="band_tag",
        how="left",
    ).merge(
        topk_lobo[
            [
                "band_tag",
                "lobo_top20_mean_cover",
                "lobo_top20_cover_lift",
                "lobo_top20_hit_rate",
                "lobo_top20_mean_prob",
                "lobo_top20_mean_pred_cover",
                "lobo_random_mean_cover",
            ]
        ],
        on="band_tag",
        how="left",
    ).merge(
        canonical_ref[
            [
                "band_tag",
                "canonical_best_target_cover_ratio_pred",
                "canonical_best_target_open_prob",
                "canonical_best_targetband_score",
            ]
        ],
        on="band_tag",
        how="left",
    )

    dashboard = dashboard.sort_values("band_tag").reset_index(drop=True)
    return dashboard


def build_baseline_comparison_table() -> pd.DataFrame:
    family_df = pd.read_csv(ROOT / "data" / "ml_runs" / "candidate_pool_seed_discovery_v10" / "seed_discovery_family_summary.csv")
    tier_df = pd.read_csv(ROOT / "data" / "ml_runs" / "candidate_pool_seed_discovery_v10" / "seed_discovery_tier_summary.csv")
    search_df = pd.read_csv(ROOT / "data" / "ml_runs" / "candidate_pool_seed_discovery_v10" / "ga_parametric_search_v1" / "ga_search_summary.csv")
    direct_df = pd.read_csv(
        ROOT
        / "data"
        / "ml_runs"
        / "candidate_pool_seed_discovery_v10"
        / "ga_parametric_search_v1"
        / "real_validation_comparison_v1"
        / "ga_stage4_seed_vs_ga_comparison_v1.csv"
    )

    family_df = family_df.assign(comparison_block="seed family summary", label=family_df["shape_family"])
    tier_df = tier_df.assign(comparison_block="seed tier summary", label=tier_df["stage1_reference_candidate_tier"])
    search_df = search_df.assign(comparison_block="GA search summary", label=search_df["shape_family"])
    direct_df = direct_df.assign(comparison_block="GA vs seed validation", label=direct_df["point_id"])

    family_view = family_df[
        [
            "comparison_block",
            "label",
            "rows",
            "contact_gate_rate",
            "positive_gate_rate",
            "cascade_gate_rate",
            "mean_contact_prob",
            "mean_positive_prob",
            "mean_cascade_score",
            "mean_stage1_reference_gap_gain_Hz",
            "mean_surrogate_pred_gap34_gain_Hz",
        ]
    ].copy()
    tier_view = tier_df[
        [
            "comparison_block",
            "label",
            "rows",
            "contact_gate_rate",
            "positive_gate_rate",
            "cascade_gate_rate",
            "mean_contact_prob",
            "mean_positive_prob",
            "mean_cascade_score",
            "mean_stage1_reference_gap_gain_Hz",
            "mean_surrogate_pred_gap34_gain_Hz",
        ]
    ].copy()
    search_view = search_df[
        [
            "comparison_block",
            "label",
            "base_cascade_score",
            "base_contact_prob",
            "base_positive_prob",
            "base_surrogate_pred_gap34_gain_Hz",
            "best_cascade_score",
            "best_contact_prob",
            "best_positive_prob",
            "best_surrogate_pred_gap34_gain_Hz",
            "best_distance_from_base",
            "best_fitness",
            "delta_cascade_score",
            "delta_surrogate_pred_gap34_gain_Hz",
        ]
    ].copy()
    direct_view = direct_df[
        [
            "comparison_block",
            "label",
            "ga_rows",
            "ga_solve_success_rate",
            "ga_contact_valid_rate",
            "ga_positive_gain_rate",
            "ga_mean_gap34_gain_Hz",
            "ga_best_gap34_gain_Hz",
            "seed_rows",
            "seed_solve_success_rate",
            "seed_contact_valid_rate",
            "seed_positive_gain_rate",
            "seed_mean_gap34_gain_Hz",
            "seed_best_gap34_gain_Hz",
            "delta_best_gap34_gain_Hz",
            "delta_mean_gap34_gain_Hz",
            "ga_beats_seed_best",
            "ga_beats_seed_mean",
        ]
    ].copy()

    family_view = family_view.rename(columns={"label": "label"})
    tier_view = tier_view.rename(columns={"label": "label"})
    search_view = search_view.rename(columns={"label": "label"})
    direct_view = direct_view.rename(columns={"label": "label"})

    return pd.concat([family_view, tier_view, search_view, direct_view], ignore_index=True, sort=False)


def generate_weak_band_dashboard() -> Path:
    run_step("src/prediction/targetband_param/tools/analyze_weak_band_dashboard_v1.py")
    return ROOT / "data" / "analysis" / "weak_band_dashboard_v1" / "weak_band_dashboard_summary_v1.csv"


def generate_local_robustness() -> Path:
    run_step("src/prediction/targetband_param/tools/analyze_canonical_local_robustness_v1.py")
    run_step("src/prediction/targetband_param/tools/plot_canonical_local_robustness_edges_v1.py")
    return ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "canonical_local_robustness_case_summary_v1.csv"


def build_table_6_1() -> pd.DataFrame:
    rows = [
        {
            "section": "6.3",
            "artifact_role": "Predictor readiness",
            "evidence_focus": "Family-CV, leave-one-band, top-k shortlist, calibration",
            "primary_source": "data/analysis/predictor_readiness_v1/",
        },
        {
            "section": "6.4",
            "artifact_role": "Canonical inverse-design cases",
            "evidence_focus": "Canonical case refinement summary and case-level comparison",
            "primary_source": "data/ml_runs/canonical_targetband_refinement_v1_allcases/",
        },
        {
            "section": "6.5",
            "artifact_role": "Baseline comparison",
            "evidence_focus": "Band ladder, generic prior, conservative supplement, exploratory mainline",
            "primary_source": "data/analysis/targetband_baseline_ladder_v1/",
        },
        {
            "section": "6.6",
            "artifact_role": "Weak-band shortlist value",
            "evidence_focus": "Coverage, shortlist lift, and mainline usefulness on weak bands",
            "primary_source": "data/analysis/weak_band_dashboard_v1/",
        },
        {
            "section": "6.7",
            "artifact_role": "Stage4 real validation",
            "evidence_focus": "Validation funnel, solved rows, positive gain, point/shape/arm summaries",
            "primary_source": "data/comsol_batch/stage4_validation_targetband_top6_v1/",
        },
        {
            "section": "6.8",
            "artifact_role": "Local robustness",
            "evidence_focus": "Center retention, edge drift, and perturbation stability",
            "primary_source": "data/analysis/canonical_local_robustness_v1/",
        },
    ]
    return pd.DataFrame(rows)


def build_table_6_2() -> pd.DataFrame:
    ref_path = ROOT / "data" / "ml_runs" / "canonical_targetband_refinement_v1_allcases" / "canonical_targetband_refinement_summary_v1.csv"
    df = pd.read_csv(ref_path)
    cols = [
        "canonical_case_id",
        "target_band_tag",
        "shape_id",
        "shape_family",
        "base_sample_id",
        "base_archive_cover_ratio",
        "base_targetband_score",
        "base_target_cover_ratio_pred",
        "base_target_overlap_pred_Hz",
        "best_targetband_score",
        "best_target_cover_ratio_pred",
        "best_target_overlap_pred_Hz",
        "best_contact_prob",
        "best_target_open_prob",
        "best_distance_from_base",
        "delta_targetband_score",
        "delta_target_cover_ratio_pred",
        "delta_target_overlap_pred_Hz",
    ]
    return df[cols].copy()


def build_table_6_3(ladder_path: Path) -> pd.DataFrame:
    df = pd.read_csv(ladder_path)
    df = df[df["target_band_tag"].isin(CANONICAL_BANDS)].copy()
    cols = [
        "target_band_tag",
        "line_id",
        "line_role",
        "real_open_rate",
        "mean_overlap_Hz",
        "mean_cover_ratio",
        "best_overlap_Hz",
        "best_cover_ratio",
        "best_shape_id",
        "family_diversity",
        "budget_proxy",
    ]
    df = df[cols].copy()
    df["line_label"] = df["line_id"].map(LINE_LABELS).fillna(df["line_id"])
    return df[
        [
            "target_band_tag",
            "line_label",
            "line_role",
            "real_open_rate",
            "mean_overlap_Hz",
            "mean_cover_ratio",
            "best_overlap_Hz",
            "best_cover_ratio",
            "best_shape_id",
            "family_diversity",
            "budget_proxy",
        ]
    ].rename(columns={"line_label": "line_id"})


def build_table_6_4() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_results.csv")
    cols = [
        "validation_id",
        "selection_label",
        "shape_id",
        "shape_family",
        "solve_success",
        "geometry_valid",
        "contact_valid",
        "contact_prob",
        "positive_prob",
        "cascade_score",
        "gap34_gain_Hz",
        "gap34_rel",
        "gap34_lower_edge_Hz",
        "gap34_upper_edge_Hz",
        "main_id",
        "point_id",
    ]
    out = df[cols].copy()
    out = out.sort_values(["selection_label", "gap34_gain_Hz"], ascending=[True, False]).reset_index(drop=True)
    return out


def build_local_robustness_table() -> pd.DataFrame:
    case_df = pd.read_csv(ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "canonical_local_robustness_case_summary_v1.csv")
    cols = [
        "canonical_case_id",
        "target_band_tag",
        "shape_id",
        "center_cover_ratio",
        "center_overlap_Hz",
        "variant_count",
        "mean_variant_cover_ratio",
        "min_variant_cover_ratio",
        "max_variant_cover_ratio",
        "variants_ge_90pct_center",
        "variants_ge_80pct_center",
        "mean_abs_lower_edge_shift_Hz",
        "mean_abs_upper_edge_shift_Hz",
        "max_abs_lower_edge_shift_Hz",
        "max_abs_upper_edge_shift_Hz",
    ]
    return case_df[cols].copy()


def plot_canonical_cases(canonical_ref: pd.DataFrame, out_path: Path) -> None:
    order = CANONICAL_BANDS
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.0), sharey=True)
    axes = axes.flatten()
    for ax, band in zip(axes, order):
        sub = canonical_ref[canonical_ref["target_band_tag"] == band].copy()
        if sub.empty:
            ax.axis("off")
            continue
        row = sub.iloc[0]
        bars = ax.bar(
            [0, 1],
            [float(row["base_target_cover_ratio_pred"]), float(row["best_target_cover_ratio_pred"])],
            width=0.62,
            color=["#9e9e9e", "#2ca02c"],
        )
        add_bar_labels(ax, bars, digits=3, dy=0.01)
        ax.set_xticks([0, 1], ["Base predicted", "Best predicted"], rotation=0)
        ax.set_ylim(0.0, 1.08)
        ax.set_ylabel("Cover ratio")
        ax.set_title(f"{band} | {row['shape_id']}", fontsize=11)
        ax.grid(True, axis="y", alpha=0.2)
        ax.text(
            0.03,
            0.95,
            f"score delta: {fmt(row['delta_targetband_score'], 4)}\nopen prob: {fmt(row['best_target_open_prob'], 3)}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8,
            color="#444444",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#dddddd", alpha=0.95),
        )

    fig.suptitle("Canonical case refinement summary", fontsize=14, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def plot_baseline_comparison(baseline: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.0))

    fam = baseline[baseline["comparison_block"] == "seed family summary"].copy()
    ax = axes[0, 0]
    x = np.arange(len(fam))
    ax.bar(x - 0.22, fam["contact_gate_rate"], width=0.22, color="#4c78a8", label="contact gate")
    ax.bar(x, fam["positive_gate_rate"], width=0.22, color="#f58518", label="positive gate")
    ax.bar(x + 0.22, fam["cascade_gate_rate"], width=0.22, color="#2ca02c", label="cascade gate")
    ax2 = ax.twinx()
    ax2.plot(x, fam["mean_surrogate_pred_gap34_gain_Hz"], color="#d62728", marker="o", linewidth=1.6, label="mean surrogate gain")
    ax.set_xticks(x, fam["label"].tolist(), rotation=20, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Seed-discovery family summary")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8, loc="upper left")
    ax2.legend(fontsize=8, loc="upper right")

    tier = baseline[baseline["comparison_block"] == "seed tier summary"].copy()
    ax = axes[0, 1]
    x = np.arange(len(tier))
    ax.bar(x - 0.22, tier["contact_gate_rate"], width=0.22, color="#4c78a8", label="contact gate")
    ax.bar(x, tier["positive_gate_rate"], width=0.22, color="#f58518", label="positive gate")
    ax.bar(x + 0.22, tier["cascade_gate_rate"], width=0.22, color="#2ca02c", label="cascade gate")
    ax2 = ax.twinx()
    ax2.plot(x, tier["mean_surrogate_pred_gap34_gain_Hz"], color="#d62728", marker="o", linewidth=1.6, label="mean surrogate gain")
    ax.set_xticks(x, tier["label"].tolist(), rotation=18, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Seed-discovery tier summary")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8, loc="upper left")
    ax2.legend(fontsize=8, loc="upper right")

    search = baseline[baseline["comparison_block"] == "GA search summary"].copy()
    ax = axes[1, 0]
    row = search.iloc[0]
    metrics = [
        ("Base contact", float(row["base_contact_prob"])),
        ("Best contact", float(row["best_contact_prob"])),
        ("Base positive", float(row["base_positive_prob"])),
        ("Best positive", float(row["best_positive_prob"])),
    ]
    bars = ax.bar(np.arange(len(metrics)), [m[1] for m in metrics], color=["#9e9e9e", "#4c78a8", "#f58518", "#2ca02c"])
    ax.set_xticks(np.arange(len(metrics)), [m[0] for m in metrics], rotation=20, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_title(f"GA search summary | {row['label']}")
    ax.grid(True, axis="y", alpha=0.18)
    add_bar_labels(ax, bars, digits=3, dy=0.01)
    ax.text(
        0.03,
        0.96,
        f"delta gain: {fmt(row['delta_surrogate_pred_gap34_gain_Hz'])}\nfitness: {fmt(row['best_fitness'])}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#dddddd", alpha=0.95),
    )

    direct = baseline[baseline["comparison_block"] == "GA vs seed validation"].copy()
    ax = axes[1, 1]
    row = direct.iloc[0]
    names = ["GA solve", "GA contact", "GA positive", "Seed solve", "Seed contact", "Seed positive"]
    vals = [
        float(row["ga_solve_success_rate"]),
        float(row["ga_contact_valid_rate"]),
        float(row["ga_positive_gain_rate"]),
        float(row["seed_solve_success_rate"]),
        float(row["seed_contact_valid_rate"]),
        float(row["seed_positive_gain_rate"]),
    ]
    colors = ["#4c78a8", "#4c78a8", "#4c78a8", "#f58518", "#f58518", "#f58518"]
    bars = ax.bar(np.arange(len(vals)), vals, color=colors)
    ax.set_xticks(np.arange(len(vals)), names, rotation=20, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("GA vs seed real validation")
    ax.grid(True, axis="y", alpha=0.18)
    add_bar_labels(ax, bars, digits=3, dy=0.01)
    ax.text(
        0.03,
        0.96,
        f"delta best gain: {fmt(row['delta_best_gap34_gain_Hz'])}\nmean gain delta: {fmt(row['delta_mean_gap34_gain_Hz'])}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#dddddd", alpha=0.95),
    )

    fig.suptitle("Baseline comparison for Chapter 6", fontsize=14, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def plot_weak_band_dashboard(dashboard: pd.DataFrame, out_path: Path) -> None:
    order = WEAK_BANDS
    dashboard = dashboard[dashboard["band_tag"].isin(order)].copy()
    dashboard["band_tag"] = pd.Categorical(dashboard["band_tag"], categories=order, ordered=True)
    dashboard = dashboard.sort_values("band_tag")

    fig, axes = plt.subplots(2, 2, figsize=(14.2, 9.4))

    ax = axes[0, 0]
    x = np.arange(len(dashboard))
    b1 = ax.bar(x - 0.2, dashboard["coverage_positive_rows"], width=0.4, color="#4c78a8", label="positive rows")
    b2 = ax.bar(x + 0.2, dashboard["coverage_positive_families"], width=0.4, color="#f58518", label="positive families")
    ax.set_xticks(x, dashboard["band_tag"].tolist(), rotation=18, ha="right")
    ax.set_ylabel("Count")
    ax.set_title("Coverage inventory")
    ax.grid(True, axis="y", alpha=0.18)
    ax2 = ax.twinx()
    ax2.plot(x, dashboard["coverage_deficiency_score"], color="#d62728", marker="o", linewidth=1.8, label="deficiency score")
    ax2.set_ylabel("Deficiency score")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)

    ax = axes[0, 1]
    x = np.arange(len(dashboard))
    b1 = ax.bar(x - 0.2, dashboard["family_cv_top20_mean_cover"], width=0.4, color="#2ca02c", label="top20 mean cover")
    b2 = ax.bar(x + 0.2, dashboard["family_cv_top20_cover_lift"], width=0.4, color="#9e9e9e", label="lift vs random")
    ax.set_xticks(x, dashboard["band_tag"].tolist(), rotation=18, ha="right")
    ax.set_ylim(0.0, max(0.6, float(max(dashboard["family_cv_top20_mean_cover"].max(), dashboard["family_cv_top20_cover_lift"].max())) + 0.05))
    ax.set_ylabel("Cover ratio")
    ax.set_title("Family-CV shortlist quality")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8, loc="upper right")

    ax = axes[1, 0]
    x = np.arange(len(dashboard))
    b1 = ax.bar(x - 0.2, dashboard["lobo_top20_mean_cover"], width=0.4, color="#1f77b4", label="top20 mean cover")
    b2 = ax.bar(x + 0.2, dashboard["lobo_top20_cover_lift"], width=0.4, color="#c7c7c7", label="lift vs random")
    ax.set_xticks(x, dashboard["band_tag"].tolist(), rotation=18, ha="right")
    ax.set_ylabel("Cover ratio")
    ax.set_title("Leave-one-band shortlist quality")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8, loc="upper right")

    ax = axes[1, 1]
    bar_x = np.arange(len(dashboard))
    main_bars = ax.bar(bar_x - 0.2, dashboard["canonical_best_target_cover_ratio_pred"], width=0.4, color="#2ca02c", label="best predicted cover")
    ax2 = ax.twinx()
    ax2.plot(bar_x, dashboard["canonical_best_target_open_prob"], color="#1f77b4", marker="o", linewidth=1.8, label="best open prob")
    ax.set_xticks(bar_x, dashboard["band_tag"].tolist(), rotation=18, ha="right")
    ax.set_ylim(0.0, max(1.05, float(np.nanmax(dashboard["canonical_best_target_cover_ratio_pred"].to_numpy())) + 0.08))
    ax2.set_ylim(0.0, 1.05)
    ax.set_ylabel("Cover ratio")
    ax2.set_ylabel("Open probability")
    ax.set_title("Canonical mainline usefulness")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8, loc="upper left")
    ax2.legend(fontsize=8, loc="upper right")

    fig.suptitle("Weak-band dashboard for Chapter 6", fontsize=14, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def plot_stage4_validation(results: pd.DataFrame, point_summary: pd.DataFrame, shape_summary: pd.DataFrame, arm_summary: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.8))

    valid = results.copy()
    solved = valid[(valid["solve_success"] == 1) & (valid["geometry_valid"] == 1) & (valid["contact_valid"] == 1)].copy()

    ax = axes[0]
    stages = [
        ("rows_total", len(valid)),
        ("geometry_valid", int(valid["geometry_valid"].sum())),
        ("contact_valid", int(valid["contact_valid"].sum())),
        ("solve_success", int(valid["solve_success"].sum())),
    ]
    stage_labels = ["Total", "Geometry\nvalid", "Contact\nvalid", "Solved"]
    stage_vals = [x[1] for x in stages]
    bars = ax.bar(stage_labels, stage_vals, color=["#9e9e9e", "#4c78a8", "#f58518", "#2ca02c"], width=0.62)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 0.08, f"{int(bar.get_height())}", ha="center", va="bottom", fontsize=8)
    ax.set_title("Validation funnel")
    ax.set_ylabel("Count")
    ax.grid(True, axis="y", alpha=0.18)

    ax = axes[1]
    summary_rows = [
        ("Arm", float(arm_summary["positive_gap34_gain_rate"].mean()), float(arm_summary["mean_gap34_gain_Hz"].mean())),
        ("Point", float(point_summary["positive_gap34_gain_rate"].mean()), float(point_summary["mean_gap34_gain_Hz"].mean())),
        ("Shape", float(shape_summary["positive_gap34_gain_rate"].mean()), float(shape_summary["mean_gap34_gain_Hz"].mean())),
    ]
    x = np.arange(len(summary_rows))
    rate_bars = ax.bar(x - 0.18, [r[1] for r in summary_rows], width=0.36, color="#1f77b4", label="positive gain rate")
    gain_bars = ax.bar(x + 0.18, [min(1.0, r[2] / 35.0) for r in summary_rows], width=0.36, color="#d62728", label="scaled mean gain")
    ax.set_xticks(x, [r[0] for r in summary_rows])
    ax.set_ylim(0.0, 1.08)
    ax.set_title("Positive gain summary")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8, loc="upper right")

    ax = axes[2]
    ax.hist(solved["gap34_gain_Hz"], bins=min(8, max(3, len(solved))), color="#2ca02c", alpha=0.82, edgecolor="white")
    ax.axvline(float(solved["gap34_gain_Hz"].mean()), color="#111111", linestyle="--", linewidth=1.2, label="mean")
    ax.axvline(float(solved["gap34_gain_Hz"].median()), color="#d62728", linestyle=":", linewidth=1.4, label="median")
    ax.set_title("Gain distribution among solved rows")
    ax.set_xlabel("Gap34 gain (Hz)")
    ax.set_ylabel("Count")
    ax.grid(True, axis="y", alpha=0.18)
    ax.legend(fontsize=8)

    fig.suptitle("Stage4 real validation summary", fontsize=14, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=240)
    plt.close(fig)


def copy_local_robustness_overview(out_path: Path) -> None:
    src = ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "plots" / "canonical_local_robustness_edge_drift_overview_v1.png"
    if not src.is_file():
        raise FileNotFoundError(src)
    shutil.copyfile(src, out_path)


def main() -> None:
    set_plot_style()
    ensure_dirs()

    coverage_path = generate_coverage_summary()
    local_robust_path = generate_local_robustness()

    coverage = pd.read_csv(coverage_path)
    canonical_ref = pd.read_csv(ROOT / "data" / "ml_runs" / "canonical_targetband_refinement_v1_allcases" / "canonical_targetband_refinement_summary_v1.csv")
    stage4_results = pd.read_csv(ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_results.csv")
    stage4_point = pd.read_csv(ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_point_summary.csv")
    stage4_shape = pd.read_csv(ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_shape_summary.csv")
    stage4_arm = pd.read_csv(ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_arm_summary.csv")

    table_6_1 = build_table_6_1()
    table_6_2 = build_table_6_2()
    table_6_3 = build_baseline_comparison_table()
    table_6_4 = build_table_6_4()
    table_6_5 = build_local_robustness_table()

    # Make the weak-band dashboard directly from the current analysis products.
    weak_dashboard = build_weak_band_dashboard(coverage)

    write_table(table_6_1, "table_6_1_experiment_lines", digits=4)
    write_table(table_6_2, "table_6_2_canonical_cases", digits=4)
    write_table(table_6_3, "table_6_3_baseline_comparison", digits=4)
    write_table(table_6_4, "table_6_4_stage4_validation", digits=4)
    write_table(table_6_5, "table_6_5_local_robustness_summary", digits=4)

    fig_6_2 = FIG_DIR / "figure_6_2_canonical_cases.png"
    fig_6_3 = FIG_DIR / "figure_6_3_baseline_comparison.png"
    fig_6_4 = FIG_DIR / "figure_6_4_weak_band_dashboard.png"
    fig_6_5 = FIG_DIR / "figure_6_5_stage4_validation.png"
    fig_6_6 = FIG_DIR / "figure_6_6_local_robustness.png"

    plot_canonical_cases(canonical_ref, fig_6_2)
    plot_baseline_comparison(table_6_3, fig_6_3)
    plot_weak_band_dashboard(weak_dashboard, fig_6_4)
    plot_stage4_validation(stage4_results, stage4_point, stage4_shape, stage4_arm, fig_6_5)
    copy_local_robustness_overview(fig_6_6)

    index_entries = [
        {
            "name": "Table 6-1 Experiment lines",
            "path": str(TAB_DIR / "table_6_1_experiment_lines.md"),
            "note": "Experimental role map for Chapter 6.",
        },
        {
            "name": "Table 6-2 Canonical cases",
            "path": str(TAB_DIR / "table_6_2_canonical_cases.md"),
            "note": "Canonical refinement summary for the four cases.",
        },
        {
            "name": "Table 6-3 Baseline comparison",
            "path": str(TAB_DIR / "table_6_3_baseline_comparison.md"),
            "note": "Seed discovery, GA search, and direct validation comparison.",
        },
        {
            "name": "Table 6-4 Stage4 validation",
            "path": str(TAB_DIR / "table_6_4_stage4_validation.md"),
            "note": "Row-level validation results on the top6 set.",
        },
        {
            "name": "Table 6-5 Local robustness",
            "path": str(TAB_DIR / "table_6_5_local_robustness_summary.md"),
            "note": "Center retention and local drift summary.",
        },
        {
            "name": "Figure 6-2 Canonical cases",
            "path": str(fig_6_2),
            "note": "Base-vs-best refinement summary for the canonical cases.",
        },
        {
            "name": "Figure 6-3 Baseline comparison",
            "path": str(fig_6_3),
            "note": "Seed-discovery family/tier and GA-vs-seed validation comparison.",
        },
        {
            "name": "Figure 6-4 Weak-band dashboard",
            "path": str(fig_6_4),
            "note": "Coverage inventory, shortlist lift, and weak-band usefulness.",
        },
        {
            "name": "Figure 6-5 Stage4 validation",
            "path": str(fig_6_5),
            "note": "Validation funnel, gain summary, and gain distribution.",
        },
        {
            "name": "Figure 6-6 Local robustness",
            "path": str(fig_6_6),
            "note": "Overview of the canonical local-robustness edge-drift panels.",
        },
    ]
    write_index(index_entries)

    summary = {
        "chapter_dir": str(CHAPTER_DIR),
        "coverage_csv": str(coverage_path),
        "canonical_ref_csv": str(ROOT / "data" / "ml_runs" / "canonical_targetband_refinement_v1_allcases" / "canonical_targetband_refinement_summary_v1.csv"),
        "stage4_validation_csv": str(ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_results.csv"),
        "local_robustness_csv": str(local_robust_path),
    }
    (CHAPTER_DIR / "chapter6_artifacts_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
