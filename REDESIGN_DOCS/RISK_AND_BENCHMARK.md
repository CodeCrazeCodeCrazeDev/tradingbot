# AlphaAlgo UCA: Benchmarking & Risk Analysis

## 1. Benchmarking Plan

To verify the UCA's superiority over the legacy system, we will use a three-stage benchmarking suite.

### 1.1 Intelligence & Reasoning Benchmarks
- **Horizon-Log**: Measuring the agent's ability to maintain goal consistency over $N$ steps.
- **Epistemic Entropy**: Measuring the reduction in World Model uncertainty after $T$ active probes.
- **Counterfactual Calibration**: Accuracy of "What-If" simulations compared to real historical outcomes ($P(\text{event} | \text{sim}) \approx P(\text{event} | \text{real})$).

### 1.2 Quantitative Trading Benchmarks
- **Regime Adaptability**: Time-to-recovery (TTR) after a 2-standard-deviation market shock.
- **Slippage vs. Simulation**: Delta between GWM-predicted slippage and realized broker execution.
- **Risk-Adjusted Alpha**: Sharpe, Sortino, and Calmar ratios compared to the legacy MT5-bot baseline.

### 1.3 Engineering Benchmarks
- **Cognitive Latency**: Time for a full Observation-Simulation-Action cycle.
- **Memory Retrieval Throughput**: Latency of HMS Tier 1-6 lookups under high-concurrency swarms.

---

## 2. Risk Analysis & Mitigations

| Risk | Impact | Probability | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Simulated Reality Gap** | High | Medium | **Anchoring**: Every GWM rollout must be cross-validated against the `RigorousBacktest` module using real tick data. |
| **Cognitive Overload** | Medium | High | **Hierarchical Delegation**: The Cognitive System Controller will dynamically "prune" inactive agents and throttle simulation depth based on compute budget. |
| **Catastrophic Forgetting** | High | Low | **Hierarchical Memory (HMS)**: Tier 6 (Institutional Knowledge) is immutable. All procedural updates undergo a "Validation Gate" before promotion. |
| **Hallucinated Alpha** | Critical | Medium | **Adversarial Debate**: Every PCA proposal must survive the `VerdictEngine` where specialist "Bear" and "Risk" reviewers attempt to falsify the hypothesis. |
| **Recursive Instability** | High | Low | **Governance Gate**: Automated code modifications (RSIE) are restricted to Tier 0-2 (Parametric). Tier 3+ (Structural) requires Human-in-the-Loop approval. |

---

## 3. Comparison Summary: Legacy vs. UCA

| Dimension | AlphaAlgo Legacy | AlphaAlgo UCA (Redesign) |
| :--- | :--- | :--- |
| **Cognitive Goal** | Task Completion (Stateless) | Problem Solving (Persistent) |
| **Internal Model** | Next-Step Prediction | Future Simulation (Rollouts) |
| **Reasoning** | Template-driven (ReAct) | Simulation-grounded (EWM) |
| **Learning** | Stochastic Gradient Descent | Active Inference & Bayesian Updating |
| **Safety** | Heuristic Risk Bounds | Constitutional Governance & Invariance |
| **Memory** | JSON Key-Value Store | 6-Tier Hierarchical Knowledge Graph |
