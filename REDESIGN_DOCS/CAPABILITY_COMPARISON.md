# AlphaAlgo Redesign: Capability Comparison & Gap Analysis

This document provides a detailed comparison between the current AlphaAlgo implementation and the redesigned Unified Cognitive Architecture (UCA).

---

## 1. Core Architectural Shift

| System | Current State | Target (UCA) | Gap |
| :--- | :--- | :--- | :--- |
| **Logic Root** | Heuristic Orchestrator | Cognitive System Controller | Consolidation of 3+ Brains. |
| **Agent State** | Transient (Task-based) | Persistent (Horizon-based) | Addition of Epistemic Beliefs. |
| **World Model** | Latent Transition (Next-Step) | Generative Simulator (Trajectories) | Path-based Rollouts. |
| **Decision Logic** | MCTS Search (Utility-only) | Active Inference (Utility + Information) | Information-Seeking behavior. |
| **Learning** | Stochastic GD (Offline) | Continual Bayesian Adaptation (Online) | Dynamic Policy Evolution. |

---

## 2. Agent Capabilities

| Capability | Legacy Agents | UCA PCA (Persistent Cognitive Agents) |
| :--- | :--- | :--- |
| **Planning** | Fixed depth; short horizon. | Recursive Goal Trees; Months/Years horizon. |
| **Reasoning** | ReAct Templates. | Simulation-Grounded Counterfactuals. |
| **Collaboration** | Message Bus (Pub/Sub). | Debate-Protocol (Adversarial Verdict). |
| **Memory Access** | Key-Value Lookups. | Hierarchical HMS Tier 1-6 Access. |
| **Self-Verification** | None (Orchestrator-level). | Internal "Lesson Learned" Feedback Loop. |

---

## 3. World Model Capabilities

| Capability | Legacy World Model | UCA GWM (Generative World Model) |
| :--- | :--- | :--- |
| **Rollouts** | Single-path (Greedy). | Multi-path (Stochastic/Intervention). |
| **Causality** | Correlations only. | SCM-driven Do-Calculus. |
| **Inspection** | Hidden (Latent) vectors. | Explicit Trajectory Projections (P/L/V). |
| **Counterfactuals** | None. | "What-If" Analysis across all layers. |
| **Calibration** | Simple MSE loss. | Epistemic Entropy & Calibration Metrics. |

---

## 4. Bottleneck Resolution Analysis

| Bottleneck | Resolution in UCA |
| :--- | :--- |
| **B1: Orchestration Conflict** | Unified under the **Cognitive System Controller**. |
| **B2: Cognitive Fragmentation** | Persistent State & Goal Hierarchies in **PCA**. |
| **B3: Simulation Gap** | **GWM** provides inspectable multi-horizon rollouts. |
| **B4: Un-grounded Learning** | All simulations anchored by **Rigorous Backtesting**. |
| **B5: Memory Window** | **6-Tier HMS** ensures evidence preservation. |

---

## 5. Migration Gap Requirements

1. **Software Engineering**:
    - Replacement of `IntegratedAgentSystem.execute_task` with UCA Cognitive Workflow.
    - Implementation of `PersistentCognitiveAgent` base class.
    - Upgrade of `FWM_DigitalTwin` to support intervention-based rollouts.
2. **Data Science**:
    - Training of Causal Structural Models for GWM.
    - Implementation of Variational Free Energy calculation for agents.
3. **Infrastructure**:
    - Migration of SQLite/JSON memory to a robust PostgreSQL-backed HMS.
    - Integration of GPU-accelerated parallel rollouts for GWM.
