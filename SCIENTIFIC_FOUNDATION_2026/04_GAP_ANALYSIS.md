# Phase 4: Gap Analysis (Scientific vs. Actual Codebase)

This document provides a systematic repository-wide architectural audit of AlphaAlgo (Audited July 2026) across 18 core subsystems and classifies findings according to the four-tier scientific schema.

---

## 1. Systematic Repository-Wide Architectural Subsystem Audit

### 1. Strategic Controller
*   **Canonical Implementation**: `CognitiveSystemController` (CSC) in `trading_bot/core/csc/controller.py`.
*   **Alternative Implementations**: `CentralController` (`trading_bot/brain/central_controller.py`), `MasterController` (`trading_bot/adaptive_systems/master_controller.py`).
*   **Consumers**: Main trading execution paths, test suites (`tests/test_scientific_modules.py`).
*   **Dependencies**: `SAGEGraphMemory`, `UnifiedDecisionBus`, `SkillRouter`.
*   **Runtime Path**: `main.py` $\to$ `CognitiveSystemController.process_market_observation()`.
*   **Tests**: `tests/test_scientific_modules.py::test_discoloop_internalization`.
*   **Known Defects**: Lack of async-safe clean resets leading to state leakages across unit test runs. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Dual-coexist with alternate controller blocks creates risk of conflicting trade signals. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High (Requires deprecating legacy master controller instances).
*   **Removal Candidates**: `trading_bot/brain/central_controller.py`, `trading_bot/adaptive_systems/master_controller.py`.

