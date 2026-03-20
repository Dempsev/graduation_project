from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, List

import build_v4_training_dataset as prev
import build_v1_training_dataset as base

ROOT = base.ROOT
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v5'
TASKS_DIR = OUT_DIR / 'tasks'
FIXED_GAP_BAND = base.FIXED_GAP_BAND
SHAPE_FEATURE_FIELDS = base.SHAPE_FEATURE_FIELDS

STAGES = [
    *prev.STAGES,
    {
        'name': 'stage4_validation_v5',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v5' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v5' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v5' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v5' / 'tbl1_exports',
    },
    {
        'name': 'stage4_validation_v6',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v6' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v6' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v6' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v6' / 'tbl1_exports',
        'manifest_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_cascade_v6' / 'validation_manifest_v6' / 'comsol_validation_manifest_v6.csv',
    },
]

SURROGATE_CORE_STAGES = [
    'stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine',
    'stage4_validation_v1', 'stage4_validation_v2', 'stage4_validation_v3', 'stage4_validation_v5', 'stage4_validation_v6',
]
PARAM_CLASSIFICATION_STAGES = SURROGATE_CORE_STAGES
SPECIALCASE_SHAPE_FAMILIES = {'ep209'}

MASTER_CSV = OUT_DIR / 'master_dataset_v5.csv'
REGRESSION_CSV = OUT_DIR / 'mlp_gap34_regression_v5.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'dataset_stage_summary_v5.csv'
DATASET_INFO_JSON = OUT_DIR / 'dataset_info_v5.json'

CONTACT_TASK_CSV = TASKS_DIR / 'shape_screening_contact_cls_v5.csv'
POSITIVE_TASK_CSV = TASKS_DIR / 'shape_screening_positive_cls_v5.csv'
PARAM_CONTACT_TASK_CSV = TASKS_DIR / 'parametric_contact_cls_v5.csv'
PARAM_POSITIVE_TASK_CSV = TASKS_DIR / 'parametric_positive_cls_v5.csv'
SURROGATE_CORE_TASK_CSV = TASKS_DIR / 'surrogate_regression_core_v5.csv'
SURROGATE_SPECIALCASE_TASK_CSV = TASKS_DIR / 'surrogate_regression_specialcase_v5.csv'

CONTEXT_TEXT_FIELDS = [
    'pool_arm', 'point_strategy', 'family_prior_source', 'seed_prior_source',
    'seed_shape_id', 'seed_family', 'seed_tier', 'seed_source',
    'step_window', 'target_rule', 'preferred_direction', 'allowed_offsets', 'v5_reference_validation_id',
]

CONTEXT_NUMERIC_FIELDS = [
    'seed_step', 'shape_step', 'step_num', 'step_offset', 'step_distance',
    'step_direction_sign', 'is_seed_shape', 'has_seed_context',
    'preferred_direction_sign', 'matches_preferred_direction', 'within_directional_window',
    'directional_offset', 'selection_priority', 'v5_reference_gain_Hz',
    'validation_round_index', 'is_confirmation_repeat',
]

MASTER_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'candidate_id', 'fourier_id', 'main_id', 'point_id',
    'shape_id', 'shape_family', 'shape_role',
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source', 'source_sample_id',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate', 'rank_cascade', 'rank_surrogate',
    *CONTEXT_TEXT_FIELDS,
    *CONTEXT_NUMERIC_FIELDS,
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    'geometry_valid', 'contact_valid', 'solve_success', 'contact_length', 'n_domains', 'has_tiny_fragments',
    *SHAPE_FEATURE_FIELDS,
    'stage_reported_gap_Hz', 'stage_reported_gap_rel', 'stage_reported_gap_lower_band', 'stage_reported_gap_upper_band',
    'gap34_Hz', 'gap34_rel', 'gap34_lower_edge_Hz', 'gap34_upper_edge_Hz', 'gap34_center_freq',
    'ref_gap34_Hz', 'ref_gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive', 'is_positive_shape', 'is_training_ready', 'label_definition', 'error_message',
]

REGRESSION_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'selection_source', 'selection_label', 'validation_id',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    *CONTEXT_TEXT_FIELDS,
    *CONTEXT_NUMERIC_FIELDS,
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    *SHAPE_FEATURE_FIELDS,
    'contact_length', 'n_domains',
    'gap34_Hz', 'gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive',
]

