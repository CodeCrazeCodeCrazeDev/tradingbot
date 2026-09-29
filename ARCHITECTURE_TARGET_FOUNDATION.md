# AlphaAlgo Target Foundation Architecture

Status: design + baseline audit. This document is the architecture contract for
converging AlphaAlgo onto a single production authority. It does not claim the
runtime already matches the design — the "Current state" section lists what is
verified implemented, partially implemented, and not implemented.

Generated: 2026-09-29 from a read-only baseline audit of the worktree.

## 1. Core rule

`ModularMonolithRuntime` is the public application boundary and delegates
lifecycle and observations to `UnifiedTradingBot`. `UnifiedTradingBot` is the
sole composed trading runtime. There is no parallel production orchestrator,
trading loop, component registry, decision bus, risk/sizing authority,
execution authority, or trading-state repository.

Registration in `UnifiedComponentRegistry` is NOT permission to run or
transact. Production permissions attach to a composition-time capability
manifest, not to `registry.register(...)` calls.

## 2. Target authority path

```text
CLI/API/ops (read-only projections or typed observation submission)
  -> ModularMonolithRuntime            public lifecycle facade, no decisions
  -> UnifiedTradingBot                 sole composition + loop + allow-list
      -> MarketDataAdapter -> MarketDataNormalizer -> MarketEvent(quality, provenance)
      -> StrategyPort / AgentCapabilityPort        advice only
      -> CognitiveSystemController                 strategic DecisionProposal
          -> AlphaAlgoCognitiveBrain               tactical evidence ONLY (opt-in)
          -> HMS / world model / skills / hypotheses / verification
      -> SqliteTradingRepository.snapshot + venue state freshness
      -> CanonicalRiskService            sole RiskDecision + approved_quantity
      -> GovernanceGate                  policy-required human approval
      -> ImmutableShield                 final explicit affirmative veto
      -> UnifiedDecisionBus              ordered decision/audit log
      -> CanonicalExecutionService -> PaperBrokerAdapter | approved BrokerAdapter
      -> SqliteTradingRepository         orders/fills/positions/audit/reconciliation
      -> interfaces/read_models          health, dashboard, reporting, notifications

OFFLINE ONLY: data custody -> walk-forward/paired replay -> independently signed
RSI evidence -> external human operator review -> separately staged config.
Research never calls runtime execution, broker adapters, or self-deploys.
```

### Authority matrix (production permissions)

| Owner | start loop | broker/order | risk & sizing | write trading state | promote research |
|---|---|---|---|---|---|
| ModularMonolithRuntime | delegate only | N | N | N | N |
| UnifiedTradingBot | Y (one) | via exec svc only | N | via repo only | N |
| CognitiveSystemController | N (per cycle) | N | proposes only | N | N |
| AlphaAlgoCognitiveBrain, strategies, AI, world model | N | N | N (advisory/veto) | N | N |
| CanonicalRiskService | N | N | Y | N | N |
| HumanApprovalPolicy | N | N | approve/deny required actions, not size | audit via repo | operator action only |
| ImmutableShield | N | N | final veto | audit via repo | N |
| UnifiedDecisionBus | N (infra worker) | N | N | audit via repo | N |
| UnifiedComponentRegistry | N | N | N | N | N |
| CanonicalExecutionService | N | Y (validated intent) | N | via repo only | N |
| Paper/approved BrokerAdapter | N | Y (service-bound) | N | N | N |
| SqliteTradingRepository | N | N | N | Y | N |
| RSI / backtesting / research | offline bounded worker | N | N | research ledger only | N |
| Interfaces, telemetry, credentials | N | N | N | read-only projections | N |

## 3. Bounded contexts and typed contracts

Contracts: `trading_bot/foundation/contracts.py` (Instrument, MarketEvent,
Signal, DecisionProposal, RiskDecision, ApprovalDecision, OrderRequest,
ExecutionReport, Fill, ReconciliationResult, AuditEvent, PortfolioSnapshot,
RiskState). Ports: `trading_bot/foundation/ports.py`.