### 2. Agent Orchestrator
*   **Canonical Implementation**: `CognitiveSystemController` (CSC) in `trading_bot/core/csc/controller.py`.
*   **Alternative Implementations**: `MasterOrchestrator` (`trading_bot/orchestration/master_orchestrator.py`).
*   **Consumers**: `run_agentic_platform.py`.
*   **Dependencies**: `UnifiedDecisionBus`, `SkillRouter`.
*   **Runtime Path**: `run_agentic_platform.py` $\to$ Orchestrator Event Loop.
*   **Tests**: `tests/test_scientific_modules.py`.
*   **Known Defects**: Redundant concurrent event scheduling in legacy master orchestrator.
*   **Research-Supported Deficiencies**: Fragmentation of orchestrators violates Single Strategic Authority principles (Effective Agents). (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: `trading_bot/orchestration/master_orchestrator.py`.

### 3. Planning
*   **Canonical Implementation**: `DiscoLoopCell` in `trading_bot/core/csc/controller.py`.
*   **Alternative Implementations**: Traditional prompt-based sequence plans.
*   **Consumers**: CSC decision paths.
*   **Dependencies**: `HypothesisGenerator`.
*   **Runtime Path**: `CognitiveSystemController._run_discoloop_reasoning()`.
*   **Tests**: `tests/test_scientific_modules.py::test_discoloop_internalization`.
*   **Known Defects**: Non-convergent loops under extremely noisy continuous price feeds. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Research-Supported Deficiencies**: Lack of explicit Information Folding (HIPIF) results in context-window bloat over long horizons. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: Legacy ad-hoc string-parsing planners.

### 4. Decision Bus
*   **Canonical Implementation**: `UnifiedDecisionBus` in `trading_bot/core/unified_event_bus.py`.
*   **Alternative Implementations**: Bridged legacy `EventBus` (`trading_bot/core/event_bus.py`).
*   **Consumers**: All core UCA V6 modules.
*   **Dependencies**: `asyncio.PriorityQueue`, `ImmutableShield`.
*   **Runtime Path**: `decision_bus.propose_action()`.
*   **Tests**: `tests/conftest.py`.
*   **Known Defects**: AttributeError: type object 'UnifiedDecisionBus' has no attribute 'reset' during setup fixtures. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Concurrent thread access to the event queue without an initialization lock can trigger race conditions. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: `trading_bot/core/event_bus.py` (legacy).

### 5. Risk Engine
*   **Canonical Implementation**: `RiskFortress` in `trading_bot/ultimate_production/risk_fortress.py`.
*   **Alternative Implementations**: `MasterRiskManager` in legacy utils.
*   **Consumers**: `CognitiveSystemController`, `UnifiedDecisionBus`.
*   **Dependencies**: `ImmutableShield`.
*   **Runtime Path**: `decision_bus._check_consensus()` $\to$ Voter evaluations.
*   **Tests**: `tests/test_risk_controller.py`.
*   **Known Defects**: Inconsistent casing checks in consensus voter maps. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Risk rules are heuristics rather than probability-calibrated VaR estimates. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Legacy `MasterRiskManager`.

### 6. World Model
*   **Canonical Implementation**: `WorldModelV2` / `UnifiedWorldModel` in `trading_bot/world_model/unified_world_model.py`.
*   **Alternative Implementations**: Legacy `causal_model.py`, `counterfactual_engine.py`.
*   **Consumers**: `CognitiveSystemController`.
*   **Dependencies**: PyTorch weights, numpy.
*   **Runtime Path**: `CognitiveSystemController.process_market_observation()` $\to$ `world_model.simulate_intervention()`.
*   **Tests**: `tests/validate_uca_science.py`.
*   **Known Defects**: Missing FAISS similarity fallback warning when library is not installed. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Lack of rigorous Pearlian structural equation boundaries in counterfactual simulations. (Category: **SCIENTIFIC OPPORTUNITY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: `trading_bot/world_model/v2_adapter.py`.

### 7. Memory
*   **Canonical Implementation**: `HierarchicalMemorySystem` in `trading_bot/core/hms/memory.py`.
*   **Alternative Implementations**: Flat SQLite files, local JSONL files (`cds_evidence_history.jsonl`).
*   **Consumers**: `CognitiveSystemController`.
*   **Dependencies**: `SAGEGraphMemory`, `MemoryOS`.
*   **Runtime Path**: `hms.store_ledger_entry()`.
*   **Tests**: `tests/test_hms_v5.py`.
*   **Known Defects**: Stale database file references during consecutive test execution. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Static memory window limits trigger high retrieval latencies under volume spikes. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Redundant JSONL logs.

### 8. Knowledge System
*   **Canonical Implementation**: `SAGEGraphMemory` in `trading_bot/core/hms/memory.py`.
*   **Alternative Implementations**: Flat RAG vector indices.
*   **Consumers**: `HierarchicalMemorySystem`.
*   **Dependencies**: NetworkX, graphml files.
*   **Runtime Path**: `sage.retrieve_subgraph()`.
*   **Tests**: `tests/test_hms_v5.py`.
*   **Known Defects**: NetworkX graphml export errors with nested python dictionary formats. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Absence of persistent, automatic graph pruning leading to node-edge density bloat. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: Flat text chunk indexing.

### 9. Research Engine
*   **Canonical Implementation**: `ResearchLab` in `trading_bot/research/quant_pipeline.py`.
*   **Alternative Implementations**: `InternetResearchEngine` in ultimate system.
*   **Consumers**: Core research automation loops.
*   **Dependencies**: `DataLineageRegistry`, pandas.
*   **Runtime Path**: `quant_pipeline.py` $\to$ backtest execution.
*   **Tests**: `test_advanced_quant_pipeline.py`.
*   **Known Defects**: Multi-threading collision during pandas pickle storage reads. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Incomplete data lineage tracking of alpha trial iterations. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: `trading_bot/ultimate_system/internet_research_engine.py`.

### 10. Hypothesis Engine
*   **Canonical Implementation**: `HypothesisGenerator` in `trading_bot/core/csc/hypothesis.py`.
*   **Alternative Implementations**: Legacy ad-hoc LLM prompting scripts.
*   **Consumers**: `CognitiveSystemController`.
*   **Dependencies**: `WorldModelV2`.
*   **Runtime Path**: `hypothesis_gen.generate_competing_branches()`.
*   **Tests**: `tests/test_scientific_modules.py::test_pivot_refine_logic`.
*   **Known Defects**: Unhandled division by zero when calculating statistical weight vectors. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Generation of non-falsifiable trading hypotheses. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: Text-only heuristic hypothesis generators.

### 11. Strategy Discovery
*   **Canonical Implementation**: `AlphaDiscoveryEngine` in `trading_bot/ultimate_system/alpha_discovery_engine.py`.
*   **Alternative Implementations**: Simple heuristic rule generators.
*   **Consumers**: Research loops.
*   **Dependencies**: `ResearchLab`.
*   **Runtime Path**: `AlphaDiscoveryEngine.run_discovery()`.
*   **Tests**: `test_advanced_quant_pipeline.py`.
*   **Known Defects**: Look-ahead bias in price shift metrics during signal calculation. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Lack of Deflated Sharpe Ratio calculation in standard alpha ranking. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Heuristic technical indicator scanners.

### 12. Evaluation
*   **Canonical Implementation**: `MultipleTestingGate` in `trading_bot/reality_gates/multiple_testing_gate.py`.
*   **Alternative Implementations**: Legacy uncorrected p-value checks.
*   **Consumers**: `CognitiveSystemController`, Research OS.
*   **Dependencies**: statsmodels.
*   **Runtime Path**: `MultipleTestingGate.evaluate_alphas()`.
*   **Tests**: `tests/test_scientific_modules.py::test_rsea_monotone_safe_gate`.
*   **Known Defects**: Statsmodels dependency importing failure when external environment lacks package. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Soft evaluation rules bypassing FDR controls. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: Heuristic raw performance checkers.

### 13. Governance
*   **Canonical Implementation**: `ImmutableShield` in `trading_bot/core/immutable_shield.py`.
*   **Alternative Implementations**: Manual validation gates.
*   **Consumers**: `UnifiedDecisionBus`, `CognitiveSystemController`.
*   **Dependencies**: Risk rule engines.
*   **Runtime Path**: `shield.validate_action()`.
*   **Tests**: `tests/test_scientific_modules.py::test_hasp_guardrail_interception`.
*   **Known Defects**: Veto logic is easily bypassed by mock voter structures. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Soft risk limits that can be dynamically altered by autonomous code mutations. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Soft validation scripts.

### 14. Execution
*   **Canonical Implementation**: `SmartExecutor` in `trading_bot/ultimate_production/smart_executor.py`.
*   **Alternative Implementations**: Standard direct API order execution calls.
*   **Consumers**: `CognitiveSystemController`, execution planners.
*   **Dependencies**: Broker adapters, MetaTrader5 interface.
*   **Runtime Path**: `SmartExecutor.execute_trade()`.
*   **Tests**: `tests/test_exec_data.py`.
*   **Known Defects**: MT5 order placement failures under paper trading environments. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Lack of liquidity-aware execution trajectories (Almgren-Chriss). (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Legacy non-adaptive direct execution hooks.

### 15. Model Management
*   **Canonical Implementation**: `ModelOptimizer` in `trading_bot/unified_evolution/advanced_model_optimizer.py`.
*   **Alternative Implementations**: Legacy model fine-tuning loops.
*   **Consumers**: Self-evolution paths.
*   **Dependencies**: PyTorch weights, huggingface-hub.
*   **Runtime Path**: `advanced_model_optimizer.py`.
*   **Tests**: `tests/test_scientific_modules.py::test_s2l_behavioral_routing`.
*   **Known Defects**: PyTorch model checkpoint mismatch across differing weight sizes. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Incomplete adapter mapping leading to weight corruption on core models. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Global weight modification scripts.

### 16. Artifact Management
*   **Canonical Implementation**: `DataLineageRegistry` in `trading_bot/research/research_os.py`.
*   **Alternative Implementations**: Flat filesystem directories.
*   **Consumers**: Research OS pipelines.
*   **Dependencies**: SQLite metadata stores.
*   **Runtime Path**: `research_os.py` artifact tracking.
*   **Tests**: `test_research_governance.py`.
*   **Known Defects**: Missing parent ID checks during recursive generation steps. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Incomplete lineage tracing. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: Flat un-versioned directories.

### 17. Self-Improvement
*   **Canonical Implementation**: `EvolutionGate` in `trading_bot/governance/evolution_gate.py`.
*   **Alternative Implementations**: Un-validated programmatic code self-writes.
*   **Consumers**: Brain state evolution paths.
*   **Dependencies**: Out-of-sample backtesters.
*   **Runtime Path**: `evolution_gate.validate_evolution()`.
*   **Tests**: `tests/test_scientific_modules.py::test_rsea_monotone_safe_gate`.
*   **Known Defects**: Synchronous vs asynchronous execution mapping mismatches. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Lack of rigid out-of-sample calibration checks. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: High.
*   **Removal Candidates**: Un-monitored programmatic code self-writing scripts.

### 18. Agent Coordination
*   **Canonical Implementation**: `VerificationSwarm` in `trading_bot/core/verification/swarm.py`.
*   **Alternative Implementations**: Competing orchestrator networks.
*   **Consumers**: `CognitiveSystemController` (CSC).
*   **Dependencies**: Verification voter classes.
*   **Runtime Path**: `verifier_swarm.run_swarm()`.
*   **Tests**: `tests/test_scientific_modules.py::test_hasp_guardrail_interception`.
*   **Known Defects**: Coordination timeouts causing system-wide loop blocks. (Category: **VERIFIED ENGINEERING DEFECT**).
*   **Research-Supported Deficiencies**: Multi-agent coordination loops leading to semantic confusion. (Category: **ARCHITECTURAL DEFICIENCY**).
*   **Migration Difficulty**: Medium.
*   **Removal Candidates**: Decentralized competitor networks.

---

## 2. Structural Classification of Findings

Every proposed change is classified into one of the four mandatory categories to guide the development and remediation efforts.

### A — VERIFIED ENGINEERING DEFECT
1.  **AttributeError in Event Bus Reset**: `conftest.py` calls `UnifiedDecisionBus.reset()`, but the method was missing, breaking state isolation. (Remediated: Added thread-safe `__new__` and in-place `reset()`).
2.  **AttributeError in SkillRouter Lock**: `router.py` references `cls._lock` in its reset method, but the lock class variable was never declared, raising immediate AttributeError. (Remediated: Declared `_lock = threading.Lock()`).
3.  **Controller Thread State Leakage**: Lack of async reset methods inside `CognitiveSystemController` allowed pending coroutines to leak state across successive unit tests. (Remediated: Added async `reset()`).

### B — ARCHITECTURAL DEFICIENCY
1.  **Multiple Competing Strategic Controllers**: The coexistence of `central_controller.py`, `master_controller.py`, and `CognitiveSystemController` violates the "One Brain" strategic authority paradigm, risking split-brain decisions.
2.  **Static Memory Window Decay**: `HierarchicalMemorySystem` maintains a static memory window. Under highly volatile trading periods, lookups generate high latency due to memory buffer saturation.
3.  **Lack of Programmatic Compaction in SAGE**: Incremental graph memory construction leads to unbound node-edge expansion, resulting in long-term memory degradation.

### C — SCIENTIFIC OPPORTUNITY
1.  **Causal counterfactual Pearlian do-calculus**: Integrating structured Pearlian equation models into the world model to predict market interventions.
2.  **Adaptive Control Policy Engine (ACPE)**: Using variational active inference metrics to dynamically tune trading confidence in real-time.

### D — SPECULATIVE IDEA
1.  **Autonomous agentic fine-tuning via direct RLHF feedback**: Highly speculative, unsupported, and risky. Excluded from production architecture considerations.
