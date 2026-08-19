"""Reusable utility functions for the ETF strategy project.

Keeping shared logic here (instead of inline in notebooks) makes it reusable
across the pipeline notebook and future scripts (EDA, modeling, reporting).

``get_summary_stats`` and ``aggregate_by_category`` are carried over from
Homework 03. ``compute_returns`` is added because the project's core unit of
analysis is a daily return series, which every later stage builds on.
"""

from __future__ import annotations

import numpy as np
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
        Column to group by (e.g. ``"ticker"``).
    value_col : str
        Numeric column to aggregate (e.g. ``"close"``).

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


def compute_returns(
    df: pd.DataFrame,
    price_col: str = "close",
    group_col: str | None = None,
    method: str = "simple",
) -> pd.DataFrame:
    """Compute per-period returns on a price column.

    For a single time series pass ``group_col=None``. For a panel of tickers
    pass the ticker column so returns are computed *within* each ticker (the
    first row of each group becomes NaN, to be dropped by a cleaning step).

    Parameters
    ----------
    df : pd.DataFrame
        Input frame (not mutated), sorted by date within each group.
    price_col : str
        Name of the price column.
    group_col : str | None
        Optional column to group by (e.g. ``"ticker"``).
    method : str
        ``"simple"`` for percent change, ``"log"`` for log returns.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with an added ``return`` column.

    Raises
    ------
    ValueError
        If ``method`` is not ``"simple"`` or ``"log"``.
    """
    out = df.copy()
    if group_col is not None:
        shifted = out.groupby(group_col)[price_col].shift(1)
    else:
        shifted = out[price_col].shift(1)

    if method == "simple":
        out["return"] = out[price_col] / shifted - 1
    elif method == "log":
        out["return"] = np.log(out[price_col] / shifted)
    else:
        raise ValueError(f"Unknown method {method!r}; use 'simple' or 'log'.")

    return out
