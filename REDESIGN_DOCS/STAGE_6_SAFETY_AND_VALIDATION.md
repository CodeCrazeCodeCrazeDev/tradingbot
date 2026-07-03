# Stage 6: Safety, Governance & Validation Framework

## 1. Safety Architecture: The "Immutable Shield"

Safety is not a wrapper; it is an intrinsic constraint of the UCA.

### 1.1 Governance Gates
The **GovernanceGate** is the final, non-bypassable node in the execution pipeline. It enforces:
- **Exposure Limits**: Gross and Net exposure caps per asset, sector, and strategy.
- **Risk Entropy**: Limits on the total "uncertainty" allowed in a portfolio.
- **OOD Detection**: If the GWM detects the market has entered an "Out of Distribution" regime (unseen volatility/liquidity), the gate triggers a system-wide "De-risk" mode.
- **Adversarial Buffering**: All agent-generated code or configuration changes must pass through an automated Red-Team suite before being applied to production.

### 1.2 Anti-Hallucination & Evidence Verification
All PCA reasoning must be grounded in **Evidence Graphs**. Any claim without a direct HMS provenance link or GWM simulation support is flagged and requires "Epistemic Justification" before proceeding.

---

## 2. Validation Framework: Measuring Intelligence

We replace "Success Rate" with the **Gain Metric** and **Fidelity Scores**.

### 2.1 The Gain Metric (from CL-Bench)
Measures the improvement of a stateful system over a stateless one:
$$Gain = Performance_{Stateful} - Performance_{Stateless}$$
This ensures the agent is actually *learning* from experience, not just relying on the base model's pre-training.

### 2.2 HORIZON Failure Attribution
Uses the HORIZON diagnostic suite to classify failures into:
- **Planning Failures**: Strategic drift, subgoal inconsistency.
- **Memory Failures**: Retrieval noise, context loss.
- **World Model Failures**: Incorrect regime prediction, counterfactual error.
- **Execution Failures**: Excessive slippage, unfilled orders.

### 2.3 System Calibration
Measures the correlation between an agent's **Reasoning Confidence** and the **Actual Outcome**. A well-calibrated system "knows what it doesn't know".

---

## 3. Benchmark Suite (The "Institutional Bar")

1.  **Alpha Integrity**: Performance vs. risk-adjusted benchmarks (Sharpe, Sortino, Calmar).
2.  **Regime Adaptability**: Accuracy of world model predictions across the 2008, 2020, and 2022 market regimes.
3.  **Latency & Throughput**: Cognitive overhead per decision (target < 500ms for tactical).
4.  **Self-Improvement Safety**: Percentage of proposed modifications rejected by the Governance Gate (Target: High rejection for low-gain/high-risk changes).

---

## 4. Production Deployment & Risk Assessment

### 4.1 Deployment Strategy (Cloud-Native)
- **Containerization**: CSC and HMS deployed as microservices (Docker/K8s).
- **Orchestration**: Managed via a platform-agnostic layer (removing Windows/MT5 coupling).
- **Monitoring**: Deep observability of the "Reasoning Trace" and "Knowledge Lineage".

### 4.2 Risk Assessment
| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **Recursive Collapse** | High | Staged evolution with "Safe Horizons" and automated rollbacks. |
| **Model Hallucination** | Medium | Mandatory Evidence Grounding and GWM simulation verification. |
| **Data Poisoning** | Low | Multi-source knowledge orchestration with provenance scoring. |
| **Platform Lock-in** | Low | Modular Institutional Adapters (FIX/REST). |
