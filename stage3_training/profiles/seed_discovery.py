from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]


COMMON_POINT_SPECS: List[Dict[str, Any]] = [
    {
        'candidate_point_id': 'cp01',
        'pool_arm': 'exploitation',
        'pool_role': 'seed_only_family_discovery_exploitation',
        'main_id': 'rf09',
        'point_id': 'rf09_h00_center',
        'a1': 0.50,
        'a2': -0.12,
        'b1': 0.0,
        'b2': 0.04,
        'a3': 0.0,
        'b3': 0.0,
        'a4': 0.0,
        'b4': 0.0,
        'a5': 0.0,
        'b5': 0.0,
        'r0': 0.012,
        'shift': 200.0,
        'neigs': 20.0,
    },
    {
        'candidate_point_id': 'cp02',
        'pool_arm': 'exploitation',
        'pool_role': 'seed_only_family_discovery_exploitation',
        'main_id': 'rf09',
        'point_id': 'rf09_h09_b5_002_a4_0015',
        'a1': 0.50,
        'a2': -0.12,
        'b1': 0.0,
        'b2': 0.04,
        'a3': 0.0,
        'b3': 0.0,
        'a4': 0.015,
        'b4': 0.0,
        'a5': 0.0,
        'b5': 0.02,
        'r0': 0.012,
        'shift': 200.0,
        'neigs': 20.0,
    },
]


def _stage4_paths(*versions: int) -> List[Path]:
    return [ROOT / 'data' / 'comsol_batch' / f'stage4_validation_ab_v{version}' / 'stage4_validation_results.csv' for version in versions]


