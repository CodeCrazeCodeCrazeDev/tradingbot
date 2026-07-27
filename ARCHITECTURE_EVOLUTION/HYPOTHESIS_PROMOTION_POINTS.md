# Hypothesis Promotion Points - AlphaAlgo Audit 2026

This document lists where hypotheses are promoted to higher levels of authority or moved into production.

## 1. Research to Production
- **`trading_bot/alpha_research/self_evolving_researcher.py`**: `SelfEvolvingResearcher._promote_winners`
  - *Description*: Moves top-ranked strategy candidates from the research pool to the deployment-ready pool.
- **`trading_bot/core/phce_d/paper_trade_promotion.py`**: `PaperTradePromotionLayer`
  - *Description*: Promotes hypotheses from simulation to paper trading, and eventually to live execution based on performance stability.
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.consolidate_memory`
  - *Description*: Step 15, promoting a validated hypothesis to "Institutional Knowledge" (Level 5).

## 2. Structural & Semantic Promotion
- **`trading_bot/core/hms/memory.py`**: `HierarchicalMemorySystem.store_scientific_lesson`
  - *Description*: Promotes a specific discovery into the persistent `ScientificMemoryObject` layer.
- **`trading_bot/alpha_research/hypothesis_extraction.py`**: Batch promotion from unstructured research to validated hypothesis models.
- **`trading_bot/core/csc/router.py`**: `SkillRouter.register_skill`
  - *Description*: Promotion of an experimental LoRA/HASP script to an "Approved Skill" used by the CSC.
