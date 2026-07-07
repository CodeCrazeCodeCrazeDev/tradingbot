# Hypothesis Creation Points

This document lists every location in the AlphaAlgo codebase where hypotheses are explicitly or implicitly created.

## Explicit Creation Points (Modules)

1.  **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
    - `ScientificReasoningEngine.observe()`: Creates a new `ScientificHypothesis` from raw data.
2.  **`trading_bot/foundation_agents/curiosity_engine/hypothesis_generator.py`**
    - `HypothesisGenerator.generate_from_anomaly()`: Creates hypotheses to explain market anomalies.
    - `HypothesisGenerator.generate_from_surprise()`: Creates hypotheses from surprising events.
    - `HypothesisGenerator.generate_from_correlation()`: Creates causal/predictive hypotheses from statistical correlations.
3.  **`trading_bot/alpha_research/hypothesis_extraction.py`**
    - `HypothesisGenerator.generate()`: Extracts testable hypotheses from academic research papers.
4.  **`trading_bot/core/csc/hypothesis.py`**
    - `HypothesisGenerator.generate_competing_branches()`: Creates parallel `ReasoningBranch` and `Hypothesis` objects for scenario analysis.
5.  **`trading_bot/core/phce_d_engine.py`**
    - `PHCEDAI._generate_hypothesis()`: Creates deterministic falsifiable hypotheses for trade validation.
6.  **`trading_bot/apex_fi/alpha_mining.py`**
    - `GeneticAlphaSearch._generate_random_expression()`: Creates `AlphaCandidate` hypotheses using genetic programming.
7.  **`trading_bot/core_agent_system/multidimensional_intelligence/hypothesis_engine.py`**
    - `HypothesisEngine.pose_hypothesis()`: Registers cross-domain scientific hypotheses (Physics, Math, etc.).

## Implicit Creation Points (Inferred Hypotheses)

1.  **`trading_bot/strategy_discovery/evolutionary_engine.py`**
    - `StrategyGenome`: Every genome is an implicit hypothesis that "X indicator combination predicts returns".
2.  **`trading_bot/world_model/imagination.py`**
    - Every "Imagined" future is a temporary hypothesis about market dynamics.
3.  **`trading_bot/ml/offline_rl/alphaalgo_autonomous_system.py`**
    - Every policy update is an implicit hypothesis about the optimal action-value mapping.
