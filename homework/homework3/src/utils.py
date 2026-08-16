"""Reusable utility functions for Homework 03.

Keeping the summary logic here (instead of inline in the notebook) makes it
reusable across notebooks and scripts, and keeps the analysis clean.
"""

from __future__ import annotations

import pandas as pd


def get_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics for every numeric column in ``df``.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.

    Returns
    -------
    pd.DataFrame
        A ``describe()``-style summary (count, mean, std, min, quartiles, max).
    """
    return df.describe()


def aggregate_by_category(
    df: pd.DataFrame, group_col: str, value_col: str
) -> pd.DataFrame:
    """Aggregate a numeric column by a categorical column.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    group_col : str
        Column to group by (e.g. ``"category"``).
    value_col : str
        Numeric column to aggregate (e.g. ``"value"``).

    Returns
    -------
    pd.DataFrame
        Count, mean, sum, min and max of ``value_col`` for each ``group_col``.
    """
    return (
        df.groupby(group_col)[value_col]
        .agg(count="count", mean="mean", sum="sum", min="min", max="max")
        .reset_index()
    )
