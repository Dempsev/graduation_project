from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stage3_training.ml_common import save_json

SOURCE_ROOT = ROOT / 'data' / 'prediction_targetband_v1'
OUT_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1' / 'v1'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a parameterized target-band dataset by stacking validated fixed windows.')
    parser.add_argument('--dataset-tags', default='band120_160,band180_220,band220_260')
    parser.add_argument('--out-tag', default='windows_120_160__180_220__220_260')
    return parser.parse_args()


def parse_dataset_tags(text: str) -> List[str]:
    tags = [part.strip() for part in text.split(',') if part.strip()]
    if not tags:
        raise ValueError('dataset tags must not be empty')
    return tags


def load_rows(tag: str) -> pd.DataFrame:
    csv_path = SOURCE_ROOT / tag / 'targetband_prediction_v1.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f'missing target-band dataset: {csv_path}')
    df = pd.read_csv(csv_path)
    df['target_band_tag'] = tag
    low = pd.to_numeric(df['target_band_low_Hz'], errors='coerce').astype(float)
    high = pd.to_numeric(df['target_band_high_Hz'], errors='coerce').astype(float)
    df['target_band_center_Hz'] = 0.5 * (low + high)
    df['target_band_width_Hz'] = high - low
    df['param_sample_id'] = (
        df['design_id'].astype(str)
        + '::'
        + low.round(6).astype(str)
        + '_'
        + high.round(6).astype(str)
    )
    return df


def build_dataset_info(df: pd.DataFrame, tags: List[str], out_dir: Path, out_csv: Path) -> Dict[str, object]:
    per_tag_rows = []
    for tag, subset in df.groupby('target_band_tag'):
        per_tag_rows.append({
            'target_band_tag': str(tag),
            'rows': int(len(subset)),
            'positive_rate': float(pd.to_numeric(subset['target_gap_is_open'], errors='coerce').fillna(0.0).mean()),
            'positive_rows': int(pd.to_numeric(subset['target_gap_is_open'], errors='coerce').fillna(0.0).sum()),
            'cover_ratio_mean_positive': float(
                pd.to_numeric(subset.loc[pd.to_numeric(subset['target_gap_is_open'], errors='coerce').fillna(0.0) > 0.5, 'target_gap_cover_ratio'], errors='coerce').mean()
            ),
        })
    return {
        'dataset_name': 'prediction_targetband_param_v1',
        'source_tags': tags,
        'task_definition': 'parameterized target-band prediction from validated fixed-window tasks',
        'rows': int(len(df)),
        'unique_designs': int(df['design_id'].astype(str).nunique()),
        'unique_families': int(df['shape_family'].astype(str).nunique()),
        'out_dir': str(out_dir),
        'dataset_csv': str(out_csv),
        'per_tag_summary': per_tag_rows,
        'notes': [
            'This dataset stacks several validated fixed frequency windows into a single conditional prediction table.',
            'Inputs remain purely structural; frequency-window bounds are appended as condition variables.',
        ],
    }


def main() -> None:
    args = parse_args()
    tags = parse_dataset_tags(args.dataset_tags)
    frames = [load_rows(tag) for tag in tags]
    df = pd.concat(frames, ignore_index=True)
    out_dir = OUT_ROOT / args.out_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / 'targetband_parametric_v1.csv'
    info_json = out_dir / 'dataset_info.json'

    df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    save_json(info_json, build_dataset_info(df, tags, out_dir, out_csv))

    print(f'[DONE] stacked rows: {len(df)}')
    print(f'[DONE] unique designs: {df["design_id"].astype(str).nunique()}')
    print(f'[OUT] {out_csv}')
    print(f'[OUT] {info_json}')


if __name__ == '__main__':
    main()
