# Autonomous Financial Intelligence Infrastructure — Architecture & Gap Map

Status: **living document**, written 2026-11-11 against the current codebase
state. Describes the target architecture, what is already real, what is
stubbed, and the ordered critical path. Every claim of "works" below is
backed by a measured result this session, not by intent.

## 1. What the goal means operationally

An Autonomous Financial Intelligence Infrastructure is a system that:

1. **Acquires** market/economic data from many sources, continuously,
   and verifies each source itself.
2. **Researches** — forms questions, reads external knowledge (papers,
   repos, datasets), tests hypotheses against real data, and keeps an
   honest knowledge graph of what survived verification.
3. **Evaluates** candidate methods in sandboxes with real-cost models
   before they are trusted.
4. **Decides** under calibrated uncertainty — sized by evidence,
   abstaining when evidence says abstain.
5. **Acts** only through a safety spine (risk → immutable shield →
   human governance → execution) with signed operator authority for
   anything that changes behavior.
6. **Reports** — every layer leaves auditable provenance an operator
   can read.

"Autonomous" applies to layers 1–3 and 6. Layer 5's authority model is
deliberately not autonomous — that is load-bearing, not a gap.

Note (2026-11-12): `trading_bot/autonomous_financial_intelligence/` —
the package behind `AUTONOMOUS_FINANCIAL_INTELLIGENCE_README.md` — is
audited legacy and now ARCHIVED at
`trading_bot/_archive/autonomous_financial_intelligence/` (its one live
dependency, `LogicalVerifier`, was rescued to
`trading_bot/verification/logical_verifier.py`). Per-component
disposition is in `DOCS/AFI_PACKAGE_AUDIT.md`. Nothing in this document
depends on it.

## 2. Layer-by-layer state

### L0 — Safety & authority spine — PROVEN
`UnifiedTradingBot → CSC → risk → immutable_shield → governance →
decision bus → execution`. 100 real paper fills passed through it on
real market data. `ProtectedPathGuard` hashes the protected modules.
Promotion/strategy changes require signed `OperatorAuthorization`
(Ed25519). Do not weaken — everything else hangs off this.

### L1 — Calibration & honesty — PROVEN
Epistemic-uncertainty sizing, explore-budget cold-start escape,
measured-outcome feedback. Measured behavior: 50 bounded probes per
universe, ~40–50% win rate, then correct abstention. The system's
refusals are evidence-driven — verified, not assumed.

### L2 — Audit & observability — PROVEN (built this session)
`RESEARCH`/`RESEARCH_KG` audit events, `scripts/research_ledger.py`
(KG claim ledger from any state dir), `--research-log` live console
echo, `var/ecie/scout_ledger.jsonl`, `var/data_scout/ledger.jsonl`.
Missing piece: no single operator dashboard/report that aggregates
them — today they are separate tools.

### L3 — Data acquisition — PARTIAL (real, manual)
- Verified keyless sources (data_scout probes, measured live):
  binance spot+vision archives, kraken OHLC, coinbase candles,
  hyperliquid meta+L2, yahoo v8, coingecko, dukascopy ticks.
- Collectors exist: `collect_orderflow.py`, `collect_fx_ticks.py`,
  `stock_sync.py`; archive pulls proven at 9.4M trades.
- **Gap**: no standing/scheduled accrual; collectors are one-shots.
- **Gap**: no ingestion contract — each source lands in its own ad-hoc
  schema/db; no unified catalog of "what data do we have, covering
  what, from when to when."

### L4 — External knowledge intake — PARTIAL (real, gated)
- `scripts/internet_scout.py` drives real fetch (GitHub/arXiv/HF) →
  ECIE gates (classify/trust/license/security) → distill → compile →
  governance proposal. Verified end-to-end; one real repo reached
  `HUMAN_APPROVAL_REQUIRED`.
- Document path: papers/cards reach governance (no fake trust gate).
- **Gap**: `distill_pattern` is mechanical — strips imports, keeps
  prose. No semantic method extraction; a paper becomes a nearly-empty
  skill. Closing this is the difference between "reads the internet"
  and "learns from the internet."
- **Gap**: HF weights never downloaded (disk); dataset candidates are
  listed, not ingested.

### L5 — Hypothesis → evaluation loop — THE MISSING LINK
- Research engine can `evaluate_strategy` (positions vs baseline on
  real bar returns) and self-replicate claims out-of-sample via
  `replication_fn`. Verified machinery.
- **Gap**: nothing translates a distilled external method into the
  (positions, baseline, returns) triple that evaluate_strategy
  consumes. This is THE loop: knowledge → candidate → measured verdict
  → KG claim. Today knowledge enters the KG but executable candidates
  never form.
- **Gap**: scheduled `run_research_cycle` generates questions from
  internal uncertainty only; it does not consume scout output.

### L6 — Continuous orchestration — MISSING
Every capability is a manual one-shot. Infrastructure requires a
scheduler: nightly data pulls → scout sweeps on rotating queries →
research cycles → aggregated intelligence report. No such runner
exists (RSI sleep-cycle is improvement-scoped, not a general loop).

