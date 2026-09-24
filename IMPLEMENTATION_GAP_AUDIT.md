# Implementation Gap Audit — Docs vs. Code (post merge-six)

> **STATUS ADDENDUM (2026-09-17 evening):** Phase 0–1 executed.
> - `import trading_bot` works; all 4 live broken modules repaired.
> - `main.py` rewritten → `AlphaAlgoCognitiveBrain`; runs the 9-stage loop on `market_data.db` (EURUSD M15 replay + rolling H1 aggregate). Verified: 60 cycles → 19 BUY / 4 SELL authorized only when multi-TF trend confirmed; 37 WAIT abstentions in ranging conditions.
> - `CognitiveSystemController` repaired (missing imports, `initialize()`, `running`, `state`, `execute_task` envelope); `tests/cognition/` + `test_uca_core.py` → **29/29 pass** (0.40 ms/cycle, ECE 0.21).
> - `trading_bot/superintelligence/` stubs replaced with full implementations (de-archived); `aamis_v3` restored via compat shim; `get_unified_brain()` compat factory added.
> - **Phase 2 (registry + shield consolidation) executed:**
>   - `UnifiedComponentRegistry.register()` had been merge-gutted (validated + logged but never stored). Restored full storage across `_components`/`_metadata`/`_services`/`_legacy_metadata`/`_registration_order`.
>   - `ServiceRegistry` in `core/service_registry.py` now aliases `UnifiedComponentRegistry` — `ServiceRegistry()` returns the shared singleton (was: `_archive` import or a dead dict fallback).
>   - `ImmutableShield` (core) is the canonical shield; merged in `GovernanceGate`'s unique capabilities — EXTREME_VOLATILITY exit-only regime veto + deterministic `check_evolution_gate` (RSEA monotone improvement). `governance/immutable_shield.py::GovernanceGate` is now a delegating adapter preserving legacy clip/ban semantics.
>   - Shield voter re-wired inside CSC init — `decision_bus.reset()` was silently orphaning the shield voter (actions vetoed by `__missing_shield__`). CSC + `AlphaAlgoCognitiveBrain` register their live engines into the canonical registry.
> - **External-horizon plumbing built (no fake data):** `trading_bot/market_feeds/` — `LOBSnapshot` contract (mid/spread_bps/imbalance/depth) + `LOBFileFeed` (recorded JSONL/CSV replay, raises on missing data) + `BrokerLOBFeed` (polls `BrokerInterface.get_order_book` — real connectivity path). `trading_bot/core/execution_bridge.py` — `BrokerExecutionBridge` (same bus contract, delegates to `BrokerInterface.place_order`, lazy-imports broker pkg), `SlippageRecorder` (expected-vs-fill bps, JSONL + mean/max/p95 stats) wired into *both* bridges, `make_execution_bridge()` factory. `main.py` gains `--execution {paper,broker}` + `--broker`/`--testnet` (env `BROKER_API_KEY/SECRET`, fails loudly absent). `process_cycle()` accepts optional `lob_snapshot` → `microstructure` features in the decision output. 10 new tests; 50/50 pass; `main.py --replay` verified end-to-end with slippage in the execution summary.
> - **Deep subpackage cleanup executed:** reachability scan (`scan_reachability.py`, AST + string-literal dynamic refs, seeds = `__init__`/`main.py`/`tests/`/root scripts) found 240 top-level subpackages → 205 reachable, 35 unreachable. **28 dead packages (~160K lines) quarantined to `trading_bot/_archive/`** (manifest: `_archive/DEAD_PACKAGES.md`); 7 kept despite unreachability because they carry `__main__` entry points (possible standalone CLIs). `import trading_bot` + 40/40 tests verified post-move.
> - **Evaluation harness added:** `trading_bot/evaluation/walk_forward.py::WalkForwardEvaluator` — chronological train/test split of real `market_data.db` history; TRAIN warms the calibrator, TEST is strict OOS with simulated positions (horizon exit or intrabar stop), per-trade raw-vs-calibrated ECE scored *before* outcome ingestion. First run (EURUSD, 1000 bars): TRAIN 133 trades, 36% win, −2.22%, ECE 0.28→0.16; TEST 77 trades, 70% win, +1.84%, ECE 0.30→0.29; abstain 74–81%; drift fired 5× (detector now z-scores the stream — absolute-unit PH thresholds could never fire on ~1e-4 FX returns). Honest findings: the raw simulator is overconfident (ECE ~0.3), in-sample calibration transfers only partially across regimes, and the brain's edge is regime-dependent, not universal.
> - **Phase 5 (orchestrator dedup) first pass executed:** inventory scan found 172 `*Orchestrator` classes in 163 files; usage classification: 53 instantiated (live), 20 referenced-only (compat), **99 init-only auto-generated stubs**. All 101 trivial stubs (99 + 2 multi-class inits) patched with `DeprecationWarning` routing to `CognitiveSystemController` — imports and `__all__` exports preserved, instantiation now loud instead of silently no-op (`dedup_orchestrators.py`, `scan_orch_usage2.py` kept as rerunnable tools). 4 skipped as real classes (aliases/non-trivial). 39/39 cognition+CSC tests pass.
> - **Phase 4 (scientific hardening) partially executed — 3 of 5 hostile-audit items:**
>   - *Calibration*: `cognition/learning/calibration.py` — Platt (online logistic) → isotonic (PAV, tie-pooled) composite `ProbabilityCalibrator` + ECE tracker. Wired into `DecisionIntelligenceEngine.calibrated_probability`; outcomes feed back via `brain.record_outcome()`.
>   - *Drift detection*: `cognition/perception/drift.py` — Page-Hinkley CUSUM detector per instrument, fed per-bar returns in `process_cycle`; `drift_detected` reported per cycle.
>   - *Fat-tailed simulation*: `CounterfactualSimulator` gains seeded Student-t (df=4) Monte Carlo (`monte_carlo_paths`, default 256 in the brain) — empirical win prob blended 50/50 with heuristic; `mc_p95_drawdown`/`mc_expected_value`/`mc_paths` reported as first-class evidence (not folded into the heuristic-unit gate — avoids category error that vetoed every trade).
>   - *Not done*: deep order-book/microstructure modeling and multi-broker execution — both need real LOB data and broker infrastructure, not synthetic substitutes.
>   - 10 new tests in `tests/cognition/test_hardening.py`; 39/39 cognition+CSC tests pass. Latency 0.40→3.76 ms/cycle.
> - **Phase 3 (doc reconciliation) executed:** `CANONICAL_COMPONENTS.md` now carries a verified-runtime-reality table — the five-way "canonical brain" contradiction is resolved in code (CSC = strategic pipeline/`main.py` entry, `AlphaAlgoCognitiveBrain` = tactical 9-stage loop, others = façades). `AgentRegistry` documented as nonexistent.
> - **Delusion loop closed:** `self_play_loop.py` primary path replays real `market_data.db` bars (parallel fixer); even `_play_game_simulated` uses `_simulate_step_grounded` (real price changes). The orphaned Gaussian-random-walk `_simulate_step` was dead code — removed. Remaining `np.random` is legitimate: episode-start randomization, slippage jitter, buffer sampling, exploration.
> - **Verification chain audited end-to-end:** EvidenceGate rejection hard-blocks (`Consensus < 80%` → TRADE_REJECTED). The earlier `TRADE_APPROVED` runs were legitimate — hypothesis branches now carry observation-grounded evidence (regime, tail-risk, liquidity nodes) that honestly satisfies the falsifiers. Verified: thin evidence → 3/5 falsify → reject.
> - **Quarantine executed:** rescan showed 113 → 39 unparseable files (parallel repair cleared all `examples/` and all `trading_bot/` files). Remaining 39 are bulk auto-generated coverage tests under `tests/` — moved to `tests/_quarantine/` and excluded via `collect_ignore` in `tests/conftest.py`. Repair them only if their coverage is actually needed.
> - Note: a parallel repair process was concurrently editing the same merge-scarred files during this work; some fixes (multi_agent_debate, router pf_result, controller imports, and a CSC-based rewrite of main.py + `PaperExecutionBridge`) landed from both directions.

