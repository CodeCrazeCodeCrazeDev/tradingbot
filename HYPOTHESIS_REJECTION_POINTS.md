# Hypothesis Rejection Points (Verified Audit 2026)

1. **`trading_bot/core/phce_d_engine.py`**: `PHCEDOutput.REJECTED` state triggered by evidence failure or conservative policies.
2. **`trading_bot/apex_fi/alpha_mining.py`**: `_retire_factor()` - Factor removal due to alpha decay.
3. **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `HypothesisState.REJECTED` terminal state.
