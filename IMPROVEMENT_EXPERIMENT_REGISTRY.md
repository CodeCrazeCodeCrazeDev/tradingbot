# Improvement Experiment Registry Specification (RSI-REGISTRY-2026)

## 1. Overview and Core Purpose

The **Improvement Experiment Registry** is a structured, permanent schema log (`IMPROVEMENT_EXPERIMENT_REGISTRY.md`) recording every sandbox and simulation trial executed by the `RecursiveSelfImprovementEngine`. It prevents duplicate experimentation, enforces rigorous baseline comparisons, and builds a comprehensive dataset of "what has been tried and with what outcome."

---

## 2. Active Experiment Trial Log

Every experiment is assigned a unique `Experiment ID` and must record the complete causal and statistical metrics comparing the Candidate against its Simpler Baseline.

| Experiment ID | Improvement ID | Domain Target | Baseline Baseline | Candidate Model | Primary Metric | Baseline Metric | Candidate Metric | Falsification Check | Trial Outcome Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-WM-01** | IMP-WM-2026-0814-01 | World Model | Linear VAR | Non-linear prior | Transition MSE | 0.0842 | 0.0614 | PASSED | Completed |
| **EXP-ST-01** | IMP-ST-02 | Strategy | Single-Factor | Multi-factor ensemble | Sharpe Ratio (OOS) | 1.45 | 1.88 | FAILED (Leakage) | REJECTED |
| **EXP-SD-01** | IMP-SD-01 | Self-Debugging | Standalone | AST filter check | AST error match % | 78.4% | 94.2% | PASSED | Completed |

---

## 3. Mandatory Experimental Baselines

Before any candidate improvement is promoted, it must be evaluated side-by-side against designated **Required Baselines**:

### A. Trading & Strategy Baselines
*   **Naive Baseline:** Simple constant holding or uniform allocation.
*   **Transaction-Cost Model Baseline:** Realized returns must remain statistically significant after subtracting double-sided transaction fees, spreads, and market impact estimates ($2 \times \text{estimated spread}$).

### B. Multi-Agent & Routing Baselines
*   **Single Agent Baseline:** Performance and accuracy of a single LLM agent without verification.
*   **Single Agent + Verification:** Simple single agent with basic rule-based checks.
*   **Multi-Agent Debate:** Current debate engine vs the candidate debate engine. Addition of agents is approved **only** if it statistically increases correctness or reduces hallucination rate without violating computational bounds.

### C. World Model Baselines
*   **Simple Statistical Baseline:** Autoregressive ARIMA or GARCH models.
*   **Latent Dynamics Baseline:** Simple linear transition matrix.
*   **Candidate World Model:** Non-linear, neural latent dynamic model.