| Family | Canonical owner | Typed boundary | Default disposition of legacy members |
|---|---|---|---|
| Orchestration, registries, buses, entry points | `foundation/runtime.py` -> `unified_bot.py`; `core/csc/controller.py`; `core/unified_registry.py`; `core/unified_event_bus.py` | ComponentLifecycle; LogAction/UnifiedEvent; DecisionProposal | one-wave facade delegating to `ModularMonolithRuntime`, else quarantine |
| Data feeds, connectivity, normalization | `data/normalizer.py`; `data/adapters.py` | `MarketDataAdapter` -> `MarketEvent` | adapter behind `LegacyMarketDataAdapter`; unproven feeds off-graph |
| Strategies, alpha, portfolios, positions | `strategies/{adapter,registry}.py`; repository owns position truth | `StrategyPort` -> `Signal`; `TradingRepository` | signal-only adapters; competing ledgers -> read-only projection or quarantine |
| AI, agents, models, cognition | `core/csc/controller.py` (strategic); `cognition/orchestrator.py` (tactical, off-graph until adapted); `foundation/capability_registry.py` | `AgentCapabilityPort`, `WorldModelPort` | advisory capability adapters; unverified models/agents quarantined |
| Risk, sizing, safety, governance | `risk/service.py`; `core/immutable_shield.py`; `governance/policy_adapter.py` | `RiskService`, subordinate `RiskPolicy` veto, `GovernanceGate` | veto-only `LegacyRiskPolicyAdapter`; managers are facades |
| Execution, brokers, reconciliation | `execution/service.py`; `brokers/adapter_bridge.py` | `ExecutionService`, `BrokerAdapter` | paper adapter default; legacy brokers behind `FoundationBrokerAdapter`, opt-in, no silent paper fallback |
| Research, backtesting, RSI | `recursive_self_improvement/` (canonical package); `evaluation/runner.py` | `ResearchCapability` -> signed evidence | research_only; legacy duplicates emit DeprecationWarnings, no authority |
| APIs, CLIs, dashboards, reporting | `main.py`; `interfaces/{read_models,adapters}.py` | runtime facade; read-only projections | facade or quarantine; queries cannot reach mutable internals |
| Telemetry, health, audit, config, credentials | `telemetry/`; `security/credential_vault.py`; `persistence/repositories.py` | health/audit projections; credential provider to broker adapters only | passive adapters; vault needs review before use |

## 4. Component-disposition method (per-file coverage)

`ARCHITECTURE_LEGACY_CLASSIFICATION.json` is the per-file index (3,163 rows,
keyed by repo-relative `path`). `ARCHITECTURE_WAVE_INVENTORY.md` renders it by
heuristic wave. Neither alone grants production eligibility. The joined
disposition record per file must add:

- `actual_import_sites:line` and `dynamic_import_edges` (AST misses
  `importlib`, `__import__`, plugin registries, config-driven loading).
- `actual_capital_receiver` for every `direct_capital_path` flag (in-memory
  simulator vs live broker call).
- `bounded_context`, `canonical_owner`, `contract`, `disposition`, the six
  production permissions, `target_delegate`, `migration_action`, `tests`,
  `acceptance_gate`, `reviewer`, `evidence_status`.

Classification precedence: explicit reviewed override > canonical path >
proven compatibility facade > proven non-network adapter > bounded research >
quarantined. Unmatched or ambiguous rows are `quarantined/unreviewed` with no
runtime permission. `archive_candidate` is a future cleanup proposal — never
deletion without separate approval.

### Baseline audit findings (2026-09-29, read-only)