**Date:** 2026-09-17
**Method:** Extracted canonical-component declarations from the spec/audit corpus, then verified each against the actual merged codebase (existence, compilability, interface match, reachability).
**Verdict:** The design corpus describes a converged "One Brain" architecture. The code contains most of the pieces — but the system **cannot currently be imported, tested, or started**, and the docs themselves name **five different components as "the canonical brain."**

---

## 1. Executive Summary

| Claim (docs) | Reality (verified in code) |
|---|---|
| "0 compilation errors, 88/88 tests passing" (`MASTER_AUDIT_REPORT.md`) | **113 files fail to compile** (61 examples, 43 tests, 5 live package files). `pytest` cannot even collect — conftest dies on a `SyntaxError`. |
| "One Brain" converged architecture | **172 `*Orchestrator` classes** in live `trading_bot/` (excluding `_archive`). At least 4 compete for the "brain" role. |
| Canonical registry = `ServiceRegistry` (`CANONICAL_COMPONENTS.md`) | File exists but **does not parse** (unterminated docstring), and its fallback imports from `_archive`. |
| Canonical decision engine = `DeepMindOrchestrator` | `master_orchestrator.py` **does not parse** (unterminated docstring). |
| "Authoritative brain" = `CognitiveSystemController` (UCA V6) | **Cannot be instantiated** — 4 unbound names (`threading`, `shield`, `InformationFolder`, `SkillRouter`). Contains `MagicMock` imports and hardcoded metrics. |
| `main.py` = UCA-2026 entry point | Merge Frankenstein: references ≥8 names that are never imported or defined; calls CSC methods that don't exist. |

