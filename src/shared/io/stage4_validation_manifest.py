from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
STAGE4_VALIDATION_MANIFEST_CONTRACT_PATH = (
    ROOT / 'shared' / 'contracts' / 'stage4_validation_manifest_contract_v1.json'
)
_EMPTY_TEXT_TOKENS = {'', 'nan', 'none', 'null', '<na>', 'nat'}
_TRUE_TOKENS = {'true', '1', 'yes'}
_FALSE_TOKENS = {'false', '0', 'no'}


def load_stage4_validation_manifest_contract() -> Dict[str, Any]:
    payload = json.loads(
        STAGE4_VALIDATION_MANIFEST_CONTRACT_PATH.read_text(encoding='utf-8')
    )
    if not isinstance(payload, dict):
        raise ValueError('Stage4 validation manifest contract root must be an object.')
    return payload


def stage4_manifest_ordered_columns() -> List[str]:
    return list(load_stage4_validation_manifest_contract()['ordered_columns'])


def _normalize_text(value: object) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    if pd.isna(value):
        return ''
    return str(value).strip()


def _is_blank_series(series: pd.Series) -> pd.Series:
    return series.map(lambda value: _normalize_text(value).lower() in _EMPTY_TEXT_TOKENS)


def _format_row_positions(mask: Iterable[bool], limit: int = 5) -> str:
    positions: List[str] = []
    for pos, flagged in enumerate(mask, start=1):
        if flagged:
            positions.append(str(pos))
        if len(positions) >= limit:
            break
    return ', '.join(positions) if positions else 'none'


def _default_value_for_column(column: str, contract: Dict[str, Any]) -> object:
    if column in set(contract.get('boolean_columns', [])):
        return False
    if column in set(contract.get('numeric_columns', [])):
        return np.nan
    return ''


def prepare_stage4_validation_manifest_frame(
    df: pd.DataFrame,
    preserve_extra: bool = True,
) -> pd.DataFrame:
    contract = load_stage4_validation_manifest_contract()
    ordered_columns = list(contract['ordered_columns'])
    out = df.copy()
    for column in ordered_columns:
        if column not in out.columns:
            out[column] = _default_value_for_column(column, contract)
    extra_columns = [column for column in out.columns if column not in ordered_columns]
    if preserve_extra:
        return out.loc[:, [*ordered_columns, *extra_columns]].copy()
    return out.loc[:, ordered_columns].copy()


def validate_stage4_validation_manifest_frame(
    df: pd.DataFrame,
    *,
    source: str = 'stage4 validation manifest',
    allow_empty: bool = False,
) -> None:
    contract = load_stage4_validation_manifest_contract()
    required_columns = list(contract.get('required_columns', []))
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(
            f'{source} is missing required columns: {", ".join(missing)}'
        )
    if df.empty and not allow_empty:
        raise ValueError(f'{source} is empty.')

    for column in contract.get('required_non_empty_columns', []):
        blanks = _is_blank_series(df[column])
        if blanks.any():
            raise ValueError(
                f'{source} has blank required text values in "{column}" '
                f'at rows: {_format_row_positions(blanks.tolist())}'
            )

    numeric_columns = set(contract.get('numeric_columns', []))
    required_numeric_columns = set(contract.get('required_numeric_columns', []))
    for column in numeric_columns:
        if column not in df.columns:
            continue
        raw = df[column]
        blanks = _is_blank_series(raw)
        parsed = pd.to_numeric(raw, errors='coerce')
        invalid = (~blanks) & parsed.isna()
        if invalid.any():
            raise ValueError(
                f'{source} has non-numeric values in "{column}" '
                f'at rows: {_format_row_positions(invalid.tolist())}'
            )
        if column in required_numeric_columns:
            missing_numeric = blanks | parsed.isna()
            if missing_numeric.any():
                raise ValueError(
                    f'{source} has blank required numeric values in "{column}" '
                    f'at rows: {_format_row_positions(missing_numeric.tolist())}'
                )

    for column in contract.get('boolean_columns', []):
        if column not in df.columns:
            continue
        normalized = df[column].map(lambda value: _normalize_text(value).lower())
        invalid = (~normalized.isin(_EMPTY_TEXT_TOKENS | _TRUE_TOKENS | _FALSE_TOKENS)) & (
            ~df[column].map(lambda value: isinstance(value, (bool, np.bool_)))
        )
        if invalid.any():
            raise ValueError(
                f'{source} has non-boolean values in "{column}" '
                f'at rows: {_format_row_positions(invalid.tolist())}'
            )


def write_stage4_validation_manifest_csv(
    df: pd.DataFrame,
    path: Path,
    *,
    preserve_extra: bool = True,
) -> pd.DataFrame:
    prepared = prepare_stage4_validation_manifest_frame(df, preserve_extra=preserve_extra)
    validate_stage4_validation_manifest_frame(prepared, source=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(path, index=False, encoding='utf-8-sig')
    return prepared
