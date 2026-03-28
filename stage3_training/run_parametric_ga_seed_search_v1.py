from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from objective_registry import DEFAULT_OBJECTIVE_NAME, GENERIC_OBJECTIVE_PREDICTION_COLUMN, GENERIC_PREDICTION_COLUMN, get_objective
from ml_common import DEFAULT_OUT_ROOT, save_csv_rows, save_json
from policy_resolution import load_policy_json, resolve_policy_settings
from run_seed_discovery_scoring_v7 import (
    assign_scores,
    attach_objective_predictions,
    predict_classifier_rows,
    predict_regressor,
    resolve_scoring_settings,
)

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'seed_discovery_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1'
DEFAULT_CONTACT_RUN = DEFAULT_OUT_ROOT / 'mlp_contact_valid_parametric_seed_discovery_v7_full'
DEFAULT_POSITIVE_RUN = DEFAULT_OUT_ROOT / 'mlp_is_positive_shape_parametric_seed_discovery_v7_full'
DEFAULT_REG_RUN = DEFAULT_OUT_ROOT / 'mlp_gap34_gain_surrogate_v7_full'
DEFAULT_CALIBRATION_JSON = ROOT / 'stage3_training' / 'seed_discovery_scoring_calibration_v1.json'
DEFAULT_WHITELIST_JSON = ROOT / 'stage3_training' / 'ga_shape_whitelist_v1.json'
DEFAULT_POLICY_JSON = ROOT / 'stage3_training' / 'policies' / 'ga_v1.json'

