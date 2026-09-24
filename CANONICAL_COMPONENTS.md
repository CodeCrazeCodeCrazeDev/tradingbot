# Canonical Components Audit (Phase 5.3)

This document identifies the authoritative implementation for each major subsystem in the AlphaAlgo ecosystem. All other overlapping implementations are marked as Redundant/Legacy.

> ## ⚠️ Verified Runtime Reality and Authority Hierarchy (2026-09-23)
>
> `ARCHITECTURE_COMPONENT_MANIFEST.json` is the machine-readable companion to this document. The active foundation uses a hybrid modular-monolith hierarchy:
>
> | Authority | Canonical implementation | Responsibility |
> |---|---|---|
> | Composition root | `trading_bot/foundation/runtime.py::ModularMonolithRuntime` -> `UnifiedTradingBot` | Public application boundary delegates lifecycle to the single runtime graph for replay, paper, and future live profiles. |
> | Strategic coordinator | `trading_bot/core/csc/controller.py::CognitiveSystemController` | Sole production decision coordinator and lifecycle-owned strategic pipeline. |
> | Tactical cognition | `trading_bot/cognition/orchestrator.py::AlphaAlgoCognitiveBrain` | Perception, state, simulation, reasoning, verification, calibration, and proposal service invoked by the coordinator. |
> | Decision/audit bus | `trading_bot/core/unified_event_bus.py::UnifiedDecisionBus` | Ordered action log, voter consensus, fail-closed capital-action dispatch. |
> | Component registry | `trading_bot/core/unified_registry.py::UnifiedComponentRegistry` | Single discovery, metadata, dependency, and lifecycle inventory. |
> | Portfolio risk | `trading_bot/risk/service.py::CanonicalRiskService` | One deterministic portfolio-level risk and position-sizing authority; `risk_manager.py` remains the compatibility surface during extraction. |
> | Final safety gate | `trading_bot/core/immutable_shield.py::ImmutableShield` | Deterministic, non-bypassable veto for capital-moving actions. |
> | Execution service | `trading_bot/execution/service.py::CanonicalExecutionService` | Idempotent execution boundary; `PaperBrokerAdapter` is the reference adapter while legacy bridges and live venues converge. |
>
> Existing IAS, MTASH, `UnifiedAIBrain`, legacy orchestrators, registries, risk managers, and direct broker implementations are not independent authorities. They must be classified as adapters, research-only components, compatibility façades, archive candidates, or quarantined modules in the manifest.
>
> The five-way brain contradiction is resolved as an authority hierarchy: CSC coordinates the production path; `AlphaAlgoCognitiveBrain` supplies tactical cognition; all other brains are non-authoritative compatibility or research surfaces.

---

## 1. Orchestration (The Brain)
- **Canonical:** `CognitiveSystemController` (strategic coordinator)
- **File:** `trading_bot/core/csc/controller.py`
- **Tactical service:** `AlphaAlgoCognitiveBrain` (`trading_bot/cognition/orchestrator.py`)
- **Justification:** CSC owns the production decision path; the tactical brain supplies the coherent perception-to-risk proposal loop. Both are composed by `UnifiedTradingBot`.
- **Redundant/compatibility:**
    - `IntegratedAgentSystem` (`trading_bot/core_agent_system/integrated_system.py`)
    - `MasterOrchestrator` (root)
    - `TradingOrchestrator` (`trading_bot/core/orchestrator.py`)
    - `AAMISMasterOrchestrator` (`trading_bot/aamis_v3/aamis_master_orchestrator.py`)

## 2. World Model (The Simulator)
- **Canonical boundary:** `WorldModelPort`
- **File:** `trading_bot/foundation/ports.py`
- **Active implementations:** `trading_bot/world_model/v2_core.py` and `trading_bot/world_model/causal/gwm.py`
- **Justification:** A universal async port prevents sync/async contradictions while allowing replay-grounded predictive and causal implementations to converge behind one boundary.
- **Migration rule:** Implementations may be selected by profile, but no implementation may become a second orchestration path or directly authorize execution.

## 3. Memory (The Knowledge Base)
- **Canonical runtime:** `HierarchicalMemorySystem`
- **File:** `trading_bot/core/hms/memory.py`
- **Tactical memory service:** `HierarchicalMemoryEngine` (`trading_bot/cognition/memory/engine.py`)
- **Justification:** HMS is the shared evidence/memory substrate; the tactical engine is a cognition-facing adapter, not a competing persistence authority.
- **Compatibility:** `MemorySystem` (`trading_bot/core_agent_system/memory_system.py`) and other legacy stores must delegate or be classified in the manifest.

## 4. Component Discovery (The Registry)
- **Canonical:** `UnifiedComponentRegistry`
- **File:** `trading_bot/core/unified_registry.py`
- **Justification:** It is the single registry used by the active runtime and exposes the compatibility methods required by legacy callers. Lifecycle and dependency metadata are being hardened incrementally.
- **Redundant/compatibility:**
    - `ServiceRegistry` (`trading_bot/core/service_registry.py`)
    - `SystemRegistry` (`trading_bot/system_registry.py`)
    - `ModuleRegistry` (`trading_bot/registry/module_registry.py`)
    - `AgentRegistry` declarations without a verified implementation
    - `ControlledObjectRegistry`

## 5. Decision Engine
- **Canonical coordinator:** `CognitiveSystemController`
- **File:** `trading_bot/core/csc/controller.py`
- **Tactical decision service:** `AlphaAlgoCognitiveBrain` (`trading_bot/cognition/orchestrator.py`)
- **Justification:** The coordinator owns the production pipeline while the tactical service performs evidence-grounded proposal synthesis and risk gating.
- **Compatibility/research:**
    - `DeepMindOrchestrator` (`trading_bot/core_agent_system/master_orchestrator.py`)
    - `InnovativeDecisionEngine` (`trading_bot/decision_layer/`)
    - `AdversarialDecisionEngine`

## 6. Execution Layer
- **Canonical boundary:** `ExecutionService` and `BrokerAdapter`
- **Contracts:** `trading_bot/foundation/ports.py`
- **Transitional implementation:** `trading_bot/core/execution_bridge.py` and `trading_bot/execution/trade_executor.py`
- **Reference adapter:** `PaperExecutionBridge`
- **Migration rule:** Paper, MT5, crypto, IB, futures, and options venues must implement the same adapter contract; strategies and agents may not call broker clients directly.

## 7. Governance & Safety
- **Canonical final gate:** `ImmutableShield`
- **File:** `trading_bot/core/immutable_shield.py`
- **Contract:** `GovernanceGate` (`trading_bot/foundation/ports.py`)
- **Supporting policies:** `EvolutionGate`, human approval, compliance, and adversarial verification may advise or veto, but cannot bypass the shield.
- **Justification:** One deterministic, non-bypassable gate prevents split-brain approval semantics while preserving defense-in-depth voters.
