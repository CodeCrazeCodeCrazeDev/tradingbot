# Phase 6 (Part 3): Validation Framework

Scientific metrics to measure the intelligence and reliability of the UCA-2026.

---

## 1. Intelligence Metrics

### 1.1 Gain Metric (CL-Bench)
Isolates genuine online learning from pre-trained capabilities.
$$G = \text{Perf}(\text{Stateful Agent}) - \text{Perf}(\text{Stateless Baseline})$$

### 1.2 Fidelity Metric (World Model)
Measures the accuracy of causal interventions.
$$\mathcal{L}_{fidelity} = |P(y | do(x))_{imagined} - P(y | do(x))_{actual}|$$

---

## 2. Reliability Metrics

### 2.1 Break Level (HORIZON)
Identifies the maximum sequence length before strategic collapse.
$$\text{Horizon Limit} = \max \{ s : P(\text{Success} | s) > 0.9 \}$$

### 2.2 Calibration Error
Measures the accuracy of the agent's probability estimates.
$$\text{ECE} = \sum_{i=1}^M \frac{|B_i|}{n} |\text{acc}(B_i) - \text{conf}(B_i)|$$

---

## 3. Institutional Stability Gates

*   **Gate A**: 0% regression on held-out safety tasks.
*   **Gate B**: < 5% divergence from human-verified causal DAGs.
*   **Gate C**: > 20% improvement in token efficiency via S2L.