---

## 2. P0 — The System Is Dead (verified)

### 2.1 `import trading_bot` fails → everything downstream is dead

```
trading_bot/__init__.py:268 → meta_governance → decision_governance
  → agents/__init__.py:13 → multi_agent_debate.py:676
  SyntaxError: invalid syntax  (elif total_score < -0.4:)
```

- Root cause: a **half-finished manual merge fix**. `git status` shows `M multi_agent_debate.py` uncommitted — someone re-indented the duplicated scoring block into `MacroStrategist.analyze` but left a `_removed_merged_duplicate` stub containing an orphaned `elif`.
- The `try/except ImportError` guards in `__init__.py` cannot catch `SyntaxError`, so it propagates.
- **Blast radius:** every import of `trading_bot.*`, `python main.py`, and `pytest` collection (conftest → `tests/__init__.py` → `test_agents` → same chain).

### 2.2 Broken live package files (from `temp_scan_broken.json` + verification)

| File | Error | Role per docs |
|---|---|---|
| `trading_bot/agents/multi_agent_debate.py` | orphaned `elif` (merge fragment) | Multi-Agent Debate swarm — required by IMPROVEMENT_GOVERNANCE (5-agent consensus) |
| `trading_bot/core/service_registry.py` | unterminated `"""` at line 5–6 | **Canonical system registry** |
| `trading_bot/core_agent_system/master_orchestrator.py` | unterminated `"""` | **Canonical decision engine** |
| `trading_bot/recursive_improvement/recursive_core.py` | invalid syntax | RSIE self-improvement core |
| `trading_bot/_archive/**` ×4 | various | archive — ignorable |
| `examples/**` ×61, `tests/**` ×43 | same merge-mangling pattern (stray lines before imports, orphaned blocks, `await`/`return` outside functions) | demos & test suite |

### 2.3 `main.py` cannot run even after imports are fixed

