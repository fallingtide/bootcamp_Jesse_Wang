# Memo — ETF Strategy: One-Year Outlook

**To:** Portfolio Manager
**From:** Research (ETF strategy robustness evaluation)
**Re:** Scoping the one-year viability review of the ETF rotation strategy

## What we're solving

You asked whether the ETF rotation strategy will still work next year. This
memo frames how we'll answer it, so the evaluation you receive is the one you
can actually act on.

## The decision

At the next quarterly rebalance you will either keep, scale, or cut the
strategy's allocation. Before that meeting we will deliver: (1) a one-year
expected return and risk band, and (2) an explicit trigger that says when to
act.

## What you'll receive

- A forecast with scenario bands (base / stress), not a single point estimate.
- A decomposition of what has driven past returns, so you can judge whether the
  edge is real and whether it is likely to persist.
- A reproducible notebook, so the numbers can be re-run and challenged.

## What we need from you

- The current capital allocated to the strategy, and the benchmark you measure
  it against.
- Any constraints on turnover, liquidity, or drawdown tolerance.
- Sign-off on the data sources we plan to use (public ETF/index data).

## Assumptions (flagged for your review)

- Public daily data is sufficient; we are not modeling intraday effects.
- We assume return relationships are roughly stable over one year, and we test
  that assumption rather than take it on faith.

## Risks we're watching

- Regime change, backtest overfitting, and capacity limits as AUM grows.

## Next steps

1. Confirm the benchmark and constraints (this week).
2. Stand up the repo and data pipeline (Stage 02–05).
3. First forecast readout ahead of the quarterly rebalance.
