# ETF Strategy Robustness Evaluation

An end-to-end evaluation of whether a systematic ETF rotation strategy will
keep working over the next year, built stage-by-stage across the data-science
lifecycle (problem framing → tooling → acquisition → storage → preprocessing →
EDA → modeling → reporting).

## Project summary

A portfolio manager runs a systematic ETF rotation strategy and needs a
forward-looking answer to one question: *"Will this strategy still work next
year?"* The edge that the strategy historically captured can decay — from
crowding, shifting market regimes, rising transaction costs, or backtest
overfitting — and the PM must decide whether to keep capital allocated, scale
it, or redeploy. This matters because a strategy whose edge silently decays can
go from a real advantage to a disguised coin-flip, exposing the book to
drawdowns the PM no longer expects.

This project frames that decision as a repeatable evaluation: characterize the
strategy's historical performance and its drivers, then produce a one-year
outlook with return and risk bands plus an explicit trigger for action — so the
PM's capital-allocation decision is tied to evidence rather than intuition.

The deliverable is a reproducible pipeline (`notebooks/project_pipeline.ipynb`)
that acquires public ETF/index data, stores it reproducibly, and cleans it into
a modeling-ready return series, backed by reusable `src/` modules and a
stakeholder memo (`docs/stakeholder_memo.md`).

## Stakeholder & user

- **Decision owner:** the Portfolio Manager (PM), who allocates or deallocates
  capital to the strategy on a quarterly review cadence. They care about
  *expected forward return, risk, and an explicit trigger for action* — not the
  mechanics of the model.
- **Tool/operator:** the quant/research analyst, who runs the pipeline, produces
  the report, and hands the PM a decision-ready summary.
- **Timing & workflow:** inputs refresh monthly; a formal readout lands before
  each quarterly rebalance. The answer must arrive *before* the allocation
  decision, not after.

## Goals → lifecycle → deliverables

| Goal | Lifecycle stage | Deliverable |
|------|-----------------|-------------|
| Frame the decision & stakeholders | Problem Framing & Scoping (Stage 01) | this README + `docs/stakeholder_memo.md` |
| Reproducible tooling & env | Tooling Setup (Stage 02) | folder scaffold, `.gitignore`, `requirements.txt`, `src/config.py` |
| Clean, importable code | Python Fundamentals (Stage 03) | `src/utils.py` + `notebooks/python_fundamentals_summary.ipynb` |
| Acquire & validate data | Data Acquisition & Ingestion (Stage 04) | `notebooks/project_pipeline.ipynb` (acquisition), raw data in `data/raw/` |
| Store & version data | Data Storage (Stage 05) | `src/io.py`, processed Parquet/CSV in `data/processed/` |
| Clean & prepare data | Data Preprocessing (Stage 06) | `src/cleaning.py`, cleaned dataset in `data/processed/` |
| Model & evaluate | Modeling (later stage) | forecast notebook + risk bands |
| Deliver decision support | Reporting (later stage) | memo + scenario readout |

## Repo structure

```
project/
├── README.md                  # you are here
├── requirements.txt           # recreate the environment
├── .env.example               # template for secrets + data paths
├── .gitignore                 # excludes .env, caches, course PDFs
├── data/
│   ├── raw/                   # immutable, as-acquired data (CSV)
│   └── processed/             # cleaned / derived data (Parquet + CSV)
├── notebooks/
│   ├── project_pipeline.ipynb # the master pipeline, extended every stage
│   └── python_fundamentals_summary.ipynb
├── src/
│   ├── config.py              # .env loading + secret lookup
│   ├── utils.py               # summary stats + return computation
│   ├── io.py                  # suffix-routing read/write + validation
│   └── cleaning.py            # fill / drop / normalize
├── docs/
│   └── stakeholder_memo.md    # the one-page brief for the PM
├── reports/                   # (empty until the reporting stage)
└── model/                     # (empty until the modeling stage)
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in any real API keys
```

Run the pipeline from `notebooks/`:

```bash
cd notebooks
jupyter nbconvert --to notebook --execute project_pipeline.ipynb --inplace
```

