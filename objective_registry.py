from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ObjectiveSpec:
    name: str
    metric_column: str
    prediction_column: str
    description: str
    higher_is_better: bool = True
    positive_threshold: float = 0.0
    is_compat_only: bool = False


_OBJECTIVES: Dict[str, ObjectiveSpec] = {
    'gap34_gain_Hz': ObjectiveSpec(
        name='gap34_gain_Hz',
        metric_column='gap34_gain_Hz',
        prediction_column='surrogate_pred_gap34_gain_Hz',
        description='Fixed 3-4 band-gap gain over the reference point in Hz.',
    ),
    'gap34_Hz': ObjectiveSpec(
        name='gap34_Hz',
        metric_column='gap34_Hz',
        prediction_column='surrogate_pred_gap34_Hz',
        description='Fixed 3-4 band-gap width in Hz.',
    ),
    'gap34_rel': ObjectiveSpec(
        name='gap34_rel',
        metric_column='gap34_rel',
        prediction_column='surrogate_pred_gap34_rel',
        description='Fixed 3-4 relative band gap.',
    ),
    'max_gap_Hz': ObjectiveSpec(
        name='max_gap_Hz',
        metric_column='max_gap_Hz',
        prediction_column='surrogate_pred_max_gap_Hz',
        description='Maximum gap width in Hz across all adjacent bands.',
    ),
    'gap34_gain_rel': ObjectiveSpec(
        name='gap34_gain_rel',
        metric_column='gap34_gain_rel',
        prediction_column='surrogate_pred_gap34_gain_rel',
        description='Fixed 3-4 relative gap gain over the reference point.',
        is_compat_only=True,
    ),
}

_NORMALIZED_ANALYSIS_METRICS: Dict[str, str] = {
    'gap34_gain_Hz_over_ref': 'gap34_gain_Hz_over_ref_gap34_Hz',
    'gap34_Hz_over_ref': 'gap34_Hz_over_ref_gap34_Hz',
    'max_gap_Hz_over_ref': 'max_gap_Hz_over_ref_gap34_Hz',
}

DEFAULT_OBJECTIVE_NAME = 'gap34_gain_Hz'
DEFAULT_OBJECTIVE = _OBJECTIVES[DEFAULT_OBJECTIVE_NAME]
GENERIC_PREDICTION_COLUMN = 'surrogate_pred_objective_value'
GENERIC_OBJECTIVE_NAME_COLUMN = 'surrogate_objective_name'
GENERIC_OBJECTIVE_PREDICTION_COLUMN = 'surrogate_prediction_column'


def list_objective_names(include_compat: bool = True) -> List[str]:
    names = []
    for name, spec in _OBJECTIVES.items():
        if spec.is_compat_only and not include_compat:
            continue
        names.append(name)
    return names


def get_objective(name: str | None) -> ObjectiveSpec:
    key = (name or DEFAULT_OBJECTIVE_NAME).strip()
    if key not in _OBJECTIVES:
        raise KeyError(f'Unknown objective: {key}')
    return _OBJECTIVES[key]


def objective_choices(include_compat: bool = True) -> List[str]:
    return list_objective_names(include_compat=include_compat)


def get_prediction_column(name: str | None) -> str:
    return get_objective(name).prediction_column


def get_metric_column(name: str | None) -> str:
    return get_objective(name).metric_column


def is_default_objective(name: str | None) -> bool:
    return get_objective(name).name == DEFAULT_OBJECTIVE_NAME


def get_selection_target(name: str | None) -> str:
    objective = get_objective(name)
    return f'contact_valid_and_positive_{objective.metric_column}'


def resolve_metric_column(name: str | None, allow_normalized: bool = False) -> str:
    key = (name or DEFAULT_OBJECTIVE_NAME).strip()
    if key in _OBJECTIVES:
        return _OBJECTIVES[key].metric_column
    if allow_normalized and key in _NORMALIZED_ANALYSIS_METRICS:
        return _NORMALIZED_ANALYSIS_METRICS[key]
    raise KeyError(f'Unknown objective metric: {key}')


def analysis_objective_choices(include_compat: bool = True) -> List[str]:
    return [*list_objective_names(include_compat=include_compat), *_NORMALIZED_ANALYSIS_METRICS.keys()]
