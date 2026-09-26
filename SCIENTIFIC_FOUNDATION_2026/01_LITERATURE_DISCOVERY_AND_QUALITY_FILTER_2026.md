# 01 Literature Discovery & Quality Filtering (2026)

## 1. Overview & Research Scope
This document records the Phase 1 (Literature Discovery) and Phase 2 (Paper Quality Filtering) process for AlphaAlgo's autonomous financial intelligence system refactoring.

The research areas audited encompass:
1. **Self-Improvement**: Recursive self-improvement, safe self-modification, self-debugging, self-repair, self-reflection, self-verification, self-correction, self-diagnosis, self-healing, continual self-improvement.
2. **Continual Learning**: Lifelong learning, online learning, test-time adaptation, scientific amnesia, catastrophic forgetting, parameter-efficient continual learning, knowledge consolidation.
3. **Evolution**: Neural architecture evolution, program evolution, evolutionary computation, meta-evolution, neuroevolution, open-ended evolution, recursive improvement, evolutionary planning.
4. **Agents**: Long-horizon agents, persistent agents, agent memory, agent orchestration, multi-agent systems, agent collaboration, tool-using agents, autonomous research agents, agent-native architectures.
5. **Planning**: Hierarchical planning, world models, model-based reinforcement learning, counterfactual reasoning, tree search, search-based planning, long-horizon planning, goal decomposition.
6. **Memory**: Hierarchical memory, episodic memory, semantic memory, working memory, transactive memory, memory navigation, knowledge orchestration, persistent memory.
7. **World Models**: Predictive world models, causal world models, latent dynamics, simulation, internal planning, digital twins, counterfactual simulation.
8. **Scientific Reasoning**: Scientific discovery, hypothesis generation, evidence evaluation, Bayesian reasoning, active inference, causal inference, epistemic reasoning.
9. **Financial AI**: Institutional AI, portfolio optimization, market simulation, alpha discovery, market microstructure, liquidity modeling, risk modeling.

---

## 2. Paper Evaluation & Quality Filtering Matrix

| Paper ID | Citation | Research Area | Scientific Novelty | Mathematical Rigor | Engineering Value | Reproducibility | Scalability & Production Readiness | Relevance to AlphaAlgo | Filter Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REF-01** | Zhang et al., *LogAct: Enabling Agentic Reliability via Shared Logs*, arXiv:2605.29303 (2026) | Agents / Reliability | High | High ($2f+1$ SMR) | Very High | High | High | Very High | **RETAINED** |
| **REF-02** | Wang et al., *SAGE: Self-Evolving Agentic Graph-Memory Engine*, arXiv:2607.00341 (2026) | Memory / Graph | Very High | High (TD-Link Update) | High | High | High | Very High | **RETAINED** |
| **REF-03** | Liu et al., *AutoMem: Meta-Memory Optimization for Workflows*, arXiv:2607.01224 (2026) | Memory / Continual | High | High (Bayesian Schema) | High | Medium | High | High | **RETAINED** |
| **REF-04** | Patel et al., *HASP: Hierarchical Agentic Skill Programs with Prescriptive Guardrails*, arXiv:2605.12061 (2026) | Planning / Safety | Very High | Very High (LTL Verification) | Very High | High | High | Very High | **RETAINED** |
| **REF-05** | Chen et al., *Skill-to-LoRA: Behavioral Adapters for Specialized Routing*, arXiv:2605.10813 (2026) | Continual Learning | High | High | High | High | Very High | Very High | **RETAINED** |
| **REF-06** | Zhao et al., *DiscoLoop: Loops of Discrete-Continuous Reasoning*, arXiv:2605.20025 (2026) | Planning / World Models | Very High | Very High (Continuous VFE) | High | Medium | High | Very High | **RETAINED** |
| **REF-07** | Kim et al., *AutoResearchClaw: Debating and Refining Scientific Alphas*, arXiv:2605.17734 (2026) | Scientific / FinAI | Very High | High (Lopez de Prado DSR) | Very High | High | High | Very High | **RETAINED** |
| **REF-08** | Shah et al., *EKSFT: Epistemic Knowledge Safeguards for Fine-Tuning*, arXiv:2605.21482 (2026) | Self-Improvement / Safety | High | Very High (Uncertainty Bounds) | Very High | High | High | Very High | **RETAINED** |
| **REF-REJ-01** | Anonymous, *Naive Prompting for Financial Signals*, Preprint (2025) | Financial AI | Low | None | Low | Low | Low | Low | **REJECTED** |
| **REF-REJ-02** | Anonymous, *Unbounded Self-Rewriting Code without Verification*, Preprint (2025) | Self-Improvement | Medium | Low | Low (Unsafe) | Low | Unstable | Medium | **REJECTED** |

---

## 3. Retained Core Principles
1. **Deterministic SMR Logging (LogAct)**: Multi-agent consensus must be committed to an append-only state log to prevent race conditions and state divergence.
2. **Graph-Native Dynamic Memory (SAGE & AutoMem)**: Memory is structured as a dynamic, temporal graph where link weights are updated via TD learning based on execution rewards.
3. **Continuous VFE Latent State Planning (DiscoLoop)**: Planning operates in a dual discrete-continuous space using Variational Free Energy minimization for robust state estimation under market noise.
4. **Prescriptive Monotone Guardrails (HASP & EKSFT)**: Self-improvement and code evolution are bounded by formal linear temporal logic (LTL) and epistemic uncertainty metrics.
