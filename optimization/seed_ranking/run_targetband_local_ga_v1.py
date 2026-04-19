from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE3_TRAINING = ROOT / 'stage3_training'
if str(STAGE3_TRAINING) not in sys.path:
    sys.path.insert(0, str(STAGE3_TRAINING))

from optimization.seed_ranking.run_targetband_seed_scoring_v1 import assign_targetband_scores
from prediction_targetband_param_v1.models.inference import build_targetband_prediction_frame
from shared.objectives.targetband import derive_band_tag
from stage3_training.ml_common import save_csv_rows, save_json
from stage3_training.run_seed_discovery_scoring_v7 import predict_classifier_rows, resolve_path


DEFAULT_SCORED_CSV = ROOT / 'data' / 'ml_runs' / 'targetband_seed_scoring_v1' / 'band180_220' / 'targetband_seed_predictions.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'ml_runs'
DEFAULT_CONTACT_RUN = ROOT / 'data' / 'ml_runs' / 'mlp_contact_valid_parametric_seed_discovery_v7_full'
DEFAULT_CLASSIFIER_RUN = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cls_dense_family' / 'stratified_group_kfold'
DEFAULT_REGRESSOR_RUN = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cover_dense_family' / 'stratified_group_kfold'

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
    parser = argparse.ArgumentParser(description='Run target-band-conditioned local GA around shortlisted seeds.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--contact-run-root', type=Path, default=DEFAULT_CONTACT_RUN)
    parser.add_argument('--contact-split', default='shape_family')
    parser.add_argument('--classifier-run-root', type=Path, default=DEFAULT_CLASSIFIER_RUN)
    parser.add_argument('--regressor-run-root', type=Path, default=DEFAULT_REGRESSOR_RUN)
    parser.add_argument('--band-low', type=float, default=180.0)
    parser.add_argument('--band-high', type=float, default=220.0)
    parser.add_argument('--band-tag', default='')
    parser.add_argument('--out-dir', type=Path, default=None)
    parser.add_argument('--top-k-seeds', type=int, default=3)
    parser.add_argument('--only-point-id', default='rf09_h00_center')
    parser.add_argument('--whitelist-json', type=Path, default=None)
    parser.add_argument('--population-size', type=int, default=20)
    parser.add_argument('--generations', type=int, default=12)
    parser.add_argument('--elite-k', type=int, default=4)
    parser.add_argument('--mutation-rate', type=float, default=0.20)
    parser.add_argument('--mutation-scale', type=float, default=0.08)
    parser.add_argument('--local-span-scale', type=float, default=1.0)
    parser.add_argument('--contact-threshold', type=float, default=0.50)
    parser.add_argument('--open-threshold', type=float, default=0.50)
    parser.add_argument('--cover-delta-cap', type=float, default=0.25)
    parser.add_argument('--overlap-delta-cap', type=float, default=10.0)
    parser.add_argument('--seed', type=int, default=20260417)
    return parser.parse_args()


def load_shape_whitelist(path: Path | None) -> List[str]:
    if path is None:
        return []
    resolved = resolve_path(path)
    if resolved is None or not resolved.exists():
        return []
    payload = json.loads(resolved.read_text(encoding='utf-8'))
    raw_ids = payload.get('enabled_shape_ids', [])
    if not isinstance(raw_ids, list):
        raise ValueError('enabled_shape_ids must be a list in whitelist json.')
    return [str(item).strip() for item in raw_ids if str(item).strip()]


def build_local_bounds(
    base_row: pd.Series,
    local_span_scale: float,
    global_bounds: Dict[str, Tuple[float, float]],
    local_half_widths: Dict[str, float],
) -> Dict[str, Tuple[float, float]]:
    bounds: Dict[str, Tuple[float, float]] = {}
    scale = float(np.clip(local_span_scale, 0.25, 1.0))
    for name, (global_lo, global_hi) in global_bounds.items():
        base_value = float(base_row.get(name, global_lo))
        half_width = float(local_half_widths.get(name, 0.0)) * scale
        if global_lo == global_hi or half_width <= 0:
            bounds[name] = (float(base_value), float(base_value))
            continue
        bounds[name] = (
            float(max(global_lo, base_value - half_width)),
            float(min(global_hi, base_value + half_width)),
        )
    return bounds