Compiles, but `main()` references names that are never imported or defined:
`HierarchicalMemorySystem`, `GenerativeWorldModel`, `GovernanceGate`, `decision_bus`, `registry`, `args`, `market_data`, `argparse`.
It also calls `csc.initialize()` and `csc.execute_task(...)` — **neither method exists** on `CognitiveSystemController`.
It is two different entry-point versions interleaved by a merge.

### 2.4 The "authoritative" CSC brain cannot be instantiated

`trading_bot/core/csc/controller.py`:
- `__new__` uses `threading.Lock()` — `threading` never imported → `NameError`
- `__init__` line 148: `self.shield = shield` — bare `shield` never defined → `NameError`
- line 149: `InformationFolder()` — exists in `folding.py`, never imported → `NameError`
- lines 178/184: `SkillRouter` — exists in `router.py`, never imported → `NameError`
- imports `MagicMock`/`AsyncMock` from `unittest.mock` into the production brain
- `variational_free_energy` property returns hardcoded `0.15`; `discrete_embeddings` always appends `"regime_shift_detected"`
- `execute_self_improvement_loop` is a 15-line heuristic — not the six-gate RSIE pipeline the spec requires
- injected `verifier_swarm` is overwritten unconditionally at line 193

---

## 3. P1 — The Docs Contradict Each Other on What the AI *Is*

Five documents declare five different canonical stacks:

| Component | CANONICAL_COMPONENTS.md | ARCHITECTURE_GAP_MATRIX | ARCHITECTURE_VERIFICATION_REPORT | COGNITIVE_ARCHITECTURE_SPEC | main.py / UCA-V6 |
|---|---|---|---|---|---|
| **Brain** | `IntegratedAgentSystem` | `CognitiveSystemController` | `MTASH` (ai/hub) | `IAS.PlannerAgent` | `CognitiveSystemController` |
| **World model** | `WorldModelV2` (v2_core) | `AgenticPlanningWorldModel` (latent_dynamics) | `world_model.WorldModel` | `deepchart.latent_state_engine` | `WorldModelV2` + `GenerativeWorldModel` (nonexistent) |
| **Memory** | `core_agent_system.MemorySystem` | — | `core_agent_system.MemorySystem` | `memory.cognitive_store` | `HierarchicalMemorySystem` (core/hms) |
| **Registry** | `ServiceRegistry` + `AgentRegistry` | `UnifiedComponentRegistry` | `registry.ServiceLocator` | — | `registry` (undefined) |
| **Decision** | `DeepMindOrchestrator` | CSC | `MasterOrchestrator` | `apex_fi.model_parliament` | CSC + `VerificationSwarm` |
| **Governance** | `ConstitutionalAI` + `MSOS` | `ImmutableShield` | `ConstitutionalAI` | `security.governance` | `ImmutableShield` + `EvolutionGate` |

**Gap #0: before any code is written, one of these must be declared authoritative and the other docs amended — otherwise every future merge re-introduces a competing "canonical" stack.**

### Doc-declared components with **no code at all**

| Declared canonical | Declared in | Reality |
|---|---|---|
| `trading_bot.registry.ServiceLocator` | ARCHITECTURE_VERIFICATION_REPORT | no `registry/` package; `class ServiceLocator` appears nowhere |
| `core_agent_system.AgentRegistry` | CANONICAL_COMPONENTS | `class AgentRegistry` appears nowhere |
| `trading_bot.memory.cognitive_store` | COGNITIVE_ARCHITECTURE_SPEC | no `memory/` package (a real `HierarchicalMemoryEngine` exists at `cognition/memory/`) |
| `trading_bot.swarm.SwarmController` | COGNITIVE_ARCHITECTURE_SPEC | no `swarm/` package (`core_agent_system/swarm/` exists) |
| `trading_bot.evaluation.evaluation_pipeline` | COGNITIVE_ARCHITECTURE_SPEC | no `evaluation/` package |

---

## 4. P2 — Competing "One Brain" Implementations (all present, all compile except one)

