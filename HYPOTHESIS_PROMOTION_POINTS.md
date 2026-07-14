# Hypothesis Promotion Points (Verified Audit 2026)

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
3.  **`trading_bot/intelligence_core/hypothesis_engine.py`**
    - `HypothesisEngine.graduate_hypothesis()`: Promotes validated hypotheses to strategy candidates (requires human approval).
4.  **`trading_bot/autonomous_research_organism/integration.py`**
    - `ResearchOrganism.share_hypothesis()`: Shares autonomous hypotheses with the central Research Lab for formal experiment orchestration.
5.  **`trading_bot/core_agent_system/self_play_loop.py`**
    - Policy versioning: Promoting the "Best" policy based on win rate in self-play tournaments.

## Institutionalization

1.  **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
    - `HypothesisState.INSTITUTIONALIZED`: Moving successful hypotheses to permanent semantic memory.
2.  **`trading_bot/core/hms/memory.py`**
    - `AutoMem`: Automating the transformation of successful episodes into generalized procedural or semantic memory.
