# ALPHAALGO_00_SYSTEM_AUDIT — 2026-11-04

Method: measured evidence only. Every claim cites a run, a count, or a test.
Statuses: implemented | tested | experimentally validated | production qualified.

## Verdict up front
AlphaAlgo is an **operational, honest abstainer** — not yet a profitable
trader. The full pipeline runs end-to-end and correctly refuses to trade
data it cannot verify. The master-prompt's smallest vertical slice
(obs→hypothesis→validation→decision→paper→outcome→improvement) **runs and
is measured**; its honest output is still WAIT.

## Capability inventory (measured)

| Capability | Status | Evidence |
|---|---|---|
| Unified pipeline (advisors→CSC→branches→verify→synth→decision→audit) | experimentally validated | 34 BTC cycles, all audited ABSTAIN |
| Paper execution (order→fill→settle→CSC reward) | experimentally validated | 22 controlled tests pass; restart dedup, cost, UNKNOWN-fault gates green |
| Operator control (pause/flatten/cancel/estop) | tested | signed Ed25519 reset; unsigned queue reset rejected |
| Signed emergency reset | tested | DPAPI key, nonce-consumed, atomic audit receipt, OS lock vs runner |
| Deadline supervisor | tested | Job-Object kill; heartbeat, stop-file, forced_stop labeling |
| Read-only dashboard | tested | correct control fields, stale/fresh labels, GET-only localhost |
| Data acquisition | implemented+validated | HL keyless 6 coins×5 TF; Kraken OHLC; data_scout ranks candidates |
| L2 orderbook | implemented+live-verified | --hl-l2 merges book onto obs, flagged order_book_time=live |
| Self-improvement (RSI) | implemented, gate green | promotion ladder + signed OperatorAuthorization; no candidates promoted |
| Calibration / research engine | implemented | EQE ledger 238 entries; no verdicts yet → floor not calibrated |
| Edge existence | **none measured** | every candidate fails cross-venue (Kraken) or window expansion |

## Highest-risk weaknesses (found by audit, ordered)

1. **No verified edge.** Every candidate (pullback/momentum/meanrev, 36+
   combos) fails bootstrap LCB, window expansion, or cross-venue. The
   simulator's EV was anti-predictive (-0.126) until alignment_prior was
   made injectable; still `no_discrimination` — EV is a function of
   alignment alone, not per-trade features. BLOCKER for any trade claim.
2. **Advisory exceptions recurring** — hivemind_collective,
   deep_agent_market, analysis_market_intel time out (empty messages);
   hawkes_event_intensity preflight parse bug; new "too many values to
   unpack" x35 defect. Evidence-only but degrades electorate quality.
3. **Warmup cost** — 17 min of a 60-min run is startup+advisory seed;
   sequential per-service seeding was the prior fix. Cycles still ~2min.
4. **L2 is live-only in replay** — attaching current book to historical
   bars is anachronistic; real L2 value needs a live-polling runner.
5. **Uncommitted other-session work** in tree (unified_bot.py, risk
   state_provider, cTrader files, deleted tv_sync.py) — not mine to merge.
6. **Two dashboards/processes** spawn duplicates on port 8080 (harmless
   but sloppy); supervisor heartbeat can die silently at deadline.

## Smallest vertical slice — status

obs(data_scout/DB) → advisors(207) → CSC branches → verification swarm →
sim(measured prior) → decision(WAIT) → [no proposal → no order] → audit +
snapshot → supervisor → report. **Working, validated.** The missing link
is a verified directional candidate → order → fill → outcome → reward —
which requires an edge the data has not yet produced.

## Prioritized backlog

P0 keep the honesty gates; P1 fix the x35 unpack defect + advisor
timeouts; P2 live-polling L2 runner (real per-bar books); P3 per-candidate
sim features so EV can discriminate; P4 more venues/instruments via scout;
P5 multi-window cross-venue walk-forward before any promotion.

Generated with Devin — measured, not asserted.

---

## Re-verification — 2026-11-05

