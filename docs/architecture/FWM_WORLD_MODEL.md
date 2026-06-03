# FWM: Hierarchical World Model Architecture

## 1. Core Architecture: Neural Hierarchical State-Space Model (NHSSM)

### Evaluation of World Model Architectures
*   **Dreamer V3 (RSSM):** Powerful latent dynamics, but struggles with the discrete jumps and non-linearities of financial markets.
*   **MuZero:** Excellent planning in discrete spaces, but financial markets are continuous and partially observable (POMDP).
*   **Transformer World Models:** Great at long-term memory, but high computational cost for continuous simulation.

### Proposed Architecture: The "Skip-Graph RSSM"
We utilize a **Hierarchical Latent Dynamics** approach:

1.  **L1 - Micro-Dynamics (Continuous RSSM):**
    - Operates at the tick/second level.
    - Predicts the next latent state $z_{t+1}$ given $z_t$ and action $a_t$.
    - Captures "physics-level" market noise and mean reversion.
2.  **L2 - Macro-Transitions (Jump Transformer):**
    - Operates at the regime/event level (e.g., FOMC meeting, news break).
    - Predicts discrete "jumps" between latent macro-regimes.
    - Gates L1's predictions based on the global context.

## 2. Agent-Based Market Simulation (The Digital Twin)

The World Model is trained to simulate the behavior of 7 distinct participant types:

| Participant | Objectives | Constraints | Reaction Function |
| :--- | :--- | :--- | :--- |
| **Retail** | Trend chasing, emotional exits. | Capital limited, high fees. | Positively correlated to 1-day momentum. |
| **Market Makers** | Spread capture, inventory neutrality. | Max inventory risk limits. | Mean-reverting to mid-price; wide spreads in high vol. |
| **CTAs / Trend** | Momentum exploitation. | Strict VAR limits, 20-day filters. | Systematic buying on breakouts. |
| **Hedge Funds** | Relative value, macro alpha. | Drawdown limits, leverage caps. | Causal response to macro data and spread dislocations. |
| **HFTs** | Latency arb, order flow toxicity. | Ultra-low latency, no overnight. | Scalp passive orders; front-run large aggressive clips. |
| **Institutions** | Large scale accumulation/distribution. | Execution quality (VWAP/IS). | VWAP schedules; large passive blocks. |
| **Options Dealers** | Gamma/Vanna hedging. | Delta neutral mandate. | Systematic hedging against price/vol moves; creates "pinned" levels. |

### Emergent Behavior
Emergent behavior (e.g., Flash Crashes, Gamma Squeezes) is produced when the **Inventory Constraints** of multiple agents are hit simultaneously. The FWM learns the **Phase Transitions** of these interactions.

## 3. Scenario Generation & Reasoning
The model generates thousands of "Dreams" (rollouts) using the **Monte Carlo Tree Search (MCTS)** guided by the Policy-Value networks.
*   **Plausibility:** Measured by the distance between the "Dream" latent trajectory and the historical distribution of that regime.
*   **Counterfactuals:** Implemented via "Do-Calculus". We force a change in a latent variable (e.g. `z_liquidity = 0`) and observe the L1/L2 response chain.
