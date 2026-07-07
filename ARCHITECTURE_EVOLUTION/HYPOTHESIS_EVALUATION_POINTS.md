# Hypothesis Evaluation Points - AlphaAlgo Audit 2026

This document lists the specific locations where hypotheses are evaluated, tested, or challenged.

## 1. Internal Validation (Pre-Execution)
- **`trading_bot/core/csc/hypothesis.py`**: `HypothesisGenerator.simulate_branches`
  - *Mechanism*: GWM simulation to estimate expected value and uncertainty.
- **`trading_bot/core/verification/swarm.py`**: `VerificationSwarm.run_swarm`
  - *Mechanism*: Multi-agent adversarial debate to find falsification triggers.
- **`trading_bot/core/phce_d/verifier.py`**: Statistical and deterministic verification of PHCE-D lanes.
- **`trading_bot/alpha_research/hypothesis_extraction.py`**: `HypothesisValidator.validate`
  - *Mechanism*: Checks for formal consistency and data availability for extracted hypotheses.

## 2. Empirical Validation (Execution)
- **`trading_bot/alpha_research/self_evolving_researcher.py`**: `BacktestEngine.backtest`
  - *Mechanism*: Historical replay on market data to calculate Sharpe, Sortino, and Drawdown.
- **`trading_bot/alpha_research/self_evolving_researcher.py`**: `StressTestEngine.run_stress_test`
  - *Mechanism*: Performance evaluation under synthetic "Black Swan" or "Liquidity Shock" scenarios.
- **`trading_bot/core/phce_d/adversarial_stress_test.py`**: Tests the entire PHCE-D pipeline against corrupted or outlier inputs.

## 3. Post-Execution & Bayesian Updating
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.evaluate_results`
  - *Mechanism*: Formal step 11 of the SRE lifecycle.
- **`trading_bot/alpha_research/unified_alpha_brain.py`**: `LessonLearner.learn_from_trade`
  - *Mechanism*: Updates strategy weights and pattern similarity scores based on trade outcomes.
- **`trading_bot/core/hms/memory.py`**: `HierarchicalMemorySystem.evolve_memory`
  - *Mechanism*: Updates the graph based on interaction history and success trajectories.
