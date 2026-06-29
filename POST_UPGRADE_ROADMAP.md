# AlphaAlgo Post-Upgrade Improvement Roadmap (Phase 2)
**Date:** March 16, 2026
**Auditor:** Jules (AI Senior Software Engineer)

---

## Executive Summary
Phase 1 successfully consolidated the architecture and established the infrastructure for real-world learning. However, many "Advanced" components added in Tier 3 are currently **functional skeletons**. Phase 2 must move from "Infrastructure Readiness" to "Production Dominance" by implementing the actual algorithmic loops inside these modules.

---

## 1. Intelligence Depth Improvements

### Finding 1.1: Symbolic Discovery is "Stateless"
*   **Problem:** The `SymbolicDiscovery` module returns a hardcoded equation rather than evolving one through genetic programming.
*   **Why it matters:** The system cannot actually "discover" new alpha; it only "demonstrates" the capability.
*   **Current limitation:** `discover_invariant` in `symbolic/engine.py` lacks a population evolution loop.
*   **Proposed solution:** Implement a real Genetic Programming (GP) loop using a library like `gplearn` or a custom tree-based evolution system.
*   **Expected impact:** True autonomous discovery of new market invariants.

### Finding 1.2: Information Bottleneck Integration Gap
*   **Problem:** The `InformationBottleneck` module is implemented but not integrated into the `WorldModel`'s training loop.
*   **Why it matters:** The `WorldModel` is still susceptible to market noise.
*   **Current limitation:** The module exists in `ml/information/` but is not imported or used in `latent_dynamics.py`.
*   **Proposed solution:** Replace the standard VAE encoder in `WorldModel` with the `InformationBottleneck` layer to force noise compression.
*   **Expected impact:** 20-30% reduction in prediction error during volatile regimes.

---

## 2. Self-Modification Frontier

### Finding 2.1: Sandbox is "Shadow-Only"
*   **Problem:** `SelfModificationEngine` performs "shadow writes" but doesn't actually mutate the live system code safely.
*   **Why it matters:** The system remains "frozen" in its current logic unless a human manually applies the shadow-written code.
*   **Current limitation:** `_write_modified_code` logs but doesn't write.
*   **Proposed solution:** Implement a **Docker-based Sandbox**. Mutations should be written to a temporary container, tested via `pytest`, and if performance improves, swapped into the live system via a symlink.
*   **Expected impact:** A truly "Living" AI system that improves its own source code 24/7.

---

## 3. Data & Learning Realism

### Finding 3.1: Data Loading Fallback
*   **Problem:** `SelfPlayLoop` has the infrastructure for real data but falls back to simulation because the data pipeline is not "hot."
*   **Why it matters:** RL training is only as good as the data. Falling back to simulation re-introduces the "Delusion Loop."
*   **Current limitation:** `_play_game` in `self_play_loop.py` uses `try-except` fallback to simulation.
*   **Proposed solution:** Implement a "Hot Data Buffer" that pre-loads the last 12 months of tick data into memory/Redis for instant access by the RL loop.
*   **Expected impact:** High-fidelity training results that translate directly to P&L.

---

## 4. Architectural Refinement

### Finding 4.1: MasterOrchestrator Search Complexity
*   **Problem:** MCTS-style search in `MasterOrchestrator` is a "shallow" search (depth 5).
*   **Why it matters:** Complex multi-step trading strategies (e.g., scale-in/scale-out) require deeper lookahead.
*   **Current limitation:** `search_depth` is limited by the performance of the non-vectorized world model.
*   **Proposed solution:** Vectorize the `WorldModel`'s `predict_next` to run on GPU, allowing search depth to increase from 5 to 50.
*   **Expected impact:** Detection of long-term strategic opportunities.

---

## 5. Summary of Next Actions

| Tier | Area | Improvement |
|------|------|-------------|
| **Next Tier 0** | Data | Hot-Buffer Tick Data Pipeline |
| **Next Tier 0** | Research | Real GP loop for Symbolic Discovery |
| **Next Tier 1** | ML | IB-Integrated World Model |
| **Next Tier 1** | Safety | Docker Sandbox for Self-Modification |
| **Next Tier 2** | Scaling | GPU-Vectorized MCTS |

---

**Status:** Ready for Phase 2 Implementation.
