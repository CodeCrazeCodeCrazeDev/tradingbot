# Next Steps Plan — post security-kernel + research-engine sessions

Status: as of latest commit. Ordered by leverage. Each item lists the
verify step — nothing counts done without it.

## P0 — Verify what just shipped

- [ ] Full test pass: `pytest tests/core/test_research_engine.py
      tests/core/test_security_kernel.py tests/core/test_rl_advisory.py
      tests/core/test_policy_lifecycle.py -q --no-cov -p no:cacheprovider`
- [ ] Restart LSE replay on current code — the running `var/lse_full`
      instance predates advisor tiering + artifact signing.
      Expected: faster cycles, `advisors_deferred` > 0 on narrow
      cycles, zero `sig_quarantined`.
- [ ] Confirm `sig` fields appear in advisory artifacts in
      `var/lse_full/snapshot.json` (spot-check one artifact).

## P1 — Data paths (the actual edge bottleneck)

- [ ] cTrader L2 credentials (`CTRADER_CLIENT_ID/SECRET/ACCESS_TOKEN`)
      → `--ctrader-l2` gives order-book fields to the order-flow
      advisors that currently abstain on every bar.
- [ ] MT5 demo credentials (rotated, demo-only) → `mt5_demo_runner
      --follow` live soak; validates the pipeline on a live feed.
- [ ] More symbols + longer history — `edge_baseline.py` needs only a
      `market_data`-shaped sqlite DB; 3 rules × more data is the
      cheapest edge test available.
- [ ] Re-run `edge_baseline.py` on H1 timeframe + longer horizons
      (`--timeframe H1 --horizon 4/12/24`) on existing LSE data —
      costs nothing, may find a slower-frequency edge M15 lacks.

## P2 — Wire the security kernel deeper

- [ ] Sign `UnifiedDecisionBus` messages, not just advisory artifacts
      — the bus is where a forged TRADE_APPROVED would actually hurt.
- [ ] Enforce `CapabilityDomain` at the risk/execution boundary —
      risk service holds RISK, execution holds EXECUTION; assert at
      attach time, deny cross-domain calls.
- [ ] Extend `verify_artifact` consumption into the electorate tilt —
      currently quarantines but tilt may still read `status` fields;
      confirm quarantined artifacts carry zero weight downstream.

## P3 — Research → experiment loop

- [ ] Operator-approve one `arbiter_hypothesis_proposal` → route
      through `investigate` with the real `hypothesis_gen` (needs the
      CSC runtime, not the bare engine).
- [ ] EQE `calibrate_floor` self-activates once ≥20 measured verdicts
      exist in `eqe_ledger.jsonl` — check ledger growth weekly.
- [ ] `creator`/`semantic_scholar`/`dblp` remain env-blocked (OAuth,
      API key, Anubis wall) — provision keys only if the 13 live
      sources prove insufficient.

## P4 — Open blind spots (measured, not urgent)

- [ ] `distill_step` cadence is checkpoint-based not divergence-based.
- [ ] `_funnel` counters unbounded on multi-day soaks (int keys only —
      watch, not fix).
- [ ] `vol_shock` trigger uses one volatility ratio — consider adding
      an ATR-based variant if false-positive full cycles appear.
- [ ] Live rollback trigger still only exercised in unit tests —
      needs a soak long enough to see real degradation.

## Standing facts (not bugs)

- `edge_baseline.py` verdict: **no_edge_detected** on EURUSD M15 —
  honest measurement, means=-5bps net on all 3 fixed rules.
- cTrader/MT5 runs blocked on credentials — provision, don't code.
- In-process HMAC is protocol enforcement, not process isolation —
  documented in `security_kernel.py`; sandbox remains the boundary.
