"""Reusable outlier-detection and -handling helpers for Stage 7: Outlier Analysis.

This module adapts the homework's single-series outlier code to the project's
*ticketed panel* of daily returns. Financial returns are fat-tailed and each ETF
has its own volatility (e.g. GLD and QQQ are far more volatile than TLT), so
outliers are best defined **within each ticker**, not against a pooled
distribution.

Three building blocks work on a single ``pd.Series``:

* ``detect_outliers_iqr``     — flag values outside ``[Q1 - k*IQR, Q3 + k*IQR]``.
* ``detect_outliers_zscore``  — flag values with ``|z| > threshold``.
* ``winsorize_series``        — clip values to a ``[lower, upper]`` quantile range.

Two group-aware helpers apply those building blocks per ``group_col`` (e.g.
``ticker``) over a DataFrame:

* ``flag_outliers``    — boolean mask, ``True`` where a row is an outlier in its group.
* ``winsorize_outliers`` — winsorized values, computed within each group.

Design notes (the "why", documented so reviewers can audit the assumptions):

* **Population std (`ddof=0`).** A Z-score judges each observation against the
  spread of the data we actually hold, not an unbiased estimate of an unseen
  population — so ``detect_outliers_zscore`` uses the population std, and says so.
* **`NaN` handling.** Statistics are computed on non-null values only, and a
  ``NaN`` is never flagged (missingness is a stage-6 concern, not an outlier).
* **Edge cases are explicit.** Empty / all-`NaN` / constant series return an
  all-``False`` mask rather than "accidentally false", and invalid parameters
  (``k <= 0``, ``threshold <= 0``, ``lower >= upper``) raise a ``ValueError``.

The only hard dependencies are pandas and numpy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_series(values) -> pd.Series:
    """Coerce an array-like into a Series, preserving a passed-in Series."""
    if isinstance(values, pd.Series):
        return values
    return pd.Series(values)


def _empty_mask(series: pd.Series) -> pd.Series:
    """Return an all-``False`` boolean mask with the same index as ``series``."""
    return pd.Series(False, index=series.index, dtype=bool)


def _require_positive(value: float, name: str) -> None:
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive number; got {value!r}")


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Flag IQR-based outliers: values outside ``[Q1 - k*IQR, Q3 + k*IQR]``.

    Args:
        series: Numeric values to test.
        k: IQR multiplier for the fences (``1.5`` mild, ``3`` extreme). Positive.

    Returns:
        Boolean mask, same index as ``series``, ``True`` where a value is an outlier.

    Raises:
        ValueError: If ``k`` is not positive.
    """
    _require_positive(k, "k")
    series = _as_series(series)
    if series.empty:
        return _empty_mask(series)

    valid = series.dropna()
    if valid.empty:
        return _empty_mask(series)

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    # NaN < scalar is False, so NaN entries fall through to "not an outlier".
    return (series < lower) | (series > upper)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Flag Z-score outliers: values with ``|z| > threshold``.

    Uses ``std(ddof=0)`` (population std) — see the module docstring for why.

    Args:
        series: Numeric values to test.
        threshold: Z-score magnitude above which a value is flagged. Positive.

    Returns:
        Boolean mask, same index as ``series``, ``True`` where a value is an outlier.

    Raises:
        ValueError: If ``threshold`` is not positive.
    """
    _require_positive(threshold, "threshold")
    series = _as_series(series)
    if series.empty:
        return _empty_mask(series)

    valid = series.dropna()
    if valid.empty:
        return _empty_mask(series)

    mu = valid.mean()
    sigma = valid.std(ddof=0)  # population std — see module docstring
    if sigma == 0 or not np.isfinite(sigma):
        return _empty_mask(series)

    z = (series - mu) / sigma
    return z.abs() > threshold


def winsorize_series(
    series: pd.Series,
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series:
    """Clip a series to its ``[lower, upper]`` quantiles (winsorize).

    Keeps extreme observations but caps their magnitude — the right choice when
    the extremes are genuine events whose information we do not want to discard.

    Args:
        series: Numeric values to winsorize.
        lower: Lower quantile to clip to.
        upper: Upper quantile to clip to.

    Returns:
        A new Series clipped to ``[quantile(lower), quantile(upper)]``.

    Raises:
        ValueError: If ``lower``/``upper`` are not in ``[0, 1]`` or ``lower >= upper``.
    """
    if not (0 <= lower < upper <= 1):
        raise ValueError(
            f"Require 0 <= lower < upper <= 1; got lower={lower!r}, upper={upper!r}"
        )
    series = _as_series(series)
    if series.empty:
        return series.copy()

    lo = series.quantile(lower)
    hi = series.quantile(upper)
    return series.clip(lower=lo, upper=hi)


# Map a method name to its single-series detector.
_METHODS = {
    "iqr": detect_outliers_iqr,
    "zscore": detect_outliers_zscore,
}


def flag_outliers(
    df: pd.DataFrame,
    value_col: str = "return",
    group_col: str = "ticker",
    method: str = "zscore",
    **kwargs,
) -> pd.Series:
    """Flag outliers in ``value_col`` *within each group* of ``group_col``.

    Group-aware detection is the key project adaptation: each ticker has its own
    volatility, so a pooled cutoff would flag high-volatility tickers wholesale
    while missing tail events in low-volatility ones.

    Args:
        df: Input DataFrame (not mutated).
        value_col: Numeric column to test.
        group_col: Column defining the within-group scope (e.g. ``"ticker"``).
        method: ``"iqr"`` or ``"zscore"``.
        **kwargs: Forwarded to the detector (e.g. ``k`` or ``threshold``).

    Returns:
        Boolean Series aligned to ``df``, ``True`` where a row is an outlier in
        its group.

    Raises:
        ValueError: If ``method`` is not ``"iqr"`` or ``"zscore"``.
    """
    if method not in _METHODS:
        raise ValueError(f"Unknown method {method!r}; use 'iqr' or 'zscore'.")
    detector = _METHODS[method]
    # Return a positional array per group so `transform` cannot mis-align on index.
    return df.groupby(group_col)[value_col].transform(
        lambda s: detector(s, **kwargs).to_numpy()
    )


def winsorize_outliers(
    df: pd.DataFrame,
    value_col: str = "return",
    group_col: str = "ticker",
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series:
    """Winsorize ``value_col`` *within each group* of ``group_col``.

    Args:
        df: Input DataFrame (not mutated).
        value_col: Numeric column to winsorize.
        group_col: Column defining the within-group scope.
        lower: Lower quantile to clip to.
        upper: Upper quantile to clip to.

    Returns:
        Series aligned to ``df`` with per-group winsorized values.
    """
    return df.groupby(group_col)[value_col].transform(
        lambda s: winsorize_series(s, lower=lower, upper=upper).to_numpy()
    )


def summarize_outliers(
    df: pd.DataFrame,
    value_col: str = "return",
    group_col: str = "ticker",
    method: str = "zscore",
    **kwargs,
) -> pd.DataFrame:
    """Report outlier counts and fractions per group and in total.

    Args:
        df: Input DataFrame (not mutated).
        value_col: Numeric column to test.
        group_col: Column defining the within-group scope.
        method: ``"iqr"`` or ``"zscore"``.
        **kwargs: Forwarded to the detector.

    Returns:
        A DataFrame indexed by group (plus a ``total`` row) with ``flagged`` and
        ``fraction`` columns.
    """
    mask = flag_outliers(df, value_col=value_col, group_col=group_col,
                         method=method, **kwargs)
    counts = mask.groupby(df[group_col]).agg(flagged="sum", n="size")
    counts["fraction"] = counts["flagged"] / counts["n"]
    out = counts[["flagged", "fraction"]].copy()
    out["flagged"] = out["flagged"].astype(int)
    total = pd.DataFrame(
        {"flagged": [int(mask.sum())], "fraction": [float(mask.mean())]},
        index=["total"],
    )
    return pd.concat([out, total])