CONTACT_TASK_FIELDS = [
    'sample_id', 'source_stage', 'shape_id', 'shape_family', 'shape_role',
    *SHAPE_FEATURE_FIELDS,
    'contact_valid',
]

POSITIVE_TASK_FIELDS = [
    'sample_id', 'source_stage', 'shape_id', 'shape_family', 'shape_role',
    *SHAPE_FEATURE_FIELDS,
    'contact_valid', 'solve_success', 'is_positive_shape',
]

PARAM_CLASSIFICATION_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'selection_source', 'selection_label', 'validation_id',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    *CONTEXT_TEXT_FIELDS,
    *CONTEXT_NUMERIC_FIELDS,
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    *SHAPE_FEATURE_FIELDS,
]

PARAM_CONTACT_TASK_FIELDS = [*PARAM_CLASSIFICATION_FIELDS, 'contact_valid']
PARAM_POSITIVE_TASK_FIELDS = [*PARAM_CLASSIFICATION_FIELDS, 'contact_valid', 'solve_success', 'is_positive_shape']

SURROGATE_TASK_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'selection_source', 'selection_label', 'validation_id',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    *CONTEXT_TEXT_FIELDS,
    *CONTEXT_NUMERIC_FIELDS,
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    *SHAPE_FEATURE_FIELDS,
    'contact_length', 'n_domains',
    'gap34_Hz', 'gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive',
]

_manifest_cache: Dict[str, Dict[str, Dict[str, str]]] = {}
_seed_direction_lookup: Dict[str, str] = {}


def parse_shape_step(shape_id: str) -> float:
    text = base.to_text(shape_id)
    match = re.search(r'_step(\d+)', text)
    if not match:
        return math.nan
    try:
        return float(match.group(1))
    except Exception:
        return math.nan


def stage_round_index(stage_name: str) -> float:
    if stage_name == 'stage4_validation_v1':
        return 1.0
    if stage_name == 'stage4_validation_v2':
        return 2.0
    if stage_name == 'stage4_validation_v3':
        return 3.0
    if stage_name == 'stage4_validation_v5':
        return 5.0
    if stage_name == 'stage4_validation_v6':
        return 6.0
    return 0.0


def sign_from_value(value: float) -> float:
    if not math.isfinite(value) or value == 0:
        return 0.0
    return 1.0 if value > 0 else -1.0


def derive_step_window(step_distance: float) -> str:
    if not math.isfinite(step_distance):
        return ''
    if abs(step_distance) < 1e-9:
        return 'seed'
    if abs(step_distance - 3.0) < 1e-9:
        return 'pm3'
    if abs(step_distance - 6.0) < 1e-9:
        return 'pm6'
    return ''


def get_manifest_lookup(stage_cfg: Dict[str, object]) -> Dict[str, Dict[str, str]]:
    key = str(stage_cfg.get('manifest_csv', ''))
    if key in _manifest_cache:
        return _manifest_cache[key]
    out: Dict[str, Dict[str, str]] = {}
    manifest_csv = stage_cfg.get('manifest_csv')
    if not manifest_csv:
        _manifest_cache[key] = out
        return out
    for row in base.read_csv_rows(Path(manifest_csv)):
        validation_id = base.to_text(row.get('validation_id'))
        if validation_id:
            out[validation_id] = row
    _manifest_cache[key] = out
    return out


def supplement_row(stage_cfg: Dict[str, object], row: Dict[str, str]) -> Dict[str, str]:
    lookup = get_manifest_lookup(stage_cfg)
    validation_id = base.to_text(row.get('validation_id'))
    if validation_id and validation_id in lookup:
        return lookup[validation_id]
    return {}


def get_seed_direction_lookup() -> Dict[str, str]:
    if _seed_direction_lookup:
        return _seed_direction_lookup
    for stage_cfg in STAGES:
        if str(stage_cfg.get('name')) != 'stage4_validation_v6':
            continue
        for row in get_manifest_lookup(stage_cfg).values():
            seed_shape_id = base.to_text(row.get('seed_shape_id'))
            preferred_direction = base.to_text(row.get('preferred_direction'))
            if seed_shape_id and preferred_direction and seed_shape_id not in _seed_direction_lookup:
                _seed_direction_lookup[seed_shape_id] = preferred_direction
    return _seed_direction_lookup


