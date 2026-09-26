# RSI current-state audit

Verified against the active tree on 2026-09-25. This is an audit of executable paths, not an endorsement of architecture claims. The repository also contains concurrent unrelated uncommitted edits; they are not RSI evidence.

## Actual runtime path and ownership

```text
main.py:91-112 → UnifiedTradingBot.start/run_cycle (unified_bot.py:88-199,329-379)
  → market-data normalizer → CognitiveSystemController.process_market_observation
  → canonical risk service / ImmutableShield → decision bus → paper execution service
  → optional evolution_layer.record_trade_experience (experience only)
```
`main.py` does not instantiate either RSI engine. `unified_bot.py:238-249` creates the optional evolution service and `:369-378` records observations/decisions; this is not independent improvement validation. The CSC holds an EvolutionGate (`core/csc/controller.py:163-176`) but its separate `execute_self_improvement_loop` (`:457-481`) reports `promoted=True` solely on an impact/confidence/cost heuristic. This path must be treated as an advisory stub, not promotion authority; review every caller before changing it. `foundation/legacy_convergence.py:45-59` labels `rsi_loop.py` canonical research, but that classification is metadata, not evidence of runtime wiring.

| Area | Executable evidence | Assessment / disposition |
|---|---|---|
| Bounded candidate coordinator | `recursive_self_improvement/rsi_loop.py:75-149` supports capped candidates, fail-closed missing approver by default, optional rollback. `:169-184` trusts evaluator callback dictionaries including booleans and user-supplied metrics. | Implemented but not runtime-wired. Reuse coordinator/genome contracts; forbid reviewer bypass and any promoter mutation in first slice. |
| Candidate provenance | `improvement_genome.py:53-84` immutable dataclass with fingerprint including creation time, parent, evaluation plan; `:87-139` has scalar score-based evidence/approved status. | Partial; no immutable evaluation-contract binding or trial accounting. |
| Legacy RSI engine | `engine.py:29-54` calls ExperimentManager then deploys on scalar `is_improved`. `:110-168` optional governance, snapshot, `_apply_configuration` returns True without applying. | Unsafe callable disconnected from main runtime. Keep import compatibility but disable deployment authorization. |
| Experiment/evaluator | `experiment_manager.py:32-100` persists experiment, injects arbitrary metrics runner and defaults `promotion_eligible=True`; synthetic fallback explicitly nonpromotable at `:103-122`. `evaluation.py:19-64` arbitrary weighted scalar; `:91-106` unpaired IID t-test. | Scientifically invalid for approval. Retain diagnostics, require independent typed evidence and paired dependent-time-series tests. |
| Replay runner | `evaluation/runner.py:26-50` passes params to evaluator constructor, labels total return as `sharpe_ratio`, declares promotion eligibility. | Cannot prove parameters altered a strategy. Remove incorrect metric and automatic eligibility. |
| Walk-forward | `evaluation/walk_forward.py:101-240` uses one instrument/split, stop and close-price fills, 1% fractional equity, no fees/spread/impact, calibrates using test outcomes `:214-239`, trades can overlap at horizon. | Useful diagnostic only; not sealed holdout or transfer evidence. Needs causality, realistic costs, paired baseline/candidate series and frozen test calibration. |
| Governance | `governance/evolution_gate.py:97-131` invents optimistic defaults for missing metrics; `:232-250` red team checks supplied behavior map, `:354-367` logs `PROMOTED` without external approval. `recursive_self_improvement/governance_bridge.py:42-53` refuses some critical domains but has no real approval request. | Do not make it the sole authority for RSI. Risk service and shield remain separate immutable runtime vetoes. |
| Memory/rollback | `memory.py:21-153` SQLite records pending/failed experiments and deployments; no immutable history, dataset hash, trial count or verified provenance. `rollback.py:47-79` returns snapshot data but does not restore production. | Reuse SQLite for offline failure ledger, never call it proof of deployed rollback. |
| Duplicates | `recursive_improvement/__init__.py:55-68` has a start/stop stub; `recursive_improvement/recursive_core.py:190-267` counts cycles but no credible acceptance. `recursive_self_improvement/loops/specialized_loops.py:17-201` hard-codes performance figures. `evolution_layer/orchestrator.py:23-105` is a service/experience facade. | Preserve compatibility, quarantine only after separate reachability analysis; never add a new independent RSI authority. |
| Strategy boundary | `strategies/registry.py:23-68` registers signal-only strategies, no sizing/ordering. `strategies/institutional_strategies.py:25-75` has a concrete mean-reversion lookback affecting signals. | Bounded diagnostic candidate adapter exists; it is not the CSC production strategy and cannot move capital. |
| Self-play/RL | `core_agent_system/self_play_loop.py:330-436` replays historical data, `:750-807` judges against mean outcomes of previously replayed games and updates in-process best policy/version without independent OOS/cost-adjusted comparison. | Implemented but distinct/disconnected from main RSI authority; do not accept as production promotion evidence. Training on own signals risks self-confirmation. |
| Evolution service | `evolution_layer/orchestrator.py:23-105` optionally instantiated in `unified_bot.py:238-249` and collects experiences; `evolver.py:210-241` accepts an arbitrary approver string and `:278+` applies provided callback after approval state. | Runtime-connected experience collection, but governance claims depend on external caller. Treat as advisory/proposal, never alternate RSI promotion gate. |
| Backtesting/monitoring | `backtesting/replay.py:22-59` splits by simple ratios, `:65-89` estimates spreads heuristically; execution service provides submit/cancel/status/reconcile (`execution/service.py:354-386`). | Neither ratio split nor heuristic spread is a sealed holdout/actual fill. Instrument, venue, time and broker-quality evidence still required. |
| Tests | `tests/foundation/test_rsi_loop.py:23-99` promotes from fake callback metrics with a true approver; `tests/foundation/test_walk_forward_runner.py:10-31` asserts false Sharpe/eligibility indirectly; `tests/recursive_self_improvement/test_rsi_system.py:77-87` expects a mock deployment. | Replace unsafe assertions with fail-closed/causality tests; don't count test fixture numbers as economic proof. |

