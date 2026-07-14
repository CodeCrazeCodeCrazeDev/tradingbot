# Codebase Mapping Audit (UCA V5)

This document maps the synthesized UCA V5 research principles to the AlphaAlgo codebase.

---

## 1. Subsystem Mapping Matrix

| Research Principle | Paper(s) | AlphaAlgo Source File(s) | Status |
| :--- | :--- | :--- | :--- |
| **Shared-Log Backbone** | LogAct | `trading_bot/core/unified_event_bus.py` | **Partial**: Logic exists but needs hardening (sequence management, voter timeout). |
| **Active Inference Loop** | VFE / AI | `trading_bot/core/csc/controller.py` | **Partial**: 12-step pipeline skeleton exists; needs explicit VFE minimization logic. |
| **Discrete-Continuous Recurrence** | DiscoLoop | `trading_bot/core/csc/controller.py` | **Missing**: Continuous hidden state tracking and discrete realignment. |
| **Information Folding** | HIPIF | `trading_bot/core/csc/folding.py` | **Partial**: Basic operator exists; needs integration into the CSC execution loop. |
| **Self-Evolving Graph-Memory** | SAGE | `trading_bot/core/hms/memory.py` | **Partial**: Basic graph exists; lacks Reader-Writer feedback and active pruning. |
| **Scientific Amnesia** | MSCL | `trading_bot/core/hms/memory.py` | **Missing**: Surprise-driven replay and principled forgetting. |
| **Monotone-Safe Gate** | RSEA | `trading_bot/governance/evolution_gate.py` | **Partial**: Gate exists; needs integration with gain metrics and held-out sets. |
| **Causal World Model** | CWMI | `trading_bot/world_model/causal_model.py` | **Partial**: SCM skeleton exists; needs deep integration with counterfactual engine. |
| **Executable Guardrails** | HASP | `trading_bot/core/csc/router.py` | **Missing**: System not found. Skills are currently prompts. |
| **Behavioral Internalization** | S2L | `trading_bot/core/csc/router.py` | **Missing**: No LoRA-adapter routing logic. |
| **Bayesian DI** | Bayesian DI | `trading_bot/core/risk/unified_risk_engine.py` | **Partial**: Calibration logic needed. |
| **Failure Attribution** | HORIZON | `trading_bot/validation/failure_analyst.py` | **Partial**: Trace logging exists; needs taxonomy-based attribution. |

---

## 2. Specific Audit Findings

### 2.1. The "Delusion Loop" (Scientific Amnesia)
The current `HierarchicalMemorySystem` in `memory.py` stores research snapshots indefinitely. Without the **MSCL** (principled forgetting) mechanism, the agent suffers from "context saturation" where stale hypotheses interfere with new regime data.

### 2.2. Functional Fragmentation (One Brain vs. Swarms)
The `CognitiveSystemController` (CSC) is currently siloed from the `VerificationSwarm`. The **LogAct** synthesis requires these to be coupled via a shared log, where the CSC proposes and the Swarm votes.

### 2.3. Heuristic vs. Causal Simulation
The `WorldModel` currently uses linear propagation. Implementing **CWMI** (Causal Induction) and **Digital Twin** principles is necessary to support Pearl's "do-calculus" for market impact.