def pick_text(row: Dict[str, str], supplement: Dict[str, str], key: str) -> str:
    value = base.to_text(row.get(key))
    if value != '':
        return value
    return base.to_text(supplement.get(key))


def pick_float(row: Dict[str, str], supplement: Dict[str, str], key: str, default=math.nan) -> float:
    value = base.to_float(row.get(key), math.nan)
    if math.isfinite(value):
        return value
    value = base.to_float(supplement.get(key), math.nan)
    if math.isfinite(value):
        return value
    return default


def pick_bool(row: Dict[str, str], supplement: Dict[str, str], key: str) -> int:
    text = base.to_text(row.get(key))
    if text != '':
        return base.to_bool(text)
    text = base.to_text(supplement.get(key))
    if text != '':
        return base.to_bool(text)
    return 0


def standardize_row_v5(stage_cfg: Dict[str, object], row: Dict[str, str]) -> Dict[str, object]:
    out = prev.standardize_row_v4(stage_cfg, row)
    supplement = supplement_row(stage_cfg, row)

    shape_step = parse_shape_step(out['shape_id'])
    seed_shape_id = pick_text(row, supplement, 'seed_shape_id')
    seed_direction_lookup = get_seed_direction_lookup()
    seed_step = pick_float(row, supplement, 'seed_step')
    step_num = pick_float(row, supplement, 'step_num', shape_step if math.isfinite(shape_step) else math.nan)
    step_offset = pick_float(row, supplement, 'step_offset')
    if not math.isfinite(step_offset) and math.isfinite(step_num) and math.isfinite(seed_step):
        step_offset = step_num - seed_step
    step_distance = pick_float(row, supplement, 'step_distance', abs(step_offset) if math.isfinite(step_offset) else math.nan)
    directional_offset = pick_float(row, supplement, 'directional_offset')
    step_window = pick_text(row, supplement, 'step_window') or derive_step_window(step_distance)
    preferred_direction = pick_text(row, supplement, 'preferred_direction')
    if preferred_direction == '' and seed_shape_id != '':
        preferred_direction = seed_direction_lookup.get(seed_shape_id, '')
    preferred_direction_sign = sign_from_value(directional_offset)
    if preferred_direction_sign == 0.0:
        preferred_direction_sign = 1.0 if preferred_direction == 'plus' else (-1.0 if preferred_direction == 'minus' else 0.0)
    step_direction_sign = sign_from_value(step_offset)
    is_seed_shape = pick_bool(row, supplement, 'is_seed_shape')
    if not is_seed_shape and math.isfinite(step_distance) and step_distance == 0:
        is_seed_shape = 1
    has_seed_context = 1 if seed_shape_id != '' else 0
    matches_preferred_direction = 1 if has_seed_context and step_direction_sign != 0.0 and step_direction_sign == preferred_direction_sign else 0
    within_directional_window = 1 if has_seed_context and math.isfinite(step_distance) and step_distance <= 3.0 else 0
    selection_priority = pick_float(row, supplement, 'selection_priority')
    if not math.isfinite(selection_priority):
        if is_seed_shape:
            selection_priority = 0.0
        elif math.isfinite(step_distance) and step_distance == 3.0:
            selection_priority = 1.0
        elif math.isfinite(step_distance) and step_distance == 6.0:
            selection_priority = 2.0
        else:
            selection_priority = math.nan

    out.update({
        'pool_arm': pick_text(row, supplement, 'pool_arm'),
        'point_strategy': pick_text(row, supplement, 'point_strategy'),
        'family_prior_source': pick_text(row, supplement, 'family_prior_source'),
        'seed_prior_source': pick_text(row, supplement, 'seed_prior_source'),
        'seed_shape_id': seed_shape_id,
        'seed_family': pick_text(row, supplement, 'seed_family'),
        'seed_tier': pick_text(row, supplement, 'seed_tier'),
        'seed_source': pick_text(row, supplement, 'seed_source'),
        'step_window': step_window,
        'target_rule': pick_text(row, supplement, 'target_rule'),
        'preferred_direction': preferred_direction,
        'allowed_offsets': pick_text(row, supplement, 'allowed_offsets'),
        'v5_reference_validation_id': pick_text(row, supplement, 'v5_reference_validation_id'),
        'seed_step': seed_step,
        'shape_step': shape_step,
        'step_num': step_num,
        'step_offset': step_offset,
        'step_distance': step_distance,
        'step_direction_sign': step_direction_sign,
        'is_seed_shape': is_seed_shape,
        'has_seed_context': has_seed_context,
        'preferred_direction_sign': preferred_direction_sign,
        'matches_preferred_direction': matches_preferred_direction,
        'within_directional_window': within_directional_window,
        'directional_offset': directional_offset,
        'selection_priority': selection_priority,
        'v5_reference_gain_Hz': pick_float(row, supplement, 'v5_reference_gain_Hz'),
        'validation_round_index': stage_round_index(str(stage_cfg['name'])),
        'is_confirmation_repeat': 1 if str(stage_cfg['name']) == 'stage4_validation_v6' else 0,
    })
    return out


