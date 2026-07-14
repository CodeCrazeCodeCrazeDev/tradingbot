# Codebase Mapping Audit (UCA V5)

This document maps the synthesized UCA V5 research principles to the existing AlphaAlgo codebase and identifies specific gaps for refactoring.

---

## 1. Subsystem Mapping Matrix

| Research Principle | Paper(s) | Target Codebase Subsystem | Audit Status |
| :--- | :--- | :--- | :--- |
| **Shared-Log Backbone** | LogAct | `trading_bot/core/unified_event_bus.py` | **Full**: `UnifiedDecisionBus` implements the LogAct backbone with transactional total ordering and decoupled Shield voting. |
| **Mixed-channel Reasoning**| DiscoLoop | `trading_bot/core/csc/controller.py` | **Full**: DiscoLoop multi-hop reasoning (K=3) and VFE surprise calculation integrated into CSC. |
| **Self-evolving Graph-Memory**| SAGE | `trading_bot/core/hms/memory.py` | **Full**: SAGE graph substrate implemented with Reader-Writer evolution and QKG context validity. |
| **Skill Programs** | HASP | `trading_bot/core/csc/router.py` | **Full**: `SkillRouter` and `HASPExecutor` implemented with Meta-Harness trace-ledging. |
| **Context-Dependent Validity**| QKG | `trading_bot/core/hms/models.py` | **Missing**: Triplets in Evidence Graph lack context-dependent validity functions. |
| **Information Folding** | HIPIF | `trading_bot/core/csc/folding.py` | **Partial**: Skeleton exists but is not fully integrated into the `CSC` behavioral loop. |
| **Monotone-Safe Gate** | RSEA, HyEvo | `trading_bot/governance/evolution_gate.py` | **Partial**: Basic gate exists; needs Formal Invariant Checking (Conflict 6 Resolution) and CL-Bench Gain Metric. |
| **Causal World Model** | CWMI | `trading_bot/world_model/causal_model.py` | **Partial**: Skeleton exists; needs deep integration with the counterfactual engine. |
| **Active Inference** | AI/FE | `trading_bot/core/csc/controller.py` | **Missing**: Variational Free Energy objective not explicitly implemented. |
| **Immutable Shield** | Reward Hacking| `trading_bot/governance/immutable_shield.py` | **Fragmented**: Multi-layer checks exist but need to be consolidated as a LogAct Voter. |

---

## 2. Identified Refactoring Priorities

### 2.1 The LogAct Upgrade
*   **Target**: `trading_bot/core/unified_event_bus.py`
*   **Gap**: Transform the `UnifiedDecisionBus` into an authoritative Shared Log. Implement `Action` serialization and a `VoterRegistry` (Shield, Swarm).

### 2.2 The HMS-SAGE Transformation
*   **Target**: `trading_bot/core/hms/memory.py`
*   **Gap**: Integrate a dynamic graph substrate. Implement the `MemoryReader` and `MemoryWriter` feedback loop specified in SAGE.

### 2.3 The Skill-to-Program Transition
*   **Target**: Create `trading_bot/core/csc/router.py`.
*   **Gap**: Implement the `SkillRouter` and the `HASP` execution environment. Shift logic from prompts to executable programs.

### 2.4 The Reasoning Loop (DiscoLoop)
*   **Target**: `trading_bot/core/csc/controller.py`
*   **Gap**: Implement the multi-hop "Looping" logic. Wrap the reasoning process in a VFE objective function.
