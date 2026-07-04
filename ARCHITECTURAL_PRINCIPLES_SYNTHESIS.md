# AlphaAlgo UCA-2026: Architectural Principles Synthesis

This document consolidates the scientific foundations and engineering principles extracted from the 2026 research foundation and redesign docs.

## 1. Core Mathematical Frameworks

| Concept | Application | Source Paper(s) |
| :--- | :--- | :--- |
| **Active Inference** | Unified objective for the Cognitive System Controller (CSC). Minimizing Variational Free Energy (VFE) balances goal-seeking with uncertainty reduction. | Active Inference |
| **Causal Do-Calculus** | The "Intervention Engine" for the World Model. Enables counterfactual "What-if" reasoning by simulating structural interventions. | CWMI |
| **Information Bottleneck** | The mathematical basis for **Information Folding**. Compresses history $H_t$ into semantic updates $F_t$ while preserving strategic relevance. | HIPIF |
| **Bayesian Decision Theory** | Wraps LLM reasoning in calibrated Expected Value (EV) optimization. | Decision Intelligence |

## 2. Engineering Principles (The "One Brain" Standard)

1.  **Unified Cognitive Controller (CSC)**: Exactly one entry point. No fragmented orchestrators.
2.  **Persistent Cognitive Agents (PCA)**: Agents are not disposable prompts; they maintain a persistent **Epistemic Core** (Bayesian belief state) and **Goal Hierarchy**.
3.  **Behavioral Internalization (S2L)**: SOPs and skills are moved from prompts into dynamically loadable **LoRA adapters** to save context and ensure stability.
4.  **Causal Evidence Graph**: Replaces passive RAG. Claims must be linked to evidence nodes with clear provenance.
5.  **Hierarchical strategic Folding**: Subgoals are compressed into semantic lessons. Raw logs are cleared once the goal is reached.
6.  **Transactive Memory**: Agents "own" domains and share artifacts (compressed results) via a shared HMS rather than raw message passing.
7.  **Monotone-Safe Evolution**: Self-improvement must pass a strict "Gain Metric" on held-out data via a non-bypassable **Evolution Gate**.
8.  **Immutable Shield**: Safety and risk limits are enforced by a separate, non-bypassable layer regardless of agent reasoning.

## 3. Superior Architecture: Target Structure

- **Core Brain (`csc/`)**: Implements Active Inference loop, HIPIF folding, and S2L routing.
- **World Model (`world_model/`)**: SCM-based simulator grounded in real tick data. Supports structural interventions.
- **Memory System (`hms/`)**: 3-tier (Working/Redis, Episodic/Vector, Semantic/Graph) with a WMR (Write-Manage-Read) loop.
- **Governance (`governance/`)**: Immutable Shield + Evolution Gate.
- **Agents (`pca/`)**: Persistent agents (Macro, Risk, Alpha) with epistemic cores.

## 4. Grounding Requirements

- **No Simulation**: All placeholders, random noise, and mock rewards must be replaced with deterministic replay of real market data.
- **Reality as Signal**: Rewards are derived from actual execution outcomes (slippage, fill probability, PnL).
