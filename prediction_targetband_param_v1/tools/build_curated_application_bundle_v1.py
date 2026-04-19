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

from stage3_training.ml_common import save_csv_rows, save_json

DEFAULT_CONFIG = ROOT / 'prediction_targetband_param_v1' / 'configs' / 'curated_band_catalog_v1.json'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1_app' / 'v1'
RUN_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1_runs'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build an application-facing curated output bundle from dense target-band training runs.')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--classifier-family-run', default='param_targetband_cls_dense_family')
    parser.add_argument('--classifier-bandloo-run', default='param_targetband_cls_dense_bandloo')
    parser.add_argument('--regressor-family-run', default='param_targetband_cover_dense_family')
    parser.add_argument('--regressor-bandloo-run', default='param_targetband_cover_dense_bandloo_n300')
    parser.add_argument('--out-tag', default='curated_serving_v1')
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding='utf-8'))


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def metric_row(df: pd.DataFrame, band_tag: str) -> Dict[str, object]:
    subset = df[df['target_band_tag'].astype(str) == band_tag]
    if subset.empty:
        raise KeyError(f'missing metrics for {band_tag} in {df}')
    return subset.iloc[0].to_dict()


def build_rows(
    config: Dict[str, object],
    cls_family_df: pd.DataFrame,
    cls_bandloo_df: pd.DataFrame,
    reg_family_df: pd.DataFrame,
    reg_bandloo_df: pd.DataFrame,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for band in config['bands']:
        band_tag = str(band['target_band_tag'])
        cls_family = metric_row(cls_family_df, band_tag)
        cls_bandloo = metric_row(cls_bandloo_df, band_tag)
        reg_family = metric_row(reg_family_df, band_tag)
        reg_bandloo = metric_row(reg_bandloo_df, band_tag)
        rows.append({
            'target_band_tag': band_tag,
            'band_low_Hz': float(band['band_low_Hz']),
            'band_high_Hz': float(band['band_high_Hz']),
            'label': str(band['label']),
            'role': str(band['role']),
            'reason': str(band['reason']),
            'family_positive_rate': float(cls_family['positive_rate']),
            'family_cls_f1': float(cls_family['f1']),
            'family_cls_balanced_accuracy': float(cls_family['balanced_accuracy']),
            'bandloo_cls_f1': float(cls_bandloo['f1']),
            'bandloo_cls_balanced_accuracy': float(cls_bandloo['balanced_accuracy']),
            'family_cover_mae': float(reg_family['mae']),
            'family_cover_r2': float(reg_family['r2']),
            'bandloo_cover_mae': float(reg_bandloo['mae']),
            'bandloo_cover_r2': float(reg_bandloo['r2']),
        })
    return rows


def build_summary(config: Dict[str, object], args: argparse.Namespace, rows: List[Dict[str, object]], out_dir: Path) -> Dict[str, object]:
    return {
        'bundle_name': 'prediction_targetband_parametric_curated_output_v1',
        'config': str(args.config),
        'training_dataset_tag': config['training_dataset_tag'],
        'training_role': config['training_role'],
        'serving_role': config['serving_role'],
        'classifier_family_run': args.classifier_family_run,
        'classifier_bandloo_run': args.classifier_bandloo_run,
        'regressor_family_run': args.regressor_family_run,
        'regressor_bandloo_run': args.regressor_bandloo_run,
        'curated_band_count': len(rows),
        'out_dir': str(out_dir),
        'notes': [
            'The dense grid is used only as the internal training base.',
            'The curated band catalog is the recommended application-facing output layer.',
            'Family CV measures generalization to unseen structure families under known target bands.',
            'Band-tag LOO measures how stable each curated output band remains when treated as an unseen condition during evaluation.',
        ],
        'bands': rows,
    }


def main() -> None:
    args = parse_args()
    config = load_json(args.config)

    cls_family_df = load_csv(RUN_ROOT / args.classifier_family_run / 'stratified_group_kfold' / 'per_band_metrics.csv')
    cls_bandloo_df = load_csv(RUN_ROOT / args.classifier_bandloo_run / 'leave_one_band_tag_out' / 'per_band_metrics.csv')
    reg_family_df = load_csv(RUN_ROOT / args.regressor_family_run / 'stratified_group_kfold' / 'per_band_metrics.csv')
    reg_bandloo_df = load_csv(RUN_ROOT / args.regressor_bandloo_run / 'leave_one_band_tag_out' / 'per_band_metrics.csv')

    rows = build_rows(config, cls_family_df, cls_bandloo_df, reg_family_df, reg_bandloo_df)

    out_dir = DEFAULT_OUT_ROOT / args.out_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_json = out_dir / 'curated_application_bundle_v1.json'
    summary_csv = out_dir / 'curated_application_bundle_v1.csv'

    save_json(summary_json, build_summary(config, args, rows, out_dir))
    save_csv_rows(
        summary_csv,
        [
            'target_band_tag',
            'band_low_Hz',
            'band_high_Hz',
            'label',
            'role',
            'reason',
            'family_positive_rate',
            'family_cls_f1',
            'family_cls_balanced_accuracy',
            'bandloo_cls_f1',
            'bandloo_cls_balanced_accuracy',
            'family_cover_mae',
            'family_cover_r2',
            'bandloo_cover_mae',
            'bandloo_cover_r2',
        ],
        rows,
    )

    print(f'[DONE] curated bands: {len(rows)}')
    print(f'[OUT] {summary_json}')
    print(f'[OUT] {summary_csv}')


if __name__ == '__main__':
    main()
