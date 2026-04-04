from __future__ import annotations

PURE_TARGET_FIELDS = [
    'gap34_Hz', 'gap34_rel', 'gap34_width_Hz', 'gap34_width_rel', 'gap34_is_open',
    'max_gap_Hz', 'max_gap_rel', 'max_gap_is_open',
]

PURE_METADATA_FIELDS = [
    'sample_id', 'source_stage', 'source_role', 'candidate_id', 'main_id', 'point_id',
    'shape_id', 'shape_family', 'shape_role',
    'geometry_valid', 'contact_valid', 'solve_success',
    'is_training_ready', 'label_definition', 'error_message',
]

PURE_REGRESSION_TARGET_CHOICES = [
    'gap34_Hz', 'gap34_rel', 'gap34_width_Hz', 'gap34_width_rel', 'max_gap_Hz', 'max_gap_rel',
]

PURE_WIDTH_TARGET_CHOICES = [
    'gap34_width_Hz', 'gap34_width_rel', 'max_gap_Hz', 'max_gap_rel',
]

PURE_OPEN_CLASSIFICATION_TARGETS = [
    'gap34_is_open', 'max_gap_is_open',
]

