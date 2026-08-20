"""Stage 7 outlier-detection and -handling package."""

from .outliers import detect_outliers_iqr, detect_outliers_zscore, winsorize_series

__all__ = ["detect_outliers_iqr", "detect_outliers_zscore", "winsorize_series"]