def clip_gene(name: str, value: float, bounds: Dict[str, Tuple[float, float]]) -> float:
    lo, hi = bounds[name]
    if lo == hi:
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
        base_value = float(base_row.get(name, 0.0))
        lo, hi = bounds[name]
        if lo == hi or name not in ACTIVE_PARAM_COLS:
            genes[name] = float(base_value)
            continue
        span = hi - lo
        value = base_value + rng.normal(0.0, span * jitter_scale) if rng.random() < 0.90 else rng.uniform(lo, hi)
        genes[name] = clip_gene(name, value, bounds)
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
        if lo == hi or name not in ACTIVE_PARAM_COLS or rng.random() > mutation_rate:
            continue
        out[name] = clip_gene(name, out[name] + rng.normal(0.0, (hi - lo) * mutation_scale), bounds)
    return out


def build_population_frame(base_row: pd.Series, population: List[Dict[str, float]], seed_label: str) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for idx, genes in enumerate(population, start=1):
        row = base_row.to_dict()
        row.update(genes)
        row['candidate_id'] = f'targetband_ga_{seed_label}_{idx:03d}'
        row['pool_arm'] = 'targetband_ga_search'
        row['point_strategy'] = 'targetband_parametric_ga_v1'
        row['sample_id'] = f'{row.get("shape_id", "shape")}_{seed_label}_{idx:03d}'
        rows.append(row)
    return pd.DataFrame(rows)


def normalized_distance(scored: pd.DataFrame, base_row: pd.Series, bounds: Dict[str, Tuple[float, float]]) -> np.ndarray:
    distances: List[np.ndarray] = []
    for name in ACTIVE_PARAM_COLS:
        lo, hi = bounds[name]
        if hi <= lo:
            continue
        base_value = float(base_row.get(name, lo))
        dist = np.abs(scored[name].to_numpy(dtype=float) - base_value) / (hi - lo)
        distances.append(dist)
    if not distances:
        return np.zeros(len(scored), dtype=float)
    return np.mean(np.vstack(distances), axis=0)


def ranked_seed_rows(
    df: pd.DataFrame,
    top_k: int,
    only_point_id: str,
    whitelist_shape_ids: List[str],
) -> pd.DataFrame:
    work = df.copy()
    if only_point_id.strip():
        work = work[work['point_id'].astype(str) == only_point_id.strip()].copy()
    if whitelist_shape_ids:
        work = work[work['shape_id'].astype(str).isin(whitelist_shape_ids)].copy()
    if work.empty:
        raise RuntimeError('No target-band scored rows available after seed filtering.')
    ranked = work.sort_values(
        [
            'targetband_gate',
            'targetband_score',
            'target_gap_cover_ratio_pred',
            'target_open_prob',
            'contact_prob',
            'target_gap_overlap_pred_Hz',
        ],
        ascending=[False, False, False, False, False, False],
    ).copy()
    ranked = ranked.drop_duplicates(subset=['shape_id'], keep='first')
    return ranked.head(max(1, int(top_k))).copy()