- Manifest staleness: the classification manifest contains 3,163 rows but the
  live `trading_bot/` tree has 3,162 non-excluded `.py` files. 23 manifest
  paths no longer exist (e.g. flat `trading_bot/research/*.py` files moved to
  `research/{alpha,core,data,discovery,experimentation,governance,orchestration}/`),
  and 23 on-disk files are unscanned (`trading_bot/main.py`,
  `trading_bot/self_mastery/mastery_orchestrator.py`,
  `trading_bot/services/mtash_service.py`, and the 19 moved research modules).
  The manifest must be regenerated on a frozen snapshot before Wave gates are
  measured; `LEGACY_CONVERGENCE_REPORT.md` still reports 3,159.
- Uncovered executable surfaces: the scanner walks only `trading_bot/` and
  seeds only root `main.py`. Scanning the 281 uncovered `.py` files
  (32 root-level, 235 `scripts/`, 7 `perfect_bot/`, 7
  `SCIENTIFIC_FOUNDATION_V5/`) with the same AST rules found:
  - 17 files with capital-call markers, including `main_original.py`
    (`execute_trade` at lines ~1924/1930/2934/2943),
    `scripts/launchers/run_paper_trading.py` (`broker.place_order` at 169/179),
    `scripts/launchers/integrated_trading_system.py`,
    `scripts/launchers/run_alphaalgo_complete.py` (673),
    `perfect_bot/perfect_bot.py`.
  - 27 loop/worker starters, including `install_service.py`,
    `autonomous_superintelligence_launcher.py`,
    `scripts/deployment/deploy_5star_production.py`,
    `scripts/launchers/{production_runner,run_production_system,
    run_trading_system,RUN_SAFE_TRADING_BOT}.py`,
    `scripts/utilities/{watchdog,system_supervisor,
    fully_automated_system}.py`.
  - `scripts/launchers/run_live_trading.py` is a standalone live-money runner
    importing `MT5BrokerAdapter` directly (`:36-42`) with `connect()`,
    `get_account_equity()`, `get_positions()`, `close_position()` calls
    (`:182-312`) — a parallel capital path outside every gate.
  - 242 files have `__main__` blocks — mostly benign CLIs, but they prove Wave
    7's single row (`trading_bot/unified_main.py`) massively undercounts
    interface surfaces.
- Until these surfaces are individually reviewed, they are all
  `quarantined/unreviewed`: not importable into the production graph, not
  counted as "accounted for."

## 5. Runtime lifecycle, trading cycle, and failure flow

### Boot

Refuse any mode outside `{"paper","analysis"}` (implemented,
`unified_bot.py:86-94`). On start: open `SqliteTradingRepository`, recover
pending orders (mark `UNKNOWN`, reconcile before new entries), start the one
`UnifiedDecisionBus`, configure the singleton `ImmutableShield`, instantiate
world model/HMS/skill router/verification, `CanonicalRiskService`, canonical
execution service on `PaperBrokerAdapter`, `PaperExecutionBridge`, then the
CSC. Runtime registers read-only interface projections (`runtime.py:28-58`).
Modules not on the profile allow-list are never instantiated.

### Trading cycle (target)

1. Observation -> `MarketDataNormalizer` -> `MarketEvent` (quality,
   provenance, correlation id). Invalid/stale -> reject before cognition
   (partially implemented: `unified_bot.py:348-365` builds the event but passes
   the raw dict onward — the event is not the payload of record).
2. Optional strategy/capability advice -> `Signal[]` marked advisory
   (`unified_bot.py:380-389`, tested `test_runtime_data_boundary.py:50-74`).
3. Human pre-gate (`trading_allowed`) — implemented fail-closed
   (`unified_bot.py:296-312`).
4. CSC 12-stage pipeline -> decision proposal (`core/csc/controller.py:762-817`).
5. Canonical risk evaluation -> `RiskDecision` with `approved_quantity`
   (`controller.py` `_stage_risk_check`, `risk/service.py:110-147`); the
   proposal quantity is clamped to `approved_quantity`.
6. Policy-required human approval via `GovernanceGate`
   (`controller.py` `_stage_governance`, `governance/policy_adapter.py`),
   fail-closed when the gate is missing or denies; the `audit_id` receipt is
   bound to the proposal.
