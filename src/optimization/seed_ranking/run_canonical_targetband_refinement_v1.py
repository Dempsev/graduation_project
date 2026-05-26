from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_TRAINING = ROOT / "stage3_training"
if str(STAGE3_TRAINING) not in sys.path:
    sys.path.insert(0, str(STAGE3_TRAINING))

from optimization.seed_ranking.run_targetband_seed_scoring_v1 import assign_targetband_scores
from prediction_targetband_param_v1.models.inference import build_targetband_prediction_frame
from prediction_targetband_param_v1.tools.build_canonical_local_robustness_manifest_v1 import (
    CANONICAL_CASES,
    select_center_rows,
)
from stage3_training.ml_common import save_csv_rows, save_json
from stage3_training.run_seed_discovery_scoring_v7 import predict_classifier_rows, resolve_path


DEFAULT_HISTORY_CSV = (
    ROOT / "data" / "comsol_batch" / "comsol_in_loop_band_supplement_exploratory_v2" / "ga_band_catalog_best_candidates_v1.csv"
)
DEFAULT_OUT_ROOT = ROOT / "data" / "ml_runs" / "canonical_targetband_refinement_v1"
DEFAULT_CONTACT_RUN = ROOT / "data" / "ml_runs" / "mlp_contact_valid_parametric_seed_discovery_v7_full"
DEFAULT_CLASSIFIER_RUN = ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cls_dense_family" / "stratified_group_kfold"
DEFAULT_REGRESSOR_RUN = ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cover_dense_family" / "stratified_group_kfold"

PILOT_CASE_IDS = [
    "band240_280_ep253",
    "band220_260_ep253",
]

GLOBAL_BOUNDS: Dict[str, Tuple[float, float]] = {
    "a1": (0.42, 0.58),
    "a2": (-0.24, 0.00),
    "b1": (-0.08, 0.08),
    "b2": (-0.04, 0.12),
    "a3": (-0.06, 0.06),
    "b3": (-0.06, 0.06),
    "a4": (-0.05, 0.05),
    "b4": (-0.05, 0.05),
    "a5": (-0.04, 0.04),
    "b5": (-0.04, 0.04),
    "r0": (0.008, 0.016),
}

LOCAL_HALF_WIDTHS: Dict[str, float] = {
    "a1": 0.0030,
    "a2": 0.0040,
    "b1": 0.0,
    "b2": 0.0040,
    "a3": 0.0,
    "b3": 0.0,
    "a4": 0.0,
    "b4": 0.0,
    "a5": 0.0,
    "b5": 0.0,
    "r0": 0.00018,
}

PARAM_COLS = list(GLOBAL_BOUNDS.keys())
ACTIVE_PARAM_COLS = ["a1", "a2", "b2", "r0"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run lightweight target-band local refinement around canonical cases."
    )
    parser.add_argument("--history-csv", type=Path, default=DEFAULT_HISTORY_CSV)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--contact-run-root", type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument("--contact-split", default="shape_family")
    parser.add_argument("--classifier-run-root", type=Path, default=DEFAULT_CLASSIFIER_RUN)
    parser.add_argument("--regressor-run-root", type=Path, default=DEFAULT_REGRESSOR_RUN)
    parser.add_argument("--case-ids", nargs="*", default=PILOT_CASE_IDS)
    parser.add_argument("--population-size", type=int, default=24)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--elite-k", type=int, default=4)
    parser.add_argument("--mutation-rate", type=float, default=0.22)
    parser.add_argument("--mutation-scale", type=float, default=0.10)
    parser.add_argument("--local-span-scale", type=float, default=1.0)
    parser.add_argument("--contact-threshold", type=float, default=0.50)
    parser.add_argument("--open-threshold", type=float, default=0.50)
    parser.add_argument("--cover-preserve-cap", type=float, default=0.12)
    parser.add_argument("--overlap-preserve-cap", type=float, default=8.0)
    parser.add_argument("--top-k-export", type=int, default=8)
    parser.add_argument("--validation-k-per-case", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260422)
    return parser.parse_args()


