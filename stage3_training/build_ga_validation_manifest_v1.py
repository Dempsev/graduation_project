from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import pandas as pd

from policy_resolution import load_policy_json, resolve_policy_settings
from ml_common import DEFAULT_OUT_ROOT, save_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GA_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1' / 'ga_candidate_manifest_v1.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_seed_discovery_v10' / 'ga_parametric_search_v1' / 'validation_manifest_v1'
DEFAULT_POLICY_JSON = ROOT / 'stage3_training' / 'policies' / 'ga_v1.json'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a compact COMSOL-ready manifest from GA candidates.')
    parser.add_argument('--policy-json', type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument('--ga-csv', type=Path, default=DEFAULT_GA_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--total-k', type=int, default=6)
    parser.add_argument('--per-seed-k', type=int, default=2)
    return parser.parse_args()


def rank_candidates(df: pd.DataFrame) -> pd.DataFrame:
    pred_col = 'surrogate_pred_gap34_gain_Hz' if 'surrogate_pred_gap34_gain_Hz' in df.columns else 'surrogate_pred_objective_value'
    return df.sort_values(
        ['fitness', 'cascade_score', 'contact_prob', pred_col, 'distance_from_base'],
        ascending=[False, False, False, False, True],
    ).copy()


def resolve_manifest_config(args: argparse.Namespace) -> Dict[str, object]:
    policy = load_policy_json(args.policy_json, section='validation_manifest') if args.policy_json else {}
    defaults = {
        'ga_csv': DEFAULT_GA_CSV,
        'out_dir': DEFAULT_OUT_DIR,
        'total_k': 6,
        'per_seed_k': 2,
    }
    cli_values = {
        'ga_csv': args.ga_csv,
        'out_dir': args.out_dir,
        'total_k': args.total_k,
        'per_seed_k': args.per_seed_k,
    }
    resolved = resolve_policy_settings(defaults, policy, cli_values, defaults, policy_enabled=args.policy_json is not None)
    for key in ['ga_csv', 'out_dir']:
        path_value = Path(resolved[key])
        if not path_value.is_absolute():
            path_value = ROOT / path_value
        resolved[key] = path_value
    return resolved


if __name__ == '__main__':
    args = parse_args()
    config = resolve_manifest_config(args)
    if not Path(config['ga_csv']).exists():
        raise FileNotFoundError(config['ga_csv'])
    Path(config['out_dir']).mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(config['ga_csv'])
    if df.empty:
        raise RuntimeError('GA candidate manifest is empty.')

    ranked = rank_candidates(df)
    selected_rows: List[Dict[str, object]] = []
    for _, subset in ranked.groupby('ga_seed_shape_id', sort=False):
        selected_rows.extend(subset.head(max(1, int(config['per_seed_k']))).to_dict(orient='records'))

    selected = rank_candidates(pd.DataFrame(selected_rows)).head(max(1, int(config['total_k']))).copy()
    if selected.empty:
        raise RuntimeError('No GA validation rows selected.')

    selected['validation_id'] = [f'ga_val{i:03d}' for i in range(1, len(selected) + 1)]
    selected['selection_source'] = 'parametric_ga_v1'
    selected['selection_label'] = f'ga_top_{len(selected)}_per_seed_{int(config["per_seed_k"])}'
    selected['rank_within_source'] = range(1, len(selected) + 1)

    manifest_path = Path(config['out_dir']) / 'ga_validation_manifest_v1.csv'
    summary_path = Path(config['out_dir']) / 'ga_validation_manifest_summary.json'
    selected.to_csv(manifest_path, index=False, encoding='utf-8-sig')
    save_json(summary_path, {
        'policy_json': str(args.policy_json) if args.policy_json else '',
        'ga_csv': str(config['ga_csv']),
        'manifest_rows': int(len(selected)),
        'total_k': int(config['total_k']),
        'per_seed_k': int(config['per_seed_k']),
        'unique_seed_shapes': int(selected['ga_seed_shape_id'].astype(str).nunique()),
        'unique_points': int(selected['point_id'].astype(str).nunique()),
        'mean_fitness': float(selected['fitness'].mean()),
        'mean_distance_from_base': float(selected['distance_from_base'].mean()),
    })

    print('[DONE] GA validation manifest built')
    print(f'[OUT] {manifest_path}')
    print(f'[SUMMARY] total={len(selected)} unique_seed_shapes={selected["ga_seed_shape_id"].astype(str).nunique()}')
