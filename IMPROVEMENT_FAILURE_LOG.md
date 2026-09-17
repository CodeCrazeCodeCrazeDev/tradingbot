# Improvement Failure Log Specification (RSI-FAILURE-2026)

## 1. Overview and Structural Post-Mortems

Every rejected candidate or failed production deployment must be documented as a structured, immutable learning artifact within `IMPROVEMENT_FAILURE_LOG.md`. AlphaAlgo uses these failure logs to systematically update its priors, ensuring the system learns from its own failures and avoids trying identical or highly correlated modifications again.

For every failure, the log records:
*   **Failing Component:** The class/subsystem containing the failure.
*   **Root Cause Category:** Data failure, model failure, reasoning/planning failure, execution failure, risk failure, or evaluation/coordination failure.
*   **Empirical Metrics at Failure:** Volatility, spread, latency, drawdown, or exception traceback.

---

## 2. Failure and Reject Log Entries

Every entry compiles the detailed post-mortem and the required **Counterfactual Corrective Hypothesis**:

### Entry FL-01
```json
{
  "failure_id": "FAIL-LOG-2026-0814-01",
  "experiment_id": "EXP-ST-01",
  "improvement_id": "IMP-ST-02",
  "failing_component": "Strategy Generator (Multi-Factor Ensemble)",
  "root_cause_category": "Data Failure (Information Leakage)",
  "failure_description": "Candidate achieved Sharpe Ratio of 1.88 in virtual backtests, but crashed to 0.45 when evaluated on the temporal hidden out-of-sample set.",
  "metrics_at_failure": {
    "oos_sharpe": 0.45,
    "leakage_coefficient": 0.48
  },
  "counterfactual_analysis": {
    "hypothesis": "If the training set features had been purged of overlapping lookahead windows and embargoed, the model would not have selected leaky indicators.",
    "corrective_action": "Order the Feature Engineering Loop to enforce 5-day purged/embargoed boundaries on all candidate features prior to optimization."
  }
}
```

---

## 3. Policy on Overfitting Remediation

AlphaAlgo strictly prohibits "remedying" failures by simply tuning parameters or overfitting a failed dataset. Parameter modifications must be justified by an explanatory, structural hypothesis that is verified across independent, out-of-sample datasets.
