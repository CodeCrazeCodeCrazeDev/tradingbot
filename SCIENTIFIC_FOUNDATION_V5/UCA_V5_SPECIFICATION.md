# UCA V5 Superior Architecture Specification (July 2026)

This document specifies the authoritative Unified Cognitive Architecture (UCA) V5, synthesized from 24 high-impact research papers. UCA V5 represents the pinnacle of autonomous institutional financial intelligence, prioritizing reliability, causal reasoning, and self-evolution.

---

## 1. Architectural Philosophy: The "One Brain" SMR

UCA V5 rejects the "Swarm Mirage" (Effective Agents, 2025) in favor of a **Unified Cognitive Controller (CSC)** governed by **State Machine Replication (SMR)** principles (LogAct, 2026). The entire system operates as a deconstructed state machine playing a **Shared-Log Backbone**.

### 1.1 The LogAct Backbone
*   **Mechanism**: All agent actions are serialized into an immutable, totally ordered Shared Log *before* execution.
*   **Reliability**: Enables semantic recovery, decoupled voting (Governance Shield), and deterministic auditability.
*   **Transactional Integrity**: Every market intervention is a "Log Entry" that must be approved by the `VerificationSwarm` and `GovernanceShield` before the "Execution Agent" can consume it.

---

## 2. Core Components

### 2.1 Cognitive System Controller (CSC)
*   **Objective**: Minimizing **Variational Free Energy (VFE)** (Active Inference).
*   **Reasoning Backbone**: **DiscoLoop** mixed-channel architecture. Integrates symbolic discrete embeddings with continuous hidden states for multi-hop causal reasoning.
*   **Intervention Logic**: Uses **HASP (Harnessing Agents with Skill Programs)**. Skills are no longer prompts but executable state-action intervention functions that trigger within the loop.

### 2.2 Hierarchical Memory System (HMS) V5
*   **Substrate**: **SAGE (Self-evolving Agentic Graph-Memory)**. Replaces static RAG with a dynamic, structure-aware graph that improves through Reader-Writer feedback loops.
*   **Evidence Grounding**: **Quantum Knowledge Graph (QKG)**. Triplet validity is context-dependent (e.g., a technical signal's validity depends on the market regime context).
*   **Population Reuse**: **MATM (Multi-Agent Transactive Memory)**. PCAs (Persistent Cognitive Agents) share "Lessons" and "Artifacts" via the Shared Log and Graph Memory.

### 2.3 Generative World Model (GWM) V3
*   **Backbone**: Transformer-Mamba hybrid (V2 Baseline) upgraded with **CWMI (Causal World Model Induction)**.
*   **Function**: Supports **Structural Interventions** ($do(X)$) using Pearl's Do-Calculus to simulate counterfactual market futures.
*   **Validation**: Grounded in high-fidelity backtest replays, eliminating the "Delusion Loop."

---

## 3. The Behavioral Loop (HASP + S2L)

1.  **Observe**: CSC ingests data via the Shared Log.
2.  **Hypothesize**: DiscoLoop generates competing multi-hop causal branches.
3.  **Simulate**: GWM runs counterfactual rollouts for each branch ($do(trade)$).
4.  **Decide**: CSC selects the policy minimizing **Expected Free Energy (EFE)**.
5.  **Act**: CSC activates a **HASP Skill Program** or a **Skill-to-LoRA (S2L)** adapter to execute the behavior.
6.  **Verify**: Action is written to the LogAct Backbone; Voters (Shield/Swarm) audit; Approved actions move to Execution.

---

## 4. Self-Evolution & Governance

### 4.1 The Evolution Gate
*   **Mechanism**: **RSEA (Recursive Self-Evolving Agents)** via Held-Out Selection.
*   **Safety**: Updates to Strategy or Skills must pass a strict "Monotone-Safe" check on a held-out backtest set.
*   **Optimization**: **EKSFT (Entropy-KL Selective Fine-Tuning)** ensures self-rewrites preserve critical risk-management anchors while optimizing alpha discovery.

### 4.2 The Immutable Shield
*   **Authority**: A non-bypassable, out-of-band voter in the LogAct backbone.
*   **Logic**: Hard-coded risk bounds (Exposure, Drawdown, Compliance) that veto any log entry violating the safety state.
