# 04_CAPABILITY_GAP_ANALYSIS.md - Institutional Requirement Mapping

## Objective
Map the current system's capabilities against the required institutional-grade World Model benchmarks.

## Capability Matrix

| Capability | Current State (V1/V2) | Target State (V3) | Gap |
| :--- | :--- | :--- | :--- |
| **Temporal Context** | 512 - 1024 steps | 100k+ steps (Mamba) | Substantial. V1/V2 collapse on long sequences. |
| **Prediction Target** | Latent vector $z$ | Trajectory $\tau$ + Reasoning | Conceptual. Moving from "prediction" to "forethought." |
| **Uncertainty** | Gaussian Mu/Var | Full Distribution / Particles | High. Need to capture multi-modality and tail risk. |
| **Causality** | Correlational | Pearlian $do(x)$ Interventions | Fundamental. Cannot currently simulate "actions as causes." |
| **Memory** | Isolated / Per-Module | HMS Unified Tiering | Integration. World Model must be a first-class HMS citizen. |
| **Execution** | External Estimation | Internalized Microstructure | High. Model must "know" the order book. |
| **Multi-Asset** | Limited Summation | Graph-Based Contagion | High. Need explicit cross-asset causal links. |
| **Reasoning** | None (Latent only) | Structured Evidence Graphs | Fundamental. No explainability in current latent core. |

## Critical Gaps

### 1. The "Foresight Bottleneck"
The current models cannot "think" more than a few steps ahead without accumulating error that makes the simulation useless for institutional planning.
*   **Requirement:** Multi-horizon future simulation with error correction.

### 2. The "Execution Blind Spot"
The current World Model treats our own actions as passive inputs rather than structural interventions that change market liquidity and price.
*   **Requirement:** Internalized execution dynamics (Impact, Slippage, Fill probability).

### 3. The "Semantic Gap"
There is no bridge between the "numbers" in the latent core and the "logic" in the Cognitive System Controller.
*   **Requirement:** Generation of machine-readable (Logic) and human-readable (Audit) reasoning traces.

### 4. The "Memory Silo"
Valuable world-state discoveries are lost because they aren't persisted in a global, tiered memory system accessible to other agents.
*   **Requirement:** Full WMR (Write-Manage-Read) loop integration with the HMS.

## Success Benchmarks (Target)
* **Calibration Error:** < 0.05 (Predicted probabilities match realized frequencies).
* **Simulation Diversity:** Generating at least 3 distinct, high-probability scenarios per trade.
* **Causal Accuracy:** > 90% accuracy in predicting the direction of impact for specific interventions.
* **Latency:** < 100ms for a full multi-path rollout of 50 steps.
