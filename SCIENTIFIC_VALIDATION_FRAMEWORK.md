# Scientific Validation Framework

## 1. Metric Suite

The SRE is validated against these core metrics:

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| **Hypothesis Survival Rate** | < 20% | Ratio of Promoted to Created hypotheses. |
| **Research Efficiency** | > 0.5 | $\frac{\text{Economic Value}}{\text{Compute Cost}}$ |
| **Calibration Error (ECE)** | < 0.05 | Difference between predicted prob and realization. |
| **Causal Stability** | > 0.8 | Persistence of edge across counterfactual simulations. |
| **Novelty Score** | > 0.3 | KL-divergence from existing hypothesis pool. |
| **Falsification Rate** | > 0.1 | Frequency of successful adversarial refutations. |

## 2. Validation Gates

### Gate 1: Epistemic Integrity
- **Criteria**: $A < 0.2$ (Ambiguity) and `LeakageRisk == LOW`.
- **Failure**: Return to `EvidenceCollection`.

### Gate 2: Adversarial Robustness
- **Criteria**: Must survive 3/3 "Hostile Regime" stress tests.
- **Failure**: `REJECTED`.

### Gate 3: Causal Validity
- **Criteria**: $\frac{P(Y|do(X))}{P(Y|X)} > 0.9$ (No hidden confounders dominating the signal).
- **Failure**: `REJECTED` or `SPLIT`.

## 3. Continuous Self-Audit

The system runs a daily "Shadow Audit" where it re-evaluates `INSTITUTIONALIZED` hypotheses against current market data. Any hypothesis showing "Drift" is moved back to `CONTINUOUS_MONITORING` or `RETIRED`.
