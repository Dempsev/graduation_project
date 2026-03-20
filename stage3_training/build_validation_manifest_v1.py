from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ml_common import DEFAULT_OUT_ROOT, ROOT

DEFAULT_SCORED_CSV = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v1' / 'cascade_predictions.csv'
DEFAULT_OUT_DIR = DEFAULT_OUT_ROOT / 'candidate_pool_cascade_v1' / 'validation_manifest_v1'

MANIFEST_FIELDS = [
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source',
    'sample_id', 'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build COMSOL validation manifest from cascade-scored candidate pool.')
    parser.add_argument('--scored-csv', type=Path, default=DEFAULT_SCORED_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument('--cascade-top-k', type=int, default=20)
    parser.add_argument('--surrogate-top-k', type=int, default=20)
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


def add_rank_rows(df: pd.DataFrame, source_name: str, score_col: str, top_k: int) -> List[Dict[str, object]]:
    ranked = df.sort_values(score_col, ascending=False).head(min(top_k, len(df))).copy()
    rows: List[Dict[str, object]] = []
    for rank, (_, row) in enumerate(ranked.iterrows(), start=1):
        rows.append({
            'selection_source': source_name,
            'selection_label': f'{source_name}_top_{top_k}',
            'rank_within_source': rank,
            **row.to_dict(),
        })
    return rows


def merge_rankings(cascade_rows: List[Dict[str, object]], surrogate_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    merged: Dict[str, Dict[str, object]] = {}

    def upsert(rows: List[Dict[str, object]], label: str) -> None:
        for item in rows:
            sample_id = str(item['sample_id'])
            if sample_id not in merged:
                merged[sample_id] = item.copy()
                merged[sample_id]['selection_source'] = label
            else:
                existing = merged[sample_id]
                if existing['selection_source'] != label:
                    existing['selection_source'] = 'both'
                if label == 'cascade':
                    existing['rank_cascade'] = item['rank_within_source']
                if label == 'surrogate_only':
                    existing['rank_surrogate'] = item['rank_within_source']

    for row in cascade_rows:
        row['rank_cascade'] = row['rank_within_source']
        row['rank_surrogate'] = ''
    for row in surrogate_rows:
        row['rank_surrogate'] = row['rank_within_source']
        row['rank_cascade'] = ''

    upsert(cascade_rows, 'cascade')
    upsert(surrogate_rows, 'surrogate_only')

    merged_rows = list(merged.values())
    merged_rows.sort(
        key=lambda item: (
            0 if item['selection_source'] == 'both' else 1,
            item.get('rank_cascade', 9999) if item.get('rank_cascade', '') != '' else 9999,
            item.get('rank_surrogate', 9999) if item.get('rank_surrogate', '') != '' else 9999,
        )
    )
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

    for col in ['cascade_score', 'surrogate_pred_gap34_gain_Hz']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    cascade_rows = add_rank_rows(df, 'cascade', 'cascade_score', args.cascade_top_k)
    surrogate_rows = add_rank_rows(df, 'surrogate_only', 'surrogate_pred_gap34_gain_Hz', args.surrogate_top_k)
    manifest_rows = merge_rankings(cascade_rows, surrogate_rows)

    cascade_csv = args.out_dir / 'cascade_top_candidates_for_validation.csv'
    surrogate_csv = args.out_dir / 'surrogate_top_candidates_for_validation.csv'
    manifest_csv = args.out_dir / 'comsol_validation_manifest_v1.csv'
    summary_json = args.out_dir / 'validation_manifest_summary.json'

    write_csv(cascade_csv, cascade_rows, ['selection_source', 'selection_label', 'rank_within_source', *[f for f in MANIFEST_FIELDS if f not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}], 'rank_cascade', 'rank_surrogate'])
    write_csv(surrogate_csv, surrogate_rows, ['selection_source', 'selection_label', 'rank_within_source', *[f for f in MANIFEST_FIELDS if f not in {'validation_id', 'selection_source', 'selection_label', 'rank_within_source'}], 'rank_cascade', 'rank_surrogate'])
    write_csv(manifest_csv, manifest_rows, [*MANIFEST_FIELDS, 'rank_cascade', 'rank_surrogate'])

    summary = {
        'scored_csv': str(args.scored_csv),
        'cascade_top_k': args.cascade_top_k,
        'surrogate_top_k': args.surrogate_top_k,
        'cascade_rows': len(cascade_rows),
        'surrogate_rows': len(surrogate_rows),
        'manifest_rows': len(manifest_rows),
        'overlap_rows': int(sum(1 for row in manifest_rows if row['selection_source'] == 'both')),
        'cascade_only_rows': int(sum(1 for row in manifest_rows if row['selection_source'] == 'cascade')),
        'surrogate_only_rows': int(sum(1 for row in manifest_rows if row['selection_source'] == 'surrogate_only')),
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('[DONE] validation manifest built')
    print(f'[OUT] {manifest_csv}')
    print(f'[SUMMARY] overlap={summary["overlap_rows"]} cascade_only={summary["cascade_only_rows"]} surrogate_only={summary["surrogate_only_rows"]}')


if __name__ == '__main__':
    main()
