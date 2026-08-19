"""Reusable data-cleaning helpers for Stage 6: Data Preprocessing.

Every function returns a *new* DataFrame and never mutates its input, so the
cleaning steps can be chained together and re-run without surprising side
effects. The only hard dependency is pandas (numpy is used for scaling).

Scaling is implemented with plain numpy rather than scikit-learn so this module
runs anywhere pandas and numpy are installed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def fill_missing_median(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Fill missing values in numeric columns with each column's median.

    The median is preferred over the mean because it is robust to outliers and
    skew, and it preserves the column's central location for most
    distributions. This choice assumes the missing data is MCAR or MAR; if the
    missingness is actually MNAR, an imputed median can hide a real signal.

    Args:
        df: Input DataFrame (not mutated).
        columns: Columns to impute. If ``None``, every numeric column is used.

    Returns:
        A new DataFrame with the selected columns' NaN values replaced by
        their column median.
    """
    out = df.copy()
    if columns is None:
        columns = list(out.select_dtypes(include=np.number).columns)
    for col in columns:
        if col in out.columns:
            out[col] = out[col].fillna(out[col].median())
    return out


def drop_missing(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    threshold: float | None = None,
) -> pd.DataFrame:
    """Drop rows that contain missing values, using one of three strategies.

    Only one strategy is applied per call, resolved in this order:

    * ``columns`` — drop rows missing a value in any of the listed columns.
    * ``threshold`` — drop rows whose fraction of non-null values is *below*
      the threshold (e.g. ``0.5`` keeps rows that are at least half complete).
    * neither — drop any row with at least one missing value (strict).

    Args:
        df: Input DataFrame (not mutated).
        columns: Columns that must be present for a row to survive.
        threshold: Minimum fraction of non-null values required to keep a row.

    Returns:
        A new DataFrame with the qualifying rows dropped.
    """
    out = df.copy()
    if columns is not None:
        return out.dropna(subset=columns)
    if threshold is not None:
        min_non_null = int(threshold * out.shape[1])
        return out.dropna(thresh=min_non_null)
    return out.dropna()


def normalize_data(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    method: str = "minmax",
) -> pd.DataFrame:
    """Rescale numeric columns onto a common scale.

    Args:
        df: Input DataFrame (not mutated).
        columns: Columns to rescale. If ``None``, every numeric column is used.
        method: ``"minmax"`` maps values onto ``[0, 1]``; ``"standard"``
            converts them to z-scores (zero mean, unit variance).

    Returns:
        A new DataFrame with the selected numeric columns rescaled.

    Raises:
        ValueError: If ``method`` is not ``"minmax"`` or ``"standard"``.
    """
    out = df.copy()
    if columns is None:
        columns = list(out.select_dtypes(include=np.number).columns)
    columns = [c for c in columns if c in out.columns]

    if method == "minmax":
        for col in columns:
            lo, hi = out[col].min(), out[col].max()
            span = hi - lo
            # A constant column has no range; map it to 0 rather than divide by zero.
            out[col] = (out[col] - lo) / span if span != 0 else 0.0
    elif method == "standard":
        for col in columns:
            mean = out[col].mean()
            std = out[col].std(ddof=0)  # population std, matching StandardScaler
            out[col] = (out[col] - mean) / std if std != 0 else 0.0
    else:
        raise ValueError(f"Unknown method {method!r}; use 'minmax' or 'standard'.")

    return out
