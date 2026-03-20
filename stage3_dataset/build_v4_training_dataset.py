from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import build_v1_training_dataset as base

ROOT = base.ROOT
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v4'
TASKS_DIR = OUT_DIR / 'tasks'
FIXED_GAP_BAND = base.FIXED_GAP_BAND
SHAPE_FEATURE_FIELDS = base.SHAPE_FEATURE_FIELDS

STAGES = [
    *base.STAGES,
    {
        'name': 'stage4_validation_v1',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v1' / 'tbl1_exports',
    },

    {
        'name': 'stage4_validation_v2',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v2' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v2' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v2' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v2' / 'tbl1_exports',
    },
    {
        'name': 'stage4_validation_v3',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v3' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v3' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v3' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v3' / 'tbl1_exports',
    },
]

SURROGATE_CORE_STAGES = ['stage2', 'stage2_refine', 'stage2_harmonics', 'stage2_harmonics_refine', 'stage4_validation_v1', 'stage4_validation_v2', 'stage4_validation_v3']
PARAM_CLASSIFICATION_STAGES = SURROGATE_CORE_STAGES
SPECIALCASE_SHAPE_FAMILIES = {'ep209'}

MASTER_CSV = OUT_DIR / 'master_dataset_v4.csv'
REGRESSION_CSV = OUT_DIR / 'mlp_gap34_regression_v4.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'dataset_stage_summary_v4.csv'
DATASET_INFO_JSON = OUT_DIR / 'dataset_info_v4.json'

CONTACT_TASK_CSV = TASKS_DIR / 'shape_screening_contact_cls_v4.csv'
POSITIVE_TASK_CSV = TASKS_DIR / 'shape_screening_positive_cls_v4.csv'
PARAM_CONTACT_TASK_CSV = TASKS_DIR / 'parametric_contact_cls_v4.csv'
PARAM_POSITIVE_TASK_CSV = TASKS_DIR / 'parametric_positive_cls_v4.csv'
SURROGATE_CORE_TASK_CSV = TASKS_DIR / 'surrogate_regression_core_v4.csv'
SURROGATE_SPECIALCASE_TASK_CSV = TASKS_DIR / 'surrogate_regression_specialcase_v4.csv'

MASTER_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'candidate_id', 'fourier_id', 'main_id', 'point_id',
    'shape_id', 'shape_family', 'shape_role',
    'validation_id', 'selection_source', 'selection_label', 'rank_within_source', 'source_sample_id',
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'cascade_score',
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate', 'rank_cascade', 'rank_surrogate',
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
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    *SHAPE_FEATURE_FIELDS,
]

PARAM_CONTACT_TASK_FIELDS = [*PARAM_CLASSIFICATION_FIELDS, 'contact_valid']
PARAM_POSITIVE_TASK_FIELDS = [*PARAM_CLASSIFICATION_FIELDS, 'contact_valid', 'solve_success', 'is_positive_shape']

SURROGATE_TASK_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'selection_source', 'selection_label', 'validation_id',
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id',
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', 'shift', 'neigs',
    *SHAPE_FEATURE_FIELDS,
    'contact_length', 'n_domains',
    'gap34_Hz', 'gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq',
    'is_gap34_positive', 'is_gap34_gain_positive',
]


def standardize_row_v4(stage_cfg: Dict[str, object], row: Dict[str, str]) -> Dict[str, object]:
    out = base.standardize_row(stage_cfg, row)
    out.update({
        'validation_id': base.to_text(row.get('validation_id')),
        'selection_source': base.to_text(row.get('selection_source')),
        'selection_label': base.to_text(row.get('selection_label')),
        'rank_within_source': base.to_float(row.get('rank_within_source')),
        'source_sample_id': base.to_text(row.get('source_sample_id')),
        'contact_prob': base.to_float(row.get('contact_prob')),
        'positive_prob': base.to_float(row.get('positive_prob')),
        'surrogate_pred_gap34_gain_Hz': base.to_float(row.get('surrogate_pred_gap34_gain_Hz')),
        'cascade_score': base.to_float(row.get('cascade_score')),
        'contact_gate': base.to_bool(row.get('contact_gate')),
        'positive_gate': base.to_bool(row.get('positive_gate')),
        'reg_positive_gate': base.to_bool(row.get('reg_positive_gate')),
        'cascade_gate': base.to_bool(row.get('cascade_gate')),
        'rank_cascade': base.to_float(row.get('rank_cascade')),
        'rank_surrogate': base.to_float(row.get('rank_surrogate')),
    })
    return out


