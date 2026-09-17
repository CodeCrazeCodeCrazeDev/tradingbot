# Architectural Redesign Proposal: The "One Brain" Realignment

## 1. Problem Statement
The AlphaAlgo codebase currently operates under a "Successive Architecture Overlay" pattern. New "Master" systems are added on top of old ones without decommissioning. This results in:
- 5+ Competing Orchestrators
- 3+ Fragmented Agent Registries
- 2+ Fragmented World Models
- 3+ Fragmented Execution Layers

## 2. Recommended Canonical Architecture: Unified Cognitive Architecture (UCA)
Based on an objective audit of completeness and scientific grounding, the **IntegratedAgentSystem (IAS)** is recommended as the canonical "One Brain" for the system.

### Justification:
- **Completeness:** IAS already integrates MCTS (DeepMind-style), ReAct (OpenAI-style), and Constitutional AI (Anthropic-style).
- **Scalability:** It uses a modular registry system (Agents, Tools, Memory) that can be easily extended.
- **Scientific Validity:** It is grounded in the UCA-2026 mathematical foundation (Active Inference/VFE).
- **Consolidation Capability:** It contains existing adapters for legacy agents, making it the natural target for migration.

## 3. Consolidation Plan

### 3.1 Orchestration
- **Canonical:** `trading_bot/core_agent_system/integrated_system.py` (IAS).
- **Migrate:** MCTS logic from `trading_bot/core_agent_system/master_orchestrator.py` into IAS internal reasoning loop.
- **Remove:** root `master_orchestrator.py`, `trading_bot/core/orchestrator.py`, and `trading_bot/aamis_v3/.../master_orchestrator.py`.
- **Entry Point:** `trading_bot/main.py` will serve as the single entry point, initializing IAS as the primary brain.

### 3.2 World Model
- **Canonical:** `trading_bot/world_model/v2_core.py` (WM-V2).
- **Migrate:** Any unique causal rules from `fwm_core.py`.
- **Remove:** `fwm_core.py` and its legacy dependencies.

### 3.3 Agent Frameworks
- **Canonical:** `trading_bot/core_agent_system/agent_registry.py`.
- **Consolidate:** All agents from `trading_bot/agents/`, `trading_bot/agents2/`, and `trading_bot/swarm/` into a single directory and register them in the canonical registry.

### 3.4 Execution Layer
- **Canonical:** `trading_bot/execution/trade_executor.py`.
- **Consolidate:** Logic from `smart_executor.py` and `execution_manager.py` into a unified executor with specialized strategy handlers (TWAP, VWAP, Smart).

## 4. Engineering Standards to Enforce
1. **Secure by Design:** No `eval()`, no `pickle`, use SHA-256.
2. **Async Integrity:** No `asyncio.run()` in library code. Use a single top-level loop.
3. **Reality Grounding:** All RL rewards must be derived from `HistoricalProvider` or `HighFidelitySimulator`.
4. **Observability:** Centralized `EventBus` for all logs and metrics.

## 5. Risk Assessment
- **Migration Risk:** Removing legacy orchestrators might break untested "zombie" features. Mitigation: Every removal will be preceded by an integration test of the corresponding feature in IAS.
- **Complexity Risk:** IAS is a complex class. Mitigation: Refactor IAS into smaller, testable sub-modules (Reasoning, Safety, Execution, Learning) within the `core_agent_system` package.

## 6. Implementation Order
1. Fix Syntax Errors (RELI-03).
2. Fix Critical Security Holes (SEC-01, SEC-02, SEC-03).
3. Consolidate Orchestration (ARCH-01).
4. Ground the Learning Loop (INTELL-01).
5. Clean up the directory structure (MAINT-01).
