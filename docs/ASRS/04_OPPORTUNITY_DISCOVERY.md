# 04. OPPORTUNITY DISCOVERY
## Opportunity Discovery Division & System Bottleneck Auditing

### 1. Architectural Mission
The **Opportunity Discovery Division (ODD)** is the continuous introspective division of ASRS. While the Research Discovery Division looks *outward* for literature, the ODD looks *inward* at the live production state of AlphaAlgo.

Its core purpose is to discover inefficiencies, performance degradation, and operational bottlenecks across all layers of the trading platform, framing these problems as scientific hypotheses and matching them to candidate solutions inside the Scientific Knowledge Graph.

---

### 2. Live System Diagnostics Metrics
The ODD polls execution logs, performance dashboards, telemetry databases, and risk logs to track nine core operational dimensions:

| Dimension | Primary Metric | Warning Threshold | Scientific Mitigation Pathway |
| :--- | :--- | :--- | :--- |
| **Slippage** | Realized vs. Quoted Execution Price | $> 1.5 \text{ bps}$ | Execute smart VWAP/TWAP; apply S2L behavioral distillation |
| **Calibration** | Expected Calibration Error (ECE) | $> 0.12$ | Trigger Bayesian calibration or EKSFT entropy masking |
| **Execution Latency** | End-to-end processing delay | $> 500 \text{ ms}$ | Apply FastRouter; compress prompts; prune SAGE graph edges |
| **Memory Waste** | Resident Set Size (RSS) slope | $> 25 \text{ MB/hr}$ | Consolidate HMS memory tiers; apply windowed buffers in CSC |
| **Sharpe Decline** | Rolling 30-day Sharpe ratio | Ratio $< 1.2$ | Re-evolve strategy genome; swap indicators; alter portfolio weights |
| **Module Instability** | Component crash or timeout rate | $> 0.01$ | Apply Fallback Hierarchy; trigger Pivot/Refine self-healing |
| **Causal Drift** | Predictive entropy of GWM | Ratio $> 1.8$ | minimize Variational Free Energy (VFE); update transition priors |
| **Validation Loss** | Out-of-sample backtest degradation | Ratio $> 0.35$ | Trigger walk-forward validation; run Monte Carlo stress checks |
| **Consensus Delay** | LogAct voter agreement wait time | $> 5.0 \text{ s}$ (timeout) | Optimize Concurrent voter registries; skip slow voters |

---

### 3. Hypothesis Generation & Proposal Pipeline
When a diagnostic threshold is breached, the ODD does not merely log a ticket. It generates a formal, machine-actionable `ResearchHypothesis` object:

```text
+-------------------------------------------------------------------------------+
|                             RESEARCH HYPOTHESIS                               |
+-------------------------------------------------------------------------------+
| - id: str (e.g., "hyp-odd-2026-0082")                                         |
| - trigger_metric: str ("calibration_error")                                   |
| - observed_value: float (0.165)                                               |
| - bottleneck_description: str ("CSC calibration drift on highly volatile M15") |
| - candidate_solutions: List[str] ("paper:eksft_2026", "paper:bayesian_calib") |
| - target_module: str ("trading_bot.core.csc.controller")                       |
| - expected_roi: float (0.24 Sharpe increase, 0.05 ECE reduction)              |
| - confidence: float (0.78 based on similar historical mitigations)             |
+-------------------------------------------------------------------------------+
```

---

### 4. Dynamic ROI Estimation & Prioritization
To prevent the evolutionary engine from wasting precious compute power on low-yield modifications, the ASRS utilizes a **Cost-Aware Research Planner (CARP)**. Before any experiment is generated, CARP computes the **Engineering return on Investment (EROI)**:

$$\text{EROI} = \frac{\Delta U \cdot P_{\text{success}} - C_{\text{compute}}}{\text{Effort} + \text{Risk}}$$

Where:
* $\Delta U$: Expected Utility Improvement. This is a multi-attribute utility function:
  $$\Delta U = w_s \cdot \Delta \text{Sharpe} + w_c \cdot \Delta \text{Calibration} + w_l \cdot \Delta \text{Latency} + w_m \cdot \Delta \text{Memory}$$
* $P_{\text{success}}$: Estimated probability of successful implementation, derived from paper complexity and empirical history.
* $C_{\text{compute}}$: Estimated computation cost (GPU hours $\times$ rate + CPU cycles).
* $\text{Effort}$: Estimated human/agent implementation complexity (1 to 10).
* $\text{Risk}$: Strategic operational risk of modifying the component (e.g., risk is high for live execution modules, low for prompt templates).

The CARP prioritizes the global experiment queue in descending order of EROI, ensuring that AlphaAlgo's computational resources are allocated to the most scientifically promising and cost-effective research pathways first.
