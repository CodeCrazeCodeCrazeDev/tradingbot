# Codebase Hypothesis Rejection Points (Comprehensive Audit 2026)

## Executive Summary
This document inventories every subsystem point where hypotheses are invalidated, vetoed, discarded, or moved to a terminal invalid state.

---

## Rejection Points Inventory

### 1. Risk & Deterministic Rejection
- **`trading_bot/core/phce_d_engine.py`**
  - *Method*: `PHCEDEngine.veto_hypothesis()`
  - *Description*: Immediately rejects trade ideas or factor proposals violating drawdown, leverage, or volatility limits.
- **`trading_bot/agents/multi_agent_debate.py`**
  - *Method*: `RiskVerifier.issue_risk_veto()`
  - *Description*: Issues binding risk vetoes rejecting trade execution hypotheses.

### 2. Scientific Reasoning Engine Rejection
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
  - *Method*: `ScientificReasoningEngine.reject()`
  - *Description*: Marks hypotheses as `Rejected` when out-of-sample calibration error exceeds threshold or Sharpe ratio is negative.

### 3. Self-Improvement Safety Rejection
- **`trading_bot/governance/evolution_gate.py`**
  - *Method*: `EvolutionGate.validate_evolution()`
  - *Description*: Synchronously rejects code modification hypotheses that attempt to alter governance limits or core evaluator routines.
