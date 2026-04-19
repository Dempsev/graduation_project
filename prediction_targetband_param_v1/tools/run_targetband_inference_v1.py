from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from prediction_targetband_param_v1.models.inference import build_targetband_prediction_frame
from shared.objectives.targetband import derive_band_tag


DEFAULT_INPUT_CSV = ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_optimization_v1' / 'candidate_pool_optimization_v1.csv'
DEFAULT_OUT_ROOT = ROOT / 'data' / 'prediction_targetband_param_v1_app' / 'v1' / 'inference'
DEFAULT_CLASSIFIER_RUN = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cls_dense_family' / 'stratified_group_kfold'
DEFAULT_REGRESSOR_RUN = ROOT / 'data' / 'prediction_targetband_param_v1_runs' / 'param_targetband_cover_dense_family' / 'stratified_group_kfold'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run parameterized target-band inference on an arbitrary candidate csv.')
    parser.add_argument('--input-csv', type=Path, default=DEFAULT_INPUT_CSV)
    parser.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument('--classifier-run-root', type=Path, default=DEFAULT_CLASSIFIER_RUN)
    parser.add_argument('--regressor-run-root', type=Path, default=DEFAULT_REGRESSOR_RUN)
    parser.add_argument('--band-low', type=float, default=180.0)
    parser.add_argument('--band-high', type=float, default=220.0)
    parser.add_argument('--band-tag', default='')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input_csv)
    if df.empty:
        raise RuntimeError(f'Empty input csv: {args.input_csv}')

    band_tag = args.band_tag.strip() or derive_band_tag(args.band_low, args.band_high)
    out_dir = args.out_dir / band_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    scored = build_targetband_prediction_frame(
        df,
        args.band_low,
        args.band_high,
        args.classifier_run_root,
        args.regressor_run_root,
        band_tag=band_tag,
    )
    out_csv = out_dir / 'targetband_predictions.csv'
    out_json = out_dir / 'targetband_inference_config.json'
    scored.to_csv(out_csv, index=False, encoding='utf-8-sig')
    out_json.write_text(
        json.dumps(
            {
                'input_csv': str(args.input_csv),
                'classifier_run_root': str(args.classifier_run_root),
                'regressor_run_root': str(args.regressor_run_root),
                'band_low_Hz': float(args.band_low),
                'band_high_Hz': float(args.band_high),
                'band_tag': band_tag,
                'rows': int(len(scored)),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding='utf-8',
    )

    print('[DONE] target-band inference complete')
    print(f'[OUT] {out_csv}')
    print(f'[TOP_OPEN] {float(scored["target_open_prob"].max()):.4f}')
    print(f'[TOP_COVER] {float(scored["target_gap_cover_ratio_pred"].max()):.4f}')


if __name__ == '__main__':
    main()
