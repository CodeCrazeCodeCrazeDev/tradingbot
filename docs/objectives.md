# Institutional Business Objectives & Constraints Specification

This document defines the quantitative target profiles, constraints, and operational guidelines for the AlphaAlgo Strategy Suite. All strategies must be evaluated against these performance and risk criteria before any live/paper deployment.

## 1. Core Objectives & Performance Targets

| Metric | Target Value | Hard Minimum | Description |
| :--- | :--- | :--- | :--- |
| **Annualized Sharpe Ratio** | `> 2.50` | `1.80` | Evaluated net of all transaction costs (fees, slippage, spread) on out-of-sample data. |
| **Sortino Ratio** | `> 3.50` | `2.50` | Focuses purely on downside deviation. |
| **Max Peak-to-Trough Drawdown** | `< 10.0%` | `15.0%` | Hard stop limit at the portfolio level. |
| **Profit Factor** | `> 1.60` | `1.30` | Gross profits divided by gross losses. |
| **Annualized Volatility Target** | `12.0%` | `[8.0% - 15.0%]` | Controlled dynamically via volatility targeting and sizing. |

## 2. Capacity & Scale Constraints

- **Single Instrument Capacity:** Target symbol must support a minimum depth of **$10M** daily volume with < 5 bps market impact.
- **Total Strategy Capacity:** Scale target is **$50M** AUM. Beyond this limit, alpha decay is expected to accelerate, requiring sub-strategy replication or allocation to secondary assets.
- **Position Sizing:** Position size must be dynamically adjusted using Volatility Targeting (e.g., ATR-based fractional Kelly or volatility scale), ensuring no single trade represents > 1.5% of total portfolio variance.

## 3. Operational & Latency Budgets

- **Execution Latency SLA:** `< 200ms` round-trip execution latency budget.
- **Slippage Tolerance:** Slippage should be modeled and tracked. Target slippage must not exceed **0.5 pips** (or 0.005% equivalent) on average for major pairs (e.g., EUR/USD).
- **Daily Turnover Limit:** Maximum daily portfolio turnover of **30%** to avoid excessive fee drag.

## 4. Hard Constraints & Circuit Breakers

1. **Spread Limit:** No new trade signal may be executed if the current bid-ask spread exceeds **2.5x** the 30-day trailing average spread for that asset.
2. **Volatility Circuit Breaker:** Disable signal generation if the annualized trailing 1-hour realized volatility is in the top 99th percentile of historical regime distribution (indicating market dislocation/flash crash).
3. **Daily Max Loss Limit:** A hard portfolio drawdown threshold of **2.5%** within any single 24-hour trading session triggers immediate position flatting and strategy suspension.
4. **Max Open Positions:** No more than **5** simultaneous active positions per symbol.
