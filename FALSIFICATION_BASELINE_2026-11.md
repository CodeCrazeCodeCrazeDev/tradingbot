# Falsification Baseline — November 2026

**Status: measured, reproducible. This document records what was tested
and rejected so future candidate searches start from the null instead
of re-running the same space.**

Every number below came out of the canonical sealed pipeline
(`csc.propose_model` → `csc.validate_model`): 70/30 chronological split,
net-of-cost expectancy (`COST_BPS`, recorded in each evaluation's
seal), bootstrap significance p(Δ>0) ≥ 0.90 **and** p(Δ>baseline) ≥ 0.5,
Benjamini–Hochberg FDR on batch sweeps. Data: `market_data.db`
EURUSD/GBPUSD/USDJPY M15 (clean windows, off-grid rows excluded) and
`hl_data.db` crypto 15m. Raw artifacts: `var/expansion/*.json`.

## Result: 91 candidates evaluated, 0 replicated survivors

| Experiment | Tested | Verdict |
|---|---|---|
| Foundry threshold rules (FX M15) | 15 | all rejected — 10 FALSIFIED (net −0.4 to −6.1 bps), 5 honest dependency-fail (no sklearn) |
| GA expressions, FDR-gated (FX M15) | 30 | all rejected — 29 FALSIFIED + 1 INCONCLUSIVE; 0 BH survivors |
| Regime-gated families (FX M15) | 12 | 1 CONFIRMED → falsified on replication (see below) |
| Cost sweep 0 / 1 / 2 / 3.25 bps (EURUSD) | 16 | all FALSIFIED — cost is not erasing hidden structure |
| Venue: HL crypto BTC/ETH/SOL 15m | 12 | all FALSIFIED on the paired baseline gate |
| Horizon sweep h8/h24/h48 (EURUSD) | 6 | all FALSIFIED — edge does not move to longer horizons |
| Cross-instrument peer features (EURUSD~GBPUSD both directions) | 16 | all FALSIFIED — `peer_corr_hi_buy` cleared significance (+2.56 bps, p=0.92) and still lost to buy-and-hold |
| Trained logistic model on 6 derived features (EURUSD, USDJPY) | 2 | all FALSIFIED — −2.75 / −2.60 net bps vs +0.17 / +0.14 baseline on sealed holdout |
| **Total** | **109** | **0** |

## What the gates caught (why the machinery is credible)

- **Positive mean ≠ edge.** EURUSD `zscore(ts_min(ts_min(low)))`: +7.34
  net bps on unseen bars, p(Δ>0)=0.82 < 0.90 → FALSIFIED. Luck-shaped.
- **Beating zero ≠ beating the market.** Crypto runs scored +32 to +48
  net bps at p(Δ>0)≈1.0 and were still rejected — they did not beat
  passive exposure (p>baseline < 0.5). In trending windows that is the
  correct bar.
- **Survivors must replicate.** `trend_momentum_sell` on USDJPY was
  CONFIRMED (+2.54 bps, p≥0.90) — then FALSIFIED on all four disjoint
  earlier windows (−3.0 to −10.9 bps). One survivor in ~74 trials was
  exactly the multiplicity false positive FDR exists to catch.
- **Dependencies fail honestly.** The logistic spec reported
  "missing dependency" (no sklearn in .venv) instead of a fabricated fit.

## What this rules out

OHLCV-derived rules — momentum, RSI thresholds, rank/zscore GA
expressions over close/high/low/volume — carry no survivable edge on
this data across horizons 4–48 bars and costs 0–3.25 bps. This signal
family is **exhausted**: more trials of the same form would be
confirmation, not research.

## What this does NOT rule out

- **Order-flow and sentiment**: `sentiment_history.db` is empty (0
  rows) and no bid/ask feed exists in any onboarded source — these
  inputs are untestable today, not exhausted.
- **Trained models** (the failing step was rule→signal mapping, not
  structure detection — the scanner measures real structure: crypto
  sign-persistence ≈ 0.68).
- **Venues/costs outside the tested grid** — crypto rejections were
  baseline-relative, not absolute; on lower-fee venues or as portfolio
  overlays the economics differ.

## Acceptance criteria for any future candidate

A candidate counts as a survivor only if it clears **all three**:

1. Sealed holdout: net > 0, p(Δ>0) ≥ 0.90, p(Δ>baseline) ≥ 0.5.
2. FDR survival across its whole proposal batch (BH q=0.05).
3. Replication on a disjoint window it never saw.

Anything failing one of these did not happen — report it here, do not
report it as progress.

## Reproduction

```bash
.venv/Scripts/python.exe scripts/expansion_foundry_run.py \
    --symbols EURUSD GBPUSD USDJPY --tail-bars 8000
.venv/Scripts/python.exe scripts/expansion_ga_run.py \
    --symbols EURUSD --tail-bars 2000 --n-proposals 10
.venv/Scripts/python.exe scripts/expansion_sweep.py \
    --experiments regime cost venue horizon --tail-bars 2000
.venv/Scripts/python.exe scripts/expansion_report.py
```

Prior independent corroboration: `var/edge_baseline.json`
(`no_edge_detected`) and the edge-gate screens (~264 candidate entries,
all rejected) arrived at the same null through a separate harness.