| Brain | File | Lines | State | Doc support |
|---|---|---|---|---|
| `AlphaAlgoCognitiveBrain` | `cognition/orchestrator.py` | 139 | **Coherent 9-stage loop** (perception→state→memory→simulation→reasoning→hypotheses→verification→decision→risk); whole `cognition/` package compiles; hostile-audit scored 80/100 in simulation | COGNITIVE_BRAIN_HOSTILE_AUDIT |
| `CognitiveSystemController` | `core/csc/controller.py` | 549 | **Uninstantiable** (4 NameErrors), singleton, mock imports, fake metrics | GAP_MATRIX, UCA-V5/V6 docs, main.py |
| `IntegratedAgentSystem` | `core_agent_system/integrated_system.py` | 820 | Compiles; MCTS + constitutional + coordination | CANONICAL_COMPONENTS, VERIFICATION_REPORT, COGNITIVE_ARCHITECTURE_SPEC |
| `MTASH` | `ai/hub.py` | 366 | Compiles | VERIFICATION_REPORT ("Unified Brain" hub) |
| `DeepMindOrchestrator` | `core_agent_system/master_orchestrator.py` | — | **Syntax error** | CANONICAL_COMPONENTS (decision engine) |

Plus 167 more `*Orchestrator` classes across the package — the "orchestration explosion" the redesign docs set out to eliminate is currently *larger* than when it was documented.

### Duplicated safety layers
- `core/immutable_shield.py::ImmutableShield` vs `governance/immutable_shield.py::GovernanceGate` — two different "Immutable Shield" implementations with different APIs.
- Registries: `ServiceRegistry` (broken) vs `UnifiedComponentRegistry` (works) vs declared-but-missing `ServiceLocator`/`AgentRegistry`.

---

## 5. P2 — Scientific-Validity Gaps (verified against ARCHITECTURE_GAP_MATRIX)

| Gap-matrix claim | Verified state |
|---|---|
| DiscoLoop "partially implemented" | `DiscoLoopCell` in controller.py is a toy: `tanh` state + argmax one-hot + a **string** `token_loop_{k}_{idx}_{val}`. Not coupled discrete-continuous reasoning. |
| `self_play_loop.py` random-walk prices | **Still present**: `price_change = np.random.randn() * volatility` (line 672), `baseline_outcome = np.random.randn() * 100` (line 800). Historical slices are used in some paths — partially remediated. |
| Gaussian simulation limits | Confirmed: `CounterfactualSimulator` uses Gaussian perturbation (hostile audit: ECE = 0.3357, uncalibrated). |
| EKSFT / AutoMem / SAGE / HASP algorithms | Exist as standalone files in `SCIENTIFIC_FOUNDATION_V5/ALGORITHMS/` — no evidence of integration into `core/csc/acpe.py` or HMS. |
| Missing owners from spec Phase-1 matrix | `memory.cognitive_store`, `swarm.SwarmController`, `evaluation.evaluation_pipeline` — no code (see §3). |
| Slice-1 deprecations (COGNITIVE_ARCHITECTURE_SPEC Phase-7) | `agents/`, `agents2.py`, `agents 2` (root), `autonomous_superintelligence/` all still present — **not done**. |

---

## 6. Prioritized Implementation Plan

Ordered by dependency: each phase gates the next. Nothing here requires new research — it is convergence work.

### Phase 0 — Resuscitate (unblock everything)
1. Finish the interrupted fix in `multi_agent_debate.py` — delete the `_removed_merged_duplicate` orphan block (the dedup was already half-done in the working tree).
2. Repair docstrings: `core/service_registry.py`, `core_agent_system/master_orchestrator.py`; repair `recursive_improvement/recursive_core.py`.
3. **Gate:** `python -c "import trading_bot"` succeeds; `pytest --collect-only` runs (failures OK, collection must not abort).
4. Quarantine or mechanically repair the 104 broken `examples/`+`tests/` files (same merge-mangling pattern — scriptable).

