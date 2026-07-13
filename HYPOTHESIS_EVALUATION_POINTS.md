# Hypothesis Evaluation Points

This document lists every location where hypotheses are tested, scored, or verified.

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

## Bayesian Updating

1.  **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
    - `ScientificReasoningEngine.bayesian_update()`: Formal update of posterior probabilities.
2.  **`trading_bot/foundation_agents/curiosity_engine/hypothesis_generator.py`**
    - `HypothesisGenerator.update_hypothesis_status()`: Updates confidence scores based on evidence.
3.  **`trading_bot/verification/confidence_calibrator.py`**
    - `PredictionRecord`: Audits historical prediction accuracy for recalibration.
4.  **`trading_bot/signals/auto_disable_sick_signals.py`**
    - `SignalHealthMonitor`: Evaluates the continuing validity of the "signal-as-hypothesis".
5.  **`trading_bot/core/adversarial_failure_analysis.py`**
    - `AdversarialAnalyzer`: Attempts to falsify signal hypotheses by simulating catastrophic market scenarios.