The notebook's first cell re-roots itself to `project/` so it runs no matter
which directory it is launched from.

## Data Storage (Stage 05)

### Folder structure

- `data/raw/` holds original, untouched data — nothing here is transformed.
- `data/processed/` holds data in columnar, ready-to-query form.

### Formats used and why

| Format | Folder | Why |
|--------|--------|-----|
| **CSV** | `data/raw/` | Human-readable, universally portable, easy to diff and inspect; the right default for an "as-acquired" snapshot. |
| **Parquet** | `data/processed/` | Columnar and compressed — faster reads, smaller files, and it **preserves dtypes** (dates, numerics, categories) across a reload, which CSV loses. |

### Reading and writing via environment variables

Paths come from `.env` (`DATA_DIR_RAW`, `DATA_DIR_PROCESSED`) with
`data/raw` / `data/processed` as fallbacks, so the same code runs anywhere:

```python
RAW, PROC = io.get_paths()   # reads env vars, falls back to data/raw & data/processed
```

IO is abstracted behind suffix-routing helpers in `src/io.py` so callers never
branch on format themselves:

- `write_df(df, path)` — creates parent dirs, picks CSV or Parquet from the
  file suffix, and raises a clear `RuntimeError` if Parquet is requested but no
  engine is installed.
- `read_df(path)` — routes on suffix, re-parses `date` columns on CSV load, and
  returns the frame with dtypes intact.

### Validation

After every save the pipeline reloads the file and checks via
`validate_loaded()` that shape matches the original, required columns are
present, and `date`/`close` have the expected dtypes.

## Data sources & acquisition (Stage 04)

- **API source:** ETF daily prices via `yfinance` (fallback to Alpha Vantage
  `TIME_SERIES_DAILY` if an API key is set in `.env`). Universe: `SPY`, `QQQ`,
  `IWM`, `GLD`, `TLT` — a representative cross-asset rotation basket.
- **Scrape source:** S&P 500 constituents from the public Wikipedia table
  `table#constituents` (`https://en.wikipedia.org/wiki/List_of_S%26P_500_companies`).
- **Secrets:** the Alpha Vantage key (if any) is read from `.env` via
  `python-dotenv` and never hard-coded. `.env` is gitignored; only
  `.env.example` is committed.
- **Reproducibility:** raw files use timestamped names so reruns never
  overwrite earlier snapshots.

## Preprocessing (Stage 06)

The cleaning step (`notebooks/project_pipeline.ipynb` → `src/cleaning.py`)
prepares the raw price panel for modeling:

1. **Impute missing closes** with the ticker median (`fill_missing_median`),
   robust to outliers and skew. In practice `yfinance` daily data has few gaps;
   the step is kept as a guard.
2. **Compute daily returns** within each ticker (`compute_returns`), the core
   unit of analysis for the strategy.
3. **Drop rows with a missing return** (`drop_missing` on the `return` column)
   — this removes only each ticker's first trading day, where no prior close
   exists to compute a return.
4. **No normalization of raw prices.** `normalize_data` is available but
   deliberately *not* applied to `close`, because rescaling prices would
   destroy cross-ticker comparability and price levels are non-stationary; it
   is reserved for return/feature rescaling in the modeling stage.

### Assumptions

- **Missingness is MCAR/MAR**, so median imputation is safe and does not hide a
  systematic signal. If missingness were MNAR it would be modeled explicitly.
- **Daily public data is sufficient**; no intraday effects are modeled.
- **Return relationships are roughly stable over one year** — an assumption we
  *test*, not take on faith.
- **Future data follows the same schema** (same columns/dtypes); a materially
  different vendor schema needs re-inspection.

## Risks & known unknowns

- **Regime change** breaking historical relationships — monitored via rolling
  windows and out-of-sample checks.
- **Backtest overfitting / data-snooping** — guarded with walk-forward
  validation.
- **Capacity:** returns may erode as AUM scales past the strategy's limit.
- **Data quality / survivorship bias** in the index history.

## Cadence

Monthly data refresh; quarterly readout aligned to the PM's rebalance cycle.
