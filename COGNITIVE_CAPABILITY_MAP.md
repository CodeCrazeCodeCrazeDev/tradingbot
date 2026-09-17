# AlphaAlgo Cognitive Capability Graph (UCA-2026)

This document maps the 15 core cognitive capabilities of the AlphaAlgo autonomous financial intelligence system, defining their canonical components, measurement metrics, and evidence-driven bottleneck detection parameters.

---

## 1. Cognitive Capability Registry & Measurement

```
                          [Self-Diagnosis Engine]
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      ▼                              ▼                              ▼
  [Reasoning]                    [Planning]                     [Memory]
  - Metric: Token Depth          - Metric: Horizon Depth        - Metric: Multi-hop ECE
  - Bottleneck: Loop Drift       - Bottleneck: Search Timeout   - Bottleneck: Hallucination
      │                              │                              │
      ▼                              ▼                              ▼
  [World Modeling]             [Multi-Agent]                  [Verification]
  - Metric: Prediction MSE       - Metric: Disagreement         - Metric: False Positive
  - Bottleneck: Regime Shift     - Bottleneck: Deadlock         - Bottleneck: Over-conservatism
```

---

## 2. Core Capabilities & Metrics

### **1. Reasoning**
*   *Measurement Metric*: Number of successful DiscoLoop steps per observation.
*   *Bottleneck Threshold*: Loop drift or timeout (> 50ms).
*   *Authority*: `CognitiveSystemController`

### **2. Planning**
*   *Measurement Metric*: Maximum lookahead depth ($H$) under tree-search pruning.
*   *Bottleneck Threshold*: Plan search timeout or plan-conditioned value degradation.
*   *Authority*: `CognitiveSystemController`

### **3. Memory**
*   *Measurement Metric*: Retrieval accuracy of relational triples from SAGE Graph Memory.
*   *Bottleneck Threshold*: Retrieval quality drops under 0.90 or hallucination index > 0.05.
*   *Authority*: `HierarchicalMemorySystem`

### **4. World Modeling**
*   *Measurement Metric*: Prediction Mean Squared Error (MSE) of interventional do-calculus outcomes.
*   *Bottleneck Threshold*: MSE > 0.05 on out-of-distribution validation runs.
*   *Authority*: `UnifiedWorldModel`

### **5. Multi-Agent Coordination**
*   *Measurement Metric*: Consensus convergence rate and disagreement map dimensionality.
*   *Bottleneck Threshold*: Debate loop deadlocks, tied votes (50/50), or communication latency > 500ms.
*   *Authority*: `HeadAI`

### **6. Verification & Falsification**
*   *Measurement Metric*: False Positive rate and adversarial red-teaming bypass detection.
*   *Bottleneck Threshold*: False consensus rate > 5% or safety check bypasses.
*   *Authority*: `VerificationSwarm` / `FalsificationGate`

### **7. Autonomous Research & Experimentation**
*   *Measurement Metric*: Validated hypothesis generation rate.
*   *Bottleneck Threshold*: Rejection rate > 80% on sandboxed mutation trials.
*   *Authority*: `SelfEvolvingResearcher`

### **8. Decision Governance**
*   *Measurement Metric*: Zero-violation compliance rate.
*   *Bottleneck Threshold*: Any compliance score < 1.0.
*   *Authority*: `ImmutableShield`

### **9. Risk Reasoning**
*   *Measurement Metric*: Drawdown reduction and CVaR boundary matching.
*   *Bottleneck Threshold*: Drawdown limit breached or overnight risk simulation failure.
*   *Authority*: `MASTER_Risk_Manager`

### **10. Execution Reasoning**
*   *Measurement Metric*: Average slippage vs. Almgren-Chriss baseline.
*   *Bottleneck Threshold*: Slippage deviation > 15% from predicted causal impact.
*   *Authority*: `MT5Interface` / `SmartOrderRouter`

### **11. Self-Diagnosis**
*   *Measurement Metric*: Diagnostic coverage of system regressions and bottlenecks.
*   *Bottleneck Threshold*: Failure to predict a live regime-shift failure.
*   *Authority*: `SelfDiagnosisEngine`

### **12. Self-Improvement**
*   *Measurement Metric*: Stateful Gain Metric ($G$) on CL-Bench task sequences.
*   *Bottleneck Threshold*: No significant improvement ($G < \text{threshold}$) over 3 successive mutation cycles.
*   *Authority*: `EvolutionGate`

---

## 3. Evidence-Driven Bottleneck Detection

Alpha is programmed to identify its own bottlenecks using empirical data rather than arbitrary self-modifications:
- If **Surprise** increases significantly while **Regime Prediction Accuracy** drops, the world model is identified as the bottleneck, triggering `SelfEvolvingResearcher` to propose SCM structure updates.
- If **Slippage** exceeds predicted Almgren-Chriss limits, the execution engine is flagged, triggering a LoRA skill update via `SkillRouter`.
