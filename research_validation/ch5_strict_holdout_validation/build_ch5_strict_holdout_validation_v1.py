from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from prediction_v3.models.feature_engineering import build_tail_prediction_frame

OUT_DIR = ROOT / "research_validation" / "ch5_strict_holdout_validation"
FIG_DIR = OUT_DIR / "figures"
COMSOL_OUT_DIR = ROOT / "data" / "comsol_batch" / "ch5_strict_holdout_validation_top5_random5"

V12_DATASET = ROOT / "data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/targetband_parametric_v1.csv"
FINAL_MODEL = ROOT / "data/prediction_targetband_param_v1_runs/param_targetband_final_hgb_dense_v12_all_history_ga20_clean_v1/final_predictor_bundle.joblib"
CH4_SUMMARY = ROOT / "research_validation/ch4_ga_real_optimization/ch4_ga_summary_20gen.csv"
CH4_TYPICAL = ROOT / "research_validation/ch4_ga_real_optimization/ch4_typical_cases_20gen.csv"
EXISTING_CH5 = ROOT / "research_validation/ch5_prediction_vs_ga/ch5_unified_candidate_comparison.csv"
SHAPE_POOL = ROOT / "data/ml_runs/targetband_baseline_abc_v1/real_ga_shape_pool_v1.csv"
SHAPE_DIR = ROOT / "data/shape_contours"

BANDS = [
    ("band140_180", "140\u2013180 Hz", 140.0, 180.0),
    ("band160_200", "160\u2013200 Hz", 160.0, 200.0),
    ("band180_220", "180\u2013220 Hz", 180.0, 220.0),
    ("band200_240", "200\u2013240 Hz", 200.0, 240.0),
    ("band220_260", "220\u2013260 Hz", 220.0, 260.0),
    ("band240_280", "240\u2013280 Hz", 240.0, 280.0),
]
BAND_ORDER = [item[0] for item in BANDS]
BAND_LABEL = {item[0]: item[1] for item in BANDS}
BAND_LOW = {item[0]: item[2] for item in BANDS}
BAND_HIGH = {item[0]: item[3] for item in BANDS}
LABEL_TO_TAG = {item[1]: item[0] for item in BANDS}

PARAM_COLS = ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]
KEY_COLS = ["point_id", "shape_id", *PARAM_COLS, "target_band_low_Hz", "target_band_high_Hz"]
SHAPE_FEATURE_PREFIXES = ("shape_",)

PARAM_BOUNDS = {
    "a1": (0.35, 0.55),
    "a2": (-0.18, 0.08),
    "b1": (-0.05, 0.05),
    "b2": (-0.08, 0.08),
    "a3": (-0.04, 0.04),
    "b3": (-0.04, 0.04),
    "a4": (-0.03, 0.03),
    "b4": (-0.03, 0.03),
    "a5": (-0.02, 0.02),
    "b5": (-0.02, 0.03),
    "r0": (0.010, 0.014),
}

PALETTE = {
    "predicted_top5": "#4E79A7",
    "random5": "#F28E2B",
    "ga20": "#59A14F",
    "grid": "#E6E6E6",
    "text": "#222222",
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    COMSOL_OUT_DIR.mkdir(parents=True, exist_ok=True)


def configure_fonts() -> str:
    for path in [Path(r"C:\Windows\Fonts\msyh.ttc"), Path(r"C:\Windows\Fonts\simhei.ttf"), Path(r"C:\Windows\Fonts\simsun.ttc")]:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            break
    else:
        font_name = "DejaVu Sans"
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_name, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": PALETTE["text"],
            "axes.labelcolor": PALETTE["text"],
            "text.color": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
        }
    )
    return font_name