7. ImmutableShield validation (`controller.py:706-719`) AND bus voter
   consensus requiring an explicit affirmative shield report for
   `TRADE_EXECUTION` (`unified_event_bus.py:496-531`) — implemented.
8. `TRADE_EXECUTION` -> `PaperExecutionBridge` -> `CanonicalExecutionService`
   -> adapter; order persisted before adapter call, execution report persisted
   after (`execution/service.py:359-370` — write-before-call is correct).
9. Fills -> typed positions in repository (`repositories.py:113-166`);
   reconciliation `matched` required before further entries.
10. Read-only projections expose health/portfolio/report.

### Fail-closed failure flow

| Failure | Required behavior |
|---|---|
| Invalid/stale/unprovenanced data | reject before cognition; no exception swallowing into "hold" |
| Risk service absent/error | veto (bus fails closed too) |
| Required human gate unavailable | deny; never treat absence as consent |
| Shield missing/non-affirmative/timeout | veto (implemented at bus `unified_event_bus.py:411-421,506-531`) |
| Repository/audit write failure | mark order UNKNOWN, halt new entries, reconcile — do NOT blind-retry |
| Broker status ambiguous after submit | hold pending, reconcile, no duplicate submit |
| Reconciliation mismatch | no new entries until resolved |
| Execution handler failure | action FAILED not APPROVED (implemented `unified_event_bus.py:533-555`) |

### Known gaps against the target (verified)

- ~~CSC calls `risk_engine.evaluate_action` but never checks
  `approved_quantity` bounds downstream, and has no GovernanceGate stage~~
  RESOLVED 2026-09-29: `_stage_governance` runs after risk and before the
  LogAct proposal, fail-closed on missing/denying gates, binding the
  `ApprovalDecision.audit_id` into the proposal; `_stage_risk_check` now
  clamps `quantity` to `RiskDecision.approved_quantity`. CSC is outside the
  protected-path list so no protected file was modified. Residual: the
  default `HumanApprovalGate.ACTION_LEVELS` marks `execute_trade` AUTO — the
  gate is consulted and can deny, but its frozen policy does not require a
  human wait for ordinary trades; tightening which actions require approval
  is a policy decision for the operator.
- ~~`CanonicalRiskService.evaluate_action` fabricates `equity=1.0`,
  `exposure=0.0` defaults~~ RESOLVED 2026-09-29:
  `CanonicalRiskService(state_provider=...)` merges an authoritative
  `PortfolioStateProvider` (`risk/state_provider.py`) that derives cash,
  equity, exposure, open positions, daily PnL, and drawdown from persisted
  fills/positions (`repositories.list_fills()` + `snapshot()`); provider
  failure fails closed (`portfolio_state_available` veto). `unified_bot.py`
  wires the provider over `SqliteTradingRepository` with
  `config["initial_equity"]` (default 10,000). Without a provider the legacy
  dict path remains for compatibility. Residual: drawdown peak is
  session-scoped and unmarked positions fall back to cost basis until a
  venue mark feed exists.
- `UnifiedDecisionBus` auto-starts when a proposal arrives while stopped
  (`unified_event_bus.py:311-313`) and treats audit-file write failure as a
  logged error (`:489-494`) — audit durability is best-effort, not fail-closed.
- `PaperExecutionBridge` keeps its own JSONL ledger + positions dict parallel
  to `SqliteTradingRepository` and has a no-service fallback path that fills
  without the canonical service (`execution_bridge.py:102-216`).
- `SqliteTradingRepository.snapshot` returns `equity=0.0, cash=0.0`
  (`repositories.py:202`) — portfolio state is positions-only.
- `AlphaAlgoCognitiveBrain.process_cycle` returns `authorized_action`/
  `authorized_size` from its own `RiskGatekeeper` (`cognition/orchestrator.py
  :144-179`) and is not invoked by the CSC — per decision it stays off-graph
  until wrapped advisory-only.
