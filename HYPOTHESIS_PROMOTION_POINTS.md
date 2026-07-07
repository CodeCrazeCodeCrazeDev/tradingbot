# Hypothesis Promotion Points

Hypotheses move toward production and institutionalization at these points.

## Staging & Validation

1.  **`trading_bot/core/phce_d_engine.py`**
    - Promotion to `PAPER_TRADE_CANDIDATE`: Once a hypothesis survives cost stress and verifier checks.
2.  **`trading_bot/foundation_agents/curiosity_engine/hypothesis_generator.py`**
    - Promotion to `PRIORITIZED`: Selected for active testing by the curiosity system.

## Production Integration

1.  **`trading_bot/core/csc/controller.py`**
    - Trade Approval: Final promotion where a hypothesis influences capital allocation.
2.  **`trading_bot/alpha_research/live_deployment.py`**
    - Moves validated alphas from research to live production environments.

## Institutionalization

1.  **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
    - `HypothesisState.INSTITUTIONALIZED`: Moving successful hypotheses to permanent semantic memory.
2.  **`trading_bot/core/hms/memory.py`**
    - `AutoMem`: Automating the transformation of successful episodes into generalized procedural or semantic memory.
