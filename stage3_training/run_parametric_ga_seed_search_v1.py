from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ml_common import DEFAULT_OUT_ROOT, save_csv_rows, save_json
from run_seed_discovery_scoring_v7 import assign_scores, predict_classifier_rows, predict_regressor

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'seed_discovery_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1'
DEFAULT_CONTACT_RUN = DEFAULT_OUT_ROOT / 'mlp_contact_valid_parametric_seed_discovery_v7_full'
DEFAULT_POSITIVE_RUN = DEFAULT_OUT_ROOT / 'mlp_is_positive_shape_parametric_seed_discovery_v7_full'
DEFAULT_REG_RUN = DEFAULT_OUT_ROOT / 'mlp_gap34_gain_surrogate_v7_full'
DEFAULT_CALIBRATION_JSON = ROOT / 'stage3_training' / 'seed_discovery_scoring_calibration_v1.json'

GLOBAL_BOUNDS: Dict[str, Tuple[float, float]] = {
    'a1': (0.46, 0.54),
    'a2': (-0.18, -0.06),
    'b1': (0.0, 0.0),
    'b2': (0.0, 0.08),
    'a3': (0.0, 0.0),
    'b3': (0.0, 0.0),
    'a4': (0.0, 0.03),
    'b4': (0.0, 0.0),
    'a5': (0.0, 0.0),
    'b5': (0.0, 0.03),
    'r0': (0.010, 0.014),
}
PARAM_COLS = list(GLOBAL_BOUNDS.keys())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run parameter-level GA around shortlisted seed shapes.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--positive-run-root', type=Path, default=DEFAULT_POSITIVE_RUN)
    parser.add_argument('--positive-split', default='shape_family')
    parser.add_argument('--reg-run-root', type=Path, default=DEFAULT_REG_RUN)
    parser.add_argument('--reg-split', default='shape_family')
    parser.add_argument('--calibration-json', type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument('--top-k-seeds', type=int, default=3)
    parser.add_argument('--only-point-id', default='rf09_h00_center')
    parser.add_argument('--population-size', type=int, default=32)
    parser.add_argument('--generations', type=int, default=18)
    parser.add_argument('--elite-k', type=int, default=6)
    parser.add_argument('--mutation-rate', type=float, default=0.25)
    parser.add_argument('--mutation-scale', type=float, default=0.12)
    parser.add_argument('--local-span-scale', type=float, default=0.35)
    parser.add_argument('--surrogate-delta-cap', type=float, default=10.0)
    parser.add_argument('--seed', type=int, default=20260324)
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def resolve_scoring_settings(calibration_json: Path) -> Dict[str, float]:
    payload = load_json(calibration_json)
    recommended = payload.get('recommended', payload)
    contact_weight = float(recommended.get('contact_weight', 0.7))
    positive_weight = float(recommended.get('positive_weight', 0.3))
    total = contact_weight + positive_weight
    if total <= 0:
        total = 1.0
    return {
        'contact_threshold': float(recommended.get('contact_threshold', 0.5)),
        'positive_threshold': float(recommended.get('positive_threshold', 0.5)),
        'contact_weight': contact_weight / total,
        'positive_weight': positive_weight / total,
        'reg_min': float(recommended.get('reg_min', 0.0)),
    }


def tier_rank(series: pd.Series) -> pd.Series:
    mapping = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    return series.astype(str).map(mapping).fillna(-1)


def pick_seed_rows(df: pd.DataFrame, top_k: int, only_point_id: str) -> pd.DataFrame:
    work = df.copy()
    if only_point_id:
        work = work[work['point_id'].astype(str) == only_point_id].copy()
    if work.empty:
        raise RuntimeError('No scored rows available after point filter.')
    work['tier_rank'] = tier_rank(work.get('stage1_reference_candidate_tier', pd.Series(dtype=object)))
    if 'cascade_gate' in work.columns:
        work['cascade_gate'] = pd.to_numeric(work['cascade_gate'], errors='coerce').fillna(0).astype(int)
    else:
        work['cascade_gate'] = 0
    ranked = work.sort_values(
        ['cascade_gate', 'cascade_score', 'contact_prob', 'positive_prob', 'tier_rank', 'surrogate_pred_gap34_gain_Hz'],
        ascending=[False, False, False, False, False, False],
    ).copy()
    ranked = ranked.drop_duplicates(subset=['shape_id'], keep='first')
    return ranked.head(max(1, top_k)).copy()


def build_local_bounds(base_row: pd.Series, local_span_scale: float) -> Dict[str, Tuple[float, float]]:
    bounds: Dict[str, Tuple[float, float]] = {}
    scale = float(np.clip(local_span_scale, 0.05, 1.0))
    for name, (global_lo, global_hi) in GLOBAL_BOUNDS.items():
        base_value = float(base_row.get(name, global_lo))
        if global_lo == global_hi:
            bounds[name] = (float(global_lo), float(global_hi))
            continue
        span = (global_hi - global_lo) * scale
        local_lo = max(global_lo, base_value - span)
        local_hi = min(global_hi, base_value + span)
        bounds[name] = (float(local_lo), float(local_hi))
    return bounds


def clip_gene(name: str, value: float, bounds: Dict[str, Tuple[float, float]]) -> float:
    lo, hi = bounds[name]
    if lo == hi:
        return float(lo)
    return float(np.clip(value, lo, hi))


def make_individual(base_row: pd.Series, bounds: Dict[str, Tuple[float, float]], rng: np.random.Generator, jitter_scale: float) -> Dict[str, float]:
    genes: Dict[str, float] = {}
    for name in PARAM_COLS:
        base_value = float(base_row.get(name, 0.0))
        lo, hi = bounds[name]
        if lo == hi:
            genes[name] = float(lo)
            continue
        span = hi - lo
        if rng.random() < 0.75:
            value = base_value + rng.normal(0.0, span * jitter_scale)
        else:
            value = rng.uniform(lo, hi)
        genes[name] = clip_gene(name, value, bounds)
    return genes


def crossover(parent_a: Dict[str, float], parent_b: Dict[str, float], bounds: Dict[str, Tuple[float, float]], rng: np.random.Generator) -> Dict[str, float]:
    child: Dict[str, float] = {}
    for name in PARAM_COLS:
        alpha = rng.random()
        value = alpha * parent_a[name] + (1.0 - alpha) * parent_b[name]
        child[name] = clip_gene(name, value, bounds)
    return child


def mutate(child: Dict[str, float], bounds: Dict[str, Tuple[float, float]], rng: np.random.Generator, mutation_rate: float, mutation_scale: float) -> Dict[str, float]:
    out = dict(child)
    for name in PARAM_COLS:
        lo, hi = bounds[name]
        if lo == hi:
            out[name] = float(lo)
            continue
        if rng.random() > mutation_rate:
            continue
        span = hi - lo
        out[name] = clip_gene(name, out[name] + rng.normal(0.0, span * mutation_scale), bounds)
    return out


def build_population_frame(base_row: pd.Series, population: List[Dict[str, float]], seed_label: str) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for idx, genes in enumerate(population, start=1):
        row = base_row.to_dict()
        row.update(genes)
        row['candidate_id'] = f'ga_{seed_label}_{idx:03d}'
        row['pool_arm'] = 'ga_search'
        row['point_strategy'] = 'parametric_ga_v1'
        row['sample_id'] = f'{row.get("shape_id", "shape")}_{seed_label}_{idx:03d}'
        rows.append(row)
    return pd.DataFrame(rows)


def normalized_distance(scored: pd.DataFrame, base_row: pd.Series, bounds: Dict[str, Tuple[float, float]]) -> np.ndarray:
    distances: List[np.ndarray] = []
    for name in PARAM_COLS:
        lo, hi = bounds[name]
        if hi <= lo:
            continue
        span = hi - lo
        base_value = float(base_row.get(name, lo))
        dist = np.abs(scored[name].to_numpy(dtype=float) - base_value) / span
        distances.append(dist)
    if not distances:
        return np.zeros(len(scored), dtype=float)
    return np.mean(np.vstack(distances), axis=0)


def score_population(pop_df: pd.DataFrame, args: argparse.Namespace, settings: Dict[str, float], base_row: pd.Series, base_surrogate: float, bounds: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
    scored = pop_df.copy()
    scored['contact_prob'] = predict_classifier_rows(scored, args.contact_run_root, args.contact_split)
    scored['positive_prob'] = predict_classifier_rows(scored, args.positive_run_root, args.positive_split)
    scored['surrogate_pred_gap34_gain_Hz'] = predict_regressor(scored, args.reg_run_root, args.reg_split)
    scored = assign_scores(scored, settings)
    scored['distance_from_base'] = normalized_distance(scored, base_row, bounds)
    surrogate_delta = scored['surrogate_pred_gap34_gain_Hz'].to_numpy(dtype=float) - float(base_surrogate)
    surrogate_bonus = np.clip(surrogate_delta, 0.0, max(args.surrogate_delta_cap, 1.0)) / max(args.surrogate_delta_cap, 1.0)
    scored['fitness'] = (
        0.70 * scored['cascade_score'].to_numpy(dtype=float)
        + 0.15 * surrogate_bonus
        + 0.10 * scored['contact_gate'].astype(float).to_numpy()
        + 0.05 * scored['positive_gate'].astype(float).to_numpy()
        - 0.10 * scored['distance_from_base'].to_numpy(dtype=float)
    )
    return scored.sort_values(['fitness', 'cascade_score', 'contact_prob', 'surrogate_pred_gap34_gain_Hz'], ascending=[False, False, False, False]).copy()


def tournament_pick(pop_records: List[Dict[str, object]], rng: np.random.Generator, size: int = 3) -> Dict[str, object]:
    if len(pop_records) <= size:
        return max(pop_records, key=lambda item: float(item['fitness']))
    idx = rng.choice(len(pop_records), size=size, replace=False)
    subset = [pop_records[int(i)] for i in idx]
    return max(subset, key=lambda item: float(item['fitness']))


def score_base_row(base_row: pd.Series, args: argparse.Namespace, settings: Dict[str, float], bounds: Dict[str, Tuple[float, float]]) -> pd.Series:
    seed_label = str(base_row.get('shape_family', 'seed')) + '_base'
    base_df = build_population_frame(base_row, [{name: float(base_row.get(name, 0.0)) for name in PARAM_COLS}], seed_label)
    scored = base_df.copy()
    scored['contact_prob'] = predict_classifier_rows(scored, args.contact_run_root, args.contact_split)
    scored['positive_prob'] = predict_classifier_rows(scored, args.positive_run_root, args.positive_split)
    scored['surrogate_pred_gap34_gain_Hz'] = predict_regressor(scored, args.reg_run_root, args.reg_split)
    scored = assign_scores(scored, settings)
    scored['distance_from_base'] = normalized_distance(scored, base_row, bounds)
    scored['fitness'] = scored['cascade_score'].to_numpy(dtype=float)
    return scored.iloc[0]


def run_ga_for_seed(base_row: pd.Series, args: argparse.Namespace, settings: Dict[str, float], rng: np.random.Generator) -> Tuple[pd.DataFrame, List[Dict[str, object]], Dict[str, object]]:
    seed_label = str(base_row.get('shape_family', 'seed'))
    bounds = build_local_bounds(base_row, args.local_span_scale)
    base_scored = score_base_row(base_row, args, settings, bounds)

    population: List[Dict[str, float]] = [
        {name: float(base_row.get(name, 0.0)) for name in PARAM_COLS}
    ]
    while len(population) < args.population_size:
        population.append(make_individual(base_row, bounds, rng, jitter_scale=0.10))

    history: List[Dict[str, object]] = []
    latest_scored = pd.DataFrame()
    for generation in range(args.generations):
        pop_df = build_population_frame(base_row, population, seed_label)
        scored = score_population(pop_df, args, settings, base_row, float(base_scored['surrogate_pred_gap34_gain_Hz']), bounds)
        latest_scored = scored.copy()
        best = scored.iloc[0]
        history.append({
            'generation': generation,
            'best_fitness': float(best['fitness']),
            'best_cascade_score': float(best['cascade_score']),
            'best_contact_prob': float(best['contact_prob']),
            'best_positive_prob': float(best['positive_prob']),
            'best_surrogate_pred_gap34_gain_Hz': float(best['surrogate_pred_gap34_gain_Hz']),
            'best_distance_from_base': float(best['distance_from_base']),
            'mean_fitness': float(scored['fitness'].mean()),
            'mean_cascade_score': float(scored['cascade_score'].mean()),
        })

        records = scored.to_dict(orient='records')
        elites = records[:max(1, min(args.elite_k, len(records)))]
        next_population: List[Dict[str, float]] = []
        for elite in elites:
            next_population.append({name: float(elite[name]) for name in PARAM_COLS})

        while len(next_population) < args.population_size:
            parent_a = tournament_pick(records, rng)
            parent_b = tournament_pick(records, rng)
            child = crossover({name: float(parent_a[name]) for name in PARAM_COLS}, {name: float(parent_b[name]) for name in PARAM_COLS}, bounds, rng)
            child = mutate(child, bounds, rng, args.mutation_rate, args.mutation_scale)
            next_population.append(child)
        population = next_population[:args.population_size]

    final_scored = latest_scored.copy()
    best_row = final_scored.iloc[0]
    summary = {
        'shape_id': str(base_row.get('shape_id', '')),
        'shape_family': str(base_row.get('shape_family', '')),
        'base_point_id': str(base_row.get('point_id', '')),
        'base_cascade_score': float(base_scored['cascade_score']),
        'base_contact_prob': float(base_scored['contact_prob']),
        'base_positive_prob': float(base_scored['positive_prob']),
        'base_surrogate_pred_gap34_gain_Hz': float(base_scored['surrogate_pred_gap34_gain_Hz']),
        'best_cascade_score': float(best_row['cascade_score']),
        'best_contact_prob': float(best_row['contact_prob']),
        'best_positive_prob': float(best_row['positive_prob']),
        'best_surrogate_pred_gap34_gain_Hz': float(best_row['surrogate_pred_gap34_gain_Hz']),
        'best_distance_from_base': float(best_row['distance_from_base']),
        'best_fitness': float(best_row['fitness']),
        'delta_cascade_score': float(best_row['cascade_score'] - base_scored['cascade_score']),
        'delta_surrogate_pred_gap34_gain_Hz': float(best_row['surrogate_pred_gap34_gain_Hz'] - base_scored['surrogate_pred_gap34_gain_Hz']),
    }
    return final_scored, history, summary


def main() -> None:
    args = parse_args()
    if args.population_size < 4:
        raise ValueError('population-size must be at least 4')
    if args.elite_k < 1:
        raise ValueError('elite-k must be at least 1')

    settings = resolve_scoring_settings(args.calibration_json)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    scored_df = pd.read_csv(args.scored_csv)
    if scored_df.empty:
        raise RuntimeError(f'Empty scored csv: {args.scored_csv}')

    seed_rows = pick_seed_rows(scored_df, args.top_k_seeds, args.only_point_id)
    all_best_rows: List[Dict[str, object]] = []
    all_summary_rows: List[Dict[str, object]] = []

    for _, base_row in seed_rows.iterrows():
        final_scored, history, summary = run_ga_for_seed(base_row, args, settings, rng)
        family = str(base_row.get('shape_family', 'seed'))
        shape = str(base_row.get('shape_id', 'shape'))
        stem = f'{family}_{shape}'.replace('\\', '_').replace('/', '_')

        history_path = args.out_dir / f'ga_history_{stem}.csv'
        top_path = args.out_dir / f'ga_top_candidates_{stem}.csv'
        save_csv_rows(history_path, list(history[0].keys()) if history else ['generation'], history)
        final_scored.head(12).to_csv(top_path, index=False, encoding='utf-8-sig')

        best_rows = final_scored.head(6).copy()
        best_rows['ga_seed_shape_id'] = shape
        best_rows['ga_base_point_id'] = str(base_row.get('point_id', ''))
        all_best_rows.extend(best_rows.to_dict(orient='records'))
        all_summary_rows.append(summary)

    if all_best_rows:
        pd.DataFrame(all_best_rows).to_csv(args.out_dir / 'ga_candidate_manifest_v1.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(args.out_dir / 'ga_search_summary.csv', list(all_summary_rows[0].keys()) if all_summary_rows else ['shape_id'], all_summary_rows)
    save_json(args.out_dir / 'ga_search_config.json', {
        'scored_csv': str(args.scored_csv),
        'top_k_seeds': int(args.top_k_seeds),
        'only_point_id': args.only_point_id,
        'population_size': int(args.population_size),
        'generations': int(args.generations),
        'elite_k': int(args.elite_k),
        'mutation_rate': float(args.mutation_rate),
        'mutation_scale': float(args.mutation_scale),
        'local_span_scale': float(args.local_span_scale),
        'surrogate_delta_cap': float(args.surrogate_delta_cap),
        'seed': int(args.seed),
        'global_bounds': {key: [float(lo), float(hi)] for key, (lo, hi) in GLOBAL_BOUNDS.items()},
        'scoring_settings': settings,
        'fitness_definition': '0.70*cascade_score + 0.15*clipped_surrogate_delta_bonus + 0.10*contact_gate + 0.05*positive_gate - 0.10*distance_from_base',
    })

    print('[DONE] parametric GA seed search complete')
    print(f'[OUT] {args.out_dir}')
    print(f'[SEEDS] optimized={len(seed_rows)} point_filter={args.only_point_id}')


if __name__ == '__main__':
    main()
