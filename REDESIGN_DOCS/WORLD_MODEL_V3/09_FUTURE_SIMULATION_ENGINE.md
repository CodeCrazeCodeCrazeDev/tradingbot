# 09_FUTURE_SIMULATION_ENGINE.md - Probabilistic Trajectory Generation

## Objective
Design a high-fidelity engine capable of generating diverse, multi-modal future market trajectories.

## 1. Beyond Point Estimates
Financial markets are non-deterministic. A single "average" future is a failure mode. The engine must generate a **Scenario Set** $\mathcal{T} = \{\tau_1, \tau_2, \dots, \tau_N\}$.

## 2. Simulation Backbone: Diffusion Trajectory Generator
We utilize a conditional diffusion model to sample future paths:
1.  **Encoder:** Maps current market context $c_t$ to a condition vector.
2.  **Denoising Process:** Starts with Gaussian noise $\tau_T$ and iteratively refines it into a realistic market trajectory $\tau_0$ conditioned on $c_t$.
3.  **Benefit:** Diffusion naturally captures multi-modality (e.g., a path can branch into either "Crash" or "Moon" rather than averaging into "Sideways").

## 3. Scenario Architecture

### A. The "Trinity" Scenarios (Minimum Requirement)
Every trade evaluation must generate at least:
*   **Scenario A (Base Case):** Continuation of current momentum and regime.
*   **Scenario B (Aggressive/Bull):** Tail event in favor of the trade (e.g., volatility expansion + directional move).
*   **Scenario C (Adverse/Bear):** Tail event against the trade (e.g., liquidity dry-up + sharp reversal).

### B. Scenario Tree Expansion
For complex multi-day plans, the model generates a tree where nodes represent significant regime transitions (e.g., "Post-CPI Data Release").

## 4. Probabilistic Weighting
Each trajectory $\tau_i$ is assigned a probability weight $w_i$ such that $\sum w_i = 1$.
*   Weights are derived from the **Uncertainty Engine** (Epistemic + Aleatoric).
*   High epistemic uncertainty (model ignorance) triggers a wider variance in scenario generation.

## 5. Causal Grounding
Each simulated future must be **Causally Consistent**.
*   If Price increases, Liquidity and Volatility must adjust according to the SCM (e.g., price spike often leads to temporary spread widening).
*   Simulations that violate Causal Adjacency (e.g., price moving without any change in order flow or macro context) are pruned by the **Causal Auditor**.

## 6. Execution Dynamics Integration
A trajectory is not just price. It is a multi-dimensional state vector:
$$\tau = \begin{bmatrix} \text{Price}_t \\ \text{Spread}_t \\ \text{Depth}_t \\ \text{Impact}_t \\ \text{Sentiment}_t \end{bmatrix}_{t:t+H}$$

## 7. Metrics for Simulation Quality
*   **Diversity Score:** Measures the variance between scenarios (preventing mode collapse).
*   **Realism Score:** Discriminator-based check (from GAN/Diffusion training) to ensure trajectories "look like" real market data.
*   **Calibration:** $P(\text{Outcome} \in \text{Scenario Range})$ should match the target confidence level.