def build_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for stage_cfg in STAGES:
        for row in base.read_csv_rows(Path(stage_cfg['results_csv'])):
            rows.append(standardize_row_v5(stage_cfg, row))
    rows.sort(key=lambda item: (item['source_stage'], item['sample_id']))
    return rows


def build_task_datasets(rows: List[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    contact_rows = [row for row in rows if row['source_stage'] == 'stage1']
    positive_rows = [row for row in rows if row['source_stage'] == 'stage1' and int(row['contact_valid']) == 1 and int(row['solve_success']) == 1]
    param_contact_rows = [row for row in rows if row['source_stage'] in PARAM_CLASSIFICATION_STAGES]
    param_positive_rows = [row for row in rows if row['source_stage'] in PARAM_CLASSIFICATION_STAGES and int(row['contact_valid']) == 1 and int(row['solve_success']) == 1]
    surrogate_core_rows = [
        row for row in rows
        if row['source_stage'] in SURROGATE_CORE_STAGES
        and int(row['is_training_ready']) == 1
        and row['shape_family'] not in SPECIALCASE_SHAPE_FAMILIES
        and row['shape_role'] != 'special_case'
    ]
    surrogate_specialcase_rows = [
        row for row in rows
        if row['source_stage'] in SURROGATE_CORE_STAGES
        and int(row['is_training_ready']) == 1
        and row['shape_family'] in SPECIALCASE_SHAPE_FAMILIES
    ]
    return {
        'contact_cls': base.project_rows(contact_rows, CONTACT_TASK_FIELDS),
        'positive_cls': base.project_rows(positive_rows, POSITIVE_TASK_FIELDS),
        'param_contact_cls': base.project_rows(param_contact_rows, PARAM_CONTACT_TASK_FIELDS),
        'param_positive_cls': base.project_rows(param_positive_rows, PARAM_POSITIVE_TASK_FIELDS),
        'surrogate_core': base.project_rows(surrogate_core_rows, SURROGATE_TASK_FIELDS),
        'surrogate_specialcase': base.project_rows(surrogate_specialcase_rows, SURROGATE_TASK_FIELDS),
    }


def build_dataset_info(rows: List[Dict[str, object]], regression_rows: List[Dict[str, object]], stage_summary: List[Dict[str, object]], task_rows: Dict[str, List[Dict[str, object]]]) -> Dict[str, object]:
    return {
        'label_definition': 'fixed_gap_band_3_4',
        'fixed_gap_band': FIXED_GAP_BAND,
        'master_rows': len(rows),
        'regression_rows': len(regression_rows),
        'source_stages': [cfg['name'] for cfg in STAGES],
        'master_csv': str(MASTER_CSV),
        'regression_csv': str(REGRESSION_CSV),
        'stage_summary_csv': str(STAGE_SUMMARY_CSV),
        'tasks': {
            'shape_screening_contact_cls_v5': {'path': str(CONTACT_TASK_CSV), 'rows': len(task_rows['contact_cls']), 'target': 'contact_valid', 'source_stages': ['stage1'], 'feature_preset': 'shape_only'},
            'shape_screening_positive_cls_v5': {'path': str(POSITIVE_TASK_CSV), 'rows': len(task_rows['positive_cls']), 'target': 'is_positive_shape', 'source_stages': ['stage1'], 'feature_preset': 'shape_only', 'row_filter': 'contact_valid=1 && solve_success=1'},
            'parametric_contact_cls_v5': {'path': str(PARAM_CONTACT_TASK_CSV), 'rows': len(task_rows['param_contact_cls']), 'target': 'contact_valid', 'source_stages': PARAM_CLASSIFICATION_STAGES, 'feature_presets': ['parametric_core', 'parametric_directional']},
            'parametric_positive_cls_v5': {'path': str(PARAM_POSITIVE_TASK_CSV), 'rows': len(task_rows['param_positive_cls']), 'target': 'is_positive_shape', 'source_stages': PARAM_CLASSIFICATION_STAGES, 'feature_presets': ['parametric_core', 'parametric_directional'], 'row_filter': 'contact_valid=1 && solve_success=1'},
            'surrogate_regression_core_v5': {'path': str(SURROGATE_CORE_TASK_CSV), 'rows': len(task_rows['surrogate_core']), 'target': 'gap34_gain_Hz', 'source_stages': SURROGATE_CORE_STAGES, 'feature_presets': ['surrogate_core', 'surrogate_geo_augmented', 'surrogate_directional', 'surrogate_directional_geo_augmented'], 'row_filter': 'is_training_ready=1 && not special_case'},
            'surrogate_regression_specialcase_v5': {'path': str(SURROGATE_SPECIALCASE_TASK_CSV), 'rows': len(task_rows['surrogate_specialcase']), 'target': 'gap34_gain_Hz', 'source_stages': SURROGATE_CORE_STAGES, 'feature_presets': ['surrogate_core', 'surrogate_geo_augmented', 'surrogate_directional', 'surrogate_directional_geo_augmented'], 'row_filter': 'shape_family in special_case_set && is_training_ready=1'},
        },
        'shape_feature_fields': SHAPE_FEATURE_FIELDS,
        'context_numeric_fields': CONTEXT_NUMERIC_FIELDS,
        'context_text_fields': CONTEXT_TEXT_FIELDS,
        'specialcase_shape_families': sorted(SPECIALCASE_SHAPE_FAMILIES),
        'stage_summary': stage_summary,
    }


def main() -> None:
    base.ensure_dir(OUT_DIR)
    base.ensure_dir(TASKS_DIR)
    rows = build_rows()
    regression_rows = [row for row in rows if int(row['is_training_ready']) == 1]
    stage_summary = base.build_stage_summary(rows)
    task_rows = build_task_datasets(rows)
    base.write_csv(MASTER_CSV, rows, MASTER_FIELDS)
    base.write_csv(REGRESSION_CSV, regression_rows, REGRESSION_FIELDS)
    base.write_csv(STAGE_SUMMARY_CSV, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
    base.write_csv(CONTACT_TASK_CSV, task_rows['contact_cls'], CONTACT_TASK_FIELDS)
    base.write_csv(POSITIVE_TASK_CSV, task_rows['positive_cls'], POSITIVE_TASK_FIELDS)
    base.write_csv(PARAM_CONTACT_TASK_CSV, task_rows['param_contact_cls'], PARAM_CONTACT_TASK_FIELDS)
    base.write_csv(PARAM_POSITIVE_TASK_CSV, task_rows['param_positive_cls'], PARAM_POSITIVE_TASK_FIELDS)
    base.write_csv(SURROGATE_CORE_TASK_CSV, task_rows['surrogate_core'], SURROGATE_TASK_FIELDS)
    base.write_csv(SURROGATE_SPECIALCASE_TASK_CSV, task_rows['surrogate_specialcase'], SURROGATE_TASK_FIELDS)
    DATASET_INFO_JSON.write_text(json.dumps(build_dataset_info(rows, regression_rows, stage_summary, task_rows), indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[DONE] master rows: {len(rows)}')
    print(f'[DONE] regression rows: {len(regression_rows)}')
    print(f'[DONE] param contact cls rows: {len(task_rows["param_contact_cls"])}')
    print(f'[DONE] param positive cls rows: {len(task_rows["param_positive_cls"])}')
    print(f'[DONE] surrogate core rows: {len(task_rows["surrogate_core"])}')
    print(f'[DONE] surrogate specialcase rows: {len(task_rows["surrogate_specialcase"])}')
    print(f'[OUT] {MASTER_CSV}')
    print(f'[OUT] {REGRESSION_CSV}')
    print(f'[OUT] {STAGE_SUMMARY_CSV}')
    print(f'[OUT] {PARAM_CONTACT_TASK_CSV}')
    print(f'[OUT] {PARAM_POSITIVE_TASK_CSV}')
    print(f'[OUT] {SURROGATE_CORE_TASK_CSV}')
    print(f'[OUT] {SURROGATE_SPECIALCASE_TASK_CSV}')


if __name__ == '__main__':
    main()