def score_targetband_population(
    pop_df: pd.DataFrame,
    args: argparse.Namespace,
    base_row: pd.Series,
    base_scored: pd.Series,
    bounds: Dict[str, Tuple[float, float]],
    band_tag: str,
) -> pd.DataFrame:
    scored = build_targetband_prediction_frame(
        pop_df,
        args.band_low,
        args.band_high,
        resolve_path(args.classifier_run_root),
        resolve_path(args.regressor_run_root),
        band_tag=band_tag,
    )
    scored['contact_prob'] = predict_classifier_rows(scored, resolve_path(args.contact_run_root), str(args.contact_split))
    scored = assign_targetband_scores(scored, args.contact_threshold, args.open_threshold)
    scored['distance_from_base'] = normalized_distance(scored, base_row, bounds)

    base_contact = float(base_scored['contact_prob'])
    base_open = float(base_scored['target_open_prob'])
    base_cover = float(base_scored['target_gap_cover_ratio_pred'])
    base_overlap = float(base_scored['target_gap_overlap_pred_Hz'])

    contact_delta = np.clip(scored['contact_prob'].to_numpy(dtype=float) - base_contact, 0.0, 0.05) / 0.05
    open_delta = np.clip(scored['target_open_prob'].to_numpy(dtype=float) - base_open, 0.0, 0.05) / 0.05
    cover_delta = np.clip(
        scored['target_gap_cover_ratio_pred'].to_numpy(dtype=float) - base_cover,
        0.0,
        max(float(args.cover_delta_cap), 1e-6),
    ) / max(float(args.cover_delta_cap), 1e-6)
    overlap_delta = np.clip(
        scored['target_gap_overlap_pred_Hz'].to_numpy(dtype=float) - base_overlap,
        0.0,
        max(float(args.overlap_delta_cap), 1e-6),
    ) / max(float(args.overlap_delta_cap), 1e-6)

    scored['fitness'] = (
        0.70 * scored['targetband_score'].to_numpy(dtype=float)
        + 0.10 * scored['contact_gate'].astype(float).to_numpy()
        + 0.10 * scored['target_open_gate'].astype(float).to_numpy()
        + 0.05 * contact_delta
        + 0.10 * open_delta
        + 0.10 * cover_delta
        + 0.05 * overlap_delta
        - 0.25 * scored['distance_from_base'].to_numpy(dtype=float)
    )
    return scored.sort_values(
        ['fitness', 'targetband_gate', 'targetband_score', 'target_gap_cover_ratio_pred', 'target_open_prob'],
        ascending=[False, False, False, False, False],
    ).copy()


def score_base_row(
    base_row: pd.Series,
    args: argparse.Namespace,
    bounds: Dict[str, Tuple[float, float]],
    band_tag: str,
) -> pd.Series:
    seed_label = str(base_row.get('shape_family', 'seed')) + '_base'
    base_df = build_population_frame(base_row, [{name: float(base_row.get(name, 0.0)) for name in PARAM_COLS}], seed_label)
    scored = build_targetband_prediction_frame(
        base_df,
        args.band_low,
        args.band_high,
        resolve_path(args.classifier_run_root),
        resolve_path(args.regressor_run_root),
        band_tag=band_tag,
    )
    scored['contact_prob'] = predict_classifier_rows(scored, resolve_path(args.contact_run_root), str(args.contact_split))
    scored = assign_targetband_scores(scored, args.contact_threshold, args.open_threshold)
    scored['distance_from_base'] = normalized_distance(scored, base_row, bounds)
    scored['fitness'] = scored['targetband_score'].to_numpy(dtype=float)
    return scored.iloc[0]


def tournament_pick(pop_records: List[Dict[str, object]], rng: np.random.Generator, size: int = 3) -> Dict[str, object]:
    if len(pop_records) <= size:
        return max(pop_records, key=lambda item: float(item['fitness']))
    idx = rng.choice(len(pop_records), size=size, replace=False)
    subset = [pop_records[int(i)] for i in idx]
    return max(subset, key=lambda item: float(item['fitness']))


