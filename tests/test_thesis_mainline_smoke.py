from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
STAGE3_TRAINING = ROOT / 'stage3_training'
WORKSPACE_TMP_ROOT = ROOT / 'data' / 'test_outputs' / 'thesis_mainline_smoke'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(STAGE3_TRAINING) not in sys.path:
    sys.path.insert(0, str(STAGE3_TRAINING))
WORKSPACE_TMP_ROOT.mkdir(parents=True, exist_ok=True)

from policy_resolution import load_policy_json
from seed_discovery_pipeline import (  # type: ignore
    build_candidate_pool_for_profile,
    build_validation_manifest_for_profile,
)
from seed_discovery_profiles import get_profile  # type: ignore
from shared.io.stage4_validation_manifest import (
    validate_stage4_validation_manifest_frame,
)


class ThesisMainlineSmokeTests(unittest.TestCase):
    def test_targetband_freeze_config_is_active_and_resolved(self) -> None:
        freeze_path = ROOT / 'src' / 'prediction' / 'targetband_param' / 'configs' / 'targetband_mainline_freeze_v1.json'
        catalog_path = ROOT / 'src' / 'prediction' / 'targetband_param' / 'configs' / 'thesis_band_catalog_v2.json'

        freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))

        self.assertEqual(freeze['status'], 'active')
        self.assertEqual(freeze['decision_name'], 'targetband_mainline_freeze_v1')
        self.assertTrue(
            (ROOT / freeze['frozen_mainline']['default_dataset_path']).exists(),
            'Frozen target-band dataset path should exist.',
        )
        shape_frontend = Path(freeze['frozen_mainline']['shape_frontend'])
        shape_frontend_path = ROOT / shape_frontend
        if not shape_frontend_path.exists():
            self.assertTrue(
                str(shape_frontend).replace('\\', '/').startswith('data/analysis/'),
                'Missing generated shape front-end should remain under ignored data/analysis.',
            )
        self.assertGreaterEqual(len(catalog['bands']), 6)

    def test_candidate_pool_profile_smoke_outputs_exist(self) -> None:
        profile = get_profile('candidate_pool_optimization_v1')
        stage1_positive_csv = Path(profile['stage1_positive_csv'])
        if not stage1_positive_csv.is_absolute():
            stage1_positive_csv = ROOT / stage1_positive_csv
        if not stage1_positive_csv.exists():
            self.skipTest(f'local generated data is not present: {stage1_positive_csv}')
        out_dir = self._reset_test_dir('candidate_pool')
        profile['out_dir'] = out_dir
        result = build_candidate_pool_for_profile(profile)

        self.assertTrue(result['point_manifest_path'].exists())
        self.assertTrue(result['seed_manifest_path'].exists())
        self.assertTrue(result['pool_csv_path'].exists())
        self.assertTrue(result['info_json_path'].exists())
        self.assertGreater(len(result['pool_rows']), 0)

        info = json.loads(result['info_json_path'].read_text(encoding='utf-8'))
        self.assertEqual(info['profile_name'], 'candidate_pool_optimization_v1')
        self.assertIn('candidate_rows', info)
        self.assertIn('family_count', info)
        self.assertIn('strategy', info)

    def test_baseline_validation_manifest_matches_shared_contract(self) -> None:
        profile = get_profile('candidate_pool_v10_seed_only_refined')
        policy = load_policy_json(Path(profile['policy_paths']['manifest']))

        out_dir = self._reset_test_dir('baseline_validation_manifest')
        result = build_validation_manifest_for_profile(
            profile,
            policy,
            out_dir=out_dir,
        )

        manifest_df = pd.read_csv(result['manifest_csv'])
        validate_stage4_validation_manifest_frame(manifest_df)
        self.assertGreater(len(manifest_df), 0)

        summary = json.loads(result['summary_json'].read_text(encoding='utf-8'))
        self.assertIn('manifest_rows', summary)
        self.assertIn('unique_shape_count', summary)
        self.assertIn('selection_source', summary)

    def test_targetband_validation_manifest_wrapper_smoke(self) -> None:
        script = ROOT / 'scripts' / 'run_ga' / 'build_targetband_validation_manifest_v1.py'
        out_dir = self._reset_test_dir('targetband_validation_manifest')
        subprocess.run(
            [
                sys.executable,
                str(script),
                '--out-dir',
                str(out_dir),
                '--total-k',
                '4',
                '--per-shape-k',
                '1',
            ],
            cwd=ROOT,
            check=True,
        )

        manifest_path = out_dir / 'targetband_ga_validation_manifest_v1.csv'
        summary_path = out_dir / 'targetband_ga_validation_manifest_summary.json'
        manifest_df = pd.read_csv(manifest_path)
        validate_stage4_validation_manifest_frame(manifest_df)

        self.assertTrue(summary_path.exists())
        summary = json.loads(summary_path.read_text(encoding='utf-8'))
        self.assertEqual(summary['total_k'], 4)
        self.assertEqual(summary['per_shape_k'], 1)

    def test_thesis_application_bundle_wrapper_smoke(self) -> None:
        script = ROOT / 'scripts' / 'export_results' / 'build_thesis_application_bundle_v1.py'
        out_tag = 'thesis_band_catalog_v2_bundle_v1'
        out_dir = ROOT / 'data' / 'prediction_targetband_param_v1_app' / 'v1' / out_tag
        shutil.rmtree(out_dir, ignore_errors=True)

        subprocess.run(
            [
                sys.executable,
                str(script),
                '--out-tag',
                out_tag,
            ],
            cwd=ROOT,
            check=True,
        )

        summary_json = out_dir / 'curated_application_bundle_v1.json'
        summary_csv = out_dir / 'curated_application_bundle_v1.csv'
        self.assertTrue(summary_json.exists())
        self.assertTrue(summary_csv.exists())

        summary = json.loads(summary_json.read_text(encoding='utf-8'))
        self.assertEqual(summary['training_dataset_tag'], 'windows_dense_v8_truth_plus_exploratory_aug_v1')
        self.assertEqual(summary['classifier_family_run'], 'param_targetband_cls_rf_dense_v8_cmp_v1')
        self.assertEqual(summary['regressor_family_run'], 'param_targetband_cover_hgb_dense_v8_cmp_v1')
        self.assertTrue(summary['allow_missing_bandloo'])
        self.assertGreaterEqual(summary['curated_band_count'], 6)

    def test_invalid_manifest_contract_rejects_missing_columns(self) -> None:
        with self.assertRaises(ValueError):
            validate_stage4_validation_manifest_frame(pd.DataFrame([{'validation_id': 'val001'}]))

    def test_thesis_runbook_sections_reference_existing_paths(self) -> None:
        doc_path = ROOT / 'docs' / 'reproducibility' / 'FINAL_RUNBOOK.md'
        text = doc_path.read_text(encoding='utf-8')
        self.assertIn('compact command', text)

        for heading in ['Output Map']:
            section = self._extract_section(text, heading)
            paths = re.findall(r'`([^`]+)`', section)
            self.assertGreater(len(paths), 0, f'{heading} should list at least one path.')
            for path_text in paths:
                local_path = ROOT / path_text.rstrip('/\\')
                self.assertTrue(local_path.exists(), f'Runbook path does not exist: {path_text}')

    @staticmethod
    def _extract_section(text: str, heading: str) -> str:
        pattern = rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)'
        match = re.search(pattern, text, flags=re.M | re.S)
        if not match:
            raise AssertionError(f'Heading not found: {heading}')
        return match.group(1)

    @staticmethod
    def _reset_test_dir(name: str) -> Path:
        path = WORKSPACE_TMP_ROOT / name
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        return path


if __name__ == '__main__':
    unittest.main()
