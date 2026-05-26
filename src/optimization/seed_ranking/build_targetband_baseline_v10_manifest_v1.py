from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.io.stage4_validation_manifest import write_stage4_validation_manifest_csv


DEFAULT_CANDIDATE_POOL = (
    ROOT
    / 'data'
    / 'ml_dataset'
    / 'v12'
    / 'candidate_pool_optimization_v1'
    / 'candidate_pool_optimization_v1.csv'
)
DEFAULT_SCORED_CSV = (
    ROOT
    / 'data'
    / 'ml_runs'
    / 'targetband_seed_scoring_v10_multiband_neighborhood_v1'
    / 'band180_220'
    / 'targetband_seed_predictions.csv'
)
DEFAULT_OUT_DIR = (
    ROOT
    / 'data'
    / 'ml_runs'
    / 'targetband_baseline_v10_v1'
    / 'validation_manifest_v1'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build Stage4 manifest for v10 predictor-vs-random target-band baseline.')
    parser.add_argument('--candidate-pool', type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--point-id', default='rf09_h00_center')
    parser.add_argument('--k', type=int, default=6)
    parser.add_argument('--random-seed', type=int, default=20260513)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def require_columns(df: pd.DataFrame, columns: List[str], source: Path) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f'{source} is missing required columns: {missing}')


def filter_point(df: pd.DataFrame, point_id: str) -> pd.DataFrame:
    if 'point_id' not in df.columns:
        return df.copy()
    out = df[df['point_id'].astype(str) == point_id].copy()
    if out.empty:
        return df.copy()
    return out


def family_balanced_random(df: pd.DataFrame, k: int, seed: int) -> pd.DataFrame:
    require_columns(df, ['shape_family', 'shape_id'], Path('candidate pool'))

    def stable_key(value: str, salt: int) -> int:
        digest = hashlib.sha256(f'{salt}::{value}'.encode('utf-8')).hexdigest()
        return int(digest[:16], 16)

    work = df.copy()
    work['_rand'] = (
        work['shape_family'].astype(str)
        + '::'
        + work['shape_id'].astype(str)
        + '::'
        + work['candidate_id'].astype(str)
    ).map(lambda value: stable_key(value, int(seed)))
    work = work.sort_values(['shape_family', '_rand']).drop_duplicates('shape_family', keep='first')
    if len(work) < k:
        remainder = df[~df['shape_id'].astype(str).isin(work['shape_id'].astype(str))].copy()
        remainder['_rand'] = (
            remainder['shape_family'].astype(str)
            + '::'
            + remainder['shape_id'].astype(str)
            + '::'
            + remainder['candidate_id'].astype(str)
        ).map(lambda value: stable_key(value, int(seed) + 1))
        work = pd.concat([work, remainder.sort_values('_rand')], ignore_index=True)
    return work.sort_values('_rand').head(k).drop(columns=['_rand'], errors='ignore').copy()


def predictor_only_topk(df: pd.DataFrame, k: int) -> pd.DataFrame:
    sort_cols = [
        'targetband_gate',
        'targetband_score',
        'target_gap_cover_ratio_pred',
        'target_open_prob',
        'contact_prob',
        'target_gap_overlap_pred_Hz',
    ]
    require_columns(df, ['shape_id', *sort_cols], Path('targetband scored csv'))
    ranked = df.sort_values(sort_cols, ascending=[False, False, False, False, False, False]).copy()
    ranked = ranked.drop_duplicates('shape_id', keep='first')
    return ranked.head(k).copy()


def arm_frame(df: pd.DataFrame, source: str, label: str, prefix: str, k: int) -> pd.DataFrame:
    out = df.head(k).copy()
    out['selection_source'] = source
    out['selection_label'] = label
    out['rank_within_source'] = range(1, len(out) + 1)
    out['validation_id'] = [f'{prefix}{idx:03d}' for idx in range(1, len(out) + 1)]
    out['sample_id'] = out.get('sample_id', pd.Series([''] * len(out))).astype(str)
    if 'candidate_id' not in out.columns:
        out['candidate_id'] = [f'{prefix}_candidate_{idx:03d}' for idx in range(1, len(out) + 1)]
    return out


def summarize_arm(df: pd.DataFrame, source: str) -> Dict[str, object]:
    row: Dict[str, object] = {
        'selection_source': source,
        'rows': int(len(df)),
        'unique_shapes': int(df['shape_id'].astype(str).nunique()) if 'shape_id' in df.columns else 0,
        'unique_families': int(df['shape_family'].astype(str).nunique()) if 'shape_family' in df.columns else 0,
    }
    for column in ['targetband_score', 'target_gap_cover_ratio_pred', 'target_gap_overlap_pred_Hz', 'contact_prob', 'target_open_prob']:
        if column in df.columns:
            row[f'mean_{column}'] = float(pd.to_numeric(df[column], errors='coerce').mean())
            row[f'best_{column}'] = float(pd.to_numeric(df[column], errors='coerce').max())
    return row


def main() -> None:
    args = parse_args()
    k = max(1, int(args.k))
    out_dir = resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidate_pool_path = resolve_path(args.candidate_pool)
    scored_path = resolve_path(args.scored_csv)
    for path in [candidate_pool_path, scored_path]:
        if not path.exists():
            raise FileNotFoundError(path)

    candidate_pool = filter_point(pd.read_csv(candidate_pool_path), args.point_id)
    scored = filter_point(pd.read_csv(scored_path), args.point_id)

    random_rows = family_balanced_random(candidate_pool, k, int(args.random_seed))
    predictor_rows = predictor_only_topk(scored, k)

    arms = [
        arm_frame(random_rows, 'random_family_balanced_v1', f'random_family_balanced_k{k}_seed_{args.random_seed}', 'rand', k),
        arm_frame(predictor_rows, 'predictor_only_topk_v10_v1', f'v10_predictor_only_180_220_top_{k}', 'predv10', k),
    ]
    manifest = pd.concat(arms, ignore_index=True, sort=False)

    manifest_path = out_dir / 'targetband_baseline_v10_manifest_v1.csv'
    prepared = write_stage4_validation_manifest_csv(manifest, manifest_path)

    summary = {
        'target_band': {'band_low_Hz': 180.0, 'band_high_Hz': 220.0, 'band_tag': 'band180_220'},
        'point_id': args.point_id,
        'k_per_arm': k,
        'random_seed': int(args.random_seed),
        'candidate_pool': str(candidate_pool_path),
        'scored_csv': str(scored_path),
        'manifest_csv': str(manifest_path),
        'rows_total': int(len(prepared)),
        'arms': [
            summarize_arm(random_rows, 'random_family_balanced_v1'),
            summarize_arm(predictor_rows, 'predictor_only_topk_v10_v1'),
        ],
    }
    summary_path = out_dir / 'targetband_baseline_v10_manifest_summary.json'
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] target-band v10 validation manifest built')
    print(f'[OUT] {manifest_path}')
    print(f'[ROWS] {len(prepared)} total, {k} per arm')


if __name__ == '__main__':
    main()
