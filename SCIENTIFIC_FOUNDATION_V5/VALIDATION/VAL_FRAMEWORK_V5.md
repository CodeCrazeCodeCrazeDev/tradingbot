# Validation Framework V5: Institutional Financial Intelligence

The V5 Validation framework unifies **Capability (CL-Bench)**, **Domain (FIRE)**, and **Strategy (HORIZON)** into a single institutional scorecard.

## 1. Unified Benchmark Suite

| Benchmark | Focus | Metric | V5 Target |
| :--- | :--- | :--- | :--- |
| **FIRE** | Domain Knowledge | Accuracy across 3,000 financial scenarios | $>85\%$ (Expert level) |
| **CL-Bench** | Continual Learning | **Gain Metric (G)**: Online vs. Stateless | $G > 0.15$ (Active learning) |
| **HORIZON** | Planning Depth | Intrinsic Horizon ($H^*$) Break-point | $H^* > 100$ steps |
| **LogAct Audit**| Reliability | Recovery Time & Consistency Score | $100\%$ Recovery Accuracy |
| **QKG Calibration**| Knowledge | Context-Validity Precision | $>90\%$ (Valid evidence) |
| **Formal Safety** | Governance | Zero-Violation Rate (Invariant Checking)| $0$ Violations |

## 2. Institutional KPI Matrix

### A. Intelligence Gain
Measures how much the bot improves from live data.
$$Gain = \frac{\text{Perf}(\text{Live\_Adaptive}) - \text{Perf}(\text{Pre-trained\_Stateless})}{\text{Perf}(\text{Pre-trained\_Stateless})}$$

### B. Strategic Coherence
Measures the ability to follow long-horizon plans without "Strategic Drift".
*   *Metric*: Consistency between the initial **DeepInsight Sketch** and the final **HIPIF Folded Summary**.
*   *Success Criterion*: $>0.8$ Semantic Similarity.

### C. Formal Reliability
Measures the success of the **Shared-Log Consensus** and **Formal Proofs**.
*   *Metric*: Ratio of approved actions that achieve their goal without violating invariants.

## 3. The "Institutional Bar" (Shipping Criteria)
Nothing is deployed to a live trading environment unless it passes:
1.  **Backtest Gate**: Statistically significant alpha on 10+ years of tick data.
2.  **Robustness Gate**: Performance degradation in "Held-out" (OOD) regimes $< 20\%$.
3.  **Formal Gate**: $100\%$ of safety invariants formally verified by the AI Proof Search.
4.  **Ablation Gate**: The new component must contribute $>5\%$ gain to the overall system performance.

## 4. Failure Mode Analysis (Red-Teaming)
The system undergoes continuous **Multi-Objective Red-Teaming** (Paper 13).
*   **Adversarial Contexts**: Feeding the QKG "Impossible" market contexts to check for logical collapse.
*   **Reward Hacking Simulation**: A sub-agent tries to edit the Shared Log or bribe the Voters to approve high-risk, high-reward (short-term) trades.
*   **Recursive Stability Test**: Stress-testing the Hyperagent's meta-modifications across 100 generations to detect "Recursive Divergence".
