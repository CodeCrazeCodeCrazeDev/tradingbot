# Canonical Components Audit (Phase 5.3)

This document identifies the authoritative implementation for each major subsystem in the AlphaAlgo ecosystem. All other overlapping implementations are marked as Redundant/Legacy.

## 1. Orchestration (The Brain)
- **Canonical:** `IntegratedAgentSystem` (IAS)
- **File:** `trading_bot/core_agent_system/integrated_system.py`
- **Justification:** Integrates MCTS reasoning, Constitutional safety, and Multi-agent coordination. Effectively routes legacy calls via shims.
- **Redundant:**
    - `MasterOrchestrator` (root)
    - `TradingOrchestrator` (`trading_bot/core/orchestrator.py`)
    - `AAMISMasterOrchestrator` (`trading_bot/aamis_v3/aamis_master_orchestrator.py`)

## 2. World Model (The Simulator)
- **Canonical:** `WorldModelV2` (WM-V2)
- **File:** `trading_bot/world_model/v2_core.py`
- **Justification:** Advanced RSSM+Mamba architecture with internalized execution and causal dynamics. Supported by high-fidelity data grounding.
- **Redundant:**
    - `FormulatedWorldModel` (JEPA-based)
    - `MarketSimulator` (Generic stub)
    - `DigitalTwinSimulator` (Component of AAMIS)

## 3. Memory (The Knowledge Base)
- **Canonical:** `MemorySystem`
- **File:** `trading_bot/core_agent_system/memory_system.py`
- **Justification:** Multi-tier architecture (Working, Episodic, Semantic, Procedural) with persistence and consolidation logic.
- **Redundant:**
    - `PersistentMemory` (`trading_bot/perplexity_trading/persistent_memory.py`)
    - `StructuralMemory` (`trading_bot/intelligence_core/structural_memory.py`)

## 4. Component Discovery (The Registry)
- **Canonical (System-wide):** `ServiceRegistry`
- **File:** `trading_bot/core/service_registry.py`
- **Canonical (Agent-specific):** `AgentRegistry`
- **File:** `trading_bot/core_agent_system/agent_registry.py`
- **Justification:** `ServiceRegistry` handles the lifecycle of the event-driven 8-layer architecture. `AgentRegistry` provides specialized cognitive entity management within IAS.
- **Redundant:**
    - `SystemRegistry` (`trading_bot/system_registry.py`)
    - `ModuleRegistry` (`trading_bot/registry/module_registry.py`)
    - `ControlledObjectRegistry` (Should be merged into `AgentRegistry`)

## 5. Decision Engine
- **Canonical:** `DeepMindOrchestrator` (Internal to IAS)
- **File:** `trading_bot/core_agent_system/master_orchestrator.py`
- **Justification:** Uses Policy/Value evaluation and MCTS search for grounded decision making.
- **Redundant:**
    - `InnovativeDecisionEngine` (`trading_bot/decision_layer/`)
    - `AdversarialDecisionEngine`

## 6. Execution Layer
- **Canonical:** `TradeExecutor`
- **File:** `trading_bot/execution/trade_executor.py`
- **Justification:** Direct, low-latency interface with MT5 and Paper support, optimized for the production target.
- **Redundant:**
    - `ExecutionManager` (`trading_bot/core/execution_manager.py`)
    - `SmartExecutor` (`trading_bot/ultimate_production/smart_executor.py`)

## 7. Governance & Safety
- **Canonical:** `ConstitutionalAI` (Pre-execution) and `MSOS` (Runtime Veto)
- **File:** `trading_bot/core_agent_system/constitutional_layer.py`, `trading_bot/services/msos_service.py`
- **Justification:** Multi-stage defense-in-depth approach.
- **Redundant:**
    - `AdversarialVerification`
    - `DecisionGovernance`