- `SecureCredentialVault` has a broken `rotate_key` (`security/
  credential_vault.py:176-185` writes to a closed handle after `with` exits)
  and stores the Fernet key at `~/.trading_bot_key` — acceptable only for
  paper; credential custody must be re-verified before any non-paper profile.

## 6. Research / RSI separation

Canonical package: `trading_bot/recursive_self_improvement/`. Legacy duplicates
(`recursive_improvement/`, `eternal_evolution/`, `alpha_evolve/`,
`autonomous_learner/`, `adaptive_systems/`, `meta_learning/`, root
`code_evolver.py`, `auto_optimizer.py`, `auto_rollback.py`,
`continual_learner.py`, `self_learning.py`, `ai_learner.py`,
`experiment_tracker.py`, `optimization.py`, `performance_optimizer.py`) emit
DeprecationWarnings and carry no improvement authority.

Evidence chain: candidate adapter allows exactly one bounded numeric parameter
on `mean_reversion`/`momentum`/`stat_arb` (`candidate_adapters.py:105-131`) ->
chronological/paired replay (`evaluation/runner.py`) -> signed contract +
signed report under independent Ed25519 anchors -> `EvaluationEngine.
evaluate_verified` (`recursive_self_improvement/evaluation.py:130-310`) ->
`eligible_for_operator_review` only (never `promotion_eligible=True`) ->
durable hash-chained `ParetoArchive` -> explicit human staging. Synthetic,
random, self-play, or unsealed replay output is diagnostic-only by contract
(`runner.py:12-53,230-235`; `experiment_manager.py:55-69`).

Current hard limit: `market_data.db` holds EURUSD 1,000 bars only; the
evaluator requires `min_instruments >= 2` (`evaluation.py:217-259`), so no
promotion-eligible evidence can exist today — this must be enforced as an
acceptance gate, not worked around.

## 7. Deployment profiles

| Profile | Feed | Adapter | Status |
|---|---|---|---|
| `analysis` | replay / labeled synthetic | none executes | implemented; kill switch verified |
| `paper` | normalized observation source | `PaperBrokerAdapter` via service | startup implemented; approval-ordering gate partial |
| `testnet` (future) | explicit sandbox endpoints + separate credentials | vetted `BrokerAdapter` | **disabled**; requires conformance + human approval |
| `live` (future) | explicit config + credential custody | vetted approved adapter | **disabled**; never activated by convergence work |

`main.py:98-132` exposes only paper/analysis. Any launcher advertising live
modes (`scripts/launchers/run_live_trading.py`, `production_runner.py`, etc.)
is not a supported entry point and is quarantined pending review. No silent
paper fallback is allowed from any requested non-paper mode.

## 8. Waves 1-7 roadmap

Wave 0 (this audit) is re-baselining, not a migration wave.

- **Wave 0 — inventory repair** (APPLIED 2026-09-29): manifest regenerated on
  the live tree — 3,162 modules reconciled with disk; scanner extended with an
  `external_surfaces` section (281 root/scripts/`perfect_bot`/
  `SCIENTIFIC_FOUNDATION_V5` files: 19 capital-call surfaces quarantined, 27
  loop starters, `cli_entrypoint` tags), `dynamic_import` tags (30 modules),
  and `close_position` in the capital marker set. Remaining gap: per-file
  manual review of the 19 capital + 27 loop surfaces and the 30
  dynamic-import modules.
- **Wave 1 — composition/facades** (partially applied): facades already in
  place for `alphaalgo_orchestrator.py`, `master_integration.py`,
  `unified_main.py`, `api.py`, `core/{event_bus,service_registry}.py`,
  `registry/`, `orchestration/master_orchestrator.py`. Applied 2026-09-29:
  `sentient_core/sentient_orchestrator.py` (real class quarantined as
  `_LegacySentientOrchestrator`, public name is now a `ModularMonolithRuntime`
  facade; sizing/trade queries fail closed), `recursive_improvement/
  orchestrator.py` (facade with `_QuarantinedLoopStub`s — the file-watcher
  auto-deploy path cannot start), `orchestration/service_managers.py`
  (background health loop disabled), `orchestration/event_bus.py` (rejects
  TRADE_/ORDER_/EXECUTION_/BROKER_/RISK_ events), `ingestion/orchestrator.py`
  (standalone `main()` disabled). Remaining: the ~55 other
  facade/authority candidates in Wave 1 plus per-surface review.