def nfmt(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
        return f"{float(value):.12g}"
    except Exception:
        return str(value)


def canonical_key(row: pd.Series | dict[str, Any]) -> str:
    get = row.get
    point_id = str(get("point_id", ""))
    shape_id = str(get("shape_id", ""))
    low = get("target_band_low_Hz", np.nan)
    high = get("target_band_high_Hz", np.nan)
    if not point_id or not shape_id or pd.isna(low) or pd.isna(high):
        return ""
    return "|".join([point_id, shape_id, *[nfmt(get(col, np.nan)) for col in PARAM_COLS], nfmt(low), nfmt(high)])


def no_point_key(row: pd.Series | dict[str, Any]) -> str:
    get = row.get
    shape_id = str(get("shape_id", ""))
    low = get("target_band_low_Hz", np.nan)
    high = get("target_band_high_Hz", np.nan)
    if not shape_id or pd.isna(low) or pd.isna(high):
        return ""
    return "|".join([shape_id, *[nfmt(get(col, np.nan)) for col in PARAM_COLS], nfmt(low), nfmt(high)])


def md_table(df: pd.DataFrame, path: Path, max_rows: int | None = None) -> None:
    show = df.copy()
    if max_rows is not None and len(show) > max_rows:
        show = show.head(max_rows)
    cols = list(show.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in show.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if pd.isna(value):
                text = ""
            elif isinstance(value, float):
                text = f"{value:.6g}"
            else:
                text = str(value)
            values.append(text.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    if max_rows is not None and len(df) > max_rows:
        lines.append("")
        lines.append(f"> 仅预览前 {max_rows} 行，完整结果见同名 CSV。")
    path.write_text("\n".join(lines), encoding="utf-8")


def save_table(df: pd.DataFrame, stem: str, max_md_rows: int | None = None) -> None:
    df.to_csv(OUT_DIR / f"{stem}.csv", index=False, encoding="utf-8-sig")
    md_table(df, OUT_DIR / f"{stem}.md", max_rows=max_md_rows)


def save_fig(fig: plt.Figure, stem: str) -> dict[str, str]:
    paths: dict[str, str] = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths[ext] = str(path)
    plt.close(fig)
    return paths


def style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.6, alpha=0.85)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(PALETTE["text"])
        ax.spines[side].set_linewidth(0.8)


def read_v12_minimal() -> pd.DataFrame:
    usecols = None
    return pd.read_csv(V12_DATASET, usecols=usecols, low_memory=False)


def load_seen_sets(v12: pd.DataFrame) -> tuple[set[str], set[str], set[str], set[str], set[str]]:
    v12_keys = set(v12.get("physical_key", pd.Series(dtype=str)).dropna().astype(str))
    v12_keys.update(v12.apply(canonical_key, axis=1))

    v12_no_point = set(v12.apply(no_point_key, axis=1))

    ga_keys: set[str] = set()
    ga_no_point: set[str] = set()
    if CH4_SUMMARY.exists():
        summary = pd.read_csv(CH4_SUMMARY)
        for _, row in summary.iterrows():
            hist_path = Path(str(row["output_dir"])) / "ga_history_v1.csv"
            if not hist_path.exists():
                continue
            hist = pd.read_csv(hist_path, low_memory=False)
            tag = str(row["target_band_tag"])
            hist["target_band_low_Hz"] = BAND_LOW[tag]
            hist["target_band_high_Hz"] = BAND_HIGH[tag]
            hist["point_id"] = hist.get("point_id", "rf09_h00_center")
            ga_keys.update(hist.apply(canonical_key, axis=1))
            ga_no_point.update(hist.apply(no_point_key, axis=1))

    existing_ch5_keys: set[str] = set()
    if EXISTING_CH5.exists():
        ch5 = pd.read_csv(EXISTING_CH5, low_memory=False)
        existing_ch5_keys.update(ch5.get("physical_key", pd.Series(dtype=str)).dropna().astype(str))
        if set(KEY_COLS).issubset(ch5.columns):
            existing_ch5_keys.update(ch5.apply(canonical_key, axis=1))

    return v12_keys, ga_keys, existing_ch5_keys, v12_no_point, ga_no_point


def load_shape_pool_and_features(v12: pd.DataFrame) -> pd.DataFrame:
    pool = pd.read_csv(SHAPE_POOL)
    pool["shape_id"] = pool["shape_id"].astype(str)
    pool["shape_family"] = pool["shape_id"].str.split("_").str[0]
    pool["shape_file"] = pool["shape_id"].map(lambda s: str(SHAPE_DIR / f"{s}.csv"))
    pool = pool[pool["shape_file"].map(lambda p: Path(p).exists())].copy()

    shape_cols = [col for col in v12.columns if col.startswith(SHAPE_FEATURE_PREFIXES)]
    shape_cols = ["shape_id", "shape_family", *[col for col in shape_cols if col not in {"shape_id", "shape_family"}]]
    shape_features = v12[shape_cols].drop_duplicates("shape_id")
    merged = pool.merge(shape_features, on=["shape_id", "shape_family"], how="left")
    return merged.dropna(subset=["shape_area"]).reset_index(drop=True)


def random_params(rng: np.random.Generator) -> dict[str, float]:
    return {name: float(rng.uniform(low, high)) for name, (low, high) in PARAM_BOUNDS.items()}


def jitter_params(base: pd.Series, rng: np.random.Generator) -> dict[str, float]:
    params: dict[str, float] = {}
    for name in PARAM_COLS:
        low, high = PARAM_BOUNDS[name]
        span = high - low
        center = float(base.get(name, (low + high) / 2))
        value = center + float(rng.normal(0, 0.035 * span))
        params[name] = float(np.clip(value, low, high))
    return params


def rounded_params(params: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, value in params.items():
        digits = 6 if name != "r0" else 7
        out[name] = round(float(value), digits)
    return out


def generate_candidate_pool(n_per_band: int = 600, min_per_band: int = 100, seed: int = 20260519) -> pd.DataFrame:
    ensure_dirs()
    v12 = read_v12_minimal()
    v12 = v12[v12["target_band_tag"].isin(BAND_ORDER)].copy()
    v12_keys, ga_keys, existing_ch5_keys, v12_no_point, ga_no_point = load_seen_sets(v12)
    seen_keys = v12_keys | ga_keys | existing_ch5_keys
    seen_no_point = v12_no_point | ga_no_point
    shape_pool = load_shape_pool_and_features(v12)

    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for band_tag in BAND_ORDER:
        band_v12 = v12[v12["target_band_tag"] == band_tag].copy()
        active_like = band_v12.sort_values(["target_gap_cover_ratio", "target_gap_overlap_Hz"], ascending=False).head(min(1000, len(band_v12)))
        accepted = 0
        attempts = 0
        local_keys: set[str] = set()
        while accepted < n_per_band and attempts < n_per_band * 300:
            attempts += 1
            use_jitter = len(active_like) > 0 and rng.random() < 0.65
            if use_jitter:
                base = active_like.iloc[int(rng.integers(0, len(active_like)))]
                params = jitter_params(base, rng)
                if rng.random() < 0.70 and str(base.get("shape_id", "")) in set(shape_pool["shape_id"]):
                    shape_row = shape_pool[shape_pool["shape_id"] == str(base["shape_id"])].sample(n=1, random_state=int(rng.integers(0, 2**31 - 1))).iloc[0]
                else:
                    shape_row = shape_pool.iloc[int(rng.integers(0, len(shape_pool)))]
                source = "jitter_from_v12_distribution"
            else:
                params = random_params(rng)
                shape_row = shape_pool.iloc[int(rng.integers(0, len(shape_pool)))]
                source = "uniform_design_domain"
            params = rounded_params(params)
            cand_idx = accepted + 1
            candidate_id = f"strict_{band_tag}_c{cand_idx:04d}"
            point_id = f"strict_{band_tag}_p{cand_idx:04d}"
            row: dict[str, Any] = {
                "target_band": BAND_LABEL[band_tag],
                "target_band_tag": band_tag,
                "target_band_low_Hz": BAND_LOW[band_tag],
                "target_band_high_Hz": BAND_HIGH[band_tag],
                "target_band_width_Hz": BAND_HIGH[band_tag] - BAND_LOW[band_tag],
                "candidate_id": candidate_id,
                "point_id": point_id,
                "shape_id": str(shape_row["shape_id"]),
                "shape_family": str(shape_row["shape_family"]),
                "shape_file": str(shape_row["shape_file"]),
                "source": source,
            }
            row.update(params)
            for col in shape_pool.columns:
                if col.startswith("shape_") and col not in row:
                    row[col] = shape_row[col]
            row["physical_key"] = canonical_key(row)
            row["_no_point_key"] = no_point_key(row)
            if not row["physical_key"] or row["physical_key"] in seen_keys or row["physical_key"] in local_keys:
                continue
            if row["_no_point_key"] in seen_no_point:
                continue
            row["in_v12_training_set"] = row["physical_key"] in v12_keys
            row["in_ga20_history"] = row["physical_key"] in ga_keys
            row["in_existing_ch5"] = row["physical_key"] in existing_ch5_keys
            row["strict_holdout_valid"] = not (row["in_v12_training_set"] or row["in_ga20_history"] or row["in_existing_ch5"])
            row["note"] = "strict physical_key and parameter-shape-band key unseen"
            rows.append(row)
            local_keys.add(row["physical_key"])
            accepted += 1
        if accepted < min_per_band:
            raise RuntimeError(f"Only generated {accepted} strict holdout candidates for {band_tag}")

    pool = pd.DataFrame(rows)
    pool = pool.drop(columns=["_no_point_key"], errors="ignore")
    save_table(pool, "ch5_strict_holdout_candidate_pool", max_md_rows=120)
    return pool


def predict_pool(pool: pd.DataFrame) -> pd.DataFrame:
    bundle = joblib.load(FINAL_MODEL)
    scored, _ = build_tail_prediction_frame(pool.copy())
    feature_cols = bundle["feature_cols"]
    X = scored.reindex(columns=feature_cols)
    fill_values = pd.Series(bundle.get("fill_values", {}))
    X = X.fillna(fill_values).fillna(0)
    scored["predicted_open_prob"] = bundle["classifier"].predict_proba(X)[:, 1]
    scored["predicted_cover_ratio"] = np.clip(bundle["regressor"].predict(X), 0, 1)
    scored["predicted_overlap_Hz"] = scored["predicted_cover_ratio"] * scored["target_band_width_Hz"]
    scored["predicted_score"] = scored["predicted_open_prob"] * scored["predicted_cover_ratio"]
    scored = scored.sort_values(["target_band_tag", "predicted_score", "predicted_cover_ratio", "predicted_open_prob"], ascending=[True, False, False, False])
    scored["rank_in_band"] = scored.groupby("target_band_tag").cumcount() + 1
    save_table(scored, "ch5_strict_holdout_predictions", max_md_rows=120)
    return scored


def build_manifest(predictions: pd.DataFrame, seed: int = 20260520) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frames: list[pd.DataFrame] = []
    used_keys: set[str] = set()
    for band_tag in BAND_ORDER:
        band = predictions[predictions["target_band_tag"] == band_tag].copy()
        top = band.sort_values(["predicted_score", "predicted_cover_ratio"], ascending=False).head(5).copy()
        top["method"] = "predicted_top5"
        top["validation_rank"] = np.arange(1, len(top) + 1)
        used_keys.update(top["physical_key"])
        frames.append(top)

        rest = band[~band["physical_key"].isin(used_keys)].copy()
        sample_n = min(5, len(rest))
        random_idx = rng.choice(rest.index.to_numpy(), size=sample_n, replace=False)
        rand = rest.loc[random_idx].copy()
        rand["method"] = "random5"
        rand["validation_rank"] = np.arange(1, len(rand) + 1)
        used_keys.update(rand["physical_key"])
        frames.append(rand)

    manifest = pd.concat(frames, ignore_index=True)
    manifest["comsol_status"] = "pending"
    manifest["output_dir"] = str(COMSOL_OUT_DIR)
    manifest["note"] = "first-stage strict_holdout COMSOL validation manifest"
    order_cols = [
        "target_band", "target_band_tag", "target_band_low_Hz", "target_band_high_Hz", "target_band_width_Hz",
        "method", "validation_rank", "candidate_id", "point_id", "physical_key", "shape_id", "shape_family", "shape_file",
        *PARAM_COLS, "predicted_open_prob", "predicted_cover_ratio", "predicted_overlap_Hz", "predicted_score",
        "comsol_status", "output_dir", "note",
    ]
    manifest = manifest[[col for col in order_cols if col in manifest.columns] + [col for col in manifest.columns if col not in order_cols]]
    save_table(manifest, "ch5_strict_holdout_comsol_manifest_top5_random5", max_md_rows=None)
    return manifest


def prepare(args: argparse.Namespace) -> None:
    pool = generate_candidate_pool(n_per_band=args.n_per_band, min_per_band=args.min_per_band, seed=args.seed)
    predictions = predict_pool(pool)
    build_manifest(predictions, seed=args.seed + 1)
    checklist = {
        "candidate_pool_csv": str(OUT_DIR / "ch5_strict_holdout_candidate_pool.csv"),
        "predictions_csv": str(OUT_DIR / "ch5_strict_holdout_predictions.csv"),
        "manifest_csv": str(OUT_DIR / "ch5_strict_holdout_comsol_manifest_top5_random5.csv"),
        "n_per_band": predictions.groupby("target_band").size().to_dict(),
        "manifest_count": int(pd.read_csv(OUT_DIR / "ch5_strict_holdout_comsol_manifest_top5_random5.csv").shape[0]),
    }
    (OUT_DIR / "CH5_STRICT_HOLDOUT_PREPARE_CHECKLIST.json").write_text(json.dumps(checklist, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(checklist, ensure_ascii=False, indent=2))


def load_results() -> pd.DataFrame:
    final_path = OUT_DIR / "ch5_strict_holdout_comsol_results_top5_random5.csv"
    if final_path.exists():
        return pd.read_csv(final_path, low_memory=False)
    shards = sorted(OUT_DIR.glob("ch5_strict_holdout_comsol_results_top5_random5_worker*.csv"))
    if not shards:
        raise FileNotFoundError("No COMSOL result CSV found yet.")
    frames = [pd.read_csv(path, low_memory=False) for path in shards]
    results = pd.concat(frames, ignore_index=True)
    results = results.drop_duplicates(["candidate_id", "method"], keep="last")
    results = results.sort_values(["target_band_low_Hz", "method", "validation_rank"])
    save_table(results, "ch5_strict_holdout_comsol_results_top5_random5", max_md_rows=None)
    return results


def summarize_results(results: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (band, method), sub in results.groupby(["target_band", "method"], sort=False):
        success = sub[sub["solve_success"].astype(str).str.lower().isin(["true", "1"]) | (sub["solve_success"] == 1)].copy()
        active = success[pd.to_numeric(success["true_overlap_Hz"], errors="coerce").fillna(0) > 0].copy()
        if len(success) > 0:
            best_idx = pd.to_numeric(success["true_overlap_Hz"], errors="coerce").fillna(-1).idxmax()
            best = success.loc[best_idx]
        else:
            best = pd.Series(dtype=object)
        rows.append(
            {
                "target_band": band,
                "method": method,
                "n_candidates": int(len(sub)),
                "n_solve_success": int(len(success)),
                "solve_success_rate": float(len(success) / max(1, len(sub))),
                "n_active": int(len(active)),
                "active_rate": float(len(active) / max(1, len(success))),
                "best_true_overlap_Hz": float(best.get("true_overlap_Hz", 0) if len(best) else 0),
                "mean_true_overlap_Hz": float(pd.to_numeric(success["true_overlap_Hz"], errors="coerce").mean()) if len(success) else math.nan,
                "median_true_overlap_Hz": float(pd.to_numeric(success["true_overlap_Hz"], errors="coerce").median()) if len(success) else math.nan,
                "best_true_cover_ratio": float(best.get("true_cover_ratio", 0) if len(best) else 0),
                "mean_true_cover_ratio": float(pd.to_numeric(success["true_cover_ratio"], errors="coerce").mean()) if len(success) else math.nan,
                "median_true_cover_ratio": float(pd.to_numeric(success["true_cover_ratio"], errors="coerce").median()) if len(success) else math.nan,
                "best_candidate_id": str(best.get("candidate_id", "")) if len(best) else "",
                "best_validation_rank": best.get("validation_rank", np.nan) if len(best) else np.nan,
                "best_predicted_score": best.get("predicted_score", np.nan) if len(best) else np.nan,
                "note": "",
            }
        )
    summary = pd.DataFrame(rows)
    save_table(summary, "ch5_strict_holdout_summary", max_md_rows=None)
    return summary


def compare_with_ga20(summary: pd.DataFrame) -> pd.DataFrame:
    ga = pd.read_csv(CH4_SUMMARY)
    rows: list[dict[str, Any]] = []
    for _, grow in ga.iterrows():
        band = str(grow["target_band"]).replace("-", "\u2013")
        pred = summary[(summary["target_band"] == band) & (summary["method"] == "predicted_top5")]
        rand = summary[(summary["target_band"] == band) & (summary["method"] == "random5")]
        p = pred.iloc[0] if len(pred) else pd.Series(dtype=object)
        r = rand.iloc[0] if len(rand) else pd.Series(dtype=object)
        ga_overlap = float(grow["best_target_overlap_Hz"])
        ga_cover = float(grow["best_cover_ratio"])
        p_overlap = float(p.get("best_true_overlap_Hz", 0) if len(p) else 0)
        r_overlap = float(r.get("best_true_overlap_Hz", 0) if len(r) else 0)
        p_cover = float(p.get("best_true_cover_ratio", 0) if len(p) else 0)
        r_cover = float(r.get("best_true_cover_ratio", 0) if len(r) else 0)
        conclusion = "pred_better" if (p_overlap > r_overlap + 1e-9 or p_cover > r_cover + 1e-9) else "random_not_worse"
        rows.append(
            {
                "target_band": band,
                "ga20_best_overlap_Hz": ga_overlap,
                "ga20_best_cover_ratio": ga_cover,
                "ga20_evaluations": int(grow["n_evaluations_actual"]),
                "strict_pred_top5_best_overlap_Hz": p_overlap,
                "strict_pred_top5_best_cover_ratio": p_cover,
                "strict_random5_best_overlap_Hz": r_overlap,
                "strict_random5_best_cover_ratio": r_cover,
                "strict_pred_top5_to_ga_overlap_ratio": p_overlap / max(ga_overlap, 1e-9),
                "strict_pred_top5_to_ga_cover_ratio": p_cover / max(ga_cover, 1e-9),
                "strict_random5_to_ga_overlap_ratio": r_overlap / max(ga_overlap, 1e-9),
                "strict_random5_to_ga_cover_ratio": r_cover / max(ga_cover, 1e-9),
                "pred_minus_random_overlap": p_overlap - r_overlap,
                "pred_minus_random_cover": p_cover - r_cover,
                "conclusion_tag": conclusion,
                "note": "",
            }
        )
    comp = pd.DataFrame(rows)
    save_table(comp, "ch5_strict_holdout_vs_ga20", max_md_rows=None)
    return comp


def draw_shape(ax: plt.Axes, shape_id: str) -> None:
    path = SHAPE_DIR / f"{shape_id}.csv"
    ax.axis("off")
    if not path.exists():
        ax.text(0.5, 0.5, "缺少轮廓", ha="center", va="center", fontsize=8)
        return
    xy = pd.read_csv(path)
    ax.fill(xy["x"], xy["y"], color="#9DB4C0", edgecolor="#333333", linewidth=0.7)
    pad = max(xy["x"].max() - xy["x"].min(), xy["y"].max() - xy["y"].min()) * 0.2
    ax.set_xlim(xy["x"].min() - pad, xy["x"].max() + pad)
    ax.set_ylim(xy["y"].min() - pad, xy["y"].max() + pad)


def draw_figures(results: pd.DataFrame, summary: pd.DataFrame, comp: pd.DataFrame) -> dict[str, dict[str, str]]:
    outputs: dict[str, dict[str, str]] = {}
    configure_fonts()

    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    ax.axis("off")
    boxes = [
        (0.10, 0.58, "候选生成\n排除seen key"),
        (0.32, 0.58, "v12最终模型\n预测排序"),
        (0.54, 0.58, "Top5/random5\n60次清单"),
        (0.76, 0.58, "COMSOL真实\n频散验证"),
        (0.54, 0.22, "第4章GA20\n基准对比"),
    ]
    for x, y, text in boxes:
        ax.text(x, y, text, ha="center", va="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.35", facecolor="#F7F7F7", edgecolor="#555555"))
    for x1, y1, x2, y2 in [(0.20, .58, .25, .58), (.42, .58, .47, .58), (.64, .58, .69, .58), (.76, .45, .58, .29)]:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.0, color="#555555"))
    ax.set_title("strict_holdout独立验证流程", fontsize=12)
    outputs["ch5_strict_fig1_holdout_pipeline"] = save_fig(fig, "ch5_strict_fig1_holdout_pipeline")

    labels = [BAND_LABEL[tag] for tag in BAND_ORDER]
    x = np.arange(len(labels))
    width = 0.35
    metric_specs = [
        ("active_rate", "ch5_strict_fig2_pred_vs_random_active_rate", "预测Top-5与随机候选有效率对比", "有效候选比例"),
        ("best_true_overlap_Hz", "ch5_strict_fig3_pred_vs_random_best_overlap", "预测Top-5与随机候选最优真实重叠宽度对比", "目标频带重叠宽度 / Hz"),
        ("best_true_cover_ratio", "ch5_strict_fig4_pred_vs_random_best_cover", "预测Top-5与随机候选最优真实覆盖率对比", "目标频带覆盖率"),
    ]
    for metric, stem, title, ylabel in metric_specs:
        fig, ax = plt.subplots(figsize=(6.4, 3.7))
        for i, method in enumerate(["predicted_top5", "random5"]):
            vals = []
            for label in labels:
                sub = summary[(summary["target_band"] == label) & (summary["method"] == method)]
                vals.append(float(sub[metric].iloc[0]) if len(sub) else 0.0)
            ax.bar(x + (i - 0.5) * width, vals, width, label=method, color=PALETTE[method], edgecolor="#333333", linewidth=0.7, alpha=0.88)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_title(title)
        ax.set_xlabel("目标频带")
        ax.set_ylabel(ylabel)
        ax.legend(loc="upper right")
        style_axis(ax)
        outputs[stem] = save_fig(fig, stem)

    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    vals = [float(comp[comp["target_band"] == label]["strict_pred_top5_to_ga_overlap_ratio"].iloc[0]) if len(comp[comp["target_band"] == label]) else 0 for label in labels]
    ax.bar(x, vals, width=0.55, color=PALETTE["predicted_top5"], edgecolor="#333333", linewidth=0.7, alpha=0.88)
    ax.axhline(1.0, color="#666666", linewidth=0.9, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_title("strict predicted Top-5达到GA20最优的比例")
    ax.set_xlabel("目标频带")
    ax.set_ylabel("Top-5 / GA20 最优重叠宽度")
    style_axis(ax)
    outputs["ch5_strict_fig5_vs_ga20_ratio"] = save_fig(fig, "ch5_strict_fig5_vs_ga20_ratio")

    case_bands = ["180\u2013220 Hz", "200\u2013240 Hz", "240\u2013280 Hz"]
    fig, axes = plt.subplots(len(case_bands), 2, figsize=(5.8, 5.8))
    for r, band in enumerate(case_bands):
        for c, method in enumerate(["predicted_top5", "random5"]):
            ax = axes[r, c]
            sub = results[(results["target_band"] == band) & (results["method"] == method)].copy()
            if len(sub):
                sub["_overlap"] = pd.to_numeric(sub["true_overlap_Hz"], errors="coerce").fillna(-1)
                best = sub.sort_values("_overlap", ascending=False).iloc[0]
                draw_shape(ax, str(best["shape_id"]))
                ax.set_title(f"{band}\n{method} {float(best['true_overlap_Hz']):.2f} Hz", fontsize=8)
            else:
                ax.axis("off")
    fig.suptitle("典型目标频带结构单胞对比", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    outputs["ch5_strict_fig6_typical_unit_cells"] = save_fig(fig, "ch5_strict_fig6_typical_unit_cells")

    fig, axes = plt.subplots(1, len(case_bands), figsize=(7.2, 2.8))
    for ax, band in zip(axes, case_bands):
        sub = results[(results["target_band"] == band) & (results["method"] == "predicted_top5")].copy()
        sub["_overlap"] = pd.to_numeric(sub["true_overlap_Hz"], errors="coerce").fillna(-1)
        if len(sub):
            best = sub.sort_values("_overlap", ascending=False).iloc[0]
            tbl = Path(str(best.get("tbl1_path", "")))
            if tbl.exists():
                data = []
                with tbl.open("r", encoding="utf-8", errors="ignore") as handle:
                    for line in handle:
                        if not line.strip() or line.startswith("%"):
                            continue
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 3:
                            try:
                                data.append((float(parts[0]), float(complex(parts[-1].replace("i", "j")).real)))
                            except Exception:
                                pass
                if data:
                    arr = np.array(data)
                    ax.scatter(arr[:, 0], arr[:, 1], s=2.0, color=PALETTE["predicted_top5"], alpha=0.55)
            low = float(best["target_band_low_Hz"])
            high = float(best["target_band_high_Hz"])
            ax.axhspan(low, high, color="#F28E2B", alpha=0.16)
            ax.set_title(band, fontsize=9)
            ax.set_xlabel("波矢参数")
            ax.set_ylabel("频率 / Hz")
            style_axis(ax)
        else:
            ax.axis("off")
    fig.suptitle("典型目标频带频散曲线与目标频带标注", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    outputs["ch5_strict_fig7_typical_dispersion"] = save_fig(fig, "ch5_strict_fig7_typical_dispersion")
    return outputs


def write_report(results: pd.DataFrame, summary: pd.DataFrame, comp: pd.DataFrame, outputs: dict[str, dict[str, str]], terminal: dict[str, Any]) -> None:
    summary_preview = summary.copy()
    comp_preview = comp.copy()
    lines = [
        "# 第5章 strict_holdout 小规模独立验证补充报告",
        "",
        "## 1. 实验目的",
        "",
        "原第5章 engineering_screening 结果中，预测候选和随机候选均来自 v12 已清洗候选池，strict_holdout 样本不足。因此本补充实验重新构建未见候选集，并用第三章最终 v12 模型进行排序，再以 COMSOL 真实频散计算给出独立验证结果。",
        "",
        "## 2. 独立候选构建方法",
        "",
        "候选池构建时同时排除了 v12 训练集、第4章 GA20 历史记录以及已有第5章 predicted_topk/random 使用过的 physical_key。为避免仅更换 point_id 造成伪独立，脚本还检查了不含 point_id 的 shape-parameter-band key。候选结构使用已有可重建的 shape_id/shape_family，连续参数限定在论文使用的参数化设计域内。",
        "",
        "## 3. 预测排序与验证清单",
        "",
        "排序模型未重新训练，直接加载第三章最终模型包 `final_predictor_bundle.joblib`。综合评分定义为 `predicted_score = predicted_open_prob × predicted_cover_ratio`，每个目标频带选取预测最高的 Top-5，并从同一 strict_holdout 候选池中随机抽取 random5，形成 60 次 COMSOL 验证清单。",
        "",
        "## 4. COMSOL 验证结果",
        "",
        "统计表见 `ch5_strict_holdout_summary.csv/md`。",
        "",
        "| target_band | method | n_candidates | n_solve_success | active_rate | best_true_overlap_Hz | best_true_cover_ratio | best_candidate_id |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary_preview.itertuples(index=False):
        lines.append(f"| {row.target_band} | {row.method} | {row.n_candidates} | {row.n_solve_success} | {row.active_rate:.3f} | {row.best_true_overlap_Hz:.3f} | {row.best_true_cover_ratio:.3f} | {row.best_candidate_id} |")
    lines.extend([
        "",
        "## 5. 与真实 GA20 基准对比",
        "",
        "对比表见 `ch5_strict_holdout_vs_ga20.csv/md`。",
        "",
        "| target_band | pred_top5/GA overlap | random5/GA overlap | pred_minus_random_overlap | conclusion_tag |",
        "| --- | ---: | ---: | ---: | --- |",
    ])
    for row in comp_preview.itertuples(index=False):
        lines.append(f"| {row.target_band} | {row.strict_pred_top5_to_ga_overlap_ratio:.3f} | {row.strict_random5_to_ga_overlap_ratio:.3f} | {row.pred_minus_random_overlap:.3f} | {row.conclusion_tag} |")
    lines.extend([
        "",
        "## 6. 结论与论文写法建议",
        "",
        "1. 该补充实验可以作为第5章 strict_holdout 独立验证材料，优先用于支撑“有限预算下预测 Top-k 相比随机候选具有一定筛选优势”这一谨慎表述。",
        "2. 若某些目标频带中 random5 不弱于 predicted_top5，应在正文中如实说明，避免写成预测模型稳定替代真实 GA。",
        "3. 第4章 GA20 仍是完整真实优化基准；本实验只说明预测模型在小预算候选筛选中的作用。",
        "4. 高频频带若仍表现较弱，应归入结构族与参数空间可达性边界分析，而不是简单归咎于排序模型。",
        "",
        "## 图件清单",
        "",
    ])
    for stem, paths in outputs.items():
        lines.append(f"- `{stem}`: `{Path(paths['png']).name}`, `{Path(paths['svg']).name}`, `{Path(paths['pdf']).name}`")
    lines.extend(["", "## 终端清单", "", "```json", json.dumps(terminal, ensure_ascii=False, indent=2), "```"])
    (OUT_DIR / "CH5_STRICT_HOLDOUT_VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def analyze(_: argparse.Namespace) -> None:
    ensure_dirs()
    results = load_results()
    if "true_overlap_Hz" not in results.columns:
        raise ValueError("COMSOL results are missing true_overlap_Hz.")
    if "active_open" not in results.columns:
        results["active_open"] = pd.to_numeric(results["true_overlap_Hz"], errors="coerce").fillna(0) > 0
    save_table(results, "ch5_strict_holdout_comsol_results_top5_random5", max_md_rows=None)
    summary = summarize_results(results)
    comp = compare_with_ga20(summary)
    outputs = draw_figures(results, summary, comp)

    terminal = {
        "candidate_pool_per_band": pd.read_csv(OUT_DIR / "ch5_strict_holdout_candidate_pool.csv").groupby("target_band").size().to_dict(),
        "manifest_count": int(pd.read_csv(OUT_DIR / "ch5_strict_holdout_comsol_manifest_top5_random5.csv").shape[0]),
        "solve_success_count": int(summary["n_solve_success"].sum()),
        "predicted_top5_better_than_random5_by_band": {
            row.target_band: bool(row.pred_minus_random_overlap > 1e-9 or row.pred_minus_random_cover > 1e-9)
            for row in comp.itertuples(index=False)
        },
        "predicted_top5_to_ga20_overlap_ratio": {
            row.target_band: float(row.strict_pred_top5_to_ga_overlap_ratio)
            for row in comp.itertuples(index=False)
        },
        "generated_files": sorted([p.name for p in OUT_DIR.glob("*") if p.is_file()] + [f"figures/{p.name}" for p in FIG_DIR.glob("*") if p.is_file()]),
        "recommend_extend_top10_random10": "根据Top5结果，若predicted_top5在多数频带优于random5且COMSOL成功率稳定，建议扩展；若高频仍明显失败，优先改结构族候选池。",
    }
    (OUT_DIR / "CH5_STRICT_HOLDOUT_TERMINAL_CHECKLIST.json").write_text(json.dumps(terminal, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(results, summary, comp, outputs, terminal)
    print(json.dumps(terminal, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--n-per-band", type=int, default=600)
    p_prepare.add_argument("--min-per-band", type=int, default=100)
    p_prepare.add_argument("--seed", type=int, default=20260519)
    p_prepare.set_defaults(func=prepare)
    p_analyze = sub.add_parser("analyze")
    p_analyze.set_defaults(func=analyze)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