def build_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for stage_cfg in STAGES:
        for row in base.read_csv_rows(Path(stage_cfg['results_csv'])):
            rows.append(standardize_row_v4(stage_cfg, row))
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
            'shape_screening_contact_cls_v4': {'path': str(CONTACT_TASK_CSV), 'rows': len(task_rows['contact_cls']), 'target': 'contact_valid', 'source_stages': ['stage1'], 'feature_preset': 'shape_only'},
            'shape_screening_positive_cls_v4': {'path': str(POSITIVE_TASK_CSV), 'rows': len(task_rows['positive_cls']), 'target': 'is_positive_shape', 'source_stages': ['stage1'], 'feature_preset': 'shape_only', 'row_filter': 'contact_valid=1 && solve_success=1'},
            'parametric_contact_cls_v4': {'path': str(PARAM_CONTACT_TASK_CSV), 'rows': len(task_rows['param_contact_cls']), 'target': 'contact_valid', 'source_stages': PARAM_CLASSIFICATION_STAGES, 'feature_preset': 'parametric_core'},
            'parametric_positive_cls_v4': {'path': str(PARAM_POSITIVE_TASK_CSV), 'rows': len(task_rows['param_positive_cls']), 'target': 'is_positive_shape', 'source_stages': PARAM_CLASSIFICATION_STAGES, 'feature_preset': 'parametric_core', 'row_filter': 'contact_valid=1 && solve_success=1'},
            'surrogate_regression_core_v4': {'path': str(SURROGATE_CORE_TASK_CSV), 'rows': len(task_rows['surrogate_core']), 'target': 'gap34_gain_Hz', 'source_stages': SURROGATE_CORE_STAGES, 'feature_presets': ['surrogate_core', 'surrogate_geo_augmented'], 'row_filter': 'is_training_ready=1 && not special_case'},
            'surrogate_regression_specialcase_v4': {'path': str(SURROGATE_SPECIALCASE_TASK_CSV), 'rows': len(task_rows['surrogate_specialcase']), 'target': 'gap34_gain_Hz', 'source_stages': SURROGATE_CORE_STAGES, 'feature_presets': ['surrogate_core', 'surrogate_geo_augmented'], 'row_filter': 'shape_family in special_case_set && is_training_ready=1'},
        },
        'shape_feature_fields': SHAPE_FEATURE_FIELDS,
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
    print(f'[DONE] contact cls rows: {len(task_rows["contact_cls"])}')
    print(f'[DONE] positive cls rows: {len(task_rows["positive_cls"])}')
    print(f'[DONE] param contact cls rows: {len(task_rows["param_contact_cls"])}')
    print(f'[DONE] param positive cls rows: {len(task_rows["param_positive_cls"])}')
    print(f'[DONE] surrogate core rows: {len(task_rows["surrogate_core"])}')
    print(f'[DONE] surrogate specialcase rows: {len(task_rows["surrogate_specialcase"])}')
    print(f'[OUT] {MASTER_CSV}')
    print(f'[OUT] {REGRESSION_CSV}')
    print(f'[OUT] {STAGE_SUMMARY_CSV}')
    print(f'[OUT] {CONTACT_TASK_CSV}')
    print(f'[OUT] {POSITIVE_TASK_CSV}')
    print(f'[OUT] {PARAM_CONTACT_TASK_CSV}')
    print(f'[OUT] {PARAM_POSITIVE_TASK_CSV}')
    print(f'[OUT] {SURROGATE_CORE_TASK_CSV}')
    print(f'[OUT] {SURROGATE_SPECIALCASE_TASK_CSV}')


if __name__ == '__main__':
    main()
