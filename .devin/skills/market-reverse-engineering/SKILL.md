---
name: market-reverse-engineering
description: Decompose a market move or regime into its structural drivers (flow, depth, positioning, vol) working backward from the data we hold
---

# Market Behavior Reverse-Engineering

Work backward from a price move / regime / anomaly window to its structural
drivers, using every surface the data estate holds. Output is structural
attribution — honest about what the resolution can't resolve.

## Surfaces available

- OHLCV bars: `market_data.db` (FX M15), `binance_data.db`, `fx_data.db`,
  `us_stocks.db`, `macro_data.db` — always filter symbol+timeframe first,
  never sort mixed windows (return/vol poisoning; see AGENTS.md).
- `var/orderflow/fx_ticks.db` — FX tick data.
- `var/l2data/` — Binance UM: `bookDepth` snapshots, `metrics` (OI,
  long/short ratios), `bookTicker1s` 1s quotes, premium-index klines,
  aggTrades (streamed, usually deleted — re-download via
  `scripts/stream_bookticker.py` / `_um_file`).
- Forecast telemetry: `var/rv_forecast_log.jsonl` (rv16 vol forecasts).

## Workflow

1. **Frame the window precisely**: symbol, timeframe, [t0,t1]. Get the move's
   own stats first (range, vol, drift, top/bottom-decile bars).
2. **Run `scripts/market_recon.py`** for the mechanical decomposition:
   regime stats, return autocorrelation, vol clustering, volume/depth/quote
   surfaces where present.
3. **Layer surfaces by information class**: price (bars) → flow (aggTrades/
   bookTicker imbalance) → depth (bookDepth bands) → positioning (metrics:
   top-trader vs retail L/S ratios, OI changes) → basis (premium index).
   Each layer answers a different "who/what" question.
4. **Compare vs the instrument's own baseline** — the same stats on
   non-event windows. An 86k-quote day means nothing until compared to the
   446k-quote day on 2024-01-02.
5. **State the resolution limit explicitly.** We can say "depth imbalance
   clustered before the move" — we cannot say "whales drove it" (no order
   attribution, no queue positions). Structural attribution only.

## Failure patterns already documented (check AGENTS.md before re-tripping)

- Mixed-symbol/mixed-timeframe window sorting → fake volatility.
- Off-grid contaminated bars (EURUSD M15, 2026-06-04→14 splice).
- Episode-clustered samples read as independent evidence.
- Correlation at same-bar = simultaneity, not lead — check lead-1 explicitly.