- **Wave 2 — risk/governance** (partially applied): `LegacyRiskPolicyAdapter`
  + `HumanApprovalPolicy` already exist and fail closed. Applied 2026-09-29:
  `risk/MASTER_risk_manager.py` now warns and is explicitly a legacy analyzer
  (was misclassified `compatibility_facade` while performing real sizing and
  `mt5.account_info()` calls). APPLIED 2026-09-29: CSC now runs risk ->
  governance -> shield -> bus ordering (`controller.py` `_stage_risk_check`
  clamps `approved_quantity`; new `_stage_governance` is fail-closed and binds
  the approval `audit_id`). APPLIED 2026-09-29 with explicit approval:
  `risk/service.py` gained `state_provider` merging + fail-closed semantics,
  `unified_bot.py` wires `PortfolioStateProvider` (`risk/state_provider.py`)
  over `SqliteTradingRepository` (`list_fills()` added) — real
  equity/exposure/open-positions now reach `evaluate_action`. Wave-1
  surface hardening applied: entry guards refuse `install_service.py`,
  `run_live_trading.py`, `real_data_trading_bot.py`, `production_runner.py`,
  `deploy_5star_production.py`, `run_paper_trading.py`,
  `run_alphaalgo_complete.py`, and 14 standalone trading-loop launchers.
  Residual review: 209 static `starts_loop` flags (none reachable) and the
  diagnostic suites remain quarantined pending per-file review.
- **Wave 3 — data/execution/persistence** (applied 2026-09-29):
  `core/execution_bridge.py` is now a strict facade — the no-service fill
  path fails closed (`no_execution_service`) and the parallel JSONL ledger
  (`_persist`) is removed; in-memory `fills`/`positions` are projections for
  diagnostics only. `repositories.py`: `list_fills()` added;
  `snapshot(account_id)` now derives real `cash`/`equity` from the fill
  ledger + `initial_equity` (wired from `unified_bot` config).
  `security/credential_vault.py`: `rotate_key` closed-handle bug fixed.
  `unified_event_bus.py`: audit-path health probe at `start()` + post-write
  failure marks `_audit_healthy=False`; shielded actions veto when the
  audit trail is unwritable (fail-closed durable-audit gate).
  Gates met: no parallel ledger, no no-service fills, real snapshot equity,
  audit-failure injection → shielded VETOED. Residual: `BrokerExecutionBridge`
  live path stays quarantined; slippage JSONL remains a diagnostics log.
- **Wave 4 — strategy/portfolio** (applied 2026-09-29): manifest sweep of
  `strategies/`, `portfolio/`, `position/`, `signals/`, `alpha_engine/` — 2
  quarantined capital managers (`position_manager.py`,
  `strategies/cross_exchange_arbitrage.py`) now warn on construction with no
  production authority (same pattern as `MASTER_risk_manager`); no reachable
  capital/loop members in these families (enforced by a new architecture
  test). `LegacyStrategyAdapter`/`StrategyRegistry` remain signal-only.
- **Wave 5 — cognition** (applied 2026-09-29): new
  `cognition/advisory_adapter.py` (`AdvisoryCognitiveBrain`) wraps
  `AlphaAlgoCognitiveBrain` and strips every `authorized_*`/`risk_*`/order
  field, emitting `{capability_id, evidence, advisory_only}` matching
  `AgentCapabilityPort` — the brain's internal `RiskGatekeeper` output can no
  longer reach order authority; tests assert forged capability output
  carries no order-capable fields. Brain remains off-graph until explicitly
  composed behind this adapter.
