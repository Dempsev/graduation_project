from __future__ import annotations

from typing import Iterable

import pandas as pd


def split_external_stage_holdout(df: pd.DataFrame, test_stage_prefixes: Iterable[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    mask = pd.Series(False, index=df.index)
    source_stage = df['source_stage'].astype(str)
    for prefix in test_stage_prefixes:
        if prefix:
            mask = mask | source_stage.str.startswith(prefix)
    train_pool = df[~mask].copy()
    test_df = df[mask].copy()
    if train_pool.empty or test_df.empty:
        raise RuntimeError('Stage-holdout split failed: train pool or test pool is empty.')
    return train_pool, test_df

