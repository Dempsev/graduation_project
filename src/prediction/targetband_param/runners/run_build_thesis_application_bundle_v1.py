from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / 'src' / 'prediction' / 'targetband_param' / 'tools' / 'build_curated_application_bundle_v1.py'
DEFAULT_ARGS = [
    '--config',
    str(ROOT / 'src' / 'prediction' / 'targetband_param' / 'configs' / 'curated_band_catalog_thesis_v2.json'),
    '--classifier-family-run',
    'param_targetband_cls_rf_dense_v8_cmp_v1',
    '--classifier-bandloo-run',
    'param_targetband_cls_dense_bandloo',
    '--regressor-family-run',
    'param_targetband_cover_hgb_dense_v8_cmp_v1',
    '--regressor-bandloo-run',
    'param_targetband_cover_dense_bandloo_n300',
    '--out-tag',
    'thesis_band_catalog_v2_bundle_v1',
    '--allow-missing-bandloo',
]


def main() -> None:
    sys.argv = [str(TARGET), *DEFAULT_ARGS, *sys.argv[1:]]
    runpy.run_path(str(TARGET), run_name='__main__')


if __name__ == '__main__':
    main()
