# Hypothesis Creation Points

The following locations in the AlphaAlgo codebase are responsible for the explicit or implicit creation of hypotheses:

| Subsystem | File Path | Mechanism |
|-----------|-----------|-----------|
| **PHCE-D** | `trading_bot/phce_d/hypothesis_generator.py` | `generate_from_anomaly()`, `generate_from_template()` |
| **SRE** | `trading_bot/core_agent_system/scientific_reasoning/core.py` | `observe()`, `generate_hypothesis()` |
| **CSC** | `trading_bot/core/csc/hypothesis.py` | `generate_competing_branches()` |
| **World Model** | `trading_bot/world_model/imagination.py` | Generates "Futures" which act as implicit hypotheses. |
| **Research** | `trading_bot/_archive/alphaalgo_institutional/research_loop.py` | `ResearchCandidate` creation. |
| **Autonomous** | `trading_bot/autonomous/alpha_factor_discovery.py` | `AlphaFactor` instantiation. |
| **Self-Improvement**| `trading_bot/autonomous/self_checklist_extended.py` | `SelfStrategyGeneration` class. |
| **Meta Learning** | `trading_bot/ai_core/meta_learning/adaptive_retrainer.py` | Implicitly creates hypotheses about regime shifts. |
| **Swarm** | `trading_bot/core_agent_system/swarm/experts.py` | Individual experts proposing "Trade Ideas". |
| **Decision Layer** | `trading_bot/core/unified_decision_gate.py` | Aggregates and implicitly validates incoming signals as hypotheses. |
