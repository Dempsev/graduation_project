from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping


def load_policy_json(path: Path | None, section: str | None = None) -> Dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding='utf-8-sig'))
    if section:
        scoped = payload.get(section, {})
        if not isinstance(scoped, Mapping):
            raise ValueError(f'Policy section "{section}" must be an object.')
        return dict(scoped)
    if not isinstance(payload, Mapping):
        raise ValueError('Policy json root must be an object.')
    return dict(payload)


def merge_policy_layers(*layers: Mapping[str, Any] | None) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for layer in layers:
        if not layer:
            continue
        for key, value in layer.items():
            if value is None:
                continue
            merged[key] = value
    return merged


def resolve_policy_settings(
    defaults: Mapping[str, Any],
    policy: Mapping[str, Any] | None,
    cli_values: Mapping[str, Any] | None = None,
    cli_defaults: Mapping[str, Any] | None = None,
    policy_enabled: bool = False,
) -> Dict[str, Any]:
    resolved = dict(defaults)
    if policy_enabled and policy:
        resolved.update({key: value for key, value in policy.items() if value is not None})
    if not cli_values:
        return resolved

    for key, value in cli_values.items():
        if value is None:
            continue
        if not policy_enabled or cli_defaults is None or key not in cli_defaults:
            resolved[key] = value
            continue
        if value != cli_defaults[key]:
            resolved[key] = value
    return resolved
