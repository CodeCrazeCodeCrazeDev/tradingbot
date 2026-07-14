# Codebase Mapping Audit (UCA V5)

This document maps the synthesized UCA V5 research principles to the existing AlphaAlgo codebase and identifies specific gaps for refactoring.

---

## 1. Subsystem Mapping Matrix

| Research Principle | Paper(s) | Target Codebase Subsystem | Audit Status |
| :--- | :--- | :--- | :--- |
| **Shared-Log Backbone** | LogAct | `trading_bot/core/unified_event_bus.py` | **Partial**: `UnifiedDecisionBus` exists as a singleton but lacks the "Voter" and "Recovery" logic of LogAct. |
| **Mixed-channel Reasoning**| DiscoLoop | `trading_bot/core/csc/controller.py` | **Missing**: Logic is currently standard LLM reasoning; no discrete-continuous looping. |
| **Self-evolving Graph-Memory**| SAGE | `trading_bot/core/hms/memory.py` | **Partial**: `HMS` exists but treats memory as static research snapshots; lacks self-evolution/graph-feedback. |
| **Skill Programs** | HASP | `trading_bot/core/csc/router.py` | **Missing**: Subsystem not found. Skills are currently prompts in `trading_bot/skills/`. |
| **Context-Dependent Validity**| QKG | `trading_bot/core/hms/models.py` | **Missing**: Triplets in Evidence Graph lack context-dependent validity functions. |
| **Information Folding** | HIPIF | `trading_bot/core/csc/folding.py` | **Partial**: Skeleton exists but is not fully integrated into the `CSC` behavioral loop. |
| **Monotone-Safe Gate** | RSEA | `trading_bot/governance/evolution_gate.py` | **Partial**: Basic gate logic exists; needs integration with "Gain Metric" and held-out validation. |
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