def numeric(value: object, default: float = 0.0) -> float:
    val = pd.to_numeric([value], errors="coerce")[0]
    if pd.isna(val):
        return float(default)
    return float(val)


def resolve_cases(case_ids: Iterable[str]) -> List[Dict[str, object]]:
    requested = [str(item).strip() for item in case_ids if str(item).strip()]
    if not requested:
        requested = list(PILOT_CASE_IDS)
    by_id = {str(case["case_id"]): case for case in CANONICAL_CASES}
    missing = [case_id for case_id in requested if case_id not in by_id]
    if missing:
        raise ValueError(f"Unknown canonical case ids: {missing}")
    return [by_id[case_id] for case_id in requested]


def build_local_bounds(
    base_row: pd.Series,
    local_span_scale: float,
) -> Dict[str, Tuple[float, float]]:
    bounds: Dict[str, Tuple[float, float]] = {}
    span_scale = float(np.clip(local_span_scale, 0.25, 1.0))
    for name, (global_lo, global_hi) in GLOBAL_BOUNDS.items():
        base_value = numeric(base_row.get(name, global_lo), default=global_lo)
        half_width = float(LOCAL_HALF_WIDTHS.get(name, 0.0)) * span_scale
        if name not in ACTIVE_PARAM_COLS or global_lo == global_hi or half_width <= 0.0:
            fixed_value = float(np.clip(base_value, global_lo, global_hi))
            bounds[name] = (fixed_value, fixed_value)
            continue
        bounds[name] = (
            float(max(global_lo, base_value - half_width)),
            float(min(global_hi, base_value + half_width)),
        )
    return bounds


def clip_gene(name: str, value: float, bounds: Dict[str, Tuple[float, float]]) -> float:
    lo, hi = bounds[name]
    if hi <= lo:
        return float(lo)
    return float(np.clip(value, lo, hi))


def make_individual(
    base_row: pd.Series,
    bounds: Dict[str, Tuple[float, float]],
    rng: np.random.Generator,
    jitter_scale: float,
) -> Dict[str, float]:
    genes: Dict[str, float] = {}
    for name in PARAM_COLS:
        base_value = numeric(base_row.get(name, 0.0))
        lo, hi = bounds[name]
        if hi <= lo or name not in ACTIVE_PARAM_COLS:
            genes[name] = float(base_value)
            continue
        span = hi - lo
        if name == "r0":
            # Favor safer inward exploration instead of pushing further upward.
            trial = base_value - abs(rng.normal(0.0, span * max(jitter_scale, 0.08)))
        elif rng.random() < 0.90:
            trial = base_value + rng.normal(0.0, span * jitter_scale)
        else:
            trial = rng.uniform(lo, hi)
        genes[name] = clip_gene(name, trial, bounds)
    return genes


def crossover(
    parent_a: Dict[str, float],
    parent_b: Dict[str, float],
    bounds: Dict[str, Tuple[float, float]],
    rng: np.random.Generator,
) -> Dict[str, float]:
    child: Dict[str, float] = {}
    for name in PARAM_COLS:
        if name not in ACTIVE_PARAM_COLS:
            child[name] = float(parent_a[name])
            continue
        alpha = rng.random()
        child[name] = clip_gene(name, alpha * parent_a[name] + (1.0 - alpha) * parent_b[name], bounds)
    return child


def mutate(
    child: Dict[str, float],
    bounds: Dict[str, Tuple[float, float]],
    rng: np.random.Generator,
    mutation_rate: float,
    mutation_scale: float,
) -> Dict[str, float]:
    out = dict(child)
    for name in PARAM_COLS:
        lo, hi = bounds[name]
        if hi <= lo or name not in ACTIVE_PARAM_COLS or rng.random() > mutation_rate:
            continue
        span = hi - lo
        if name == "r0":
            delta = -abs(rng.normal(0.0, span * mutation_scale))
        else:
            delta = rng.normal(0.0, span * mutation_scale)
        out[name] = clip_gene(name, out[name] + delta, bounds)
    return out


