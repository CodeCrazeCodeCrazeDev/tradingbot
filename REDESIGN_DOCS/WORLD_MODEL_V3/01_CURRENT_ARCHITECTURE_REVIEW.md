# 01_CURRENT_ARCHITECTURE_REVIEW.md - World Model Architectural Audit

## Objective
Provide a critical audit of the existing World Model implementations (Legacy JEPA and V2 Skeleton) to identify structural weaknesses and architectural drift.

## Assumptions
* The current production system relies on the JEPA-based `WorldModel` in `latent_dynamics.py`.
* `WorldModelV2` exists as an experimental skeleton and is not fully integrated into the Cognitive System Controller (CSC).

## Current Implementations

### 1. Legacy JEPA Architecture (`latent_dynamics.py`)
* **Mechanism:** Joint-Embedding Predictive Architecture. It attempts to predict the next latent state $z_{t+1}$ given current state $z_t$ and action $a_t$.
* **Strengths:** Computationally efficient for short-term latent transitions.
* **Weaknesses:**
    * **Latent-Only:** Predictions are abstract vectors with no physical grounding in market dynamics (e.g., price, liquidity).
    * **Passive Foresight:** It lacks a mechanism for multi-step scenario branching.
    * **Execution Blindness:** Does not model the feedback loop between the agent's action and the market's response (e.g., slippage, impact).
    * **Fragmentation:** Overlaps with `DreamerV3` logic in the ensemble, leading to "orchestration debt."

### 2. Experimental V2 Skeleton (`v2_core.py`)
* **Mechanism:** Hybrid Transformer-Mamba (SSM).
* **Strengths:**
    * Introduction of State-Space Models for linear-scaling temporal dependencies.
    * Initial attempt at a "Predictive Market Core."
* **Weaknesses:**
    * **Simplified SSM:** The Mamba implementation is a basic recurrent approximation, lacking the rigorous discretization and parallel associative scans required for institutional tick-data processing.
    * **Isolated Memory:** Maintains its own `MarketWorldState` instead of leveraging the Unified Hierarchical Memory System (HMS).
    * **Naive Simulation:** Scenarios are generated via simple Gaussian perturbations rather than probabilistic trajectory sampling (e.g., Diffusion or Quantile-based).
    * **Causal Deficit:** The `CausalDynamicsModel` is a linear projection layer, failing to implement true Pearlian interventions or structural causal graphs.

### 3. Orchestration & Integration
* **The "Swarm Mirage":** The system suffers from multiple overlapping orchestrators (IntegratedAgentSystem, MasterOrchestrator) trying to manage different versions of the World Model.
* **Information Bottlenecks:** World state information is often "trapped" within the model instead of being "folded" into the HMS for cross-agent reasoning.

## Architectural Drift
The codebase contains at least three distinct World Model paradigms:
1. **V1 (JEPA):** Latent transition focus.
2. **V2 (Predictive):** Early transformer-mamba focus.
3. **FWM (Foresight):** Incomplete agentic foresight experiments.

## References
* `trading_bot/world_model/latent_dynamics.py`
* `trading_bot/world_model/v2_core.py`
* `WORLD_MODEL_ARCHITECTURAL_AUDIT.md`
