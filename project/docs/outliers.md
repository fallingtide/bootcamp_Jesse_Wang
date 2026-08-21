# Outlier Analysis (Stage 07)

## What counts as an "outlier" here

An outlier is a **daily return far from its own ticker's typical range** — not a
data-entry error. We use two detectors, both applied **within each ticker**
because the ETFs span very different volatility regimes (GLD/QQQ vs TLT):

- **IQR (k=1.5):** flag returns outside `[Q1 − 1.5·IQR, Q3 + 1.5·IQR]`.
- **Z-score (threshold=3):** flag returns with `|z| > 3` (population std).

**Default for the pipeline: Z-score (`threshold=3`).** Financial returns are
fat-tailed, so the IQR fence — calibrated for a roughly symmetric, non-fat-tailed
bulk — over-flags (42 of 1,255 days, ~3.3%). The Z-score flags 11 days (~0.9%),
the right order of magnitude for a 1-year daily-return panel, and it cleanly
separates genuine tail events from ordinary noise.

## Findings

| ticker | days | Z-flagged | IQR-flagged | notable events |
|--------|------|-----------|-------------|----------------|
| GLD | 251 | 3 | 15 | −10.3% (2026-01-30), +6.4% (2026-02-03), −6.4% (2025-10-21) |
| IWM | 251 | 2 | 6 | — |
| QQQ | 251 | 1 | 9 | — |
| SPY | 251 | 4 | 9 | — |
| TLT | 251 | 1 | 3 | — |
| **total** | **1,255** | **11** | **42** | — |

The GLD −10.3% day is the largest event and is **a genuine market move, not a
data error** — deleting it would materially understate gold's downside tail risk,
which is exactly the risk the rotation strategy needs to see.

## Sensitivity

**Volatility (the thing a PM sizes risk on).** Pooled daily-return standard
deviation with outliers kept, dropped (Z-score), or winsorized (5%/95%):

| treatment | mean | std |
|-----------|------|-----|
| all (keep) | 0.084% | 1.206% |
| filtered (drop \|z\|>3) | 0.098% | 1.117% |
| winsorized (5%/95%) | 0.085% | 1.030% |

The mean barely moves; the **standard deviation shrinks ~7% when the 11 tail days
are dropped, ~15% when they are capped.** The effect is concentrated in GLD, whose
std falls from 1.81% → 1.60% when its three tail days are removed (~12%).

**Correlation structure (beta vs SPY).** Regressing each ETF's return on SPY:

| ticker | beta (all → filtered) | R² (all → filtered) |
|--------|----------------------|---------------------|
| GLD | 0.704 → 0.716 | 0.099 → 0.133 |
| IWM | 1.214 → 1.187 | 0.670 → 0.656 |
| QQQ | 1.413 → 1.394 | 0.861 → 0.855 |
| TLT | 0.178 → 0.160 | 0.057 → 0.047 |

Betas are **largely robust** (a few percent shift), which is reassuring — the tail
days do not wildly distort the correlation structure. The exception is GLD, whose
R² vs SPY *improves* (0.099 → 0.133) once its idiosyncratic gold-specific crash
days are removed, because those days are market-*unrelated* noise in the SPY-beta.

## Assumptions

- **Each ticker's returns are roughly stationary over the year** — the within-ticker
  mean/std behind the Z-score are meaningful summaries. A regime shift (e.g. a
  volatility spike) would make one fixed threshold misleading.
- **Tail events are real, not errors.** We therefore *flag and report*, never
  auto-delete. Deletion/capping are offered only as explicit sensitivity treatments.
- **Winsorizing bakes in a cap assumption** — it assumes extremes are
  overly-influential but informative, and must be applied **consistently to both
  sides of a relationship** (predictor and target), or it distorts it.
- **Independence of observations** — the Z-score treats days as i.i.d.; volatility
  clustering means extreme days tend to arrive together, which a single-day test
  only partly captures.

## Risks if the assumptions are wrong

- **Understating tail risk.** If we filtered/dropped outliers before modeling, the
  −10% gold day (a real crash) would vanish and the risk bands would be too tight —
  the PM could over-allocate to a strategy whose downside is larger than reported.
- **Regime change.** A year with a volatility shock raises the Z-score threshold and
  *hides* the very events we want to detect; rolling/robust detection should be
  revisited in the modeling stage.
- **Masking.** With many outliers, the inflated std hides some of them. Here there
  are few, so it is acceptable; for heavier tails, a robust (MAD-based) threshold is
  safer.
- **Mis-classifying genuine moves as noise.** Deleting the 11 Z-flagged days removes
  information about how the strategy behaves in stress — the exact scenario the PM
  cares about.
