# Stage 07 — Outliers + Risk Assumptions

Reusable outlier-detection and -handling functions applied to a synthetic return
series, with a sensitivity analysis (all vs. IQR-filtered vs. winsorized) and a
reflection on the assumptions and risks behind each choice.

## Folder structure

```
homework7/
├── src/
│   ├── __init__.py        # makes `src` importable, re-exports the functions
│   └── outliers.py        # detect_outliers_iqr / detect_outliers_zscore / winsorize_series
├── data/
│   ├── raw/               # generated sample (outliers_homework.csv)
│   └── processed/         # flagged + winsorized output
├── homework07_outliers-risk-assumptions_submission.ipynb
└── README.md
```

## Dataset

The Setup cell generates the sample (no dataset is handed out for this stage):
115 business days (2022-01-03 → 2022-06-10) with two correlated numeric columns,
`daily_return` and `daily_return_2` (true slope ≈ 0.6). Five large "shock" values
(±0.17 … ±0.21) are injected into `daily_return` during May. There are **no missing
values** — missingness was stage 06; this stage is about outliers.

## Functions

| Function | What it does | Default behaviour |
|----------|--------------|-------------------|
| `detect_outliers_iqr(series, k=1.5)` | Flag values outside `[Q1 − k·IQR, Q3 + k·IQR]` | Boolean mask, `k=1.5` |
| `detect_outliers_zscore(series, threshold=3.0)` | Flag values with `\|z\| > threshold` | Boolean mask, population std (`ddof=0`), `threshold=3` |
| `winsorize_series(series, lower=0.05, upper=0.95)` | Clip values to the `[lower, upper]` quantiles | 5%/95% clip |

All three return a new object and never mutate the input, so they can be chained
and re-run safely. Improvements over the starter versions (documented in the module
docstring and exercised in the notebook's edge-case cell):

- **Empty / all-`NaN` / constant series** → an explicit all-`False` mask (no
  "accidentally false" behaviour).
- **`NaN` handling stated** — statistics use only non-null values; a `NaN` is never
  flagged as an outlier.
- **`ddof=0` explained** — a Z-score is judged against the spread of the data we hold.
- **Input validation** — `k > 0`, `threshold > 0`, and `0 <= lower < upper <= 1`.

## Key findings

- **Z-score (`threshold=3`)** flagged exactly the five injected shocks
  (min `|z|` among shocks = 4.1 vs. 0.8 max among non-shocks). **IQR (`k=1.5`)**
  flagged 9 — the same five plus four milder draws that fall outside the tight IQR fence.
- **Summary stats:** removing outliers collapses `std` from 0.0406 → 0.0094 and moves
  the mean from −0.00143 → −0.00004; the median barely moves (robust).
- **Regression:** the slope is robust (all 0.606 vs. filtered 0.590; true ≈ 0.6), but
  **R² falls 0.96 → 0.57** — not because the model worsened, but because the shocks were
  the largest, easiest variance to explain. Winsorizing **both** columns yields the
  lowest MAE (0.0037).

## Assumptions & risks

- **Z-score** assumes a roughly normal bulk; its mean/std can be inflated by the very
  outliers it seeks (masking). **IQR** assumes the quartiles summarize the distribution;
  its fence stays tight when the bulk is narrow.
- **Winsorizing** assumes extremes are genuine-but-overly-influential, worth capping not
  deleting. It must be applied **consistently to both columns** — capping only the
  predictor while the response keeps its shocks breaks the X→Y relationship (slope → 1.47).
- The extra IQR flags are **genuine returns, not errors**; deleting them would understate
  tail risk. Hence flag-and-report rather than auto-delete.

## Reproducibility

- The sample is generated once with `np.random.seed(17)` and saved to `data/raw/`.
- The notebook is meant to be run from `homework7/` (relative paths + `from src import outliers`).
- Detection, winsorizing, and the regression are all deterministic; re-running from its
  own folder reproduces identical numbers and figures.
