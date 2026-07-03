# Phase 6 (Part 2): Implementation Roadmap

This document provides a detailed 90-day execution strategy for implementing the UCA-2026.

---

## 1. Phase 1: Foundation Consolidation (Days 1-30)

*   **Objective**: Establish the "One Brain" and ground the environment in reality.
*   **Tasks**:
    1.  Decommission redundant orchestrators.
    2.  Implement the unified `IntegratedAgentSystem` (CSC) as the sole entry point.
    3.  Connect RL loops to real tick data (Eliminate Delusion Loop).
*   **Success Metric**: 100% of internal requests routed through CSC; Zero reliance on `np.random` for pricing.

---

## 2. Phase 2: Cognitive Capability (Days 31-60)

*   **Objective**: Internalize behaviors and solve long-horizon drift.
*   **Tasks**:
    1.  Implement the **Information Folding Buffer**.
    2.  Distill 10 core SOPs into **Skill-to-LoRA** adapters.
    3.  Implement the **Bayesian Decision Layer** (EV-Optimization).
*   **Success Metric**: 50% reduction in token cost; HORIZON break level $s > 10$.

---

## 3. Phase 3: Autonomous Evolution (Days 61-90)

*   **Objective**: Safe self-improvement and causal reasoning.
*   **Tasks**:
    1.  Induce the **Causal World Model** (SCM).
    2.  Implement the **Strict Keep-Better Gate** (RSEA).
    3.  Build the **Causal Evidence Graph** for research.
*   **Success Metric**: Measured positive "Alpha Gain" via CL-Bench; Zero unvalidated code commits.
