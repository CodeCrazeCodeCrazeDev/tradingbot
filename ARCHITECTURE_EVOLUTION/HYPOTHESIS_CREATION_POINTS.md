# Hypothesis Creation Points - AlphaAlgo Audit 2026

This document lists the specific locations in the codebase where hypotheses are explicitly or implicitly created.

## 1. Explicit Creation Points
- **`trading_bot/core/csc/hypothesis.py`**: `HypothesisGenerator.generate_competing_branches`
  - *Description*: Generates multiple `ReasoningBranch` objects (hypotheses) for current market state.
- **`trading_bot/core/phce_d/hypothesis_generator.py`**: `HypothesisGenerator`
  - *Description*: Creates parallel hypotheses for the PHCE-D correction engine.
- **`trading_bot/alpha_research/self_evolving_researcher.py`**: `StrategyGenerator.generate_random_strategy`
  - *Description*: Creates new `StrategyDNA` (hypotheses) using genetic building blocks.
- **`trading_bot/alpha_research/hypothesis_extraction.py`**: `HypothesisExtractionEngine.extract_from_research`
  - *Description*: Converts unstructured research papers/text into formal `ScientificHypothesis` objects.
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.observe`
  - *Description*: Initial creation of a `ScientificHypothesis` object from a raw observation.

## 2. Implicit Creation Points
- **`trading_bot/alpha_research/feature_mining_system.py`**: Feature candidates.
  - *Description*: Every discovered feature is a hypothesis that the feature has predictive power.
- **`trading_bot/core/hms/memory.py`**: `SAGEGraphMemory.add_evidence`
  - *Description*: New triplets in the graph often represent new beliefs or assumptions about causal relationships.
- **`trading_bot/alpha_research/unified_alpha_brain.py`**: `UnifiedAlphaBrain.register_strategy`
  - *Description*: Registering a strategy is an implicit hypothesis that the strategy is profitable in current regimes.
- **`trading_bot/core/aletheia_browser_research.py`**: `AletheiaClaim` generation.
  - *Description*: Every claim extracted from browser research is a hypothesis requiring verification.
- **`trading_bot/core/csc/router.py`**: `SkillRouter.register_skill`
  - *Description*: A new skill artifact is a hypothesis that a specific code/LoRA adapter can solve a class of problems.
