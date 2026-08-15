# Phase 6 & 7: Evidence-Driven Self-Improvement Architecture & Promotion Invariant Specification (2026)

## 1. Introduction

Autonomous self-improvement in high-stakes financial environments must operate under strict, monotone-safe constraints to avoid model collapse or tail-risk expansion. This document details the architectural specifications for an evidence-driven improvement loop and formalizes multi-dimensional promotion invariants, ensuring the system never concludes: *"I changed myself, therefore I improved."*

---

## 2. Evidence-Driven Improvement Loop

The self-improvement pipeline operates as a closed loop, restricted to offline sandbox environments and branching validation paths:

```
[Observe Production Behavior]
          ↓
[Detect Regression / Weakness]
          ↓
[Diagnose Structural Root Cause]
          ↓
[Research Literature Corpus]
          ↓
[Generate Competing Hypotheses]
          ↓
[Design Scientific Experiment]
          ↓
[Sandbox Branch Implementation]
          ↓
[Automated Backtest & stress evaluation]
          ↓
[Statistical Champion-Challenger Comparison]
          ↓
[Adversarial Committee & Governance Gate]
          ↓
[Monotone-Safe Promotion or Rollback]
          ↓
[Update Institutional Knowledge / SAGE Graph]
```

### 12-Step Cognitive Stages:
1.  **Observe:** Continually monitor production metrics (Expected Calibration Error, Sharpe, Max Drawdown, Latency).
2.  **Detect:** Run anomaly detection to flag statistically significant deviations from expected performance.
3.  **Diagnose:** Execute Step-Level failure attribution (*HORIZON*) to isolate the exact subsystem causing the degradation.
4.  **Research:** Query SAGE Knowledge Graph (*Agents-K1*) to locate transferable design patterns or parameter limits.
5.  **Hypothesize:** Propose concrete structural or parameter modifications as competing hypotheses.
6.  **Experiment:** Synthesize automated execution harnesses (*Self-Harness*) to test the proposed change in isolation.
7.  **Sandbox:** Spawn an isolated, ephemeral process-level container to execute the experimental strategy.
8.  **Evaluate:** Perform high-fidelity out-of-sample backtests under noisy market simulations (*CWMI*).
9.  **Compare:** Compute the Gain Metric (*CL-Bench*) comparing the candidate's active online gains against stateless baseline controls.
10. **Gate:** Pass candidate results to the *Adversarial Committee* (Risk, Hallucination, Regime Verifiers).
11. **Promote:** Commit changes to the active branch *only if* all promotion invariants are strictly satisfied.
12. **Institutionalize:** Update the shared MATM transactive index and SAGE graph with the newly discovered structural insights.

---

## 3. Formal Multi-Dimensional Promotion Invariants

A candidate modification **MUST** satisfy all of the following mathematical inequalities across multiple dimensions before promotion is permitted:

$$\text{sharpe}_{\text{challenger}} \geq \text{sharpe}_{\text{champion}} \cdot (1 + \epsilon_{\text{improvement}})$$

$$\text{drawdown}_{\text{challenger}} \leq \text{drawdown}_{\text{champion}}$$

$$\text{ece}_{\text{challenger}} \leq 0.15 \quad (\text{Expected Calibration Error Constraint})$$

$$\text{latency}_{\text{challenger}} \leq 5.0\text{ ms} \quad (\text{Strict Production SLA Bound})$$

$$\text{failed\_assertions}_{\text{challenger}} = 0 \quad (\text{Formal Verification Constraint})$$

### Invariant Dimensions:

1.  **Capability & Correctness (Neuro-Symbolic Gate):**
    *   The compiled AST must contain zero syntax or typing errors.
    *   Must satisfy 100% of the formal safety assertions verified via Automatic Theorem Proving (*SMT Solver*).
2.  **Robustness & Calibration (Bayesian Calibration Gate):**
    *   Expected Calibration Error (ECE) must remain $\leq 0.15$. Uncalibrated overconfidence is rejected immediately.
3.  **Efficiency & Compute Resources (System SLA Gate):**
    *   Average decision latency must not exceed $5.0\text{ ms}$.
    *   Context-window memory overhead must remain linear ($\mathcal{O}(L)$) and utilize *HIPIF* folding.
4.  **Security (Adversarial Security Gate):**
    *   No dynamically synthesized script can bypass system shell barriers, utilize insecure imports, or execute un-sanitized pickle serialization.
5.  **Financial Stability (Active Risk Gate):**
    *   Challenger must show positive, statistically significant alpha gains ($p \leq 0.05$) while keeping Max Drawdown equal to or strictly less than the champion baseline.
