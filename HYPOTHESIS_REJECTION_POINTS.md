# Hypothesis Rejection Points (Institutional Audit 2026)

## Logical & Structural Rejection
1. **`trading_bot/alpha_research/hypothesis_extraction.py`**: `HypothesisValidator` (Lacks mechanism/falsification).
2. **`trading_bot/core/talos_cerberus_v23.py`**: `EvidenceScorecard` (Source unreliability, compliance failure).

## Performance & Decay Rejection
1. **`trading_bot/apex_fi/alpha_mining.py`**: `LivingFactorLibrary._retire_factor()` (Sharpe/Entropy decay).
2. **`trading_bot/signals/auto_disable_sick_signals.py`**: `SignalHealthMonitor` (Recent failure rate).
3. **`trading_bot/strategy_discovery/evolutionary_engine.py`**: Fitness-based selection (Natural selection of genomes).

## Safety & Governance Rejection
1. **`trading_bot/core/unified_event_bus.py`**: `LogAction` status `REJECTED` or `VETOED` (Voter consensus).
2. **`trading_bot/core/immutable_shield.py`**: Hard constraint violation (Risk/Exposure).
3. **`trading_bot/core/phce_d_engine.py`**: `SimpleValidationGateway` (Market hostility).

## Scientific Rejection
1. **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `HypothesisState.REJECTED` (Posterior belief < 0.2).
2. **`trading_bot/core/adversarial_failure_analysis.py`**: `AdversarialAnalyzer` (Successful falsification simulation).
