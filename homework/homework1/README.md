# ETF Strategy Robustness Evaluation

**Stage:** Problem Framing & Scoping (Stage 01)

## Problem Statement

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

## Stakeholder & User

- **Decision owner:** the Portfolio Manager (PM), who allocates or deallocates
  capital to the strategy on a quarterly review cadence.
- **Tool/operator:** the quant/research analyst, who runs the model, produces
  the report, and hands the PM a decision-ready summary.
- **Timing & workflow:** inputs refresh monthly; a formal readout lands before
  each quarterly rebalance. The answer must arrive *before* the allocation
  decision, not after.

## Useful Answer & Decision

- **Framing:** primarily *predictive* (one-year expected performance and risk),
  supported by a *descriptive* decomposition of what drove past returns
  (factor / regime attribution).
- **Metric:** forward 12-month return and volatility bands (expected Sharpe and
  max-drawdown scenarios), plus an explicit decision trigger.
- **Artifact:** a short stakeholder memo (`docs/`) and a reproducible notebook
  that shows the forecast and its assumptions.

## Assumptions & Constraints

- Daily ETF/index price data is available and cleaned; no intraday data.
- Relationships that drove historical performance are roughly stable over the
  one-year horizon — an assumption we *test*, not take on faith.
- Liquidity and transaction costs are material and must be modeled.
- Public data only; no material non-public information (compliance).
- Low latency is not required — the answer is reviewed monthly, not live.

## Known Unknowns / Risks

- Regime change that breaks historical relationships (monitor via rolling
  windows and out-of-sample checks).
- Backtest overfitting / data-snooping (guard with walk-forward validation).
- Capacity: returns may erode as AUM scales past the strategy's limit.
- Data quality gaps or survivorship bias in the index history.

## Lifecycle Mapping

Goal → Stage → Deliverable

- Frame the decision & stakeholders → Problem Framing & Scoping (Stage 01) →
  this README + `docs/stakeholder_memo.md`
- Reproducible tooling & env → Tooling Setup (Stage 02) → venv + `requirements.txt`
- Clean, importable code → Python Fundamentals (Stage 03) → `src/` modules + tests
- Acquire & validate data → Data Acquisition & Ingestion (Stage 04) → raw
  ETF/index data in `data/raw/`
- Store & version data → Data Storage (Stage 05) → processed dataset in
  `data/processed/`
- Model & evaluate → Modeling (later stage) → forecast notebook + risk bands
- Deliver decision support → Reporting (later stage) → memo + scenario readout

## Repo Plan

- `data/` (raw + processed), `src/`, `notebooks/`, `docs/`
- Cadence: monthly data refresh; quarterly readout aligned to the PM's
  rebalance cycle.