### Phase 1 — One brain decision (the fork in the road)
Recommend `AlphaAlgoCognitiveBrain` (`cognition/`) as the **runtime brain** — it is the only complete, compilable, audit-validated loop. Then either:
- **(a)** Repair CSC into the strategic/meta layer above it (add missing imports, remove `MagicMock`, real VFE, real RSIE gate), or
- **(b)** Deprecate CSC/IAS/MTASH to `_archive` and name `AlphaAlgoCognitiveBrain` canonical in `CANONICAL_COMPONENTS.md`.
5. Rewrite `main.py` against the chosen brain's real API (a ~40-line entry point, not the current 103-line merge artifact).
6. **Gate:** `python main.py` completes at least one cognitive cycle on mock observations.

### Phase 2 — Registry & safety consolidation
7. Pick `UnifiedComponentRegistry` as the single registry (works today); fix or delete `ServiceRegistry`; create `AgentRegistry` only if the brain actually needs it.
8. Merge `ImmutableShield`/`GovernanceGate` into one non-bypassable shield with the HASP-style deterministic triggers the gap matrix requires.
9. **Gate:** every component lookup in the brain goes through one registry; one shield intercepts execution.

### Phase 3 — Spec↔code reconciliation
10. Update `COGNITIVE_ARCHITECTURE_SPEC.md` Phase-1 owner matrix to point at real modules (`cognition/memory/engine.py` for memory, `core_agent_system/swarm/` for coordination, etc.) **or** create the missing packages — prefer updating the spec, the real implementations already exist elsewhere.
11. Amend the four other canonical-component docs to the Phase-1 decision; add a rule that `CANONICAL_COMPONENTS.md` is the single source of truth.
12. **Gate:** every "canonical" declaration in the docs resolves to an existing, compilable class.

### Phase 4 — Scientific grounding (from verified gap matrix)
13. ECE calibration (Platt/isotonic) inside `EvolutionGate` — hostile audit's #1 missing capability (ECE 0.3357 → <0.05).
14. Student-t/GARCH perturbations in `CounterfactualSimulator` (order-book microstructure later).
15. Eliminate remaining `np.random` price/baseline paths in `self_play_loop.py` — historical replay only.
16. Replace `execute_self_improvement_loop` heuristic with the six-gate RSIE pipeline + human-approval write from `IMPROVEMENT_GOVERNANCE.md`.
17. Restore Multi-Agent Debate swarm to the 5-verifier consensus the governance spec requires (currently unimportable).
18. **Gate:** hostile-audit script re-run shows ECE < 0.05 and no random-walk evaluation paths.

### Phase 5 — Dedup sweep (largest, do last)
19. Route the 172 orchestrators through the canonical brain or archive them; enforce the "one authoritative implementation" rule per subsystem (orchestrators, registries, world models, risk managers — duplicate lists already exist in §2 of `ARCHITECTURE_GAP_MATRIX.md`).
20. Execute COGNITIVE_ARCHITECTURE_SPEC Slice-1 deprecations (`agents`, `agents2`, `autonomous_superintelligence`, root `agents 2`).
21. **Gate:** one brain, one registry, one shield, one world model reachable from `main.py`; everything else under `_archive`.

---

## 7. Doc-credibility notes for future audits

- `MASTER_AUDIT_REPORT.md` / `ISSUE_TRACKER.md` describe a **pre-merge** state — treat "0 errors / 88 tests" claims as stale until re-verified.
- `COGNITIVE_BRAIN_HOSTILE_AUDIT_REPORT.md` is the most empirically grounded doc (real metrics, ablations, stated limits) — but its "production-ready" verdict predates the merge damage.
- `ARCHITECTURE_GAP_MATRIX.md` component statuses ("partially implemented") proved accurate where checked — usable as the gap baseline.
- Recommendation: add a `VERIFIED_AT` + commit-hash header to audit docs; several reports assert states that were already false when written.
