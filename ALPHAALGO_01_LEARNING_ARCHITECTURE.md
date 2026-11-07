# ALPHAALGO_01_LEARNING_ARCHITECTURE — 2026-11-07

Logical-layer → concrete-module mapping. Every label is evidence-based
per ALPHAALGO_00_SYSTEM_AUDIT.md: implemented | tested | experimentally
validated | production qualified. No layer is claimed stronger than its
measured evidence.

## Layer map (Phase-1 diagram → actual code)

| Logical layer | Concrete module(s) | Status |
|---|---|---|
| External information + internal experience | `scripts/hyperliquid_sync.py` (keyless HL, 6 coins × 5 TF), Kraken OHLC in `data_scout.py`, `trading_bot/feeds/hl_l2.py` (L2 book), `trading_state.db` audit tables (own-experience records) | implemented+validated |
| Data ingestion | `paper_runner.py` sources: `db`, `cross`, `hl_live` (polls new closed bars, `volume_kind="real"` distinguishes traded volume from tick proxies), `synthetic` | implemented+validated |
| Validation + provenance | `data_scout` dedup/gap checks; obs fields `data_source`, `ts_is_broker_time`, `order_book_time` ∈ {live, anachronistic} — point-in-time honesty enforced in code | implemented+validated |
| Knowledge/data storage | `hl_data.db` (SQLite candles), `trading_state.db` (durable state), snapshot.json, append-only audit_events | implemented |
| Market representation | `_BarHistory` + ~200 advisory modules (`core/csc/advisory.py`) — trend/vol/liquidity/regime/microstructure electorate | implemented (uneven quality; timeouts + unpack defect fixed `572a2aed`) |
| Prediction + uncertainty | CSC hypothesis branches (`core/csc/controller.py`), verification swarm (market-structure/cost/risk verifiers), simulator with injectable alignment_prior | implemented — EV still no_discrimination (audit weakness #1) |
| Research + discovery | `scripts/data_scout.py` (2-venue candidate ranking, embargoed block-bootstrap LCB), `scripts/edge_baseline.py` (chronological split + costs) | implemented+validated — every candidate falsified so far |
| Experimental validation | RSI package `trading_bot/recursive_self_improvement/` (contracts/evaluator/anti-gaming); EQE ledger; cross-venue falsification is the strongest falsifier in the system | implemented, gates green |
| Strategy registry | RSI promotion ladder + strategy allow-list (mean_reversion/momentum/stat_arb bounded params only) | implemented |
| Decision + allocation | CSC synthesis → terminal WAIT/TRADE_PROPOSED; abstain is a first-class audited decision (40+ audited abstains) | experimentally validated |
| Independent risk gates | `trading_bot/risk/service.py` + `core/immutable_shield.py` + governance — fail-closed; `directional_proposals=0` means risk never reached (by design) | implemented, untested live (no proposal survived) |
| Execution | `execution/service.py` → paper broker; 22 controlled tests (fills, costs, settlement, restart dedup, fault gates) | experimentally validated — AI-selected order path never exercised live |
| Outcome monitoring | `scripts/dashboard.py` (GET-only localhost, honest stale/fresh labels), audit_events, funnel counters | implemented+validated |
| Controlled improvement | RSI + signed `OperatorAuthorization` (Ed25519, DPAPI key custody); signed emergency reset (nonce-consumed, audit receipt) | tested |
| Governance | Operator CLI (pause/resume/flatten/cancel-all/estop/reset); signed approvals for promotion; no order-entry command by design | tested |

## Data-flow contract (typed)

obs dict → AdvisoryModuleAdapter.analyze(ctx: Mapping) → AgentArgument/
artifact payload → hypothesis branches → verifier terminal verdicts →
synthesis (EV = f(alignment_prior, cost)) → terminal decision row →
[risk→shield→governance→exec bus→paper broker] → audit_events +
snapshot.json → operator CLI / dashboard (read-only).

## What this architecture does NOT yet have

1. A verified edge — every candidate fails LCB/window/cross-venue.
2. Per-candidate simulator features — EV is a function of alignment
   alone; it cannot rank two proposals. (P3 backlog item.)
3. Live point-in-time L2 evidence accumulated over time — `hl_live`
   emits it but no historical L2 archive exists for backtesting.
4. Advisor-quality hygiene — recurring timeouts (hivemind_collective,
   deep_agent_market, analysis_market_intel) reduce electorate signal.

## Minimal next increments (dependency order)

P1 land multi_agent_rl fix verification in a live run (committed
`572a2aed`, unverified in production yet).
P2 run `hl_live` soak — first true point-in-time orderflow evidence.
P3 per-candidate sim features (EV discrimination).
P4 archive L2 books per bar → backtestable orderflow history.
