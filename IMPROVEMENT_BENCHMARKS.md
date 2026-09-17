# AlphaAlgo Self-Improvement Benchmarks

## 1. Comparative Evaluation Philosophy
To prevent the self-improving intelligence from gaming its evaluation or suffering from look-ahead and selection bias, we enforce **immutable baseline benchmarks** and **frozen, out-of-sample (OOS) validation datasets**.

Every proposed candidate must run alongside its corresponding frozen baseline to calculate the exact capability improvement.

---

## 2. Benchmark Suites

### 2.1 The CL-Bench Suite (Continual Learning)
Measures the system's ability to retain historical performance and generalize to new environments without forgetting previously learned strategies or rules.
- **Metric:** CL Gain $G = \text{Perf}(\text{Candidate}) - \text{Perf}(\text{Baseline})$.
- **Required Threshold:** $G \ge 0.05$ (Significant capability improvement).

### 2.2 SRE-Bench (Scientific Reasoning)
Measures the precision and recall of the 19-step Scientific Reasoning Engine.
- **Metrics:**
  - Precision: % of confirmed hypotheses that avoid downstream performance decay.
  - Recall: % of viable market signals successfully identified.
  - Expected Calibration Error (ECE): Accuracy-to-confidence alignment.
- **Baseline Target:** Precision $\ge 95\%$, Recall $\ge 90\%$, ECE $\le 0.15$.

### 2.3 Stress-Bench (Adversarial Robustness)
Measures latency stability, memory footprint growth, and risk-management resilience under extreme simulated conditions.
- **Metrics:**
  - Decision Latency: Maximum average latency $\le 1.5\text{ ms}$ (Decision lane) / $150\text{ ms}$ (Research lane).
  - Safety-score: Zero safety violations under $100$ simulated flash-crash episodes.

---

## 3. Dataset Segregation and Sanity Rules

```
┌─────────────────────────────────┐
│        Total Market Data        │
├─────────────────┬───────────────┤
│    Training     │   Validation  │
│    (In-Sample)  │ (Out-of-Sample)
│      60%        │      40%      │
└─────────────────┴───────────────┘
```

1. **Strict Temporal Isolation:** The Out-of-Sample validation set must always reside strictly forward in time compared to the training set.
2. **Zero-Overlap Policy:** Any data leakage, indicator overlap, or feature sharing between training and validation spaces will trigger an immediate **validation-engine exception** and quarantine the candidate.
3. **Reproducibility Guarantee:** Every benchmark run must explicitly record the random seed (default: 42) and system environmental properties, ensuring that any claimed improvement can be replicated identically.
