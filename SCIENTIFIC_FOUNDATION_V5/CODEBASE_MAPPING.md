# Codebase Mapping Audit (UCA V5)

This document maps the synthesized UCA V5 research principles to the AlphaAlgo codebase.

---

## 1. Subsystem Mapping Matrix

| Research Principle | Paper(s) | AlphaAlgo Source File(s) | Status |
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

## 2. Specific Audit Findings

### 2.1. The "Delusion Loop" (Scientific Amnesia)
The current `HierarchicalMemorySystem` in `memory.py` stores research snapshots indefinitely. Without the **MSCL** (principled forgetting) mechanism, the agent suffers from "context saturation" where stale hypotheses interfere with new regime data.

### 2.2. Functional Fragmentation (One Brain vs. Swarms)
The `CognitiveSystemController` (CSC) is currently siloed from the `VerificationSwarm`. The **LogAct** synthesis requires these to be coupled via a shared log, where the CSC proposes and the Swarm votes.

### 2.3. Heuristic vs. Causal Simulation
The `WorldModel` currently uses linear propagation. Implementing **CWMI** (Causal Induction) and **Digital Twin** principles is necessary to support Pearl's "do-calculus" for market impact.
