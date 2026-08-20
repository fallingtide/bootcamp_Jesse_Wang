"""Reusable outlier-detection and -handling helpers for Stage 7.

Three functions:

* ``detect_outliers_iqr``  — flag values outside ``[Q1 - k*IQR, Q3 + k*IQR]``.
* ``detect_outliers_zscore`` — flag values with ``|z| > threshold``.
* ``winsorize_series``    — clip values to a ``[lower, upper]`` quantile range.

Improvements over the starter versions, each documented where it applies:

* **Empty series.** The starter would return a mask of ``False`` *by accident*
  (``NaN`` quantiles / mean make every comparison false) but never say so.
  These versions short-circuit early and return an explicit all-``False`` mask,
  so the behaviour is stated, not an accident.
* **``NaN`` values.** Statistics are computed on the non-null values only, and
  ``NaN`` entries are never flagged as outliers (a missing value is not an
  extreme value — it is a stage-6 cleaning concern, not a stage-7 one).
* **Population vs sample std.** ``detect_outliers_zscore`` uses ``ddof=0``
  (population standard deviation) *and says why*: a Z-score is defined against
  the true population spread, and for the "is this whole observation extreme?"
  question we want the standard deviation of the data we actually have, not an
  unbiased estimate of a larger unknown population.
* **Constant series.** A series with zero spread (``sigma == 0``) is handled
  explicitly instead of dividing by zero.
* **Input validation.** ``k``, ``threshold`` must be positive; ``winsorize_series``
  requires ``0 <= lower < upper <= 1``. The starter silently accepted nonsense
  values (``k=-1`` flips the fences, ``lower=0.9, upper=0.1`` clips backwards).

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


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Return a boolean mask flagging IQR-based outliers.

    A value is flagged when it falls outside
    ``[Q1 - k*IQR, Q3 + k*IQR]``, where ``IQR = Q3 - Q1``.

    Assumptions:
        * The distribution is reasonably summarised by its quartiles (works for
          skewed data because the fences are not centred on the mean).
        * ``k`` trades off sensitivity: ``1.5`` is the common "mild" fence,
          ``3`` is the "extreme" fence.

    Behaviour on edge cases (see module docstring for the reasoning):
        * Empty or all-``NaN`` series -> all-``False`` mask.
        * ``NaN`` values are never flagged.

    Args:
        series: Numeric values to test.
        k: IQR multiplier for the fences. Must be positive.

    Returns:
        Boolean mask, same index as ``series``, ``True`` where a value is an
        outlier.

    Raises:
        ValueError: If ``k`` is not a positive number.
    """
    if not np.isfinite(k) or k <= 0:
        raise ValueError(f"k must be a positive number; got {k!r}")
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
    """Return a boolean mask flagging Z-score outliers (``|z| > threshold``).

    The Z-score is ``(x - mean) / sigma`` with ``sigma = std(ddof=0)`` — the
    *population* standard deviation — because we are judging each observation
    against the spread of the dataset we actually hold, not estimating an
    unseen population.

    Assumptions:
        * The data is roughly normally distributed. The mean/std are themselves
          distorted by heavy tails, so extreme values can "mask" each other.
        * ``threshold`` is the number of standard deviations beyond which an
          observation is deemed extreme (``3`` is the common choice).

    Behaviour on edge cases (see module docstring for the reasoning):
        * Empty or all-``NaN`` series -> all-``False`` mask.
        * Constant series (``sigma == 0``) -> all-``False`` mask.
        * ``NaN`` values are never flagged.

    Args:
        series: Numeric values to test.
        threshold: Z-score magnitude above which a value is flagged. Must be
            positive.

    Returns:
        Boolean mask, same index as ``series``, ``True`` where a value is an
        outlier.

    Raises:
        ValueError: If ``threshold`` is not a positive number.
    """
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError(f"threshold must be a positive number; got {threshold!r}")
    series = _as_series(series)
    if series.empty:
        return _empty_mask(series)

    valid = series.dropna()
    if valid.empty:
        return _empty_mask(series)

    mu = valid.mean()
    sigma = valid.std(ddof=0)  # population std — see docstring
    if sigma == 0 or not np.isfinite(sigma):
        return _empty_mask(series)

    z = (series - mu) / sigma
    return z.abs() > threshold


def winsorize_series(
    series: pd.Series,
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series:
    """Clip values to the ``[lower, upper]`` quantiles (winsorize).

    Instead of deleting outliers, winsorizing caps them at the chosen quantile
    boundaries, so the observation is kept but its extreme magnitude is
    constrained. This is useful when the extreme values are genuine events
    whose information we do not want to throw away entirely.

    ``NaN`` values pass through unchanged (quantiles are computed on the
    non-null values; ``clip`` leaves ``NaN`` as ``NaN``).

    Args:
        series: Numeric values to winsorize.
        lower: Lower quantile to clip to (default ``0.05``).
        upper: Upper quantile to clip to (default ``0.95``).

    Returns:
        A new Series with values clipped to ``[quantile(lower), quantile(upper)]``.

    Raises:
        ValueError: If ``lower``/``upper`` are not in ``[0, 1]`` or if
            ``lower >= upper``.
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
