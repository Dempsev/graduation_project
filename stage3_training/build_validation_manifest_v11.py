from __future__ import annotations

"""Legacy baseline bridge for the old v11 stage4 validation manifest line."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from policy_resolution import load_policy_json, resolve_policy_settings
from seed_discovery_pipeline import build_validation_manifest_for_profile
from seed_discovery_profiles import get_profile

PROFILE_NAME = 'candidate_pool_v11_seed_only_refined'


def parse_args() -> argparse.Namespace:
    profile = get_profile(PROFILE_NAME)
    manifest_cfg = profile['manifest']
    policy_path = Path(profile['policy_paths']['manifest'])
    parser = argparse.ArgumentParser(description='Build v11 COMSOL validation manifest for remaining seed-only discovery.')
    parser.add_argument('--policy-json', type=Path, default=policy_path)
    parser.add_argument('--scored-csv', type=Path, default=Path(manifest_cfg['scored_csv']))
    parser.add_argument('--out-dir', type=Path, default=Path(manifest_cfg['out_dir']))
    parser.add_argument('--primary-k', type=int, default=6)
    parser.add_argument('--probe-k', type=int, default=2)
    parser.add_argument('--diversity-k', type=int, default=0)
    parser.add_argument('--max-per-shape', type=int, default=0)
    parser.add_argument('--max-per-family', type=int, default=0)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    profile = get_profile(PROFILE_NAME)
    defaults = {
        'scored_csv': Path(profile['manifest']['scored_csv']),
        'out_dir': Path(profile['manifest']['out_dir']),
        'primary_k': 6,
        'probe_k': 2,
        'diversity_k': 0,
        'max_per_shape': 0,
        'max_per_family': 0,
    }
    policy = load_policy_json(args.policy_json)
    cli_values = {
        'scored_csv': args.scored_csv,
        'out_dir': args.out_dir,
        'primary_k': args.primary_k,
        'probe_k': args.probe_k,
        'diversity_k': args.diversity_k,
        'max_per_shape': args.max_per_shape,
        'max_per_family': args.max_per_family,
    }
    merged = resolve_policy_settings(defaults, policy, cli_values, defaults, policy_enabled=args.policy_json is not None)
    scored_csv = Path(merged['scored_csv'])
    if not scored_csv.is_absolute():
        scored_csv = ROOT / scored_csv
    out_dir = Path(merged['out_dir'])
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    result = build_validation_manifest_for_profile(profile, merged, scored_csv=scored_csv, out_dir=out_dir)
    summary = result['summary']
    print('[DONE] validation manifest v11 built')
    print(f"[OUT] {result['manifest_csv']}")
    print(f"[SUMMARY] total={summary['manifest_rows']} primary={summary['primary_rows']} probe={summary['probe_rows']} diversity={summary['diversity_rows']} unique_shapes={summary['unique_shape_count']}")
