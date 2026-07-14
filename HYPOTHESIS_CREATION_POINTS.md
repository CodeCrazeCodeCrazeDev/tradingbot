# Hypothesis Creation Points (Verified Audit 2026)

## Explicit Creation
1. **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.observe()` - Core entry point.
2. **`trading_bot/foundation_agents/curiosity_engine/hypothesis_generator.py`**: `HypothesisGenerator` - Specialized for anomalies and surprises.
3. **`trading_bot/apex_fi/alpha_mining.py`**: `AlphaMiningEngine` - Genetic and LLM-driven alpha/hypothesis discovery.

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
8.  **`trading_bot/core_agent_system/self_play_loop.py`**
    - `SelfPlayLoop.generate_hypothesis()`: Generates hypotheses from self-play experiences and policy improvements.
9.  **`trading_bot/world_model/imagination.py`**
    - `ImaginationEngine.simulate_scenarios()`: Generates diverse future market scenarios as testable state hypotheses.
10. **`trading_bot/market_teacher/absolute_laws.py`**
    - `AbsoluteLaws._create_draft_strategy()`: Transforms observed market patterns into draft strategy hypotheses.
11. **`trading_bot/alpha_research/hypothesis_extraction.py`**
    - `CausalMechanismExtractor`: Explicitly extracts causal mechanism hypotheses (Cause -> Effect -> Condition) from research.

## Implicit Creation Points (Inferred Hypotheses)

1.  **`trading_bot/strategy_discovery/evolutionary_engine.py`**
    - `StrategyGenome`: Every genome is an implicit hypothesis that "X indicator combination predicts returns".
2.  **`trading_bot/world_model/imagination.py`**
    - Every "Imagined" future is a temporary hypothesis about market dynamics.
3.  **`trading_bot/ml/offline_rl/alphaalgo_autonomous_system.py`**
    - Every policy update is an implicit hypothesis about the optimal action-value mapping.
4.  **`trading_bot/profit_maximizer/market_regime_adapter.py`**
    - `RegimeAnalysis`: Every regime classification is a hypothesis about the current market environment and optimal strategy adaptation.
5.  **`trading_bot/world_model/v2_training.py`**
    - Reasoning Traces: Every generated reasoning trace is a hypothesis about the causal chain leading to a predicted outcome.
