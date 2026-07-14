# Hypothesis Rejection Points (Verified Audit 2026)

Hypotheses die or are rejected at the following points.

## Immediate Filtering

1.  **`trading_bot/alpha_research/hypothesis_extraction.py`**
    - `HypothesisValidator.validate()`: Rejects hypotheses lacking clear causal mechanisms or failure modes.
2.  **`trading_bot/core/phce_d_engine.py`**
    - `PHCEDAI._intake_evidence()`: Rejects hypotheses if the underlying evidence is stale or untrusted.

## Performance-Based Rejection

1.  **`trading_bot/apex_fi/alpha_mining.py`**
    - `LivingFactorLibrary._retire_factor()`: Retires alphas (hypotheses) that fall below a decay threshold.
2.  **`trading_bot/strategy_discovery/evolutionary_engine.py`**
    - Tournament selection naturally rejects low-fitness strategy genomes.

## Governance & Safety Rejection

1.  **`trading_bot/core/immutable_shield.py`**
    - `ImmutableShield.validate_action()`: Rejects execution of hypotheses that violate risk or safety constraints.
2.  **`trading_bot/core/phce_d_engine.py`**
    - `SimpleValidationGateway.validate()`: Rejects Buy/Sell recommendations due to market hostility or portfolio drawdown.
3.  **`trading_bot/strategy_discovery/validation.py`**
    - `StrategyValidationPipeline`: Explicitly rejects strategies dependent on a single regime or where transaction costs exceed 50% of alpha.
4.  **`trading_bot/core/talos_cerberus_v23.py`**
    - `EvidenceScorecard`: Rejects (quarantines) claims from forbidden sources or with low compliance/reliability scores.
5.  **`trading_bot/core/aletheia_browser_research.py`**
    - `AlphaAlgoBrowserUsePlanner`: Rejects research task plans that violate financial-domain safety rails.
