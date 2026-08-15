# SELF_IMPROVEMENT_BENCHMARK.md
## Self-Improvement Benchmark Suite & Comparative Baseline Matrix

This document establishes the official benchmarking suite, comparative parameters, and test-bed configurations used to evaluate self-improving agents.

---

## 1. Baseline Configurations for Comparison

Every self-improved agent iteration must be evaluated against the following comparative baselines under identical seed settings:

1.  **Baseline A: Single-Agent Baseline (Stateless)**:
    A pure stateless ReAct loop without memory, active perception, or SAGE Graph evidence tracking.
2.  **Baseline B: Single-Agent + Verification**:
    A single-agent model combined with basic out-of-line verification, but lacking recursive learning.
3.  **Baseline C: Existing Multi-Agent**:
    The baseline UCA-2026 multi-agent debate platform before self-improvement.
4.  **Baseline D: Redesigned Multi-Agent + Recursive Self-Improvement**:
    Our full UCA-2026 cognitive model, SAGE memory, and active feedback loops, running live recursive self-improvement.

---

## 2. Measurable Benchmark Evaluation Metrics

| Metric | Evaluation Method | Target / Success Threshold |
| :--- | :--- | :--- |
| **Correctness** | Directional accuracy of alpha proposals over out-of-sample data. | > 65% accuracy |
| **Calibration** | Expected Calibration Error (ECE) under extreme OOD regimes. | ECE < 0.05 |
| **Robustness** | Performance preservation under simulated market crashes (OOD). | < 12% max drawdown |
| **Latency** | End-to-end controller loop execution speed. | Loop latency < 10ms |
| **Research Efficiency** | Compute cost and prompt tokens per valid hypothesis generation. | > 40% reduction in token count |
| **Replay Success** | Percentage of trajectories correctly reproduced during replay checks. | 100.0% exact match |
