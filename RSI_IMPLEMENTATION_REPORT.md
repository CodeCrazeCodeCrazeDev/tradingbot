# RSI Implementation Report — 2026-09-26

Mission: first-principles audit + implementation of a scientifically
controlled recursive self-improvement system for AlphaAlgo.

## Evidence ladder (mission §18)

| Claim level | Status |
|---|---|
| IMPLEMENTED | Yes — all components below exist and are wired |
| TESTED | Yes — 68 new tests + 19 pre-existing RSI tests pass |
| EMPIRICALLY IMPROVED | **No** — only synthetic planted fixtures; no real-market evidence is possible (1,000 EURUSD bars / 10 days) |
| FORWARD-VALIDATED | No — no forward data exists |
| PRODUCTION-READY | No — by design; promotion requires operator authorization path that does not exist in code |

## What was built

### Audit (mission §0)
- `scripts/rsi_reachability_inventory.py` — proves executable reachability via AST import-BFS from `main.py`/`bot_cli.py`/`unified_bot.py`/`foundation/runtime.py` + `git grep` importer census → `RSI_REACHABILITY_INVENTORY.json`.
- Classification: only `evolution_layer` (experience logging) and `governance/evolution_gate` (advisory, optimistic defaults — not an authority) are runtime-reachable. `ai_learner` is DEAD. `recursive_improvement.py`, `auto_optimizer.py`, `self_learning.py`, `optimization.py` are DEAD shadowed files (packages of the same name win). All others DISCONNECTED.
- Import-time `DeprecationWarning` shims added to 15 legacy modules + 3 shadowing packages; public APIs unchanged (tested).

### Level-1 RSI loop (mission §4, all inside the canonical package)
```
ObservationEngine -> RootCauseEngine -> HypothesisEngine (competing,
falsifiable) -> ExperimentPrioritizer (VOI proxy) -> CandidateGenerator
(1 bounded param) -> SandboxManager (deadline + ProtectedPathGuard)
-> IndependentVerifier (own Ed25519 key, own replay, dataset-hash bound)
-> MultiObjectiveEvaluator -> TransferEvaluator -> ParetoArchive
(hash-chained, lineage) -> append-only evidence ledger -> PromotionLadder
(signed operator authorization) -> ChampionRollback
```

- `contracts.py` — schema-2 signed improvement contract: 26 original gates + metric directions, Pareto objectives, regression budgets, economic materiality, regime panel, holdout query budget, recursion depth, protected paths, expiry. `assert_frozen` prevents mid-experiment criteria changes.
- `metric_registry.py` — every metric with unit and direction; contracts can't redefine directions.
- `candidate_adapters.py` — `mean_reversion{lookback,entry_threshold}`, `momentum{fast,slow}`, `stat_arb{lookback}` pairs. `VolatilityArbitrageStrategy` excluded: it can only emit `hold` without options implied-vol data — an honest limitation, not a bug.
- `evaluation/runner.py::PairedFamilyReplay` — causal replay (prior bars → next open→close, position-change turnover, explicit costs), multi-instrument and pair-spread aware.
- `multi_objective.py` — ordered gates: schema → provenance → cost/causality rows → instrument non-regression → anti-gaming → hard bounds → regression budgets → economic hurdle → Pareto → corrected paired bootstrap. Outcome space: `rejected | insufficient_evidence | eligible_for_operator_review`. **Never promotes.**
- `anti_gaming.py` — 7 checks (mission §11): foresight, cost floor, sample exclusion, risk hiding, turnover exploitation, regime cherry-pick, contract mutation.
- `multiplicity.py` — Bonferroni/Holm, block bootstrap with contract-derived seed, deflated Sharpe, PBO-CSCV; all return `None` when preconditions unmet.
- `archive.py` — append-only JSONL hash chain; roles champion/challenger/specialist/stepping_stone/failed_informative/ancestor; lineage walk; non-dominated frontier; parent sampling.
- `memory.py` — `evidence_ledger` now enforces append-only via SQL triggers (was convention-only before).
- `transfer.py` — LOCAL/ROBUST/TRANSFERABLE/SYSTEMIC ladder over regime×seed×cost panels; one-regime winners become `specialist`, never champion.
- `rollback.py::ChampionRollback` — deterministic `ChampionState` snapshots/restore; previous champions never deleted. Does not write live config.
- `scorecard.py` — mission §14 metrics computed only from archive+ledger.
- `meta_proposals.py` — L2/L3 genomes recorded and gated: `level_requires_out_of_band_authorization`; `max_recursion_depth` enforced.
- `protected_control_plane.py` — risk/shield/execution/evaluator/governance paths hashed before and after every sandbox run; drift = rejection + security event.
- `evaluation/synthetic_market.py` — seeded multi-regime OHLCV generator (planted oscillations create checkable edges); `SqliteSource` adapter for real data later.

### Not done (explicit non-goals for this milestone)
- Code-diff/model/RL candidates; real-data ingestion; container/process sandbox isolation; external verifier service; live/paper config mutation. `walk_forward.py` remains unpaired diagnostic.
- L2/L3 execution — measured via scorecard + gated proposals only.

## Tests (mission §17)

`tests/rsi/` — 68 tests, ~36s (package import dominates). Every §17 bullet is covered:

profitable-but-riskier reject · overfit/insignificant reject · future-leakage reject · unrealistic-cost reject · one-regime catastrophic-failure → reject or constrained specialist · Pareto improvement → eligible (never promoted) · evaluator manipulation fail · holdout budget/attestation · risk-constraint self-modification reject · failed experiments retained · rollback restores champion · lineage preserved · reproducibility · interrupted sandbox safe · budget exhaustion terminates · production requires signed authorization · meta levels gated · legacy shims warn.

`tests/foundation/test_rsi_*` + `tests/recursive_self_improvement` — 19/19 pass unchanged. `tests/recursive_improvement`/`eternal_evolution` — green through shims.

## Benchmark (engineering machinery only)

`python scripts/rsi_synthetic_benchmark.py --seeds 3` → `ABLATION_RSI_SYNTHETIC.json`:

| Arm | eligible | rejected | insufficient |
|---|---|---|---|
| planted edge (12 candidates) | 3 | 0 | 9 |
| pure noise (12 candidates) | **0** | 5 | 7 |

Zero false-eligible on noise; planted-edge candidates detected; correct
`insufficient_evidence` for no-effect parameters. This is machinery
validation, not alpha.

## Exact verification commands

```bash
python scripts/rsi_reachability_inventory.py
python -m pytest tests/rsi -q --no-cov -p no:cacheprovider
python -m pytest tests/foundation/test_rsi_evidence.py tests/foundation/test_rsi_loop.py tests/foundation/test_rsi_replay_causality.py tests/foundation/test_walk_forward_runner.py tests/recursive_self_improvement -q --no-cov
python scripts/rsi_synthetic_benchmark.py --seeds 20
python -m compileall -q trading_bot/recursive_self_improvement trading_bot/evaluation
```

## Remaining technical debt

- Real-market evaluation requires multi-instrument history + sealed holdout + operator-held contract keys (none exist).
- Sandbox is thread-deadline in-process, not a container.
- Verifier key is in-process; production needs external custody.
- `improvement_genome.EvaluationEvidence` still carries a scalar `score` field (legacy compat).
- ~9,800 Python files remain unaudited line-by-line; the inventory is import-reachability-based.