DEFAULT_GLOBAL_BOUNDS: Dict[str, Tuple[float, float]] = {
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

DEFAULT_LOCAL_HALF_WIDTHS: Dict[str, float] = {
    'a1': 0.0030,
    'a2': 0.0040,
    'b1': 0.0,
    'b2': 0.0035,
    'a3': 0.0,
    'b3': 0.0,
    'a4': 0.0020,
    'b4': 0.0,
    'a5': 0.0,
    'b5': 0.0020,
    'r0': 0.00025,
}

ACTIVE_PARAM_COLS = ['a1', 'a2', 'b2', 'a4', 'b5', 'r0']
PARAM_COLS = list(DEFAULT_GLOBAL_BOUNDS.keys())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run conservative parameter-level GA around shortlisted center-point seeds.')
    parser.add_argument('--policy-json', type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--positive-run-root', type=Path, default=DEFAULT_POSITIVE_RUN)
    parser.add_argument('--positive-split', default='shape_family')
    parser.add_argument('--reg-run-root', type=Path, default=DEFAULT_REG_RUN)
    parser.add_argument('--reg-split', default='shape_family')
    parser.add_argument('--objective', default=DEFAULT_OBJECTIVE_NAME)
    parser.add_argument('--calibration-json', type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument('--whitelist-json', type=Path, default=DEFAULT_WHITELIST_JSON)
    parser.add_argument('--top-k-seeds', type=int, default=3)
    parser.add_argument('--only-point-id', default='rf09_h00_center')
    parser.add_argument('--population-size', type=int, default=20)
    parser.add_argument('--generations', type=int, default=12)
    parser.add_argument('--elite-k', type=int, default=4)
    parser.add_argument('--mutation-rate', type=float, default=0.20)
    parser.add_argument('--mutation-scale', type=float, default=0.08)
    parser.add_argument('--local-span-scale', type=float, default=1.0)
    parser.add_argument('--surrogate-delta-cap', type=float, default=3.0)
    parser.add_argument('--seed', type=int, default=20260324)
    return parser.parse_args()


def load_shape_whitelist(path: Path | None) -> List[str]:
    if path is None or not path.exists():
        return []
    payload = load_policy_json(path)
    raw_ids = payload.get('enabled_shape_ids', [])
    if not isinstance(raw_ids, list):
        raise ValueError('enabled_shape_ids must be a list in whitelist json.')
    return [str(item).strip() for item in raw_ids if str(item).strip()]


def resolve_search_config(args: argparse.Namespace) -> Dict[str, object]:
    policy = load_policy_json(args.policy_json, section='search') if args.policy_json else {}
    defaults = {
        'scored_csv': DEFAULT_SCORED_CSV,
        'out_dir': DEFAULT_OUT_DIR,
        'contact_run_root': DEFAULT_CONTACT_RUN,
        'contact_split': 'shape_family',
        'positive_run_root': DEFAULT_POSITIVE_RUN,
        'positive_split': 'shape_family',
        'reg_run_root': DEFAULT_REG_RUN,
        'reg_split': 'shape_family',
        'objective_name': DEFAULT_OBJECTIVE_NAME,
        'calibration_json': DEFAULT_CALIBRATION_JSON,
        'whitelist_json': DEFAULT_WHITELIST_JSON,
        'top_k_seeds': 3,
        'only_point_id': 'rf09_h00_center',
        'population_size': 20,
        'generations': 12,
        'elite_k': 4,
        'mutation_rate': 0.20,
        'mutation_scale': 0.08,
        'local_span_scale': 1.0,
        'surrogate_delta_cap': 3.0,
        'seed': 20260324,
        'bounds': {key: list(value) for key, value in DEFAULT_GLOBAL_BOUNDS.items()},
        'local_half_widths': dict(DEFAULT_LOCAL_HALF_WIDTHS),
        'fitness_objective': 'cascade_score_with_distance_penalty',
    }
    cli_values = {
        'scored_csv': args.scored_csv,
        'out_dir': args.out_dir,
        'contact_run_root': args.contact_run_root,
        'contact_split': args.contact_split,
        'positive_run_root': args.positive_run_root,
        'positive_split': args.positive_split,
        'reg_run_root': args.reg_run_root,
        'reg_split': args.reg_split,
        'objective_name': args.objective,
        'calibration_json': args.calibration_json,
        'whitelist_json': args.whitelist_json,
        'top_k_seeds': args.top_k_seeds,
        'only_point_id': args.only_point_id,
        'population_size': args.population_size,
        'generations': args.generations,
        'elite_k': args.elite_k,
        'mutation_rate': args.mutation_rate,
        'mutation_scale': args.mutation_scale,
        'local_span_scale': args.local_span_scale,
        'surrogate_delta_cap': args.surrogate_delta_cap,
        'seed': args.seed,
    }
    resolved = resolve_policy_settings(defaults, policy, cli_values, defaults, policy_enabled=args.policy_json is not None)
    for key in ['scored_csv', 'out_dir', 'contact_run_root', 'positive_run_root', 'reg_run_root', 'calibration_json', 'whitelist_json']:
        value = resolved.get(key)
        if value not in (None, ''):
            path = Path(value)
            if not path.is_absolute():
                path = ROOT / path
            resolved[key] = path
    bounds = resolved.get('bounds', {})
    resolved['bounds'] = {key: (float(value[0]), float(value[1])) for key, value in bounds.items()}
    half_widths = resolved.get('local_half_widths', {})
    resolved['local_half_widths'] = {key: float(value) for key, value in half_widths.items()}
    return resolved


def build_scoring_settings(config: Dict[str, object]) -> Dict[str, float]:
    namespace = SimpleNamespace(
        contact_threshold=0.50,
        positive_threshold=0.50,
        contact_weight=0.70,
        positive_weight=0.30,
        reg_min=0.0,
        calibration_json=config.get('calibration_json'),
        policy_json=None,
    )
    return resolve_scoring_settings(namespace)


def resolve_scored_prediction_column(df: pd.DataFrame) -> str:
    if GENERIC_OBJECTIVE_PREDICTION_COLUMN in df.columns and len(df):
        col = str(df[GENERIC_OBJECTIVE_PREDICTION_COLUMN].iloc[0])
        if col and col in df.columns:
            return col
    if GENERIC_PREDICTION_COLUMN in df.columns:
        return GENERIC_PREDICTION_COLUMN
    if 'surrogate_pred_gap34_gain_Hz' in df.columns:
        return 'surrogate_pred_gap34_gain_Hz'
    raise KeyError('Unable to resolve surrogate prediction column from scored csv.')


def tier_rank(series: pd.Series) -> pd.Series:
    mapping = {'strong_positive': 2, 'weak_positive': 1, 'neutral_or_baseline_like': 0}
    return series.astype(str).map(mapping).fillna(-1)


def pick_seed_rows(df: pd.DataFrame, top_k: int, only_point_id: str, whitelist_shape_ids: List[str]) -> pd.DataFrame:
    work = df.copy()
    pred_col = resolve_scored_prediction_column(work)
    if only_point_id:
        work = work[work['point_id'].astype(str) == only_point_id].copy()
    if whitelist_shape_ids:
        work = work[work['shape_id'].astype(str).isin(whitelist_shape_ids)].copy()
    if work.empty:
        raise RuntimeError('No scored rows available after point/whitelist filtering.')
    work['tier_rank'] = tier_rank(work.get('stage1_reference_candidate_tier', pd.Series(dtype=object)))
    if 'cascade_gate' in work.columns:
        work['cascade_gate'] = pd.to_numeric(work['cascade_gate'], errors='coerce').fillna(0).astype(int)
    else:
        work['cascade_gate'] = 0
    ranked = work.sort_values(
        ['cascade_gate', 'cascade_score', 'contact_prob', 'positive_prob', 'tier_rank', pred_col],
        ascending=[False, False, False, False, False, False],
    ).copy()
    ranked = ranked.drop_duplicates(subset=['shape_id'], keep='first')
    return ranked.head(max(1, top_k)).copy()


def build_local_bounds(base_row: pd.Series, local_span_scale: float, global_bounds: Dict[str, Tuple[float, float]], local_half_widths: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
    bounds: Dict[str, Tuple[float, float]] = {}
    scale = float(np.clip(local_span_scale, 0.25, 1.0))
    for name, (global_lo, global_hi) in global_bounds.items():
        base_value = float(base_row.get(name, global_lo))
        half_width = float(local_half_widths.get(name, 0.0)) * scale
        if global_lo == global_hi or half_width <= 0:
            bounds[name] = (float(base_value), float(base_value))
            continue
        local_lo = max(global_lo, base_value - half_width)
        local_hi = min(global_hi, base_value + half_width)
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
        if lo == hi or name not in ACTIVE_PARAM_COLS:
            genes[name] = float(base_value)
            continue
        span = hi - lo
        value = base_value + rng.normal(0.0, span * jitter_scale) if rng.random() < 0.90 else rng.uniform(lo, hi)
        genes[name] = clip_gene(name, value, bounds)
    return genes


def crossover(parent_a: Dict[str, float], parent_b: Dict[str, float], bounds: Dict[str, Tuple[float, float]], rng: np.random.Generator) -> Dict[str, float]:
    child: Dict[str, float] = {}
    for name in PARAM_COLS:
        if name not in ACTIVE_PARAM_COLS:
            child[name] = float(parent_a[name])
            continue
        alpha = rng.random()
        value = alpha * parent_a[name] + (1.0 - alpha) * parent_b[name]
        child[name] = clip_gene(name, value, bounds)
    return child


def mutate(child: Dict[str, float], bounds: Dict[str, Tuple[float, float]], rng: np.random.Generator, mutation_rate: float, mutation_scale: float) -> Dict[str, float]:
    out = dict(child)
    for name in PARAM_COLS:
        lo, hi = bounds[name]
        if lo == hi or name not in ACTIVE_PARAM_COLS or rng.random() > mutation_rate:
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
        row['point_strategy'] = 'parametric_ga_v1_conservative'
        row['sample_id'] = f'{row.get("shape_id", "shape")}_{seed_label}_{idx:03d}'
        rows.append(row)
    return pd.DataFrame(rows)


def normalized_distance(scored: pd.DataFrame, base_row: pd.Series, bounds: Dict[str, Tuple[float, float]]) -> np.ndarray:
    distances: List[np.ndarray] = []
    for name in ACTIVE_PARAM_COLS:
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


def score_population(pop_df: pd.DataFrame, config: Dict[str, object], settings: Dict[str, float], base_row: pd.Series, base_scored: pd.Series, bounds: Dict[str, Tuple[float, float]], objective_name: str, pred_col: str) -> pd.DataFrame:
    scored = pop_df.copy()
    scored['contact_prob'] = predict_classifier_rows(scored, config['contact_run_root'], str(config['contact_split']))
    scored['positive_prob'] = predict_classifier_rows(scored, config['positive_run_root'], str(config['positive_split']))
    predictions = predict_regressor(scored, config['reg_run_root'], str(config['reg_split']), objective_name=objective_name)
    scored, pred_col = attach_objective_predictions(scored, objective_name, predictions)
    scored = assign_scores(scored, settings, pred_col)
    if pred_col == 'surrogate_pred_gap34_gain_Hz':
        scored['surrogate_pred_gap34_gain_Hz'] = scored[pred_col]
    scored['distance_from_base'] = normalized_distance(scored, base_row, bounds)

    base_contact = float(base_scored['contact_prob'])
    base_positive = float(base_scored['positive_prob'])
    base_surrogate = float(base_scored[pred_col])

    contact_delta = np.clip(scored['contact_prob'].to_numpy(dtype=float) - base_contact, 0.0, 0.05) / 0.05
    positive_delta = np.clip(scored['positive_prob'].to_numpy(dtype=float) - base_positive, 0.0, 0.02) / 0.02
    surrogate_delta = np.clip(scored[pred_col].to_numpy(dtype=float) - base_surrogate, 0.0, max(float(config['surrogate_delta_cap']), 1.0)) / max(float(config['surrogate_delta_cap']), 1.0)

    scored['fitness'] = (
        0.72 * scored['cascade_score'].to_numpy(dtype=float)
        + 0.08 * contact_delta
        + 0.03 * positive_delta
        + 0.02 * surrogate_delta
        + 0.10 * scored['contact_gate'].astype(float).to_numpy()
        + 0.05 * scored['positive_gate'].astype(float).to_numpy()
        - 0.25 * scored['distance_from_base'].to_numpy(dtype=float)
    )
    return scored.sort_values(['fitness', 'cascade_score', 'contact_prob', pred_col], ascending=[False, False, False, False]).copy()


def tournament_pick(pop_records: List[Dict[str, object]], rng: np.random.Generator, size: int = 3) -> Dict[str, object]:
    if len(pop_records) <= size:
        return max(pop_records, key=lambda item: float(item['fitness']))
    idx = rng.choice(len(pop_records), size=size, replace=False)
    subset = [pop_records[int(i)] for i in idx]
    return max(subset, key=lambda item: float(item['fitness']))


def score_base_row(base_row: pd.Series, config: Dict[str, object], settings: Dict[str, float], bounds: Dict[str, Tuple[float, float]], objective_name: str, pred_col: str) -> pd.Series:
    seed_label = str(base_row.get('shape_family', 'seed')) + '_base'
    base_df = build_population_frame(base_row, [{name: float(base_row.get(name, 0.0)) for name in PARAM_COLS}], seed_label)
    scored = base_df.copy()
    scored['contact_prob'] = predict_classifier_rows(scored, config['contact_run_root'], str(config['contact_split']))
    scored['positive_prob'] = predict_classifier_rows(scored, config['positive_run_root'], str(config['positive_split']))
    predictions = predict_regressor(scored, config['reg_run_root'], str(config['reg_split']), objective_name=objective_name)
    scored, pred_col = attach_objective_predictions(scored, objective_name, predictions)
    scored = assign_scores(scored, settings, pred_col)
    if pred_col == 'surrogate_pred_gap34_gain_Hz':
        scored['surrogate_pred_gap34_gain_Hz'] = scored[pred_col]
    scored['distance_from_base'] = normalized_distance(scored, base_row, bounds)
    scored['fitness'] = scored['cascade_score'].to_numpy(dtype=float)
    return scored.iloc[0]


def run_ga_for_seed(base_row: pd.Series, config: Dict[str, object], settings: Dict[str, float], rng: np.random.Generator, objective_name: str, pred_col: str) -> Tuple[pd.DataFrame, List[Dict[str, object]], Dict[str, object]]:
    seed_label = str(base_row.get('shape_family', 'seed'))
    bounds = build_local_bounds(base_row, float(config['local_span_scale']), config['bounds'], config['local_half_widths'])
    base_scored = score_base_row(base_row, config, settings, bounds, objective_name, pred_col)

    population: List[Dict[str, float]] = [{name: float(base_row.get(name, 0.0)) for name in PARAM_COLS}]
    while len(population) < int(config['population_size']):
        population.append(make_individual(base_row, bounds, rng, jitter_scale=0.08))

    history: List[Dict[str, object]] = []
    latest_scored = pd.DataFrame()
    for generation in range(int(config['generations'])):
        pop_df = build_population_frame(base_row, population, seed_label)
        scored = score_population(pop_df, config, settings, base_row, base_scored, bounds, objective_name, pred_col)
        latest_scored = scored.copy()
        best = scored.iloc[0]
        history.append({
            'generation': generation,
            'best_fitness': float(best['fitness']),
            'best_cascade_score': float(best['cascade_score']),
            'best_contact_prob': float(best['contact_prob']),
            'best_positive_prob': float(best['positive_prob']),
            f'best_{pred_col}': float(best[pred_col]),
            'best_distance_from_base': float(best['distance_from_base']),
            'mean_fitness': float(scored['fitness'].mean()),
            'mean_cascade_score': float(scored['cascade_score'].mean()),
        })
        records = scored.to_dict(orient='records')
        elites = records[:max(1, min(int(config['elite_k']), len(records)))]
        next_population: List[Dict[str, float]] = [{name: float(elite[name]) for name in PARAM_COLS} for elite in elites]
        while len(next_population) < int(config['population_size']):
            parent_a = tournament_pick(records, rng)
            parent_b = tournament_pick(records, rng)
            child = crossover({name: float(parent_a[name]) for name in PARAM_COLS}, {name: float(parent_b[name]) for name in PARAM_COLS}, bounds, rng)
            child = mutate(child, bounds, rng, float(config['mutation_rate']), float(config['mutation_scale']))
            next_population.append(child)
        population = next_population[:int(config['population_size'])]

    final_scored = latest_scored.copy()
    best_row = final_scored.iloc[0]
    summary = {
        'shape_id': str(base_row.get('shape_id', '')),
        'shape_family': str(base_row.get('shape_family', '')),
        'base_point_id': str(base_row.get('point_id', '')),
        'base_cascade_score': float(base_scored['cascade_score']),
        'base_contact_prob': float(base_scored['contact_prob']),
        'base_positive_prob': float(base_scored['positive_prob']),
        f'base_{pred_col}': float(base_scored[pred_col]),
        'best_cascade_score': float(best_row['cascade_score']),
        'best_contact_prob': float(best_row['contact_prob']),
        'best_positive_prob': float(best_row['positive_prob']),
        f'best_{pred_col}': float(best_row[pred_col]),
        'best_distance_from_base': float(best_row['distance_from_base']),
        'best_fitness': float(best_row['fitness']),
        'delta_cascade_score': float(best_row['cascade_score'] - base_scored['cascade_score']),
        f'delta_{pred_col}': float(best_row[pred_col] - base_scored[pred_col]),
    }
    return final_scored, history, summary


def main() -> None:
    args = parse_args()
    config = resolve_search_config(args)
    if int(config['population_size']) < 4:
        raise ValueError('population-size must be at least 4')
    if int(config['elite_k']) < 1:
        raise ValueError('elite-k must be at least 1')

    objective = get_objective(str(config['objective_name']))
    settings = build_scoring_settings(config)
    whitelist_shape_ids = load_shape_whitelist(config.get('whitelist_json'))
    Path(config['out_dir']).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(int(config['seed']))

    scored_df = pd.read_csv(config['scored_csv'])
    if scored_df.empty:
        raise RuntimeError(f'Empty scored csv: {config["scored_csv"]}')

    seed_rows = pick_seed_rows(scored_df, int(config['top_k_seeds']), str(config['only_point_id']), whitelist_shape_ids)
    all_best_rows: List[Dict[str, object]] = []
    all_summary_rows: List[Dict[str, object]] = []

    for _, base_row in seed_rows.iterrows():
        final_scored, history, summary = run_ga_for_seed(base_row, config, settings, rng, objective.name, objective.prediction_column)
        family = str(base_row.get('shape_family', 'seed'))
        shape = str(base_row.get('shape_id', 'shape'))
        stem = f'{family}_{shape}'.replace('\\', '_').replace('/', '_')

        history_path = Path(config['out_dir']) / f'ga_history_{stem}.csv'
        top_path = Path(config['out_dir']) / f'ga_top_candidates_{stem}.csv'
        save_csv_rows(history_path, list(history[0].keys()) if history else ['generation'], history)
        final_scored.head(12).to_csv(top_path, index=False, encoding='utf-8-sig')

        best_rows = final_scored.head(6).copy()
        best_rows['ga_seed_shape_id'] = shape
        best_rows['ga_base_point_id'] = str(base_row.get('point_id', ''))
        all_best_rows.extend(best_rows.to_dict(orient='records'))
        all_summary_rows.append(summary)

    if all_best_rows:
        pd.DataFrame(all_best_rows).to_csv(Path(config['out_dir']) / 'ga_candidate_manifest_v1.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(Path(config['out_dir']) / 'ga_search_summary.csv', list(all_summary_rows[0].keys()) if all_summary_rows else ['shape_id'], all_summary_rows)
    save_json(Path(config['out_dir']) / 'ga_search_config.json', {
        'policy_json': str(args.policy_json) if args.policy_json else '',
        'scored_csv': str(config['scored_csv']),
        'objective_name': objective.name,
        'top_k_seeds': int(config['top_k_seeds']),
        'only_point_id': str(config['only_point_id']),
        'population_size': int(config['population_size']),
        'generations': int(config['generations']),
        'elite_k': int(config['elite_k']),
        'mutation_rate': float(config['mutation_rate']),
        'mutation_scale': float(config['mutation_scale']),
        'local_span_scale': float(config['local_span_scale']),
        'surrogate_delta_cap': float(config['surrogate_delta_cap']),
        'seed': int(config['seed']),
        'whitelist_json': str(config['whitelist_json']) if config.get('whitelist_json') else '',
        'whitelist_shape_ids': list(whitelist_shape_ids),
        'global_bounds': {key: [float(lo), float(hi)] for key, (lo, hi) in config['bounds'].items()},
        'local_half_widths': {key: float(val) for key, val in config['local_half_widths'].items()},
        'active_param_cols': list(ACTIVE_PARAM_COLS),
        'scoring_settings': settings,
        'fitness_definition': '0.72*cascade_score + 0.08*contact_delta + 0.03*positive_delta + 0.02*clipped_surrogate_delta + 0.10*contact_gate + 0.05*positive_gate - 0.25*distance_from_base',
        'fitness_objective': str(config.get('fitness_objective', 'cascade_score_with_distance_penalty')),
    })

    print('[DONE] conservative parametric GA seed search complete')
    print(f"[OUT] {config['out_dir']}")
    print(f"[SEEDS] optimized={len(seed_rows)} point_filter={config['only_point_id']} whitelist={len(whitelist_shape_ids)}")


if __name__ == '__main__':
    main()