def run_ga_for_seed(
    base_row: pd.Series,
    args: argparse.Namespace,
    rng: np.random.Generator,
    band_tag: str,
) -> Tuple[pd.DataFrame, List[Dict[str, object]], Dict[str, object]]:
    seed_label = str(base_row.get('shape_family', 'seed'))
    bounds = build_local_bounds(base_row, float(args.local_span_scale), DEFAULT_GLOBAL_BOUNDS, DEFAULT_LOCAL_HALF_WIDTHS)
    base_scored = score_base_row(base_row, args, bounds, band_tag)

    population: List[Dict[str, float]] = [{name: float(base_row.get(name, 0.0)) for name in PARAM_COLS}]
    while len(population) < int(args.population_size):
        population.append(make_individual(base_row, bounds, rng, jitter_scale=0.08))

    history: List[Dict[str, object]] = []
    latest_scored = pd.DataFrame()
    for generation in range(int(args.generations)):
        pop_df = build_population_frame(base_row, population, seed_label)
        scored = score_targetband_population(pop_df, args, base_row, base_scored, bounds, band_tag)
        latest_scored = scored.copy()
        best = scored.iloc[0]
        history.append(
            {
                'generation': generation,
                'best_fitness': float(best['fitness']),
                'best_targetband_score': float(best['targetband_score']),
                'best_contact_prob': float(best['contact_prob']),
                'best_target_open_prob': float(best['target_open_prob']),
                'best_target_cover_ratio_pred': float(best['target_gap_cover_ratio_pred']),
                'best_target_overlap_pred_Hz': float(best['target_gap_overlap_pred_Hz']),
                'best_distance_from_base': float(best['distance_from_base']),
                'mean_fitness': float(scored['fitness'].mean()),
                'mean_targetband_score': float(scored['targetband_score'].mean()),
            }
        )
        records = scored.to_dict(orient='records')
        elites = records[:max(1, min(int(args.elite_k), len(records)))]
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
        'shape_id': str(base_row.get('shape_id', '')),
        'shape_family': str(base_row.get('shape_family', '')),
        'base_point_id': str(base_row.get('point_id', '')),
        'band_low_Hz': float(args.band_low),
        'band_high_Hz': float(args.band_high),
        'base_targetband_score': float(base_scored['targetband_score']),
        'base_contact_prob': float(base_scored['contact_prob']),
        'base_target_open_prob': float(base_scored['target_open_prob']),
        'base_target_cover_ratio_pred': float(base_scored['target_gap_cover_ratio_pred']),
        'base_target_overlap_pred_Hz': float(base_scored['target_gap_overlap_pred_Hz']),
        'best_targetband_score': float(best_row['targetband_score']),
        'best_contact_prob': float(best_row['contact_prob']),
        'best_target_open_prob': float(best_row['target_open_prob']),
        'best_target_cover_ratio_pred': float(best_row['target_gap_cover_ratio_pred']),
        'best_target_overlap_pred_Hz': float(best_row['target_gap_overlap_pred_Hz']),
        'best_distance_from_base': float(best_row['distance_from_base']),
        'best_fitness': float(best_row['fitness']),
        'delta_targetband_score': float(best_row['targetband_score'] - base_scored['targetband_score']),
        'delta_target_cover_ratio_pred': float(best_row['target_gap_cover_ratio_pred'] - base_scored['target_gap_cover_ratio_pred']),
        'delta_target_overlap_pred_Hz': float(best_row['target_gap_overlap_pred_Hz'] - base_scored['target_gap_overlap_pred_Hz']),
    }
    return final_scored, history, summary


