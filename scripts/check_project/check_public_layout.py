from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_PATHS = [
    "README.md",
    "README_CN.md",
    "ARCHIVE_ORIGINAL_STATE.md",
    "FINAL_REFACTOR_PLAN.md",
    "REFACTOR_AUDIT.md",
    "P3_REFACTOR_REPORT.md",
    "P4_REFACTOR_REPORT.md",
    "P5_PUBLISH_READINESS_REPORT.md",
    "configs/local.example.json",
    "docs/project/PROJECT_STRUCTURE.md",
    "docs/project/COMSOL_SCRIPT_INDEX.md",
    "docs/project/GITHUB_PUBLISH_CHECKLIST.md",
    "docs/project/RUNNER_RISK_INDEX.md",
    "docs/reproducibility/FINAL_RUNBOOK.md",
    "docs/reproducibility/FINAL_RESULTS_INDEX.md",
    "docs/reproducibility/DATASET_MANIFEST.md",
    "docs/reproducibility/GA_FINAL_SUMMARY.md",
    "docs/reproducibility/VALIDATION_SUMMARY.md",
    "docs/thesis/THESIS_MAINLINE.md",
    "docs/thesis/THESIS_METHOD_MAP.md",
    "docs/thesis/THESIS_RESULT_MAP.md",
    "research_validation/README.md",
    "archive/ARCHIVE_NOTES.md",
    "archive/baselines/README.md",
    "archive/legacy_prediction/README.md",
    "archive/legacy_runners/README.md",
    "archive/legacy_stage_pipelines/README.md",
    "scripts/run_comsol/README.md",
    "scripts/run_comsol/run_comsol_stage4_targetband_top6_v1.m",
    "scripts/run_comsol/run_comsol_stage4_targetband_v1.m",
    "scripts/run_comsol/run_real_ga_thesis_band_overlap_v1.m",
    "scripts/run_comsol/run_real_ga_targetband180_220_overlap_v1.m",
    "scripts/run_comsol/run_real_ga_fourier_only_band_v1.m",
    "scripts/run_comsol/run_real_ga_fourier_only_bands_ga20_v1.m",
    "src/shared/contracts/stage4_validation_manifest_contract_v1.json",
    "src/prediction/targetband_param/configs/targetband_mainline_freeze_v1.json",
    "src/prediction/targetband_param/configs/thesis_band_catalog_v2.json",
    "src/optimization/seed_ranking/run_targetband_seed_scoring_v1.py",
    "src/optimization/seed_ranking/run_targetband_local_ga_v1.py",
    "src/optimization/seed_ranking/build_targetband_ga_validation_manifest_v1.py",
    "shared/__init__.py",
    "prediction_targetband_param_v1/__init__.py",
    "optimization/seed_ranking/__init__.py",
    "prediction_v3/__init__.py",
]

PUBLIC_PYTHON_ENTRYPOINTS = [
    "scripts/build_dataset/build_parametric_targetband_dataset_v1.py",
    "scripts/train_prediction/train_parametric_targetband_classifier_v1.py",
    "scripts/train_prediction/train_parametric_targetband_regressor_v1.py",
    "scripts/run_ga/score_targetband_candidates_v1.py",
    "scripts/run_ga/run_targetband_local_ga_v1.py",
    "scripts/run_ga/build_targetband_validation_manifest_v1.py",
    "scripts/export_results/build_curated_application_bundle_v1.py",
    "scripts/export_results/build_thesis_application_bundle_v1.py",
    "scripts/make_figures/ch2/build_ch2_typical_stats_v1.py",
    "scripts/make_figures/ch2/build_ch2_reliability_stats_v1.py",
    "scripts/make_figures/ch3/build_ch3_predictor_v12_report.py",
    "scripts/make_figures/ch4/build_ch4_ga_real_optimization_assets_20gen.py",
    "scripts/make_figures/ch5/build_ch5_prediction_vs_ga_v12.py",
    "scripts/make_figures/ch5/build_ch5_strict_holdout_validation_v1.py",
    "scripts/make_figures/ch5/build_fourier_only_ablation_v1.py",
    "scripts/make_figures/postprocess/plot_bandgap_summary.py",
]

JSON_CONFIGS = [
    "configs/local.example.json",
    "src/prediction/targetband_param/configs/targetband_mainline_freeze_v1.json",
    "src/prediction/targetband_param/configs/thesis_band_catalog_v2.json",
]


def require_paths() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        joined = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing public layout paths:\n{joined}")


def compile_entrypoints() -> None:
    for path in PUBLIC_PYTHON_ENTRYPOINTS:
        py_compile.compile(str(ROOT / path), doraise=True)


def load_json_configs() -> None:
    for path in JSON_CONFIGS:
        json.loads((ROOT / path).read_text(encoding="utf-8"))


def check_compatibility_imports() -> None:
    from prediction_v3.dataset.build_pure_prediction_dataset_v3 import (  # noqa: PLC0415
        PURE_V3_FEATURE_FIELDS,
    )
    from src.prediction.targetband_param.models.inference import (  # noqa: PLC0415
        prepare_targetband_inference_frame,
    )

    if not PURE_V3_FEATURE_FIELDS:
        raise RuntimeError("prediction_v3 compatibility import returned no features")
    if prepare_targetband_inference_frame.__name__ != "prepare_targetband_inference_frame":
        raise RuntimeError("target-band inference import resolved unexpectedly")


def main() -> None:
    require_paths()
    compile_entrypoints()
    load_json_configs()
    check_compatibility_imports()
    print("[OK] public layout paths, Python entrypoints, JSON configs, and compatibility imports are valid")


if __name__ == "__main__":
    main()
