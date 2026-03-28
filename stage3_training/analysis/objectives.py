from objective_registry import analysis_objective_choices, resolve_metric_column


def analysis_metric_column(name: str) -> str:
    return resolve_metric_column(name, allow_normalized=True)


def analysis_objective_names():
    return analysis_objective_choices()
