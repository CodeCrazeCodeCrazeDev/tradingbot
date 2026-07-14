# Hypothesis Evaluation Points (Verified Audit 2026)

## Core Evaluation
1. **`trading_bot/core/phce_d_engine.py`**: `ParallelHypothesisCorrectionEngine.process()` - Main evaluation pipeline using EvidencePackets.
2. **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.evaluate_results()` / `bayesian_update()`.

## Deterministic Verification

1.  **`trading_bot/core/phce_d_engine.py`**
    - `PHCEDAI._verify()`: Performs deterministic/statistical checks (spread, cost, sample size).
    - `PHCEDAI._apply_policy()`: Final gate for paper-trade promotion.
2.  **`trading_bot/core/csc/controller.py`**
    - `CSC._verify_evidence_hard_constraint()`: Enforces graph density and verifier consensus.

## Adversarial Evaluation

1.  **`trading_bot/core_agent_system/cds/epistemology_engine.py`**
    - `EpistemologyEngine.analyze_hypothesis()`: Calculates belief scores and uncertainty using adversarial questioning.
2.  **`trading_bot/core/verification/swarm.py`**
    - `VerificationSwarm.run_swarm()`: Peer-review of hypotheses by specialized agents (Hallucination detector, etc.).

## Statistical & Machine Learning Evaluation

1.  **`trading_bot/strategy_discovery/evolutionary_engine.py`**
    - `EvolutionaryStrategyEngine._fitness_function()`: Evaluates genomes based on Sharpe, Drawdown, and Win Rate.
2.  **`trading_bot/alpha_research/alpha_death_clock.py`**
    - `AlphaDeathClockManager`: Continuously monitors alpha decay (hypothesis degradation).
3.  **`trading_bot/alpha_research/strategy_diagnostics.py`**
    - Performs robustness and over-fitting checks.
4.  **`trading_bot/strategy_discovery/validation.py`**
    - `StrategyValidationPipeline.validate_strategy()`: Systematic validation including in-sample, out-of-sample, and regime testing.
5.  **`trading_bot/profit_maximizer/profit_maximizer_core.py`**
    - `SignalConfluenceScorer.score_signal()`: Evaluates signal confidence by adjusting base confidence with confluence and conflict scores.
6.  **`trading_bot/market_student/market_teacher.py`**
    - `MarketTeacher`: Post-hoc evaluation of AI predictions against actual market outcomes to extract lessons.
7.  **`trading_bot/world_model/v2_training.py`**
    - Uncertainty Calibration Loss: Evaluates the calibration of the model's predictive distributions.

## Bayesian Updating

1.  **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
    - `ScientificReasoningEngine.bayesian_update()`: Formal update of posterior probabilities.
2.  **`trading_bot/foundation_agents/curiosity_engine/hypothesis_generator.py`**
    - `HypothesisGenerator.update_hypothesis_status()`: Updates confidence scores based on evidence.