- **Wave 6 — research separation** (applied 2026-09-29): all legacy
  self-improvement packages (`recursive_improvement/`, `eternal_evolution/`,
  `alpha_evolve/`, `autonomous_learner/`, `adaptive_systems/`,
  `meta_learning/`) and root duplicate modules (`code_evolver`,
  `auto_rollback`, `continual_learner`, `ai_learner`, `experiment_tracker`,
  `performance_optimizer`) emit DeprecationWarnings; `backtesting/
  strategy_backtester.py` flagged `execute_trade` is a simulated backtester
  (research_only, not reachable). Gate test added: no research-family module
  may be runtime-reachable with capital/loop flags; every legacy RSI root
  module warns on import. RSI evidence/promotion gates already enforced by
  `test_rsi_*` suites.
- **Wave 7 — interfaces/operations** (applied 2026-09-29): all 281 external
  surfaces + 368 package `cli_entrypoint` modules swept. Every
  capital/loop-flagged standalone surface now refuses at `__main__`
  (~40 guards added across `scripts/`, root launchers, package CLIs including
  `install_service.py`, `production/interactive_brokers_live.py`,
  `brain/mt5_brain_trader.py`, `ultimate_bot/*`, `watchdog.py`,
  `system_supervisor.py`, autonomous launchers). Read-only
  monitors/dashboards/analysis validators remain runnable as documented
  exceptions; `main_original.py`/`realtime_trading_core.py` delegate to
  canonical `main.py`; console script `trading-bot` -> `trading_bot.main`
  -> canonical `main.py`. Gate test enforces zero unguarded capital/loop
  CLIs outside the documented exception list.

Every wave: baseline -> failing negative-path test -> bounded change ->
conformance + boundary tests -> refresh joined manifest -> reviewer sign-off.
Protected files (`risk/service.py`, `core/immutable_shield.py`,
`execution/service.py`, `unified_bot.py`, `main.py`, RSI contracts/evaluator/
anti-gaming/archive) are never edited as part of an RSI candidate; architecture
changes to them require separate explicit approval.

## 9. Verification and completion criteria

- Boundary: `python -m pytest tests/architecture tests/foundation -q --no-cov
  -p no:cacheprovider` — plus new tests for single-loop/single-bus/single-
  registry, dynamic-import coverage, facade signatures, forbidden capital
  receivers.
- Conformance: `test_conformance.py`, `test_market_data_adapter.py`,
  `test_concrete_broker_bridge.py`, `test_strategy_adapter.py`,
  `test_policy_adapters.py`, `test_execution_repository_lifecycle.py`,
  `test_persistence_repository.py` + new restart/idempotency/cancel/partial-
  fill cases.
- Failure injection: stale/NaN/missing provenance data; absent repository;
  failed durable audit write; missing/timed-out approval; missing risk; shield
  error/timeout; ambiguous broker ack; fill-write failure; reconciliation
  mismatch; duplicate submit; forged AI sizing. Assert zero adapter submits on
  any prerequisite failure and stop-and-reconcile (not retry) after ambiguous
  acks.
- Smoke: bounded `main.py --mode analysis --cycles N --interval 0`; in-process
  synthetic paper run with a temp `trading_state.db`; assert correlation from
  MarketEvent id -> decision -> order -> fill -> position -> projection.
- RSI: `tests/rsi`, `tests/foundation/test_rsi_*.py`,
  `tests/recursive_self_improvement` per `AGENTS.md`.
- Completion metrics: 100% of in-scope files joined exactly once; 100% of
  high-risk flags manually reviewed; zero unapproved capital calls, loops,
  buses, registries reachable; zero orders on injected hard-gate failure; all
  order/fill/audit durable and correlated; paper restart/idempotency pass;
  RSI promotion readiness = 0 while real data covers one instrument.
- `trading_bot/__init__.py` import takes ~1-3 min; tests must import only the
  submodules they need. Pytest runs use `-p no:cacheprovider` (~2 GB free).
