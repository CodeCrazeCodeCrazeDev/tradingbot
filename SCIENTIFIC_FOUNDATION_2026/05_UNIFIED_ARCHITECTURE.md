# Phase 5: AlphaAlgo Unified Scientific Architecture (UCA-2026)

The UCA-2026 is a single, coherent cognitive architecture synthesized from the 16 foundational papers. It rejects the "Swarm Mirage" in favor of a **Unified Cognitive Controller** managing **Persistent Persistent Agents** via **Information Folding** and **Causal Sandboxing**.

---

## 1. The UCA-2026 Schematic

```mermaid
graph TD
    subgraph "Cognitive System Controller (CSC)"
        direction TB
        CSC_Brain["LLM Reasoner (Bayesian Objective)"]
        Folding_Operator["Information Folding Buffer (HIPIF)"]
        S2L_Router["Skill-to-LoRA Router (S2L)"]
    end

    subgraph "Hierarchical Memory System (HMS)"
        direction LR
        Episodic["Episodic (WMR Loop)"]
        Semantic["Semantic (Causal Evidence Graph)"]
        LoRA_Store["Procedural (S2L Adapters)"]
    end

    subgraph "Generative World Model (GWM)"
        direction TB
        SCM["Structural Causal Model (CWMI)"]
        Do_Calculus["Intervention Engine (Pearl's Do)"]
        Simulator["High-Fidelity Environment (Tick-Grounded)"]
    end

    subgraph "Persistent Cognitive Agents (PCA)"
        Macro["Macro Agent (Epistemic Core)"]
        Risk["Risk Agent (Bayesian Policy)"]
        Alpha["Alpha Agent (Socratic Discovery)"]
    end

    subgraph "Governance Shield"
        Evolution_Gate["Monotone-Safe Gate (RSEA)"]
        Risk_Limit["Immutable Exposure Limits (Safety Gate)"]
    end

    CSC_Brain --> Folding_Operator
    CSC_Brain --> S2L_Router
    S2L_Router --> LoRA_Store
    CSC_Brain --> SCM
    SCM --> Do_Calculus
    Do_Calculus --> Simulator
    CSC_Brain --> PCA
    PCA --> Semantic
    Semantic --> Episodic
    CSC_Brain --> Governance_Shield
```

---

## 2. Core Architectural Pillars

### 2.1 The Unified Cognitive Controller (CSC)
*   **Role**: The "One Brain." Replaces every existing orchestrator.
*   **Mechanism**: Implements **Active Inference** (Minimizing Free Energy) as its global objective. It manages the lifecycle of all PCAs and governs the flow of information.
*   **Context Management**: Uses the **Folding Operator** to compress interaction logs every time a subgoal is reached.

### 2.2 Persistent Cognitive Agents (PCA)
*   **Role**: Specialized reasoning entities that carry state across market sessions.
*   **Mechanism**: Each PCA has an **Epistemic Core** (Bayesian Belief State). They do not communicate via raw text but via **Transactive Memory** (sharing artifacts in the Semantic Graph).
*   **Efficiency**: PCAs use **S2L LoRA Adapters** to execute standardized trading behaviors without prompt overhead.

### 2.3 The Causal World Model (GWM)
*   **Role**: The system's "Imagination" and "Risk Simulator."
*   **Mechanism**: A **Structural Causal Model (SCM)** that maps the causal relationships between market variables. It supports **Counterfactual Reasoning** ("What if I had taken trade X?").
*   **Grounding**: Grounded in the **High-Fidelity Environment**, which uses real tick data and order book depth, eliminating the "Delusion Loop."

### 2.4 The Causal Evidence Graph (HMS)
*   **Role**: The source of truth for all research and decision-making.
*   **Mechanism**: Replaces passive RAG with a **Graph of Evidence**. Every claim (e.g., "Market is Bullish") must be logically linked to a source (e.g., "CPI Data") and a mechanism (e.g., "Rate Cut Expectation").

---

## 3. The OSA Loop (Observe-Simulate-Act)

1.  **Observe**: Ingest multi-modal data; update the **Epistemic Core** of relevant PCAs.
2.  **Simulate (Sandbox)**:
    *   Propose a plan branch.
    *   Query the GWM for a **Structural Intervention** ($do(X)$).
    *   Analyze the distribution of world states and calculate **Expected Value (EV)**.
3.  **Act**:
    *   Select the policy that minimizes **Expected Free Energy**.
    *   Activate the required **S2L LoRA** (e.g., `ExecutionLoRA`).
    *   Execute via institutional adapters.
4.  **Reflect**:
    *   Use **SocraticPO** feedback from the Backtest Engine to diagnose errors.
    *   **Fold** the subgoal history into the Semantic Graph.

---

## 4. Safety & Evolution Governance

*   **Immutable Shield**: The Governance Shield is a separate, non-bypassable layer. No trade can exceed exposure limits, regardless of the CSC's "Reasoning."
*   **Strict Evolution Gate**: Any self-proposed code or parameter change must pass a **Held-out Backtest Set** with a strict "Gain Metric" check. If it does not improve performance, it is rejected and logged.
