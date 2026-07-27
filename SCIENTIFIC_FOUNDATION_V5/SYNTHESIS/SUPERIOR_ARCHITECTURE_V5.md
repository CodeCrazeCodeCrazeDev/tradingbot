# Superior Architecture Design: AlphaAlgo UCA V5 (July 2026)

This document defines the "Superior Architecture" of AlphaAlgo V5, synthesized from 34 authoritative research papers. It resolves fundamental conflicts between autonomous evolution and institutional safety through a multi-layered, formally verified design.

---

## 1. The "One Brain" Recursive Active Inference Pipeline

The core of AlphaAlgo V5 is a 12-step **Recursive Active Inference** pipeline governed by the `CognitiveSystemController` (CSC). This pipeline unifies perception, reasoning, and action under a single objective: **Minimizing Variational Free Energy (VFE)**.

### The 12-Step Pipeline:
1.  **Observation Ingestion**: Streaming market data (tick/orderbook/macro).
2.  **Surprise Calculation**: Measuring deviation from World Model predictions.
3.  **Evidence Collection (SAGE/QKG)**: Multi-hop graph retrieval filtered by context-dependent validity.
4.  **HASP Intervention**: Execution of hard-coded Skill Programs (guardrails) based on observation.
5.  **Multi-Hypothesis Generation (DiscoLoop)**: Generating diverse market scenarios using discrete-continuous reasoning.
6.  **Causal Simulation (CausalEvolve)**: Interventional rollouts ($do(x)$) using the Causal Scratchpad.
7.  **Decision Synthesis**: Optimizing Expected Value (EV) over the hypothesis space.
8.  **LogAct Action Proposal**: Appending the intended action to the authoritative Shared Log.
9.  **Voter Consensus (Verification Swarm)**: Parallel validation by specialized agents (Risk, Logic, Compliance).
10. **Execution via Decision Bus**: Transactional commitment of approved actions.
11. **Outcome Monitoring**: Real-time feedback collection and drift detection.
12. **Information Folding (HIPIF)**: Semantic compression of the episode into long-term memory.

---

## 2. Shared-Log Backbone (LogAct Architecture)

AlphaAlgo V5 replaces the fire-and-forget message bus with a **LogAct Shared Log**.

*   **Transactional Integrity**: Every strategic decision is a log entry that must be "voted" on before it becomes an "Action".
*   **Deterministic Recovery**: The system state is defined as `State = FoldedMemory + SharedLog`. This ensures 100% recovery to the exact tick/logical state.
*   **Decoupled Verification**: Voters (Governance Shield, Hallucination Detector) read the log and post "Veto" or "Approve" signals asynchronously, ensuring zero-bypass safety.

---

## 3. Resolving the Evolution-Governance Conflict

### Conflict: ACE (Self-Evolving Code) vs. LogAct (Immutable Governance)
*   **The Solution: Hierarchical Sandboxing & Formal Invariants.**
    *   **The Task Layer (Mutable)**: The `TaskAgent` and `ToolRegistry` are managed by the **ACE (Adversarial Coding Evolution)** engine. It can rewrite its own logic, add new indicators, and refine research steps based on backtest failures.
    *   **The Meta Layer (Governed)**: All code changes proposed by ACE are treated as "LogAct Actions". They must pass the **Evolution Gate (RSEA)**.
    *   **The Governance Layer (Immutable)**: The `EvolutionGate`, `ImmutableShield`, and `RiskEngine` are **Formally Verified** (Proof Search). They use deterministic logic and dependent types (Lean-inspired) to ensure that even if the Task Agent evolves, it can NEVER propose a change that violates institutional risk bounds (e.g., "Exposure > $10M" or "Modify Governance Code").

---

## 4. Memory Tiering (SAGE + SimpleMem + L2CL)

V5 implements a **Hierarchical Memory System (HMS)** with dynamic tiering:

*   **Tier 0: Working Memory (DiscoLoop)**: Latent states and discrete tokens for active reasoning.
*   **Tier 1: Episodic Memory (SimpleMem)**: Gated linear attention for fast, recent history retrieval.
*   **Tier 2: Semantic Knowledge (SAGE)**: Self-evolving graph-memory where nodes are Alpha Insights and edges are context-sensitive causal links (QKG).
*   **Tier 3: Meta-Memory (L2CL)**: Task-specific memory schemas evolved via meta-learning for different asset classes.

---

## 5. Causal World Model (World Model V5)

The world model is no longer a simple predictor; it is a **Causal Intervention Engine**.

*   **Causal Scratchpad (CausalEvolve)**: Maintains a persistent DAG of market drivers.
*   **Interventional Planning**: Instead of asking "What will happen?", the agent asks "What happens if I execute this 50-lot order given the current OBI?"
*   **Counterfactual Reasoning**: Post-trade, the agent performs "Abduction-Action-Prediction" to understand why a trade failed (e.g., "If volatility hadn't spiked, would the stop have been hit?").

---

## 6. Institutional Validation (FIRE + CL-Bench)

V5 architectural integrity is measured by two primary benchmarks:
1.  **FIRE (Domain Intelligence)**: 3,000-question institutional finance exam evaluating the bot's macro, risk, and portfolio logic.
2.  **CL-Bench (Learning Gain)**: Measuring the "Gain Metric" to ensure the system is genuinely improving from market data rather than just relying on pre-trained capability.

---

## 7. Mathematical Objective: Formal Active Inference

The entire system optimizes for the **Unified Free Energy Objective**:
$$\mathcal{F} = \text{Complexity} - \text{Accuracy} + \lambda \cdot \text{RiskViolation}$$
Where:
*   **Complexity**: Information cost of the internal model.
*   **Accuracy**: Alignment with market observations.
*   **RiskViolation**: Formal penalty for approaching safety bounds (Logic Invariants).

By minimizing $\mathcal{F}$, AlphaAlgo V5 becomes a **Safe Superintelligence**: it explores for Alpha aggressively while being mathematically constrained by the institutional shield.
