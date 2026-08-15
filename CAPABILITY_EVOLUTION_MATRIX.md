# Capability Evolution Matrix (RSI-MATRIX-2026)

This specification acts as the global system catalog mapping system-wide capabilities, their designated optimization metric targets, current autonomy tiers, and the validated evolutionary outcome statuses.

| Capability ID | Subsystem Domain | Primary Optimization Target | Baseline Benchmark Method | Autonomy Tier | Evolution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CAP-WM-01** | World Model | Transition Prediction Surprise | RMSE vs Hold-Last-Value | Tier 2 (Experimental) | Stable |
| **CAP-WM-02** | World Model | Causal Regime Shift Classification | Macro F1-Score vs statistical GARCH | Tier 2 (Experimental) | Under Optimization |
| **CAP-ST-01** | Strategy Discovery | Information Leakage Rate | Contamination coefficient vs purged | Tier 3 (Candidate) | Under Audit |
| **CAP-ST-02** | Strategy Discovery | Strategy Generation (Alpha) | Information Ratio vs Walk-Forward | Tier 2 (Experimental) | Active |
| **CAP-TP-01** | Trading Policy | Position Sizing & Entry/Exit | Expected Gain vs Kelly Criterion | Tier 1 (Bounded) | Stable |
| **CAP-RK-01** | Risk Intelligence | Expected Tail Loss (CVaR) | Calibration Error vs Var-Covariance VaR | Tier 1 (Bounded) | Stable |
| **CAP-SE-01** | Sentiment Intelligence | Extracted Information Predictive Value | Mutual Information vs lagged returns | Tier 2 (Experimental) | Active |
| **CAP-RS-01** | Research Intelligence | Source Reliability Ranking | Reproducibility Rate vs historical trials | Tier 1 (Bounded) | Stable |
| **CAP-AG-01** | Agent Intelligence | debate consensus calibration | Disagreement vector norm vs baseline | Tier 1 (Bounded) | Stable |
| **CAP-PL-01** | Planning | Long-Horizon Step Decomposition | Execution Rate vs DFS search planner | Tier 1 (Bounded) | Active |
| **CAP-MM-01** | Memory | multi-hop graph retrieval | Retrieval Latency vs flat vector lookup | Tier 1 (Bounded) | Active |
| **CAP-FE-01** | Feature Engineering | Non-stationary scaling | Out-of-sample prediction vs raw features | Tier 2 (Experimental) | Active |
| **CAP-EX-01** | Execution Intelligence | Average Market Slippage | Realized Cost vs VWAP curve baseline | Tier 1 (Bounded) | Active |
| **CAP-PO-01** | Portfolio Intelligence | Active Diversification Weighting | Sharpe Ratio vs equal-weighted baseline | Tier 1 (Bounded) | Stable |
| **CAP-SD-01** | Self-Debugging | AST Error Location rate | Detection latency vs standard traceback | Tier 1 (Bounded) | Active |

---

### Core Evolutionary Bounds

No capability may be transitioned to a higher autonomy tier without fulfilling the complete verification criteria described in `IMPROVEMENT_GOVERNANCE.md` and logging the empirical metrics within the `IMPROVEMENT_VALIDATION_REPORT.md`.
