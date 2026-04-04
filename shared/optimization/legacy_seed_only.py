from __future__ import annotations

from pathlib import Path

from shared.io.python_runner import ROOT


STAGE3_TRAINING = ROOT / 'stage3_training'

CANDIDATE_POOL_SCRIPT = STAGE3_TRAINING / 'build_candidate_pool_v10.py'
SCORING_SCRIPT = STAGE3_TRAINING / 'run_seed_discovery_scoring_v7.py'
MANIFEST_SCRIPT = STAGE3_TRAINING / 'build_validation_manifest_v10.py'
LOCAL_GA_SCRIPT = STAGE3_TRAINING / 'run_parametric_ga_seed_search_v1.py'

DEFAULT_SCORING_DATASET = ROOT / 'data' / 'ml_dataset' / 'v10' / 'candidate_pool_v10_seed_only_refined' / 'candidate_pool_v10.csv'
DEFAULT_SCORING_POLICY = STAGE3_TRAINING / 'policies' / 'seed_discovery_v10.json'
DEFAULT_SCORING_RUN_NAME = 'candidate_pool_seed_discovery_v10'

DEFAULT_MANIFEST_POLICY = STAGE3_TRAINING / 'policies' / 'manifest_v10.json'
DEFAULT_LOCAL_GA_POLICY = STAGE3_TRAINING / 'policies' / 'ga_v1.json'

