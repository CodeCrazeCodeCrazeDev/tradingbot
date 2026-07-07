# 08_CAUSAL_REASONING_ENGINE.md - Hybrid SCM and do-calculus Logic

## Objective
Design the engine that allows the World Model to reason about cause-and-effect rather than just correlations.

## 1. The Hybrid Causal Framework
The engine combines **Explicit Causal Graphs** (Institutional Knowledge) with **Learned Latent Causal Models** (Neural Discovery).

### A. Explicit Financial Causal Graph (EFCG)
Hard-coded or HMS-driven relationships:
*   $\text{Interest Rates} \to \text{Yield Curve} \to \text{Currency Demand} \to \text{FX Pair Value}$.
*   $\text{VIX} \to \text{Option Premium} \to \text{Delta Hedging} \to \text{Market Liquidity}$.

### B. Latent Causal Discovery (LCD)
The Neural Core learns a causal adjacency matrix $\mathcal{A}$ in the latent space $z$:
$$z_{t+1} = \sigma(\mathcal{A} \cdot z_t + \Phi(z_t, a_t))$$
$\mathcal{A}$ is constrained to be a Directed Acyclic Graph (DAG) during training via a sparsity penalty and acyclicity constraint (e.g., NOTEARS algorithm).

## 2. Structural Causal Model (SCM) Components
An SCM is defined as a triplet $(\mathcal{U}, \mathcal{V}, \mathcal{F})$:
*   $\mathcal{U}$: Exogenous variables (unobserved market shocks).
*   $\mathcal{V}$: Endogenous variables (Price, Volume, Volatility, Our Actions).
*   $\mathcal{F}$: Functions $v_i = f_i(\text{parents}(v_i), u_i)$ representing the mechanisms.

## 3. Pearl's Intervention Engine ($do$-calculus)
The engine supports three levels of the "Ladder of Causation":

### Level 1: Association (Seeing)
*   "What is the probability of a price move given I see a large order?"
*   $P(y | x)$

### Level 2: Intervention (Doing)
*   "What happens to the price if **I** place a large order?"
*   $P(y | do(x))$
*   Implementation: Replace the node $X$ in the graph with a constant $x$, prune incoming edges to $X$, and propagate the change through the remaining graph.

### Level 3: Counterfactuals (Imagining)
*   "What would have happened to my profit if I had NOT placed that order 5 minutes ago?"
*   $P(y_x | x', y')$
*   Implementation: Update the exogenous distribution $P(\mathcal{U})$ based on the observed outcome $(x', y')$, then perform the $do(x)$ intervention on the updated model.

## 4. Institutional Application: Action-as-Cause
The World Model explicitly treats the agent's action as a causal intervention.
*   **Action:** `LimitOrder(size=1M, price=1.05)`
*   **Causal Effect:** Reduces available liquidity at 1.05, moves queue position, triggers HFT response, potentially moves mid-price.

## 5. Validation of Causality
*   **Interventional Faithfulness:** Does the model's $do(x)$ prediction match reality when we actually perform $x$?
*   **Sparsity:** Is the causal graph minimal, or does it suffer from "dense correlation" (where everything causes everything)?