## Threats and unresolved checks

The current EURUSD-only replay cannot demonstrate cross-instrument/regime transfer, realistic cost/capacity, a sealed untouched holdout or statistical significance. Dynamic imports and independent scripts in the huge legacy tree may create additional disconnected RSI paths; inventory by executable call site and tests, not filename count. Cross-reference `RSI_THREAT_MODEL.md`. Production decisions must continue to pass `risk/service.py`, `core/immutable_shield.py`, `execution/service.py` and human approval policy; this project will not reconfigure them. No evidence presently supports a claim that any self-modification has improved live performance.

## Post-audit first-slice status
After this initial audit, `evaluation/runner.py` was made diagnostic-only and its false Sharpe alias removed; `walk_forward.py` delays training outcome feedback until the exit horizon and freezes test updates. `recursive_self_improvement/evaluation.py` now validates operator/verifier-signed paired net-return envelopes against explicit thresholds; tests use generated keys only. `rsi_loop.py` emits review-only decisions and rejects missing durable ledger/signatures. Legacy `engine.py` deployment returns False and CSC's triage no longer asserts promotion. These are engineering safeguards, **not** operator-backed or live economic validation. A separate `BoundedMeanReversionReplay` now exercises a real bounded mean-reversion lookback parameter on prior-bar signals with next-bar open/close arithmetic and explicit turnover costs, but labels its output unsealed and nonpromotable. The old cognitive replay still lacks real fills; neither path has a point-in-time externally sealed holdout or an operator-verified candidate strategy attestation.

## 2026-09-26 verification — executable reachability proof

Generated by `scripts/rsi_reachability_inventory.py` (AST import-BFS from `main.py`, `bot_cli.py`, `unified_bot.py`, `foundation/runtime.py`; importers via `git grep`). Raw data: `RSI_REACHABILITY_INVENTORY.json`. This section classifies by **executable reachability**, not by filename.

| Module | Classification | Runtime-reachable | Importers |
|---|---|---|---|
| `trading_bot.evolution_layer` | ACTIVE (experience service only — not an improvement authority) | yes | 10 |
| `trading_bot.governance.evolution_gate` | ACTIVE (advisory stub; optimistic defaults; not a promotion authority) | yes | 0 (injected) |
| `trading_bot.recursive_self_improvement` | DISCONNECTED (canonical research package; runs via tests/experiments only) | no | 4 |
| `trading_bot.evaluation` | DISCONNECTED (diagnostic replay) | no | 3 |
| `trading_bot.recursive_improvement` | DISCONNECTED duplicate (parallel "RSIE": own approvals/validation/loops) | no | 7 |
| `trading_bot.eternal_evolution` | DISCONNECTED duplicate | no | 7 |
| `trading_bot.alpha_evolve` | DISCONNECTED duplicate | no | 7 |
| `trading_bot.autonomous_learner` | DISCONNECTED | no | 4 |
| `trading_bot.adaptive_systems` | DISCONNECTED (large; importers are themselves disconnected) | no | 23 |
| `trading_bot.meta_learning` | DISCONNECTED | no | 3 |
| `trading_bot.optimization` | DISCONNECTED | no | 4 |
| `trading_bot.self_learning` | DISCONNECTED | no | 4 |
| `trading_bot.auto_optimizer` | DISCONNECTED | no | 6 |
| `trading_bot.performance_optimizer` | DISCONNECTED | no | 2 |
| `trading_bot.auto_rollback` | DISCONNECTED | no | 1 |
| `trading_bot.code_evolver` | DISCONNECTED | no | 1 |
| `trading_bot.continual_learner` | DISCONNECTED | no | 1 |
| `trading_bot.experiment_tracker` | DISCONNECTED | no | 1 |
| `trading_bot.ai_learner` | DEAD (zero importers) | no | 0 |
| `trading_bot/recursive_improvement.py` | DEAD — shadowed by the `recursive_improvement/` package and can never be imported | no | 0 |

Notes:
- The only runtime-reachable "evolution" component is `evolution_layer`, which records trade experiences; it neither proposes nor evaluates modifications. `evolution_gate` is constructed in `unified_bot.py` but only receives observations; it still invents optimistic defaults for missing metrics and must never be the sole RSI authority.
- Every DISCONNECTED legacy subsystem keeps its import API; import-time `DeprecationWarning` shims were added pointing at `trading_bot.recursive_self_improvement` as the canonical research RSI. Nothing was moved or deleted; `tests/recursive_improvement/` and `tests/eternal_evolution/` continue to exercise those packages' own logic.
- `main.py` still does not instantiate any RSI engine; RSI remains research-only by design until operator-controlled contract custody and an external holdout exist.
- Data constraint unchanged and now hard-verified: `market_data.db` holds only 1,000 EURUSD bars (2026-06-04 → 2026-06-14). No multi-instrument/multi-regime claim can be made on real data; all v2 evaluation evidence is synthetic-fixture engineering evidence.