def main() -> None:
    args = parse_args()
    if int(args.population_size) < 4:
        raise ValueError('population-size must be at least 4')
    if int(args.elite_k) < 1:
        raise ValueError('elite-k must be at least 1')

    scored_csv = resolve_path(args.scored_csv)
    if scored_csv is None or not scored_csv.exists():
        raise FileNotFoundError(scored_csv)

    scored_df = pd.read_csv(scored_csv)
    if scored_df.empty:
        raise RuntimeError(f'Empty scored csv: {scored_csv}')

    band_tag = args.band_tag.strip() or derive_band_tag(args.band_low, args.band_high)
    out_dir = resolve_path(args.out_dir) if args.out_dir else DEFAULT_OUT_ROOT / 'targetband_local_ga_v1' / band_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    whitelist_shape_ids = load_shape_whitelist(args.whitelist_json)
    rng = np.random.default_rng(int(args.seed))
    seed_rows = ranked_seed_rows(scored_df, args.top_k_seeds, args.only_point_id, whitelist_shape_ids)

    all_best_rows: List[Dict[str, object]] = []
    all_summary_rows: List[Dict[str, object]] = []
    for _, base_row in seed_rows.iterrows():
        final_scored, history, summary = run_ga_for_seed(base_row, args, rng, band_tag)
        family = str(base_row.get('shape_family', 'seed'))
        shape = str(base_row.get('shape_id', 'shape'))
        stem = f'{family}_{shape}'.replace('\\', '_').replace('/', '_')

        history_path = out_dir / f'targetband_ga_history_{stem}.csv'
        top_path = out_dir / f'targetband_ga_top_candidates_{stem}.csv'
        save_csv_rows(history_path, list(history[0].keys()) if history else ['generation'], history)
        final_scored.head(12).to_csv(top_path, index=False, encoding='utf-8-sig')

        best_rows = final_scored.head(6).copy()
        best_rows['ga_seed_shape_id'] = shape
        best_rows['ga_base_point_id'] = str(base_row.get('point_id', ''))
        best_rows['target_band_low_Hz'] = float(args.band_low)
        best_rows['target_band_high_Hz'] = float(args.band_high)
        all_best_rows.extend(best_rows.to_dict(orient='records'))
        all_summary_rows.append(summary)

    if all_best_rows:
        pd.DataFrame(all_best_rows).to_csv(out_dir / 'targetband_ga_candidate_manifest_v1.csv', index=False, encoding='utf-8-sig')
    save_csv_rows(out_dir / 'targetband_ga_search_summary.csv', list(all_summary_rows[0].keys()) if all_summary_rows else ['shape_id'], all_summary_rows)
    save_json(
        out_dir / 'targetband_ga_config.json',
        {
            'scored_csv': str(scored_csv),
            'contact_run_root': str(args.contact_run_root),
            'contact_split': str(args.contact_split),
            'classifier_run_root': str(args.classifier_run_root),
            'regressor_run_root': str(args.regressor_run_root),
            'band_low_Hz': float(args.band_low),
            'band_high_Hz': float(args.band_high),
            'band_tag': band_tag,
            'top_k_seeds': int(args.top_k_seeds),
            'only_point_id': str(args.only_point_id),
            'population_size': int(args.population_size),
            'generations': int(args.generations),
            'elite_k': int(args.elite_k),
            'mutation_rate': float(args.mutation_rate),
            'mutation_scale': float(args.mutation_scale),
            'local_span_scale': float(args.local_span_scale),
            'contact_threshold': float(args.contact_threshold),
            'open_threshold': float(args.open_threshold),
            'cover_delta_cap': float(args.cover_delta_cap),
            'overlap_delta_cap': float(args.overlap_delta_cap),
            'seed': int(args.seed),
            'whitelist_json': str(args.whitelist_json) if args.whitelist_json else '',
            'whitelist_shape_ids': list(whitelist_shape_ids),
            'global_bounds': {key: [float(lo), float(hi)] for key, (lo, hi) in DEFAULT_GLOBAL_BOUNDS.items()},
            'local_half_widths': {key: float(val) for key, val in DEFAULT_LOCAL_HALF_WIDTHS.items()},
            'active_param_cols': list(ACTIVE_PARAM_COLS),
            'score_definition': '0.30*contact_prob + 0.45*target_open_prob + 0.20*target_cover_ratio_pred + 0.05*stage1_gain_prior, with contact/open gates ranked first',
            'fitness_definition': '0.70*targetband_score + 0.10*contact_gate + 0.10*target_open_gate + 0.05*contact_delta + 0.10*open_delta + 0.10*cover_delta + 0.05*overlap_delta - 0.25*distance_from_base',
            'notes': [
                'This run turns target-band seed scoring into target-band local refinement.',
                'The GA remains local and conservative; it is not intended to replace true global GA.',
                'The manifest is intended for the next real-validation step.',
            ],
        },
    )

    print('[DONE] target-band local GA complete')
    print(f'[OUT] {out_dir}')
    print(f'[BAND] {band_tag} [{args.band_low:.1f}, {args.band_high:.1f}] Hz')
    print(f'[SEEDS] optimized={len(seed_rows)} point_filter={args.only_point_id or "ALL"} whitelist={len(whitelist_shape_ids)}')


if __name__ == '__main__':
    main()
