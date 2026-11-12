# AFI Package Audit — `trading_bot/autonomous_financial_intelligence/`

Status: audit, written 2026-11-12. Scope: the 26-component package
behind `AUTONOMOUS_FINANCIAL_INTELLIGENCE_README.md` (v2.0.0, ~16k LOC,
33 files). Method: full wiring audit (git grep over tracked sources),
per-file reads of representative members of every subpackage, and
fabrication-marker sweep. Statuses use the repo vocabulary:
VERIFIED / VERIFIED_BOUNDED / UNPROVEN / RETIRED_BY_DESIGN /
FABRICATES.

## Verdict

**Quarantine the package; retire the README's claims.** The package is
real code — not stubs — but it is (a) unwired: the only live import is
`LogicalVerifier` types in `core/chainofthoughtreasoner.py`, behind a
try/except fallback; (b) unmeasured: no test file references it, no
accuracy/latency figure exists for any detector; (c) partially
fabricating: two modules invent "canonical" market data; (d) describing
a fictional API: every method the README documents
(`verify_and_approve_decision`, `initialize`,
`continuous_evolution_loop`, `run_evolution_cycle`,
`get_cumulative_metrics`, `get_comprehensive_statistics`) has **zero
matches** in the package — the orchestrators were rewritten down to
61/85-line facades.

The destination the README names is real, but it is reached through
the canonical path documented in `DOCS/AUTONOMOUS_FI_INFRASTRUCTURE.md`
(CSC → advisory → evidence ledger → RSI → OperatorAuthorization), not
through this package.

## Wiring audit (who actually imports it)

| Consumer | What it takes | Status |
|---|---|---|
| `core/chainofthoughtreasoner.py:24` | `ArgumentForm`, `LogicalVerifier`, `VerificationStatus` from `verified_reasoning.logical_verifier` | LIVE (soft dep, try/except) |
| `autonomous_superintelligence/verified_intelligence_integration.py` | `FinancialIntelligenceOrchestrator`, `EvidenceType` | QUARANTINED legacy; nothing imports it |
| `core/csc/advisory.py:6763` | catalog entry only | "legacy compat, no decision role" |
| `scripts/`, `tests/` | — | zero references |

## Per-layer findings

### evidence_verification/ — FABRICATES (partial)

- `data_canonicalizer.py:484-500` — `_fetch_canonical_price` returns
  `base_price + random.gauss(0, base*0.001)` from a hardcoded table
  (BTC 65000, ETH 3500, EURUSD 1.08…). "Canonical" Bloomberg/Reuters
  prices are invented. Any verification routed through this certifies
  data against fabrication — strictly worse than no verification.
- `evidence_provenance.py` — real HMAC-SHA256 provenance records and
  chains, but `_initialize_trusted_sources` hardcodes trust scores
  (`bloomberg: 0.99`) — asserted, not measured.
- `merkle_verifier.py`, `evidence_stake.py` — real hashing/staking
  machinery; single-operator "slashing" is theater; unwired.

### adversarial_verification/ — UNPROVEN

`ValidatorAgent` (697 LOC), `FormalProver` (698), `ClaimChallenger`
(775), `VerificationMarket` (705). Heuristic validators and an
in-process "bounty" ledger. No measured precision/recall; no external
challenger exists; unwired.

### governance_consensus/ — UNPROVEN (n=1 theater)

`ConsensusEngine` (597), `GovernanceToken` (808), `VotingContract`
(673), `DisputeResolution` (893). Genuinely structured voting/stake
code — but with one operator there is exactly one voter. The real
equivalents already exist and are stronger: Ed25519
`OperatorAuthorization`, hash-chained ledgers, `ProtectedPathGuard`.

### verified_reasoning/ — MIXED (one live piece)

- `logical_verifier.py` — real argument-form/fallacy checking; the
  ONLY live dependency (chain-of-thought reasoner). **KEEP** —
  candidate for extraction to a neutral module if the package is
  archived.
- `evidence_reasoner.py`, `citation_validator.py`,
  `uncertainty_quantifier.py` — plausible heuristics, unwired,
  unmeasured.

### anti_hallucination/ — FABRICATES (partial) + UNPROVEN

- `fact_checker.py:322-331` — `_get_canonical_numerical_value`
  returns hardcoded `simulated_prices` as canonical truth.
- `hallucination_detector.py` — real scoring pipeline, but detection
  = pattern matching against a hardcoded set of ~30 entities
  (`_initialize_known_entities`). "98% detection" in the README is
  unmeasured marketing.
- `confidence_calibrator.py`, `anomaly_detector.py` — unwired,
  unmeasured.

### self_improvement/ — UNPROVEN, superseded

`ExperimentRegistry` (612), `PromotionGates` (547), `RiskGovernance`
(602), `ComputeBudgetController` (579), `SelfImprovementEngine`
(655): substantial code, but `EvolutionOrchestrator` (rewritten to 85
lines) never calls them — it only iterates `register_gate` duck-typed
objects. The canonical RSI subsystem
(`trading_bot/recursive_self_improvement/`) does this job with an
evidence ledger, anti-gaming evaluator, protected-path guard, and
paired-replay promotion — strictly stronger.

### Orchestrators — REWRITTEN STUBS vs README

- `FinancialIntelligenceOrchestrator` — 61 lines: engine registry +
  start/stop/status. README's `initialize`,
  `verify_and_approve_decision`, `get_status`,
  `get_comprehensive_statistics` do not exist.
- `EvolutionOrchestrator` — 85 lines: trivial gate loop. README's
  7-phase cycle, experiment metrics, compute budgets, cumulative
  metrics do not exist.

## README audit

`AUTONOMOUS_FINANCIAL_INTELLIGENCE_README.md` is not merely
aspirational — it is **inaccurate about the code**: APIs, metrics
("+3-5% accuracy per cycle"), file tree, and component counts
describe a system that is not in the tree. Retitled status: STALE —
see the header notice added 2026-11-12 and this audit.

## Disposition

| Component | Status | Recommended action |
|---|---|---|
| `verified_reasoning/logical_verifier.py` | VERIFIED_BOUNDED (live dep) | Extract to `core/` neutral module, then archive package |
| All other 25 components | UNPROVEN / FABRICATES / theater | Move package to `_archive/` after `logical_verifier` extraction; keep git history |
| `AUTONOMOUS_FINANCIAL_INTELLIGENCE_README.md` | STALE | Header notice → this audit + `AUTONOMOUS_FI_INFRASTRUCTURE.md` |
| `autonomous_superintelligence/verified_intelligence_integration.py` | Already quarantined legacy | Unchanged — its AFI import dies with the archive move |

Non-negotiable before any archive move: confirm no live path imports
the package (verified above — only `chainofthoughtreasoner`, which
tolerates ImportError via its try/except, and the already-quarantined
integration module). Physical moves are an operator decision; this
audit recommends, it does not execute.

## What this means for the goal

"Autonomous Financial Intelligence Infrastructure" remains the
destination — `DOCS/AUTONOMOUS_FI_INFRASTRUCTURE.md` defines it
operationally (L0–L7) with an honest critical path (M1 method→candidate
loop, M2 continuous runner, M3 data catalog, M4 operator surface,
M5 edge program). This package was a parallel, unverifiable attempt at
the same brand. Retiring it concentrates effort on the path that
already produces measured results.