PROFILES: Dict[str, Dict[str, Any]] = {
    'candidate_pool_v10_seed_only_refined': {
        'name': 'candidate_pool_v10_seed_only_refined',
        'source_stage': 'candidate_pool_v10',
        'sample_prefix': 'candidate_pool_v10',
        'shape_dataset': ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv',
        'stage1_positive_csv': ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'stage1_positive_shapes.csv',
        'stage4_result_files': _stage4_paths(1, 2, 3, 5, 6, 7, 8, 9),
        'out_dir': ROOT / 'data' / 'ml_dataset' / 'v10' / 'candidate_pool_v10_seed_only_refined',
        'point_manifest_name': 'candidate_point_manifest.csv',
        'seed_manifest_name': 'candidate_seed_manifest.csv',
        'pool_csv_name': 'candidate_pool_v10.csv',
        'info_json_name': 'candidate_pool_info.json',
        'point_strategy': 'v10_seed_only_refined_cluster',
        'family_prior_source': 'stage1_positive_family_best_seed_excluding_all_stage4_validated_families_through_v9',
        'seed_prior_source': 'stage1_positive_family_best_seed',
        'strategy_summary': 'one best stage1-positive seed per never-stage4-validated family through v9, focused on the rf09 center point with the old rf09 anchor retained as a lightweight control arm',
        'manifest': {
            'scored_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v10' / 'seed_discovery_predictions.csv',
            'out_dir': ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v10' / 'validation_manifest_v10',
            'manifest_csv_name': 'comsol_validation_manifest_v10.csv',
            'ordered_csv_name': 'seed_only_refined_candidates_for_validation_v10.csv',
            'selection_source': 'seed_only_refined',
            'selection_label_prefix': 'seed_only_refined',
        },
        'policy_paths': {
            'scoring': ROOT / 'stage3_training' / 'policies' / 'seed_discovery_v10.json',
            'manifest': ROOT / 'stage3_training' / 'policies' / 'manifest_v10.json',
        },
    },
    'candidate_pool_v11_seed_only_refined': {
        'name': 'candidate_pool_v11_seed_only_refined',
        'source_stage': 'candidate_pool_v11',
        'sample_prefix': 'candidate_pool_v11',
        'shape_dataset': ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv',
        'stage1_positive_csv': ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'stage1_positive_shapes.csv',
        'stage4_result_files': _stage4_paths(1, 2, 3, 5, 6, 7, 8, 9, 10),
        'out_dir': ROOT / 'data' / 'ml_dataset' / 'v11' / 'candidate_pool_v11_seed_only_refined',
        'point_manifest_name': 'candidate_point_manifest.csv',
        'seed_manifest_name': 'candidate_seed_manifest.csv',
        'pool_csv_name': 'candidate_pool_v11.csv',
        'info_json_name': 'candidate_pool_info.json',
        'point_strategy': 'v11_seed_only_refined_cluster',
        'family_prior_source': 'stage1_positive_family_best_seed_excluding_all_stage4_validated_families_through_v10',
        'seed_prior_source': 'stage1_positive_family_best_seed',
        'strategy_summary': 'one best stage1-positive seed per never-stage4-validated family through v10, focused on the rf09 center point with the old rf09 anchor retained as a lightweight control arm',
        'manifest': {
            'scored_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v11' / 'seed_discovery_predictions.csv',
            'out_dir': ROOT / 'data' / 'ml_runs' / 'candidate_pool_seed_discovery_v11' / 'validation_manifest_v11',
            'manifest_csv_name': 'comsol_validation_manifest_v11.csv',
            'ordered_csv_name': 'seed_only_refined_candidates_for_validation_v11.csv',
            'selection_source': 'seed_only_refined_v11',
            'selection_label_prefix': 'seed_only_refined_v11',
        },
        'policy_paths': {
            'scoring': ROOT / 'stage3_training' / 'policies' / 'seed_discovery_v11.json',
            'manifest': ROOT / 'stage3_training' / 'policies' / 'manifest_v11.json',
        },
    },    'candidate_pool_optimization_v1': {
        'name': 'candidate_pool_optimization_v1',
        'source_stage': 'candidate_pool_optimization_v1',
        'sample_prefix': 'candidate_pool_optimization_v1',
        'shape_dataset': ROOT / 'data' / 'ml_dataset' / 'v4' / 'tasks' / 'shape_screening_contact_cls_v4.csv',
        'stage1_positive_csv': ROOT / 'data' / 'comsol_batch' / 'stage1_shape_screening' / 'stage1_positive_shapes.csv',
        'stage4_result_files': _stage4_paths(1, 2, 3, 5, 6, 7, 8, 9, 10, 11),
        'exclude_stage4_validated_families': False,
        'out_dir': ROOT / 'data' / 'ml_dataset' / 'v12' / 'candidate_pool_optimization_v1',
        'point_manifest_name': 'candidate_point_manifest.csv',
        'seed_manifest_name': 'candidate_seed_manifest.csv',
        'pool_csv_name': 'candidate_pool_optimization_v1.csv',
        'info_json_name': 'candidate_pool_info.json',
        'pool_role': 'optimization_seed_pool_exploitation',
        'point_strategy': 'optimization_seed_pool_v1',
        'family_prior_source': 'stage1_positive_family_best_seed_with_stage4_history_retained',
        'seed_prior_source': 'stage1_positive_family_best_seed',
        'strategy_summary': 'one best stage1-positive seed per family with historical stage4-validated families retained for optimization-oriented high-recall basin selection',
        'target_rule': 'optimization_seed_pool',
        'manifest': {
            'scored_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_optimization_v1' / 'optimization_seed_predictions.csv',
            'out_dir': ROOT / 'data' / 'ml_runs' / 'candidate_pool_optimization_v1' / 'validation_manifest_v1',
            'manifest_csv_name': 'comsol_validation_manifest_optimization_v1.csv',
            'ordered_csv_name': 'optimization_candidates_for_validation_v1.csv',
            'selection_source': 'optimization_seed_pool_v1',
            'selection_label_prefix': 'optimization_seed_pool_v1',
        },
        'policy_paths': {
            'scoring': ROOT / 'stage3_training' / 'policies' / 'seed_discovery_v10.json',
            'manifest': ROOT / 'stage3_training' / 'policies' / 'manifest_v10.json',
        },
    },
}


for profile in PROFILES.values():
    point_specs = deepcopy(COMMON_POINT_SPECS)
    for point in point_specs:
        point['point_strategy'] = profile['point_strategy']
        point['family_prior_source'] = profile['family_prior_source']
        point['seed_prior_source'] = profile['seed_prior_source']
        if 'pool_role' in profile:
            point['pool_role'] = profile['pool_role']
    profile['point_specs'] = point_specs


def get_profile(name: str) -> Dict[str, Any]:
    key = str(name).strip()
    if key not in PROFILES:
        raise KeyError(f'Unknown seed discovery profile: {key}')
    return deepcopy(PROFILES[key])


def list_profiles() -> List[str]:
    return sorted(PROFILES.keys())