### L7 — Edge — THE REAL FRONTIER (honest)
Everything tested to date on public data at retail costs: ~0.
- Bar-close MR/momentum (M15/H1/H4), FX/crypto cross-lead,
  volume→direction, taker imbalance, funding: null.
- Crypto OFI: real microstructure (+0.5 corr @50-trade blocks) but
  ~0.7bps gross vs ~13bps cost; decays at scale (9.4M-trade test).
- Verified skill: vol-ratio forecasting (rv16 +0.43 OOS, transfers
  EURUSD→GBPUSD; JPY needs own weights) — a sizing/vol signal, not
  direction.
- Consequence: the infrastructure's honest output today is
  "no tradeable edge found" — correct, but the goal requires the
  discovery loop to actually produce candidates worth evaluating.

## 3. Critical path (ordered)

### M1 — Close the loop: method → candidate → verdict
The single highest-leverage build. Without it every other layer feeds
nothing.

Components:
a. **Method extraction** — from distilled patterns/papers produce a
   *spec*: hypothesis, signal definition, testable predictions,
   falsification criteria, required data. Either an LLM step (the
   cognitive engine exists; a local model or API-backed extractor)
   or a constrained template DSL that only emits allow-listed
   strategy families (mean_reversion/momentum/stat_arb — the only
   valid Level-1 candidate space anyway).
b. **Candidate compiler** — spec → concrete positions/baseline/
   returns mapping over local data → `csc.evaluate_strategy` /
   sandbox replay. Output must be a bounded numeric-parameter
   candidate, not free code.
c. **Ledger handoff** — verdict + confidence written as KG claim;
   replication auto-queued at DIFFERENT_DATASET (machinery exists).

Acceptance: feed the OFI paper → system emits a bounded OFI strategy
candidate → evaluated on the 9.4M-trade dataset → KG records verdict
with replication. Human sees the whole path in the ledger.

### M2 — Continuous operation runner
`scripts/autonomous_cycle.py` — scheduled, bounded, advisory:
data pulls (rotating verified sources) → scout sweeps (rotating query
queue) → N research cycles → aggregated daily report
(`var/reports/YYYYMMDD.md`) covering: what data accrued, what the
scouts found and where each candidate stopped, research verdicts,
open KG claims, and explicit "no edge found yet" honesty lines.
Runs under hermes env; every subprocess bounded; all writes auditable;
zero authority — it can only propose.

Acceptance: 24h unattended run produces a readable daily report with
real contents and no operator babysitting.

### M3 — Unified data catalog
`var/data_catalog.json` + writer in collectors: source, symbol set,
schema, coverage range, freshness timestamp, file/db pointer. Both
scouts and the paper_runner consume it — `--universe auto` should rank
from the catalog, not re-scan DBs. Cheap build, large payoff in
legibility.

### M4 — Operator surface
Aggregate L2 outputs: `scripts/intel_report.py` merging research
ledger + scout ledgers + run snapshots + catalog into one status
command. The daily report from M2 can be the same renderer.

### M5 — Edge program (research direction, gated by M1)
Once the loop exists, the queue of hypotheses that plausibly survive
costs — in rough order of information novelty:
1. **Cross-venue flow** (needs 2+ venues' L2/trades — binance+coinbase+
   kraken all verified reachable): venue-lead relationships, not
   single-venue OFI.
2. **Vol-regime strategies**: the one verified skill (rv16) mapped to
   structures that monetize vol directly (option-like overlays don't
   exist in spot — but vol-scaled mean reversion in measured range
   regimes is testable).
3. **HF dataset candidates** from data_scout search (e.g., L2 tick
   datasets) — new instruments where retail-cost dynamics differ.
4. **Funding/basis term structure** on perp venues (hyperliquid
   verified) — carry trades, not direction.
Each enters as a bounded candidate through M1 — never as tuned code.

## 4. Invariants that must survive every milestone

- No external artifact executes outside the sandbox; promotion needs
  `OperatorAuthorization`. Ever.
- Research/scout output is advisory — verdicts inform, never order.
- Cost model is part of evaluation: gross-edge claims are not
  candidates; net-of-cost claims are.
- Falsification is a first-class output — a daily report full of
  FALSIFIED claims is a working system, not a failing one.
- Fail-closed everywhere: fetch failures, parse failures, and empty
  results are recorded as facts, never patched over.

## 5. What "done" looks like

The infrastructure is real when an operator can read a daily report
that says: "acquired X records from N verified sources; scouts found K
candidates (3 rejected on security, 1 awaiting signature); the research
engine investigated M questions, verified i claims, falsified j,
replicated k; evaluated C strategy candidates against real data —
P showed net-positive expectation under the cost model" — and P is
occasionally nonzero *with reproducible evidence*. Everything up to
the last clause is engineering. The last clause is discovery — the
infrastructure's job is to make that search continuous, honest, and
cheap.
