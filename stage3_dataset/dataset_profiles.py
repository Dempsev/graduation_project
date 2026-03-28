from __future__ import annotations

from copy import deepcopy
from typing import Dict

from dataset_stage_registry import get_stage_entries


DATASET_PROFILES: Dict[str, Dict[str, object]] = {
    'training_dataset_v5_mainline': {
        'name': 'training_dataset_v5_mainline',
        'stage_names': [
            'stage4_validation_v1',
            'stage4_validation_v2',
            'stage4_validation_v3',
            'stage4_validation_v5',
            'stage4_validation_v6',
        ],
        'surrogate_core_stage_names': [
            'stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine',
            'stage4_validation_v1', 'stage4_validation_v2', 'stage4_validation_v3', 'stage4_validation_v5', 'stage4_validation_v6',
        ],
        'param_classification_stage_names': [
            'stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine',
            'stage4_validation_v1', 'stage4_validation_v2', 'stage4_validation_v3', 'stage4_validation_v5', 'stage4_validation_v6',
        ],
        'specialcase_shape_families': ['ep209'],
        'enable_stage1_reference': False,
    },
    'training_dataset_v7_mainline': {
        'name': 'training_dataset_v7_mainline',
        'stage_names': [
            'stage4_validation_v1',
            'stage4_validation_v2',
            'stage4_validation_v3',
            'stage4_validation_v5',
            'stage4_validation_v6',
            'stage4_validation_v7',
            'stage4_validation_v8',
        ],
        'surrogate_core_stage_names': [
            'stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine',
            'stage4_validation_v1', 'stage4_validation_v2', 'stage4_validation_v3', 'stage4_validation_v5', 'stage4_validation_v6', 'stage4_validation_v7', 'stage4_validation_v8',
        ],
        'param_classification_stage_names': [
            'stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine',
            'stage4_validation_v1', 'stage4_validation_v2', 'stage4_validation_v3', 'stage4_validation_v5', 'stage4_validation_v6', 'stage4_validation_v7', 'stage4_validation_v8',
        ],
        'specialcase_shape_families': ['ep209'],
        'enable_stage1_reference': True,
    },
}


def get_dataset_profile(name: str) -> Dict[str, object]:
    key = str(name).strip()
    if key not in DATASET_PROFILES:
        raise KeyError(f'Unknown dataset profile: {key}')
    profile = deepcopy(DATASET_PROFILES[key])
    profile['stages'] = get_stage_entries(list(profile['stage_names']))
    return profile
