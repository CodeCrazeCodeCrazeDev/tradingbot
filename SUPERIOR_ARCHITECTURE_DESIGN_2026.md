# AlphaAlgo Superior Architecture: The Unified Cognitive Architecture (UCA-2026)

This document synthesizes the engineering principles from 16 foundational papers into a superior architecture for the AlphaAlgo Institutional Financial Intelligence system.

---

## 1. The Architectural Synthesis

The UCA-2026 rejects the "Swarm Mirage" (fragmented orchestrators) and the "Delusion Loop" (random simulators) in favor of a **Unified Cognitive Controller** managing **Persistent Persistent Agents** via **Information Folding** and **Causal Sandboxing**.

### 1.1 The "One Brain" Controller (CSC)
*   **Synthesis of**: *Effective Agents*, *Active Inference*, *Strategic DI*.
*   **Design**: A single high-capability **Cognitive System Controller (CSC)** governed by the Variational Free Energy (VFE) objective. It replaces 82+ redundant orchestrators with strict, debuggable **Trading Workflows**.
*   **Objective**: Minimize "Systemic Surprise" (Portfolio Error) while maximizing "Epistemic Gain" (Market Discovery).

### 1.2 Hierarchical Strategic Folding (HSF)
*   **Synthesis of**: *HIPIF*, *Memory Survey*, *RSEA*.
*   **Design**: Tasks are decomposed into a **Subgoal Tree**. Interaction logs are processed through a **Folding Operator** that compresses raw execution traces into "Semantic Lessons" once a subgoal is achieved.
*   **Outcome**: Prevents strategic drift and context-window saturation during long-horizon trading sessions.

### 1.3 The Generative World Model (GWM) with Causal Sandboxing
*   **Synthesis of**: *CWMI*, *Active Inference*, *Strategic DI*.
*   **Design**: A hybrid Transformer-Mamba world model grounded in real tick data. It supports **Counterfactual Interventions** (Pearl's Do-Calculus) to simulate "What If" scenarios (e.g., market impact, tail-risk events).
*   **Grounding**: Replaces Gaussian noise with **High-Fidelity Replay** and **Backtest-Oracle feedback**.

### 1.4 Hierarchical Memory System (HMS) & Transactive Memory
*   **Synthesis of**: *Memory Survey*, *MATM*, *Agents-K1*.
*   **Design**: A multi-tier memory architecture:
    1.  **Episodic**: Recent execution traces (WMR loop).
    2.  **Semantic**: A **Causal Evidence Graph** of market entities, claims, and provenance (replaces flat JSON logs).
    3.  **Procedural**: A library of **Skill-to-LoRA (S2L)** behavioral adapters for stable execution.
*   **Transactive Loop**: PCAs (Macro, Risk, Alpha) share compressed artifacts in the shared Semantic Graph.

### 1.5 Diagnostic Policy Optimization & Evolution Gate
*   **Synthesis of**: *SocraticPO*, *RSEA*, *CL-Bench*, *Self-Harness*.
*   **Design**: Self-improvement is not a stub but a **Strict Keep-Better Gate**.
    *   **Teacher**: A deterministic **Backtest-Oracle** providing diagnostic feedback.
    *   **Gate**: Proposed changes must show a measurable **Gain Metric** over a stateless baseline on held-out data before being committed.

### 1.6 The Immutable Shield (Governance Gate)
*   **Synthesis of**: *Reward Hacking*, *Effective Agents*.
*   **Design**: A non-bypassable safety layer that enforces exposure limits and risk bounds independently of the CSC's reasoning.

---

## 2. Superior Engineering Metrics

The UCA-2026 is superior because it optimizes for:

1.  **Fidelity**: World model predictions are grounded in causal structure and real tick data, not random noise.
2.  **Calibration**: Decision layers use Bayesian EV optimization rather than uncalibrated LLM sentiment.
3.  **Efficiency**: Token consumption is reduced by >60% via **S2L** adapters and **Information Folding**.
4.  **Stability**: Procedural skills are internalized into weights (LoRA), eliminating "Instruction Drift."
5.  **Scientific Rigor**: Every decision is linked to a causal chain of evidence in the graph, ensuring multi-hop reasoning provenance.

---

## 3. Contradiction Resolution

*   **Brain vs. Swarm**: The CSC provides unified management and global state, while PCAs provide decentralized domain ownership through Transactive Memory.
*   **RAG vs. Graph**: The system uses a **Hybrid Causal Graph**. Standard RAG handles high-frequency news updates; the Graph handles long-term causal relationships and scientific provenance.
*   **RL vs. Oracle**: The system uses **Socratic RL**, where the RL process is guided by a deterministic "Teacher" (Backtester) to eliminate reward hacking.
