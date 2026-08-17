# Stage 05 — Data Storage

A reproducible storage layer for one dataset: environment-driven paths, CSV vs
Parquet, reload-and-validate, and suffix-routing IO utilities.

## Data Storage

### Folder structure

```
homework5/
├── data/
│   ├── raw/          # immutable, as-acquired data (CSV)
│   └── processed/    # cleaned / derived data (Parquet)
├── .env.example      # template for DATA_DIR_RAW / DATA_DIR_PROCESSED
└── stage05_..._homework-starter.ipynb
```

- `data/raw/` holds the original, untouched dataset. Nothing here is transformed.
- `data/processed/` holds the dataset in a columnar, ready-to-query form.

### Formats used and why

| Format | Folder | Why |
|--------|--------|-----|
| **CSV**  | `data/raw/`      | Human-readable, universally portable, easy to diff and inspect; the right
default for an "as-acquired" snapshot. |
| **Parquet** | `data/processed/` | Columnar and compressed — faster reads, smaller files, and it **preserves
dtypes** (dates, numerics, categories) across a reload, which CSV loses. The
cost is it needs an engine (`pyarrow`/`fastparquet`). |

### Reading and writing via environment variables

The notebook loads `DATA_DIR_RAW` and `DATA_DIR_PROCESSED` from `.env` with
`python-dotenv` and falls back to `data/raw` / `data/processed` if they are
unset:

```python
RAW  = pathlib.Path(os.getenv('DATA_DIR_RAW',       'data/raw'))
PROC = pathlib.Path(os.getenv('DATA_DIR_PROCESSED', 'data/processed'))
```

IO is abstracted behind two suffix-routing helpers so callers never branch on
format themselves:

- `write_df(df, path)` — creates parent dirs, picks CSV or Parquet from the
  file suffix, and raises a clear `RuntimeError` if Parquet is requested but no
  engine is installed.
- `read_df(path)` — routes on suffix, re-parses `date` columns on CSV load, and
  returns the frame with dtypes intact.

### Validation

After every save the notebook reloads the file and checks, via
`validate_loaded()`:

- shape matches the original,
- required columns are present,
- `date` is a datetime dtype and `price` is numeric.

### Assumptions

- Timestamped filenames (`sample_YYYYMMDD-HHMMSS.csv`) so reruns never overwrite.
- `numpy` RNG is seeded so the synthetic sample is identical on every run.
- Parquet requires `pyarrow` (or `fastparquet`); the code fails loudly with a
  remediation message rather than silently skipping.
