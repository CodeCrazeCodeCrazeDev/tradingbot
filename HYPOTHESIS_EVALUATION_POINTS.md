# Codebase Hypothesis Evaluation Points (Comprehensive Audit 2026)

## Executive Summary
This document maps every location in the AlphaAlgo codebase where hypotheses (predictions, signals, factor expressions, regime models) are subjected to quantitative, empirical, or deterministic evaluation.

---

## Evaluation Points Inventory

### 1. Deterministic & Risk Boundaries
- **`trading_bot/core/phce_d_engine.py`**
  - *Method*: `PHCEDEngine.evaluate_falsification_checks()`
  - *Description*: Runs deterministic verification routines evaluating leverage, execution friction, drawdowns, and tail-risk bounds.
- **`trading_bot/core/security/defense.py`**
  - *Method*: `HardenedGovernanceRoot.verify_risk_invariants()`
  - *Description*: Evaluates execution candidate proposals against immutable financial risk safety invariants.

### 2. Scientific & Statistical Reasoning
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
  - *Method*: `ScientificReasoningEngine.evaluate()`
  - *Description*: Evaluates hypothesis empirical performance using Expected Calibration Error (ECE), Sharpe ratio, and Bayesian evidence scores.
- **`trading_bot/world_model/counterfactual_engine.py`**
  - *Method*: `CounterfactualEngine.evaluate_intervention()`
  - *Description*: Evaluates state trajectories under counterfactual market conditions.

### 3. Swarm & Governance Review
- **`trading_bot/agents/multi_agent_debate.py`**
  - *Method*: `StrategicPeerReviewer.falsify_proposal()`
  - *Description*: Conducts multi-agent peer review falsification looking for logical fallacies or risk oversights in trade ideas.
