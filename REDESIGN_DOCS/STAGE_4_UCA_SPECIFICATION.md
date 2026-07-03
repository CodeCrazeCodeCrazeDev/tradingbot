# Stage 4: Unified Cognitive Architecture (UCA) Specification

## 1. The "One Brain" Philosophy
UCA replaces the fragmented multi-orchestrator mess with a single **Cognitive System Controller (CSC)**. The CSC is the sole entry point and lifecycle manager for all intelligence. It does not "orchestrate" agents as disposable workers; instead, it manages a population of **Persistent Cognitive Agents (PCA)** that share a unified **Generative World Model (GWM)** and **Transactive Memory**.

---

## 2. Persistent Cognitive Agent (PCA) Architecture

Every specialist (Macro, Risk, Alpha) is a PCA.

### 2.1 Internal Components
- **Epistemic Core**: A persistent Bayesian belief state representing the agent's understanding of its domain.
- **Goal Hierarchy**: A tree of long-horizon and short-term objectives (e.g., "Preserve Capital" -> "Hedge JPY" -> "Execute VWAP").
- **Skill-to-LoRA (S2L) Adapters**: Lightweight, parameter-side modules containing behavioral patterns (tool-use, verification), reducing prompt overhead.
- **Information Folding Buffer**: A planning buffer that compresses execution traces into high-level "Lessons Learned".

### 2.2 The PCA Loop (Observe-Simulate-Act)
1.  **Sense**: Ingest multi-modal data through the GWM.
2.  **Think (Sandboxing)**: Query the GWM to simulate potential plan branches.
3.  **Coordinate**: Use Transactive Memory to share artifacts or consult other PCAs.
4.  **Act**: Execute via S2L-optimized tool calls.
5.  **Reflect**: Use SocraticPO to diagnose mistakes and update the Epistemic Core.

---

## 3. Generative World Model (GWM)

The GWM is a hybrid **SSM (Mamba) + Transformer** core that serves as the "Dreamer" for all PCAs.

### 3.1 Capabilities
- **Multi-Path Rollouts**: Generates Bull, Bear, and Volatile scenarios with calibrated uncertainty.
- **Causal Sandbox**: Implements Pearl's **Do-Calculus**. Agents ask: *"If I dump 1000 BTC, what is the fill probability and price impact?"*
- **Regime Awareness**: Internalizes market microstructure and macro regimes as native latent states.

---

## 4. Hierarchical Memory System (HMS) & Transactive Memory

Memory is no longer a passive database; it is an orchestrated service.

### 4.1 Memory Tiers
1.  **Working**: Real-time context (high churn).
2.  **Episodic**: Trace of recent sessions.
3.  **Semantic**: Distilled facts (Market relationships, causal links).
4.  **Procedural (S2L)**: Behavioral adapters (LoRA).
5.  **Research**: Persistent hypotheses and backtest results.
6.  **Institutional**: Strategic bounds and immutable governance.

### 4.2 Transactive Memory
Agents "own" specific knowledge domains. If a Risk Agent needs Macro context, it doesn't search a global DB; it queries the Macro Agent's artifacts via the Transactive Bus.

---

## 5. Hierarchical Planning with Information Folding (HIPIF)

### 5.1 Levels of Planning
- **Strategic**: Horizon = Months (Alpha discovery, regime adaptation).
- **Tactical**: Horizon = Days (Portfolio rebalancing, hedging).
- **Operational**: Horizon = Hours (Execution strategy selection).
- **Execution**: Horizon = Ticks (Microstructure optimization).

### 5.2 Information Folding
As subgoals are completed, their raw logs are "folded" (summarized into semantic updates) to prevent context saturation, keeping the strategic horizon visible.

---

## 6. Knowledge Orchestration Pipeline

The system dynamically selects knowledge sources:
1.  **Parametric**: Immediate "Intuition" from model weights (LoRA).
2.  **Retrieval**: Historical evidence from HMS.
3.  **Simulation**: GWM rollouts for future-uncertainty.
4.  **Tool-Use**: Real-time data fetching or calculation.

---

## 7. Mathematical Foundation

### 7.1 Active Inference (Agents)
Agents minimize **Variational Free Energy**:
$$\mathcal{F} = \mathbb{E}_{q(s)}[\ln q(s) - \ln p(o,s)]$$
This balances **Expected Utility** (reward) with **Epistemic Value** (information gain).

### 7.2 Causal Do-Calculus (World Model)
Interventions are modeled as:
$$P(Y | do(X=x), Z)$$
Where $Z$ is the current latent market state.

### 7.3 Information Bottleneck (Memory)
Distillation preserves information $I(M, S_{future})$ while minimizing $I(M, S_{past})$.
