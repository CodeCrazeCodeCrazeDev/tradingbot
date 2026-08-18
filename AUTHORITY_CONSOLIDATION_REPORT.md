# AUTHORITY CONSOLIDATION SPECIFICATION
**AlphaAlgo Single-Authority Enforcement Architecture (UCA-2026)**
**Status:** FACT & EVIDENCE AUDIT
**Date:** 2026-03-30

---

## 1. AUTHORITY SELECTION & REJECTION MATRIX

[FACT] Based on Phase 0 discovery evidence, AlphaAlgo consolidates duplicate, fragmented, and legacy implementations into exactly **ONE authoritative implementation** for every security-sensitive operation:

| Authority Domain | Selected Authoritative Implementation | Rejected Duplicates / Legacy Wrappers | Consolidation & Migration Plan |
| :--- | :--- | :--- | :--- |
| **Agent Identity** | `trading_bot/agents/multi_agent_debate.py::TradingAgent` | `intelligence_core/agent_army.py`, `agent_swarm.py` | Enforce `TradingAgent` as sole identity class. Redirect legacy calls. |
| **Messaging Authority** | `trading_bot/core/unified_event_bus.py::UnifiedDecisionBus` | `core/event_bus.py`, `agent_swarm.py::AgentMessage` | Mandate `SignedInterAgentMessage` passing through `UnifiedDecisionBus`. |
| **Persistent Memory** | `trading_bot/core/hms/memory.py::HierarchicalMemorySystem` | `foundation_agents/cognitive_core/memory_system.py`, `structural_memory.py` | Wrap persistent memory around HMS with `ProvenanceAwareMemoryRecord`. |
| **Governance Root** | `trading_bot/governance/evolution_gate.py::EvolutionGate` | `intelligence_core/governance.py`, `gets/core/governance_promotion.py` | Consolidate model promotion into `EvolutionGate`. Lock governance root. |
| **Risk Authorization** | `trading_bot/risk/MASTER_risk_manager.py::MasterRiskManager` | `unified_risk_manager.py`, `advanced_risk_manager.py` | Mandate pre-trade risk stamping via `MasterRiskManager`. |
| **Execution Boundary** | `trading_bot/core/csc/controller.py::CognitiveSystemController` | `execution/advanced_execution.py`, `execution_agent.py` | Enforce CSC + `ImmutableShield` as sole live order route. |
| **Audit Logging** | `trading_bot/security/audit_logging.py::AuditLogger` | `foundation_agents/safety/audit_logger.py`, `advanced_security.py` | Direct all security audit events to `AuditLogger`. |
| **Kill Switch** | `trading_bot/core/emergency_kill_switch.py::EmergencyKillSwitch` | `aamis_v3/meta/meta_systems.py`, `circuit_breaker.py` | Bind global kill switch to `EmergencyKillSwitch` singleton. |

---

## 2. BYPASS ELIMINATION VERIFICATION

[PROPOSED DESIGN] All potential bypass paths are systematically eliminated:
- **Direct Imports:** Legacy classes deprecated and replaced with import redirects.
- **Alternate APIs:** Direct broker order submission functions wrapped by `ImmutableShield` check gates.
- **Test Fixtures:** Mocks (`MockRiskManager`) prohibited in live execution pipelines.
- **Async & Background Tasks:** Unified bus enforces payload signature checking across async task boundaries.
- **Environment Variables:** Direct secret overrides guarded by `secureconfig.py`.
