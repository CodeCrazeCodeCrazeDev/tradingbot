# Hypothesis Evaluation Points (Institutional Audit 2026)

## Core Scientific Evaluation
1. **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.evaluate_results()` & `bayesian_update()`.
2. **`trading_bot/core_agent_system/cds/epistemology_engine.py`**: `EpistemologyEngine.analyze_hypothesis()` (Adversarial questioning).

## Tactical Evaluation (Decision Layer)
1. **`trading_bot/core/phce_d_engine.py`**: `ParallelHypothesisCorrectionEngine.process()` (Evidence synthesis).
2. **`trading_bot/core/csc/controller.py`**: `CSC._verify_evidence_hard_constraint()` (Graph-based verification).
3. **`trading_bot/core_agent_system/cds/verdict_engine.py`**: `VerdictEngine.synthesize_verdict()` (Weighted consensus).

## Statistical & Technical Evaluation
1. **`trading_bot/alpha_research/strategy_diagnostics.py`**: `StrategyDiagnostics` (Overfitting, health, and robustness).
2. **`trading_bot/strategy_discovery/validation.py`**: `StrategyValidationPipeline` (Regime testing, transaction costs).
3. **`trading_bot/alpha_research/alpha_death_clock.py`**: `AlphaDeathClockManager` (Decay monitoring).
4. **`trading_bot/world_model/imagination.py`**: `PlanEvaluator.evaluate_plan()` (Lookahead utility across scenarios).

## Governance & Institutional Evaluation
1. **`trading_bot/core/unified_event_bus.py`**: `LogAction.wait_for_decision()` (Consensus/Voter auditing).
2. **`trading_bot/core/immutable_shield.py`**: `ImmutableShield.validate_action()` (Hard safety rails).
