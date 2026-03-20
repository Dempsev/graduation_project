from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v4' / 'cascade_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v4' / 'validation_manifest_v4'

MANIFEST_FIELDS = [
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source',
    'sample_id', 'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'pool_arm', 'point_strategy', 'family_prior_source',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'class_score', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build split-arm v4 COMSOL validation manifest.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--broad-top-k', type=int, default=12)
    parser.add_argument('--exploit-top-k', type=int, default=8)
    parser.add_argument('--surrogate-top-k', type=int, default=20)
    parser.add_argument('--max-per-family', type=int, default=2)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def select_ranked(df: pd.DataFrame, source_name: str, score_cols: List[str], top_k: int, max_per_family: int, gated_only: bool, pool_arm: str | None = None) -> List[Dict[str, object]]:
    ranked = df.copy()
    if pool_arm is not None:
        ranked = ranked[ranked['pool_arm'].astype(str) == pool_arm].copy()
    if gated_only:
        gated = ranked[ranked['cascade_gate'] == 1].copy()
        if not gated.empty:
            ranked = gated
    ranked = ranked.sort_values(score_cols, ascending=[False] * len(score_cols))
    rows: List[Dict[str, object]] = []
    family_counts: Dict[str, int] = {}
    for _, row in ranked.iterrows():
        family = str(row.get('shape_family', ''))
        if max_per_family > 0 and family_counts.get(family, 0) >= max_per_family:
            continue
        family_counts[family] = family_counts.get(family, 0) + 1
        rows.append({
            'selection_source': source_name,
            'selection_label': f'{source_name}_top_{top_k}',
            'rank_within_source': len(rows) + 1,
            **row.to_dict(),
        })
        if len(rows) >= top_k:
            break
    return rows


def merge_rankings(*rank_groups: List[Dict[str, object]]) -> List[Dict[str, object]]:
    merged: Dict[str, Dict[str, object]] = {}
    for rows in rank_groups:
        for item in rows:
            sample_id = str(item['sample_id'])
            source = str(item['selection_source'])
            if sample_id not in merged:
                merged[sample_id] = item.copy()
            else:
                existing = merged[sample_id]
                if existing['selection_source'] != source:
                    existing['selection_source'] = 'both'
                existing['selection_label'] = f"{existing['selection_label']}|{item['selection_label']}"
    merged_rows = list(merged.values())
    merged_rows.sort(key=lambda item: (0 if item['selection_source'] == 'both' else 1, item['rank_within_source']))
    for idx, row in enumerate(merged_rows, start=1):
        row['validation_id'] = f'val{idx:03d}'
    return merged_rows


def main() -> None:
    args = parse_args()
    if not args.scored_csv.exists():
        raise FileNotFoundError(args.scored_csv)
    ensure_dir(args.out_dir)

    df = pd.read_csv(args.scored_csv)
    if df.empty:
        raise RuntimeError('Scored candidate pool is empty.')
    for col in ['cascade_score', 'class_score', 'surrogate_pred_gap34_gain_Hz']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    cascade_broad = select_ranked(df, 'cascade_broad', ['cascade_score', 'surrogate_pred_gap34_gain_Hz'], args.broad_top_k, args.max_per_family, True, 'broad')
    cascade_exploit = select_ranked(df, 'cascade_exploitation', ['cascade_score', 'surrogate_pred_gap34_gain_Hz'], args.exploit_top_k, args.max_per_family, True, 'exploitation')
    surrogate_rows = select_ranked(df, 'surrogate_only', ['surrogate_pred_gap34_gain_Hz', 'class_score'], args.surrogate_top_k, args.max_per_family, False, None)
    manifest_rows = merge_rankings(cascade_broad, cascade_exploit, surrogate_rows)

    broad_csv = args.out_dir / 'cascade_broad_top_candidates_for_validation.csv'
    exploit_csv = args.out_dir / 'cascade_exploitation_top_candidates_for_validation.csv'
    surrogate_csv = args.out_dir / 'surrogate_top_candidates_for_validation.csv'
    manifest_csv = args.out_dir / 'comsol_validation_manifest_v4.csv'
    summary_json = args.out_dir / 'validation_manifest_summary.json'

    extra_fields = [f for f in MANIFEST_FIELDS if f not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}]
    write_csv(broad_csv, cascade_broad, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(exploit_csv, cascade_exploit, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(surrogate_csv, surrogate_rows, ['selection_source', 'selection_label', 'rank_within_source', *extra_fields])
    write_csv(manifest_csv, manifest_rows, MANIFEST_FIELDS)

    summary = {
        'scored_csv': str(args.scored_csv),
        'broad_top_k': args.broad_top_k,
        'exploit_top_k': args.exploit_top_k,
        'surrogate_top_k': args.surrogate_top_k,
        'max_per_family': args.max_per_family,
        'cascade_broad_rows': len(cascade_broad),
        'cascade_exploitation_rows': len(cascade_exploit),
        'surrogate_rows': len(surrogate_rows),
        'manifest_rows': len(manifest_rows),
        'overlap_rows': int(sum(1 for row in manifest_rows if row['selection_source'] == 'both')),
        'cascade_rows_total': len(cascade_broad) + len(cascade_exploit),
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] validation manifest v4 built')
    print(f'[OUT] {manifest_csv}')
    print(f"[SUMMARY] broad={len(cascade_broad)} exploit={len(cascade_exploit)} surrogate={len(surrogate_rows)} overlap={summary['overlap_rows']}")


if __name__ == '__main__':
    main()
