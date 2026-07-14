# 10_PLANNING_ENGINE.md - Predictive Planning and Scenario Evaluation

## Objective
Design the engine that uses future simulations to make optimal trading decisions under uncertainty.

## 1. Predictive Planning Paradigm
The World Model V3 does not output "buy/sell." It outputs a **Plan Evaluation** for a sequence of actions $a_{t:t+H}$.

## 2. The Planning Loop (Lookahead Search)

1.  **Proposal:** The CSC proposes a set of candidate plans $\{\pi_1, \pi_2, \dots\}$.
2.  **Simulation:** For each plan $\pi_j$:
    *   The **Future Simulation Engine** generates $N$ scenarios $\{\tau_{j,1}, \dots, \tau_{j,N}\}$.
    *   The **Causal Engine** ensures each scenario incorporates the impact of plan $\pi_j$ ($do(\pi_j)$).
3.  **Evaluation:** Calculate the **Expected Utility** $U(\pi_j)$ for each plan:
    $$U(\pi_j) = \sum_{i=1}^N w_i \cdot \text{Utility}(\tau_{j,i})$$
    Where Utility is the risk-adjusted return (Sharpe/CVaR) realized in that specific future.
4.  **Selection:** Select the plan that maximizes Expected Utility while staying within the **Governance Shield** limits.

## 3. Opportunity Ranking
The engine ranks trading opportunities not by "expected price move," but by **Risk-Adjusted Expected Foresight (RAEF)**:
$$\text{RAEF} = \frac{\mathbb{E}[\text{Profit}]}{\text{CVaR} + \text{UncertaintyPenalty}}$$
This ensures we avoid "high profit / high ignorance" trades.

## 4. Counterfactual Planning
The engine continuously evaluates "What if we hadn't taken this trade?" (The Null Plan).
If the Null Plan's utility becomes superior to the Active Plan (due to new market information), the engine triggers an **Emergency Exit** recommendation.

## 5. Hierarchical Planning (HIPIF)
Planning happens at multiple horizons:
*   **Tactical (1-60s):** Execution dynamics, queue position, slippage.
*   **Strategic (1-60m):** Alpha decay, trend persistence, liquidity shifts.
*   **Structural (1-24h):** Regime evolution, macro announcements.

Higher-level plans set the constraints and objectives for lower-level plans.

## 6. Planning Algorithms
*   **Monte Carlo Tree Search (MCTS):** For long-horizon strategic discrete decisions (e.g., "Enter now vs. Enter after NY Open").
*   **Cross-Entropy Method (CEM):** For continuous optimization of order sizing and execution timing.
*   **Model Predictive Control (MPC):** For real-time tactical adjustments to execution trajectories.

## 7. Reasoning Trace Generation
For the selected plan, the engine produces a **Decision Graph**:
*   "We chose Action X because Scenario A (60% prob) leads to target profit, and Scenario C (10% prob) has a manageable 1% drawdown, whereas Action Y had a 5% tail risk in Scenario B."
*   This is exported to the **HMS** as the authoritative record of the decision.
