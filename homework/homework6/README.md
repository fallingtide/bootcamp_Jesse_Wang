# Stage 06 — Data Preprocessing

Modular, reusable cleaning functions applied to a sample dataset, with the
cleaning strategy and its assumptions documented.

## Folder structure

```
homework6/
├── src/
│   ├── __init__.py       # makes `src` importable
│   └── cleaning.py       # fill_missing_median / drop_missing / normalize_data
├── data/
│   ├── raw/              # as-acquired sample (sample_data.csv)
│   └── processed/        # cleaned output (sample_data_cleaned.csv)
├── stage06_data-preprocessing_homework-starter.ipynb
└── README.md
```

## Cleaning strategy

The pipeline in the notebook runs in this order, each step a separate,
re-runnable function:

1. **Drop the near-empty column.** `extra_data` is missing in 5 of 7 rows
   (~71%). A column this sparse carries almost no signal, and the only ways to
   "keep" it are to impute a mostly-invented value or to drop most of the
   dataset. We drop it.
2. **Impute numeric missing values with the column median**
   (`fill_missing_median`). Median is used over the mean because it is robust
   to outliers and skew.
3. **Drop rows still too incomplete** (`drop_missing`, threshold `0.5`). After
   steps 1–2 this drops nothing — which is itself a finding (see below).
4. **Rescale numeric columns** (`normalize_data`, min-max) onto `[0, 1]` so
   columns with different units (age, income, score) are comparable.

### Why the row-drop threshold removed nothing

`drop_missing(threshold=0.5)` keeps rows that are at least half complete. In
this dataset the missingness is **concentrated in one column** (`extra_data`),
not spread across rows, so no row is less than half complete. The threshold
step is kept in the pipeline as a guard for future data, but the column drop
in step 1 is what actually resolves the missingness here. This is why we
inspect the *shape* of missingness before choosing a strategy.

## Functions

| Function | What it does | Default behaviour |
|----------|--------------|-------------------|
| `fill_missing_median(df, columns=None)` | Fill NaN with the column median | All numeric columns |
| `drop_missing(df, columns=None, threshold=None)` | Drop rows missing in `columns`, below a completeness `threshold`, or any NaN | Strict any-NaN drop |
| `normalize_data(df, columns=None, method='minmax')` | Rescale to `[0, 1]` (minmax) or z-scores (standard) | All numeric columns, minmax |

All three return a new DataFrame and never mutate the input, so they can be
chained and re-run safely.

## Assumptions

- **Missingness is MCAR/MAR.** Median imputation is valid only if the missing
  values are not systematically biased (i.e. not MNAR). If missingness were
  MNAR, imputing would hide a real signal and a model should be built for it
  instead.
- **`extra_data` is non-essential.** Dropping a mostly-empty column assumes it
  is not a critical analytical field.
- **Median is representative.** Imputing with the median assumes the column is
  not so skewed that the median misleads downstream analysis.
- **Min-max ranges are representative.** Scaling onto `[0, 1]` assumes the
  observed min/max are not extreme outliers that would crush the rest of the
  values into a tiny band.
- **Future data follows the same structure.** The functions assume later
  datasets have the same numeric/text columns; truly different schemas need
  re-inspection.

## Reproducibility

- The sample dataset is generated once and saved to `data/raw/sample_data.csv`.
- Cleaning is deterministic (median imputation + min-max scaling); re-running
  the notebook from its own folder produces identical output.
- The cleaned frame is saved to `data/processed/sample_data_cleaned.csv` and
  reloaded to verify shape and values.
