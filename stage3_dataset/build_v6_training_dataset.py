from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import build_v5_training_dataset as prev
import build_v1_training_dataset as base

ROOT = base.ROOT
OUT_DIR = ROOT / 'data' / 'ml_dataset' / 'v6'
TASKS_DIR = OUT_DIR / 'tasks'
FIXED_GAP_BAND = base.FIXED_GAP_BAND
SHAPE_FEATURE_FIELDS = base.SHAPE_FEATURE_FIELDS

STAGES = [
    *prev.STAGES,
    {
        'name': 'stage4_validation_v7',
        'results_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v7' / 'stage4_validation_results.csv',
        'tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v7' / 'tbl1_exports',
        'baseline_mode': 'by_point',
        'baseline_csv': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v7' / 'baseline_by_point.csv',
        'baseline_tbl1_dir': ROOT / 'data' / 'comsol_batch' / 'stage4_validation_ab_v7' / 'tbl1_exports',
        'manifest_csv': ROOT / 'data' / 'ml_runs' / 'candidate_pool_cascade_v7' / 'validation_manifest_v7' / 'comsol_validation_manifest_v7.csv',
    },
]

SURROGATE_CORE_STAGES = [*prev.SURROGATE_CORE_STAGES, 'stage4_validation_v7']
PARAM_CLASSIFICATION_STAGES = SURROGATE_CORE_STAGES
SPECIALCASE_SHAPE_FAMILIES = prev.SPECIALCASE_SHAPE_FAMILIES

MASTER_CSV = OUT_DIR / 'master_dataset_v6.csv'
REGRESSION_CSV = OUT_DIR / 'mlp_gap34_regression_v6.csv'
STAGE_SUMMARY_CSV = OUT_DIR / 'dataset_stage_summary_v6.csv'
DATASET_INFO_JSON = OUT_DIR / 'dataset_info_v6.json'

CONTACT_TASK_CSV = TASKS_DIR / 'shape_screening_contact_cls_v6.csv'
POSITIVE_TASK_CSV = TASKS_DIR / 'shape_screening_positive_cls_v6.csv'
PARAM_CONTACT_TASK_CSV = TASKS_DIR / 'parametric_contact_cls_v6.csv'
PARAM_POSITIVE_TASK_CSV = TASKS_DIR / 'parametric_positive_cls_v6.csv'
SURROGATE_CORE_TASK_CSV = TASKS_DIR / 'surrogate_regression_core_v6.csv'
SURROGATE_SPECIALCASE_TASK_CSV = TASKS_DIR / 'surrogate_regression_specialcase_v6.csv'


def build_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for stage_cfg in STAGES:
        for row in base.read_csv_rows(Path(stage_cfg['results_csv'])):
            rows.append(prev.standardize_row_v5(stage_cfg, row))
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
        'contact_cls': base.project_rows(contact_rows, prev.CONTACT_TASK_FIELDS),
        'positive_cls': base.project_rows(positive_rows, prev.POSITIVE_TASK_FIELDS),
        'param_contact_cls': base.project_rows(param_contact_rows, prev.PARAM_CONTACT_TASK_FIELDS),
        'param_positive_cls': base.project_rows(param_positive_rows, prev.PARAM_POSITIVE_TASK_FIELDS),
        'surrogate_core': base.project_rows(surrogate_core_rows, prev.SURROGATE_TASK_FIELDS),
        'surrogate_specialcase': base.project_rows(surrogate_specialcase_rows, prev.SURROGATE_TASK_FIELDS),
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
            'shape_screening_contact_cls_v6': {'path': str(CONTACT_TASK_CSV), 'rows': len(task_rows['contact_cls']), 'target': 'contact_valid', 'source_stages': ['stage1'], 'feature_preset': 'shape_only'},
            'shape_screening_positive_cls_v6': {'path': str(POSITIVE_TASK_CSV), 'rows': len(task_rows['positive_cls']), 'target': 'is_positive_shape', 'source_stages': ['stage1'], 'feature_preset': 'shape_only', 'row_filter': 'contact_valid=1 && solve_success=1'},
            'parametric_contact_cls_v6': {'path': str(PARAM_CONTACT_TASK_CSV), 'rows': len(task_rows['param_contact_cls']), 'target': 'contact_valid', 'source_stages': PARAM_CLASSIFICATION_STAGES, 'feature_presets': ['parametric_core', 'parametric_directional']},
            'parametric_positive_cls_v6': {'path': str(PARAM_POSITIVE_TASK_CSV), 'rows': len(task_rows['param_positive_cls']), 'target': 'is_positive_shape', 'source_stages': PARAM_CLASSIFICATION_STAGES, 'feature_presets': ['parametric_core', 'parametric_directional'], 'row_filter': 'contact_valid=1 && solve_success=1'},
            'surrogate_regression_core_v6': {'path': str(SURROGATE_CORE_TASK_CSV), 'rows': len(task_rows['surrogate_core']), 'target': 'gap34_gain_Hz', 'source_stages': SURROGATE_CORE_STAGES, 'feature_presets': ['surrogate_core', 'surrogate_geo_augmented', 'surrogate_directional', 'surrogate_directional_geo_augmented'], 'row_filter': 'is_training_ready=1 && not special_case'},
            'surrogate_regression_specialcase_v6': {'path': str(SURROGATE_SPECIALCASE_TASK_CSV), 'rows': len(task_rows['surrogate_specialcase']), 'target': 'gap34_gain_Hz', 'source_stages': SURROGATE_CORE_STAGES, 'feature_presets': ['surrogate_core', 'surrogate_geo_augmented', 'surrogate_directional', 'surrogate_directional_geo_augmented'], 'row_filter': 'shape_family in special_case_set && is_training_ready=1'},
        },
        'shape_feature_fields': SHAPE_FEATURE_FIELDS,
        'context_numeric_fields': prev.CONTEXT_NUMERIC_FIELDS,
        'context_text_fields': prev.CONTEXT_TEXT_FIELDS,
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
    base.write_csv(MASTER_CSV, rows, prev.MASTER_FIELDS)
    base.write_csv(REGRESSION_CSV, regression_rows, prev.REGRESSION_FIELDS)
    base.write_csv(STAGE_SUMMARY_CSV, stage_summary, list(stage_summary[0].keys()) if stage_summary else ['source_stage'])
    base.write_csv(CONTACT_TASK_CSV, task_rows['contact_cls'], prev.CONTACT_TASK_FIELDS)
    base.write_csv(POSITIVE_TASK_CSV, task_rows['positive_cls'], prev.POSITIVE_TASK_FIELDS)
    base.write_csv(PARAM_CONTACT_TASK_CSV, task_rows['param_contact_cls'], prev.PARAM_CONTACT_TASK_FIELDS)
    base.write_csv(PARAM_POSITIVE_TASK_CSV, task_rows['param_positive_cls'], prev.PARAM_POSITIVE_TASK_FIELDS)
    base.write_csv(SURROGATE_CORE_TASK_CSV, task_rows['surrogate_core'], prev.SURROGATE_TASK_FIELDS)
    base.write_csv(SURROGATE_SPECIALCASE_TASK_CSV, task_rows['surrogate_specialcase'], prev.SURROGATE_TASK_FIELDS)

    info = build_dataset_info(rows, regression_rows, stage_summary, task_rows)
    DATASET_INFO_JSON.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')

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
