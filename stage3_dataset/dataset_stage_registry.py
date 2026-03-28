from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


def _stage4(name: str, version: str, manifest_suffix: str | None = None) -> Dict[str, object]:
    stage = {
        'name': name,
        'results_csv': ROOT / 'data' / 'comsol_batch' / f'stage4_validation_ab_{version}' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / f'stage4_validation_ab_{version}' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / f'stage4_validation_ab_{version}' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / f'stage4_validation_ab_{version}' / 'tbl1_exports',
        'include_in_surrogate_core': True,
    }
    if manifest_suffix:
        stage['manifest_csv'] = ROOT / 'data' / 'ml_runs' / manifest_suffix / f'validation_manifest_{version}' / f'comsol_validation_manifest_{version}.csv'
    return stage


STAGE_REGISTRY: Dict[str, Dict[str, object]] = {
    'stage4_validation_v1': _stage4('stage4_validation_v1', 'v1'),
    'stage4_validation_v2': _stage4('stage4_validation_v2', 'v2'),
    'stage4_validation_v3': _stage4('stage4_validation_v3', 'v3'),
    'stage4_validation_v5': _stage4('stage4_validation_v5', 'v5'),
    'stage4_validation_v6': _stage4('stage4_validation_v6', 'v6', 'candidate_pool_cascade_v6'),
    'stage4_validation_v7': _stage4('stage4_validation_v7', 'v7', 'candidate_pool_cascade_v7'),
    'stage4_validation_v8': _stage4('stage4_validation_v8', 'v8', 'candidate_pool_cascade_v8'),
}


def get_stage_registry_entry(name: str) -> Dict[str, object]:
    key = str(name).strip()
    if key not in STAGE_REGISTRY:
        raise KeyError(f'Unknown dataset stage: {key}')
    return deepcopy(STAGE_REGISTRY[key])


def get_stage_entries(names: List[str]) -> List[Dict[str, object]]:
    return [get_stage_registry_entry(name) for name in names]