def build_population_frame(
    base_row: pd.Series,
    population: List[Dict[str, float]],
    case: Dict[str, object],
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    case_id = str(case["case_id"])
    for idx, genes in enumerate(population, start=1):
        row = base_row.to_dict()
        row.update(genes)
        row["candidate_id"] = f"{case_id}_refine_{idx:03d}"
        row["pool_arm"] = "canonical_targetband_refinement"
        row["point_strategy"] = "canonical_targetband_refinement_v1"
        row["sample_id"] = f"{row.get('shape_id', 'shape')}__{case_id}__{idx:03d}"
        row["canonical_case_id"] = case_id
        row["target_band_tag"] = str(case["target_band_tag"])
        row["target_band_low_Hz"] = float(case["target_band_low_Hz"])
        row["target_band_high_Hz"] = float(case["target_band_high_Hz"])
        rows.append(row)
    frame = pd.DataFrame(rows)
    # The contact-valid checkpoint expects stage1-reference columns to exist,
    # even when this refinement run intentionally has no stage1 anchor.
    defaults: Dict[str, object] = {
        "stage1_reference_candidate_tier": "",
        "stage1_reference_sample_id": "",
        "stage1_reference_gap_Hz": np.nan,
        "stage1_reference_contact_length": np.nan,
        "stage1_reference_gap_gain_Hz": np.nan,
    }
    for col, default in defaults.items():
        if col not in frame.columns:
            frame[col] = default
    return frame


def normalized_distance(
    scored: pd.DataFrame,
    base_row: pd.Series,
    bounds: Dict[str, Tuple[float, float]],
) -> np.ndarray:
    distances: List[np.ndarray] = []
    for name in ACTIVE_PARAM_COLS:
        lo, hi = bounds[name]
        if hi <= lo:
            continue
        base_value = numeric(base_row.get(name, lo), default=lo)
        dist = np.abs(scored[name].to_numpy(dtype=float) - base_value) / (hi - lo)
        distances.append(dist)
    if not distances:
        return np.zeros(len(scored), dtype=float)
    return np.mean(np.vstack(distances), axis=0)


def r0_distance(
    scored: pd.DataFrame,
    base_row: pd.Series,
    bounds: Dict[str, Tuple[float, float]],
) -> np.ndarray:
    lo, hi = bounds["r0"]
    if hi <= lo:
        return np.zeros(len(scored), dtype=float)
    base_value = numeric(base_row.get("r0", lo), default=lo)
    return np.abs(scored["r0"].to_numpy(dtype=float) - base_value) / (hi - lo)


def score_base_row(
    base_row: pd.Series,
    case: Dict[str, object],
    args: argparse.Namespace,
    bounds: Dict[str, Tuple[float, float]],
) -> pd.Series:
    case_id = str(case["case_id"])
    base_df = build_population_frame(
        base_row,
        [{name: numeric(base_row.get(name, 0.0)) for name in PARAM_COLS}],
        case,
    )
    scored = build_targetband_prediction_frame(
        base_df,
        float(case["target_band_low_Hz"]),
        float(case["target_band_high_Hz"]),
        resolve_path(args.classifier_run_root),
        resolve_path(args.regressor_run_root),
        band_tag=str(case["target_band_tag"]),
    )
    scored["contact_prob"] = predict_classifier_rows(
        scored,
        resolve_path(args.contact_run_root),
        str(args.contact_split),
    )
    scored = assign_targetband_scores(scored, args.contact_threshold, args.open_threshold)
    scored["distance_from_base"] = normalized_distance(scored, base_row, bounds)
    scored["r0_distance_from_base"] = r0_distance(scored, base_row, bounds)
    scored["case_id"] = case_id
    scored["fitness"] = scored["targetband_score"].to_numpy(dtype=float)
    return scored.iloc[0]


def score_population(
    pop_df: pd.DataFrame,
    case: Dict[str, object],
    args: argparse.Namespace,
    base_row: pd.Series,
    base_scored: pd.Series,
    bounds: Dict[str, Tuple[float, float]],
) -> pd.DataFrame:
    band_low = float(case["target_band_low_Hz"])
    band_high = float(case["target_band_high_Hz"])
    band_width = max(1e-12, band_high - band_low)
    scored = build_targetband_prediction_frame(
        pop_df,
        band_low,
        band_high,
        resolve_path(args.classifier_run_root),
        resolve_path(args.regressor_run_root),
        band_tag=str(case["target_band_tag"]),
    )
    scored["contact_prob"] = predict_classifier_rows(
        scored,
        resolve_path(args.contact_run_root),
        str(args.contact_split),
    )
    scored = assign_targetband_scores(scored, args.contact_threshold, args.open_threshold)
    scored["distance_from_base"] = normalized_distance(scored, base_row, bounds)
    scored["r0_distance_from_base"] = r0_distance(scored, base_row, bounds)

    base_cover = float(base_scored["target_gap_cover_ratio_pred"])
    base_overlap = float(base_scored["target_gap_overlap_pred_Hz"])
    base_r0 = float(base_row.get("r0", np.nan))
    local_r0_span = max(1e-12, bounds["r0"][1] - bounds["r0"][0])

    cover_delta = (
        scored["target_gap_cover_ratio_pred"].to_numpy(dtype=float) - base_cover
    ) / max(float(args.cover_preserve_cap), 1e-6)
    overlap_delta = (
        scored["target_gap_overlap_pred_Hz"].to_numpy(dtype=float) - base_overlap
    ) / max(float(args.overlap_preserve_cap), 1e-6)
    cover_delta = np.clip(cover_delta, -1.0, 1.0)
    overlap_delta = np.clip(overlap_delta, -1.0, 1.0)

    r0_values = scored["r0"].to_numpy(dtype=float)
    r0_safety_gain = np.clip((base_r0 - r0_values) / local_r0_span, 0.0, 1.0)
    target_cover = scored["target_gap_overlap_pred_Hz"].to_numpy(dtype=float) / band_width

    scored["target_cover_fraction_pred"] = np.clip(target_cover, 0.0, 1.0)
    scored["cover_delta_from_base"] = scored["target_gap_cover_ratio_pred"].to_numpy(dtype=float) - base_cover
    scored["overlap_delta_from_base_Hz"] = scored["target_gap_overlap_pred_Hz"].to_numpy(dtype=float) - base_overlap
    scored["r0_safety_gain"] = r0_safety_gain

    scored["fitness"] = (
        0.58 * scored["targetband_score"].to_numpy(dtype=float)
        + 0.08 * scored["contact_gate"].astype(float).to_numpy()
        + 0.08 * scored["target_open_gate"].astype(float).to_numpy()
        + 0.12 * cover_delta
        + 0.06 * overlap_delta
        + 0.08 * r0_safety_gain
        - 0.18 * scored["distance_from_base"].to_numpy(dtype=float)
        - 0.12 * scored["r0_distance_from_base"].to_numpy(dtype=float)
    )
    return scored.sort_values(
        [
            "fitness",
            "targetband_score",
            "target_gap_cover_ratio_pred",
            "target_gap_overlap_pred_Hz",
            "target_open_prob",
            "contact_prob",
        ],
        ascending=[False, False, False, False, False, False],
    ).copy()


def tournament_pick(pop_records: List[Dict[str, object]], rng: np.random.Generator, size: int = 3) -> Dict[str, object]:
    if len(pop_records) <= size:
        return max(pop_records, key=lambda item: float(item["fitness"]))
    idx = rng.choice(len(pop_records), size=size, replace=False)
    subset = [pop_records[int(i)] for i in idx]
    return max(subset, key=lambda item: float(item["fitness"]))


def run_case_refinement(
    base_row: pd.Series,
    case: Dict[str, object],
    args: argparse.Namespace,
    rng: np.random.Generator,
) -> Tuple[pd.DataFrame, List[Dict[str, object]], Dict[str, object]]:
    bounds = build_local_bounds(base_row, args.local_span_scale)
    base_scored = score_base_row(base_row, case, args, bounds)

    population: List[Dict[str, float]] = [{name: numeric(base_row.get(name, 0.0)) for name in PARAM_COLS}]
    while len(population) < int(args.population_size):
        population.append(make_individual(base_row, bounds, rng, jitter_scale=0.10))

    history: List[Dict[str, object]] = []
    latest_scored = pd.DataFrame()
    for generation in range(int(args.generations)):
        pop_df = build_population_frame(base_row, population, case)
        scored = score_population(pop_df, case, args, base_row, base_scored, bounds)
        latest_scored = scored.copy()
        best = scored.iloc[0]
        history.append(
            {
                "generation": generation,
                "best_fitness": float(best["fitness"]),
                "best_targetband_score": float(best["targetband_score"]),
                "best_target_cover_ratio_pred": float(best["target_gap_cover_ratio_pred"]),
                "best_target_overlap_pred_Hz": float(best["target_gap_overlap_pred_Hz"]),
                "best_contact_prob": float(best["contact_prob"]),
                "best_target_open_prob": float(best["target_open_prob"]),
                "best_distance_from_base": float(best["distance_from_base"]),
                "best_r0_distance_from_base": float(best["r0_distance_from_base"]),
                "best_r0_safety_gain": float(best["r0_safety_gain"]),
                "mean_fitness": float(scored["fitness"].mean()),
            }
        )
        records = scored.to_dict(orient="records")
        elites = records[: max(1, min(int(args.elite_k), len(records)))]
        next_population: List[Dict[str, float]] = [{name: float(elite[name]) for name in PARAM_COLS} for elite in elites]
        while len(next_population) < int(args.population_size):
            parent_a = tournament_pick(records, rng)
            parent_b = tournament_pick(records, rng)
            child = crossover(
                {name: float(parent_a[name]) for name in PARAM_COLS},
                {name: float(parent_b[name]) for name in PARAM_COLS},
                bounds,
                rng,
            )
            child = mutate(child, bounds, rng, float(args.mutation_rate), float(args.mutation_scale))
            next_population.append(child)
        population = next_population[: int(args.population_size)]

    final_scored = latest_scored.copy()
    best_row = final_scored.iloc[0]
    summary = {
        "canonical_case_id": str(case["case_id"]),
        "target_band_tag": str(case["target_band_tag"]),
        "shape_id": str(base_row.get("shape_id", "")),
        "shape_family": str(base_row.get("shape_family", "")),
        "base_sample_id": str(base_row.get("sample_id", "")),
        "base_generation": int(numeric(base_row.get("generation", 0))),
        "base_individual_index": int(numeric(base_row.get("individual_index", 0))),
        "base_archive_cover_ratio": numeric(base_row.get("archive_cover_ratio", np.nan), default=np.nan),
        "base_archive_overlap_Hz": numeric(base_row.get("archive_overlap_Hz", np.nan), default=np.nan),
        "base_gap34_lower_edge_Hz": numeric(base_row.get("gap34_lower_edge_Hz", np.nan), default=np.nan),
        "base_gap34_upper_edge_Hz": numeric(base_row.get("gap34_upper_edge_Hz", np.nan), default=np.nan),
        "base_targetband_score": float(base_scored["targetband_score"]),
        "base_target_cover_ratio_pred": float(base_scored["target_gap_cover_ratio_pred"]),
        "base_target_overlap_pred_Hz": float(base_scored["target_gap_overlap_pred_Hz"]),
        "best_targetband_score": float(best_row["targetband_score"]),
        "best_target_cover_ratio_pred": float(best_row["target_gap_cover_ratio_pred"]),
        "best_target_overlap_pred_Hz": float(best_row["target_gap_overlap_pred_Hz"]),
        "best_contact_prob": float(best_row["contact_prob"]),
        "best_target_open_prob": float(best_row["target_open_prob"]),
        "best_distance_from_base": float(best_row["distance_from_base"]),
        "best_r0_distance_from_base": float(best_row["r0_distance_from_base"]),
        "best_r0_safety_gain": float(best_row["r0_safety_gain"]),
        "delta_targetband_score": float(best_row["targetband_score"] - base_scored["targetband_score"]),
        "delta_target_cover_ratio_pred": float(best_row["target_gap_cover_ratio_pred"] - base_scored["target_gap_cover_ratio_pred"]),
        "delta_target_overlap_pred_Hz": float(best_row["target_gap_overlap_pred_Hz"] - base_scored["target_gap_overlap_pred_Hz"]),
        "base_a1": numeric(base_row.get("a1", np.nan), default=np.nan),
        "base_a2": numeric(base_row.get("a2", np.nan), default=np.nan),
        "base_b2": numeric(base_row.get("b2", np.nan), default=np.nan),
        "base_r0": numeric(base_row.get("r0", np.nan), default=np.nan),
        "best_a1": float(best_row["a1"]),
        "best_a2": float(best_row["a2"]),
        "best_b2": float(best_row["b2"]),
        "best_r0": float(best_row["r0"]),
    }
    return final_scored, history, summary


def enrich_candidate_rows(
    df: pd.DataFrame,
    case: Dict[str, object],
    base_row: pd.Series,
) -> pd.DataFrame:
    out = df.copy()
    out["canonical_case_id"] = str(case["case_id"])
    out["canonical_case_rank"] = range(1, len(out) + 1)
    out["ga_seed_shape_id"] = str(base_row.get("shape_id", ""))
    out["ga_base_point_id"] = str(base_row.get("point_id", ""))
    out["ga_base_sample_id"] = str(base_row.get("sample_id", ""))
    out["ga_base_generation"] = int(numeric(base_row.get("generation", 0)))
    out["ga_base_archive_cover_ratio"] = numeric(base_row.get("archive_cover_ratio", np.nan), default=np.nan)
    out["ga_base_archive_overlap_Hz"] = numeric(base_row.get("archive_overlap_Hz", np.nan), default=np.nan)
    out["ga_base_gap34_lower_edge_Hz"] = numeric(base_row.get("gap34_lower_edge_Hz", np.nan), default=np.nan)
    out["ga_base_gap34_upper_edge_Hz"] = numeric(base_row.get("gap34_upper_edge_Hz", np.nan), default=np.nan)
    out["delta_a1"] = out["a1"].to_numpy(dtype=float) - numeric(base_row.get("a1", 0.0))
    out["delta_a2"] = out["a2"].to_numpy(dtype=float) - numeric(base_row.get("a2", 0.0))
    out["delta_b2"] = out["b2"].to_numpy(dtype=float) - numeric(base_row.get("b2", 0.0))
    out["delta_r0"] = out["r0"].to_numpy(dtype=float) - numeric(base_row.get("r0", 0.0))
    return out


def ensure_stage4_compat_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    defaults: Dict[str, object] = {
        "positive_prob": pd.to_numeric(out.get("target_open_prob"), errors="coerce").fillna(0.0)
        if "target_open_prob" in out.columns
        else 0.0,
        "surrogate_pred_gap34_gain_Hz": 0.0,
        "class_score": pd.to_numeric(out.get("target_open_prob"), errors="coerce").fillna(0.0)
        if "target_open_prob" in out.columns
        else 0.0,
        "cascade_score": pd.to_numeric(out.get("targetband_score"), errors="coerce").fillna(0.0)
        if "targetband_score" in out.columns
        else 0.0,
        "positive_gate": out.get("target_open_gate", False),
        "reg_positive_gate": out.get("target_open_gate", False),
        "cascade_gate": out.get("targetband_gate", False),
        "rank_cascade": pd.NA,
        "rank_surrogate": pd.NA,
        "selection_source": "canonical_targetband_refinement_v1",
        "selection_label": "canonical_targetband_refinement_v1",
        "step_num": pd.NA,
        "step_offset": pd.NA,
        "step_distance": pd.to_numeric(out.get("distance_from_base"), errors="coerce")
        if "distance_from_base" in out.columns
        else pd.NA,
        "step_window": "local_refinement",
        "target_rule": "canonical_targetband_refinement_v1",
        "preferred_direction": "",
        "v5_reference_validation_id": "",
        "v5_reference_gain_Hz": pd.NA,
        "stage1_reference_sample_id": "",
        "stage1_reference_fourier_id": "",
        "stage1_reference_gap_Hz": pd.NA,
        "stage1_reference_gap_gain_Hz": pd.NA,
        "stage1_reference_contact_length": pd.NA,
        "stage1_reference_candidate_tier": "",
        "is_seed_shape": False,
        "family_prior_source": "canonical_case_freeze_v1",
        "seed_prior_source": "canonical_case_freeze_v1",
        "seed_shape_id": out.get("ga_seed_shape_id", out.get("shape_id", "")),
        "seed_family": out.get("shape_family", ""),
        "seed_tier": "canonical_case_center",
        "seed_source": "band_supplement_exploratory_v2",
    }
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default
    return out


def build_validation_manifest(df: pd.DataFrame, validation_k_per_case: int) -> pd.DataFrame:
    selected_rows: List[pd.DataFrame] = []
    for case_id, subset in df.groupby("canonical_case_id", sort=False):
        ranked = subset.sort_values(
            [
                "fitness",
                "targetband_score",
                "target_gap_cover_ratio_pred",
                "target_gap_overlap_pred_Hz",
                "distance_from_base",
            ],
            ascending=[False, False, False, False, True],
        ).copy()
        selected_rows.append(ranked.head(max(1, int(validation_k_per_case))))
    selected = pd.concat(selected_rows, ignore_index=True)
    selected = ensure_stage4_compat_columns(selected)
    selected["validation_id"] = [
        f"{case_id}__refine_{idx:02d}"
        for case_id, idx in zip(selected["canonical_case_id"].astype(str), selected.groupby("canonical_case_id").cumcount() + 1)
    ]
    selected["rank_within_source"] = selected.groupby("canonical_case_id").cumcount() + 1
    return selected


def main() -> None:
    args = parse_args()
    if int(args.population_size) < 6:
        raise ValueError("population-size must be at least 6")
    if int(args.elite_k) < 1:
        raise ValueError("elite-k must be at least 1")

    history_csv = resolve_path(args.history_csv)
    if history_csv is None or not history_csv.exists():
        raise FileNotFoundError(history_csv)

    out_root = resolve_path(args.out_root) if args.out_root else DEFAULT_OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    history = pd.read_csv(history_csv)
    active_cases = resolve_cases(args.case_ids)
    selected_lookup = {str(item["case"]["case_id"]): item["row"] for item in select_center_rows(history)}
    rng = np.random.default_rng(int(args.seed))

    all_candidates: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, object]] = []
    per_case_reports: List[Dict[str, object]] = []
    for case in active_cases:
        case_id = str(case["case_id"])
        if case_id not in selected_lookup:
            raise RuntimeError(f"Canonical case center not found: {case_id}")
        base_row = selected_lookup[case_id]
        final_scored, history_rows, summary = run_case_refinement(base_row, case, args, rng)
        final_scored = enrich_candidate_rows(final_scored, case, base_row)
        case_dir = out_root / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        final_scored.head(int(args.top_k_export)).to_csv(
            case_dir / "canonical_targetband_refinement_top_candidates_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        save_csv_rows(
            case_dir / "canonical_targetband_refinement_history_v1.csv",
            list(history_rows[0].keys()) if history_rows else ["generation"],
            history_rows,
        )
        save_json(case_dir / "canonical_targetband_refinement_summary_v1.json", summary)

        all_candidates.append(final_scored.head(int(args.top_k_export)).copy())
        summary_rows.append(summary)
        per_case_reports.append(
            {
                "canonical_case_id": case_id,
                "target_band_tag": str(case["target_band_tag"]),
                "base_archive_cover_ratio": summary["base_archive_cover_ratio"],
                "base_target_cover_ratio_pred": summary["base_target_cover_ratio_pred"],
                "best_target_cover_ratio_pred": summary["best_target_cover_ratio_pred"],
                "delta_target_cover_ratio_pred": summary["delta_target_cover_ratio_pred"],
                "base_target_overlap_pred_Hz": summary["base_target_overlap_pred_Hz"],
                "best_target_overlap_pred_Hz": summary["best_target_overlap_pred_Hz"],
                "delta_target_overlap_pred_Hz": summary["delta_target_overlap_pred_Hz"],
                "base_r0": summary["base_r0"],
                "best_r0": summary["best_r0"],
                "best_distance_from_base": summary["best_distance_from_base"],
                "best_r0_safety_gain": summary["best_r0_safety_gain"],
            }
        )

    if not all_candidates:
        raise RuntimeError("No refinement candidates were produced.")

    candidate_manifest = pd.concat(all_candidates, ignore_index=True)
    candidate_manifest_path = out_root / "canonical_targetband_refinement_candidate_manifest_v1.csv"
    candidate_manifest.to_csv(candidate_manifest_path, index=False, encoding="utf-8-sig")

    summary_csv = out_root / "canonical_targetband_refinement_summary_v1.csv"
    save_csv_rows(summary_csv, list(summary_rows[0].keys()), summary_rows)

    report_json = {
        "history_csv": str(history_csv),
        "case_ids": [str(case["case_id"]) for case in active_cases],
        "population_size": int(args.population_size),
        "generations": int(args.generations),
        "elite_k": int(args.elite_k),
        "mutation_rate": float(args.mutation_rate),
        "mutation_scale": float(args.mutation_scale),
        "local_span_scale": float(args.local_span_scale),
        "active_param_cols": list(ACTIVE_PARAM_COLS),
        "global_bounds": {key: [float(lo), float(hi)] for key, (lo, hi) in GLOBAL_BOUNDS.items()},
        "local_half_widths": {key: float(value) for key, value in LOCAL_HALF_WIDTHS.items()},
        "fitness_definition": "0.58*targetband_score + 0.08*contact_gate + 0.08*target_open_gate + 0.12*cover_preservation + 0.06*overlap_preservation + 0.08*r0_safety_gain - 0.18*distance_from_base - 0.12*r0_distance_from_base",
        "notes": [
            "This is a canonical-case local refinement probe, not a new global search line.",
            "The trust region is centered on the real canonical solution and only opens a1/a2/b2/r0.",
            "r0 exploration is biased inward because local robustness showed r0_plus to be the riskiest direction.",
        ],
        "per_case_report": per_case_reports,
    }
    save_json(out_root / "canonical_targetband_refinement_config_v1.json", report_json)

    validation_dir = out_root / "validation_manifest_v1"
    validation_dir.mkdir(parents=True, exist_ok=True)
    validation_manifest = build_validation_manifest(candidate_manifest, int(args.validation_k_per_case))
    validation_manifest_path = validation_dir / "canonical_targetband_refinement_validation_manifest_v1.csv"
    validation_manifest.to_csv(validation_manifest_path, index=False, encoding="utf-8-sig")
    validation_summary = {
        "candidate_manifest_csv": str(candidate_manifest_path),
        "validation_manifest_rows": int(len(validation_manifest)),
        "validation_k_per_case": int(args.validation_k_per_case),
        "case_ids": [str(case["case_id"]) for case in active_cases],
        "unique_shapes": int(validation_manifest["shape_id"].astype(str).nunique()),
    }
    save_json(validation_dir / "canonical_targetband_refinement_validation_manifest_summary_v1.json", validation_summary)

    print("[DONE] canonical target-band refinement probe complete")
    print(f"[OUT] {out_root}")
    for row in per_case_reports:
        print(
            "[CASE] {case} cover_pred {base_cover:.4f} -> {best_cover:.4f} "
            "overlap_pred {base_overlap:.2f} -> {best_overlap:.2f} r0 {base_r0:.6f} -> {best_r0:.6f}".format(
                case=row["canonical_case_id"],
                base_cover=row["base_target_cover_ratio_pred"],
                best_cover=row["best_target_cover_ratio_pred"],
                base_overlap=row["base_target_overlap_pred_Hz"],
                best_overlap=row["best_target_overlap_pred_Hz"],
                base_r0=row["base_r0"],
                best_r0=row["best_r0"],
            )
        )


if __name__ == "__main__":
    main()
