"""Storage IO utilities for the ETF strategy project.

Centralises read/write so the pipeline (and any future script) routes on file
suffix instead of branching on format. Carried over from Homework 05 and moved
into ``src/`` so it is importable rather than defined inline in the notebook.
"""

from __future__ import annotations

import datetime as dt
import os
import pathlib
import typing as t

import pandas as pd


def ts() -> str:
    """Return a ``YYYYMMDD-HHMMSS`` timestamp for reproducible filenames."""
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def get_paths(raw_env: str = "DATA_DIR_RAW", proc_env: str = "DATA_DIR_PROCESSED"):
    """Return ``(raw, processed)`` directories from env vars with defaults.

    Falls back to ``data/raw`` and ``data/processed`` when the variables are
    unset, and creates both directories so callers never touch the filesystem
    just to save a file.
    """
    raw = pathlib.Path(os.getenv(raw_env, "data/raw"))
    proc = pathlib.Path(os.getenv(proc_env, "data/processed"))
    raw.mkdir(parents=True, exist_ok=True)
    proc.mkdir(parents=True, exist_ok=True)
    return raw, proc


def detect_format(path: t.Union[str, pathlib.Path]) -> str:
    """Route a path to ``"csv"`` or ``"parquet"`` by its suffix."""
    s = str(path).lower()
    if s.endswith(".csv"):
        return "csv"
    if s.endswith((".parquet", ".pq", ".parq")):
        return "parquet"
    raise ValueError("Unsupported format: " + s)


def write_df(df: pd.DataFrame, path: t.Union[str, pathlib.Path]) -> pathlib.Path:
    """Write ``df`` to ``path``, choosing the format from the suffix.

    Creates any missing parent directories. Raises ``RuntimeError`` with a
    remediation message if Parquet is requested but no engine is installed.
    """
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fmt = detect_format(p)
    if fmt == "csv":
        df.to_csv(p, index=False)
    else:
        try:
            df.to_parquet(p)
        except Exception as e:
            raise RuntimeError(
                "Parquet engine not available. Install pyarrow or fastparquet."
            ) from e
    return p


def read_df(path: t.Union[str, pathlib.Path]) -> pd.DataFrame:
    """Read a CSV or Parquet file, routing on suffix.

    On CSV load a ``date`` column (if present) is re-parsed to datetime, since
    CSV does not preserve dtypes.
    """
    p = pathlib.Path(path)
    fmt = detect_format(p)
    if fmt == "csv":
        out = pd.read_csv(p)
        if "date" in out.columns:
            out["date"] = pd.to_datetime(out["date"])
        return out
    try:
        return pd.read_parquet(p)
    except Exception as e:
        raise RuntimeError(
            "Parquet engine not available. Install pyarrow or fastparquet."
        ) from e


def validate_loaded(
    original: pd.DataFrame,
    reloaded: pd.DataFrame,
    cols: t.Iterable[str] = ("date", "ticker", "close"),
) -> dict:
    """Check that a reloaded frame matches the original on key properties.

    Returns a dict of booleans for shape equality, required-column presence,
    and (where applicable) the datetime/numeric dtypes of ``date`` / ``close``.
    """
    checks = {
        "shape_equal": original.shape == reloaded.shape,
        "cols_present": all(c in reloaded.columns for c in cols),
    }
    if "date" in reloaded.columns:
        checks["date_is_datetime"] = pd.api.types.is_datetime64_any_dtype(reloaded["date"])
    if "close" in reloaded.columns:
        checks["close_is_numeric"] = pd.api.types.is_numeric_dtype(reloaded["close"])
    return checks
