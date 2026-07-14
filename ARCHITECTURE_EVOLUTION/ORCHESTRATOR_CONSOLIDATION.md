# Legacy Orchestrator Inventory and UCA V5 Mapping

This document tracks the systematic consolidation of fragmented legacy orchestrators into the authoritative UCA V5 "One Brain" architecture (CSC + IAS).

## 1. Inventory of Orchestrators

| Legacy Orchestrator | Responsibilities | Status | UCA V5 Destination |
| :--- | :--- | :--- | :--- |
| `MasterOrchestrator` | System lifecycle, event routing, module management. | Archived | `UnifiedDecisionBus`, `UnifiedComponentRegistry`, `IAS`. |
| `AAMISMasterOrchestrator` | Multi-agent autonomous intelligence, strategic planning. | Target Archive | `CognitiveSystemController` (CSC). |
| `HivemindOrchestrator` | Consensus, collective memory, "neural mesh". | Target Archive | `VerificationSwarm`, `HMS`. |
| `MOSEFSOrchestrator` | Multi-objective optimization, self-evolution. | Target Archive | `EvolutionGate`, `CSC`. |
| `MasterSystemHub` | Central integration, system-wide config. | Target Archive | `UnifiedComponentRegistry`, `IAS`. |
| `SuperPowerfulOrchestrator`| High-level mission planning. | Target Archive | `CSC` (Strategic Reasoning). |
| `AnalysisOrchestrator` | Coordinating market analysis signals. | Target Archive | `IAS` (Tactical Specialists). |

## 2. Capability Mapping Detail

### 2.1 AAMIS (Automated Autonomous Multi-agent Intelligence System)
- **Capability**: Autonomous research and strategy generation.
- **Migration**: Ported to `trading_bot/core_agent_system/scientific_reasoning/`.
- **Status**: Logic internalized by CSC.

### 2.2 Hivemind (Collective Consciousness)
- **Capability**: Multi-agent consensus reaching.
- **Migration**: Logic mapped to `trading_bot/core/verification/swarm.py` (Verification Swarm) and `AgentNegotiator` in IAS.
- **Status**: Consensus mechanism unified under LogAct Voter pattern.

### 2.3 MOSEFS (Multi-Objective Self-Evolving Financial System)
- **Capability**: Recursive self-improvement and evolution.
- **Migration**: Logic mapped to `trading_bot/governance/evolution_gate.py`.
- **Status**: Monotone-safe rule enforcement centralized.

## 3. Consolidation Progress

- [x] Identify redundant orchestrators.
- [ ] Create compatibility shims for critical entry points.
- [ ] Archive code to `_archive/legacy_orchestrators/`.
- [ ] Verify zero-bypass of CSC via Architectural Enforcement Tests.
