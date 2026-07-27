# Phase 3: Cross-Paper Analysis & First Principles

This document extracts the "Strongest Common Principles" and engineering patterns from the 16 scientific papers to form the foundational logic for the AlphaAlgo Unified Scientific Architecture.

---

## 1. Principal Comparative Matrix

| Domain | Strongest Pattern | Overlapping Papers | Conflicting Ideas | Unified Principle |
| :--- | :--- | :--- | :--- | :--- |
| **Planning** | Hierarchical + Folding | HIPIF, RSEA, Effective Agents | Flat ReAct vs. Subgoal Trees | **Hierarchical Strategic Folding**: Decompose goals into a tree; fold logs into semantic state updates. |
| **Memory** | Multi-Tier WMR Loop | Memory Survey, MATM, HIPIF | Centralized vs. Transactive | **Hierarchical Transactive Memory**: Agents own local domains but share compressed artifacts globally. |
| **Learning** | Interactive Diagnostic | SocraticPO, CL-Bench, RSEA | Pure RL vs. Teacher-Guided | **Diagnostic Policy Optimization**: Use deterministic oracles (Backtests) as teachers with reward decay. |
| **Knowledge** | Agent-Native Orchestration | Agents-K1, PT-RAG, MATM | Passive RAG vs. Graph Traversal | **Active Knowledge Orchestration**: Agents traverse a causal evidence graph to synthesize provenance. |
| **Evolution** | Monotone-Safe Gate | RSEA, Self-Harness, Reward Hacking | Unguarded Evolution vs. Strict Gates | **Immutable Evolution Horizon**: Self-rewrites must pass a strict held-out validation gate. |
| **Execution** | Parameterized Behavioral LoRA | Skill-to-LoRA, Parametric Injection | Prompt-based vs. Weight-based | **Behavioral Parameterization**: Stable procedural skills (SOPs) are stored in loadable LoRA weights. |
| **Reasoning** | Bayesian Decision Theory | Strategic DI, Active Inference, CWMI | LLM Overconfidence vs. Calibrated EV | **Calibrated Decision Intelligence**: Reasoning must be wrapped in Bayesian EV-optimization and Do-calculus. |

---

## 2. Strongest Engineering Patterns

### 2.1 The "One Brain" Controller (CSC)
*   **Source**: Building Effective Agents, Strategic DI.
*   **Principle**: Consolidate every orchestrator into a single **Cognitive System Controller**. Avoid the "Swarm Mirage" where fragmentation leads to functional collapse.
*   **Pattern**: Single high-capability model managing strict workflows and persistent sub-agents.

### 2.2 The Observe-Simulate-Act (OSA) Loop
*   **Source**: Active Inference, CWMI.
*   **Principle**: Actions must be preceded by counterfactual simulation.
*   **Pattern**: Query the Causal World Model (do-calculus) before every market intervention.

### 2.3 The "Folding" Buffer
*   **Source**: HIPIF.
*   **Principle**: Context is a scarce resource. Information must be compressed at the "Subgoal Horizon."
*   **Pattern**: After a trade sequence (subgoal) completes, the raw logs are summarized into a "Lesson" and cleared from the active context.

---

## 3. Contradictions & Scientific Resolutions

### 3.1 Swarm vs. Unified Brain
*   **Conflict**: Some papers suggest decentralized swarms for scalability; others warn of functional collapse.
*   **Resolution**: **Unified Management, Decentralized Ownership**. Use a unified CSC for global state and governance, but use **Transactive Memory** to allow specialized agents (Macro, Risk) to "own" their knowledge domains and share artifacts.

### 3.2 RAG vs. Graph
*   **Conflict**: Standard RAG is easier to scale; Knowledge Graphs (Agents-K1) provide better multi-hop logic.
*   **Resolution**: **The Causal Evidence Graph**. Build a graph of *claims and evidence* (not just text). Use graph traversal for "Why" questions (Strategy Research) and standard vector-RAG for "What" questions (Real-time data).

---

## 4. Derived First Principles for AlphaAlgo

1.  **Principle of Persistence**: Agents are not disposable prompts; they are persistent Bayesian entities with an "Epistemic Core."
2.  **Principle of Causal Sandboxing**: No action is taken without a counterfactual "Do-Calculus" rollout in the World Model.
3.  **Principle of Information Bottleneck**: Memory and Planning must be compressed (folded) to preserve the strategic horizon.
4.  **Principle of Monotone Safety**: Self-evolution is permitted only if it provides a measurable "Gain" over a stateless baseline on held-out data.
5.  **Principle of Behavioral Internalization**: Standardized trading behaviors (SOPs) must be moved from the context window into the weights (LoRA).
