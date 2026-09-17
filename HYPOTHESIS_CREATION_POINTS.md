# Codebase Hypothesis Creation Points (Comprehensive Audit 2026)

## Executive Summary
This document provides a subsystem-by-subsystem inventory of every location in the **AlphaAlgo Autonomous Trading System** where hypotheses (explicit or implicit) are created, instantiated, or proposed.

---

## Creation Points Inventory

### 1. Research & Strategy Discovery
- **`trading_bot/alpha_research/hypothesis_extraction_engine.py`**
  - *Method/Class*: `HypothesisExtractionEngine.extract_hypotheses()`
  - *Description*: Extracts explicit falsifiable alpha hypothesis expressions and causal mechanisms from academic PDFs and papers.
- **`trading_bot/alpha_research/alpha_mining_engine.py`**
  - *Method/Class*: `AlphaMiningEngine.mine_candidate_alpha()`
  - *Description*: Synthesizes candidate alpha mathematical formulas from raw feature correlations.
- **`trading_bot/alpha_research/curiosity_engine.py`**
  - *Method/Class*: `CuriosityEngine.generate_novel_hypothesis()`
  - *Description*: Generates novelty-driven market structural hypotheses based on high prediction error clusters.

### 2. World Model & Causal Reasoning
- **`trading_bot/world_model/unified_world_model.py`**
  - *Method/Class*: `UnifiedWorldModel.predict_state_rollout()`
  - *Description*: Generates multi-horizon latent state projection hypotheses under $do(X)$ interventions.
- **`trading_bot/world_model/causal_reasoning_engine.py`**
  - *Method/Class*: `CausalReasoningEngine.propose_causal_dag()`
  - *Description*: Proposes structural causal graphs representing underlying market mechanics.

### 3. Cognitive & Decision System
- **`trading_bot/core/csc/controller.py`**
  - *Method/Class*: `CognitiveSystemController.synthesize_decision()`
  - *Description*: Generates trade execution candidate hypotheses combining multi-agent outputs.
- **`trading_bot/core_agent_system/scientific_reasoning/core.py`**
  - *Method/Class*: `ScientificReasoningEngine.observe()`
  - *Description*: Authoritative entry point instantiating formal 19-stage SRE hypothesis records.

### 4. Swarm & Multi-Agent Reasoning
- **`trading_bot/agents/multi_agent_debate.py`**
  - *Method/Class*: `HivemindAgentManager.propose_trade_hypothesis()`
  - *Description*: Generates structured agent trade proposals backed by confidence estimates and risk checks.

### 5. Self-Improvement & Evolution
- **`trading_bot/systems_ai/self_improvement.py`**
  - *Method/Class*: `AutonomousSelfImprovementEngine.propose_code_mutation()`
  - *Description*: Creates architectural or algorithmic code mutation hypotheses for self-evolution.