Verified the 2026-11-04 findings against current code and fixed the
top-priority advisory defects. Measured evidence below.

### Defects fixed this pass

1. **x35 "too many values to unpack" — root caused and fixed.**
   `feeds/hl_l2.py` emitted raw Hyperliquid level dicts (`{"px","sz","n"}`)
   while its own contract (and ctrader_l2/mt5_l2) is `[price, size]`
   pairs. `upgrades LiquidityAnalyzer.analyze` unpacks pairs → crash
   every observation with a live book. Feed now normalizes to pairs.
   Verified: stubbed HL response → `[[px, sz], ...]` output; adapter
   `liquidity` probe returns real numbers instead of `{"error": ...}`.
2. **`hft_orderbook_imbalance` imbalance probe was dead on arrival.**
   The adapter passed the raw `{"bids":..., "asks":...}` dict to
   `OrderBookImbalanceDetector.analyze`, which expects an `OrderBook`
   dataclass → `AttributeError` every cycle (silently contained by
   `_probe_all`). Adapter now converts dict/pair/dict-level inputs into
   `OrderBook`/`OrderBookLevel`. Verified: probe emits a real
   `ImbalanceSignal` (ratio, direction, magnitude) on synthetic ctx.
   Net effect: HL L2 evidence now actually reaches the electorate.
3. **`hawkes_event_intensity` preflight crash — fixed.** The preflight
   probe sends `timestamp="preflight"`; `datetime.fromisoformat` threw.
   Parse now guarded with a utcnow fallback.
4. **Heavy-advisor timeouts — fixed at the declared-budget layer.**
   `hivemind_collective` and `analysis_market_intel` already declared
   `timeout_s=20.0` but `_ADVISORY_TIMEOUT_CEILING_S=10.0` clamped them
   to 10s while hivemind measures ~10s/cycle → TimeoutError (empty
   `str()`, matching the empty failure messages) on every due cycle.
   Ceiling raised to 20.0 (still bounded vs the 3600-abuse it exists
   to catch; these advisors run only on full/defer cycles anyway —
   none is in MEASURED_ACTIVE_SET). `deep_agent_market` now declares
   `timeout_s=20.0` like its heavy peers (was default 5s).

### Pre-existing test failures root-caused (not regressions)

- `test_advisor_timeout_coerced_and_ceiling_enforced`: broken by the
  long-tail deferral feature (second consult lands on cycle 2, advisor
  absent from MEASURED_ACTIVE_SET → deferred, never times out). Fixed
  by declaring `defer_n = 1` on the test's hogging service — the
  idiomatic "always due" override. Fails identically at HEAD.
- `test_directional_beating_cost_survives`: encodes pre-calibration
  gate semantics. The net-of-cost gate now compares *calibrated* EV
  (commit 969d1fcc, cold prior 0.05 — deliberately distrusts raw sim
  EV with zero realized evidence). Updated the test to seed `_ev_pairs`
  at par (cal=1.0 → survives) and added
  `test_directional_beating_cost_downgrades_without_evidence` locking
  in the cold-prior downgrade. Fails identically at HEAD.

### Test evidence (.venv)

- tests/foundation/test_advisory_blind_spots.py — 9/9 pass (was 8+1 fail)
- tests/core/test_csc_advisory_influence + csc_v5 + csc_v5_fix +
  rl_advisory — 215 pass, 28 skip (incl. every-wired-service contract)
- tests/core/test_csc_feedback_loop — 27/27 pass (was 26+1 fail)
- decision_bus_isolation + brain_audit_integrity — pass
- tests/data_feeds — 2 collection errors: `aiohttp` missing from .venv
  (documented env limitation, pre-existing; not a code failure)

### Still open (unchanged from 2026-11-04)

- No verified edge remains the blocker; honesty gates are intact and
  now also verified by the new cold-prior regression test.
- Uncommitted foreign-session files (unified_bot.py,
  risk/state_provider.py, cTrader trio, docs readme) left untouched.
- Warmup cost, live-only L2 replay caveat, dashboard duplicates as
  before.
