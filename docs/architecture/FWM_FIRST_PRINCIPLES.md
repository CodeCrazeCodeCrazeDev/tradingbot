# Financial World Model: First Principles & Conceptual Framework

## 1. Defining the Financial World Model
A Financial World Model (FWM) is not a price predictor; it is a **Generative Digital Twin** of the global financial system. It models the causal mechanisms that generate market data, enabling the system to reason about "Why" the market is moving, not just "What" the next price might be.

## 2. Fundamental Flaws in Current Architectures
*   **The Stationarity Fallacy:** Current systems assume the statistical properties of markets are stable. In reality, markets are non-stationary, adversarial systems where the rules of the game change once they are discovered.
*   **Correlation vs. Causality:** Standard bots rely on historical correlations which breakdown during tail events. An FWM must use **Causal Do-Calculus** to understand structural relationships.
*   **The "Price is All" Myth:** Most systems ignore **Latent Positioning** and **Dealer Gamma**. Price is merely the residual of participant interactions, not the primary state variable.
*   **Lack of Epistemic Awareness:** Trading systems rarely distinguish between "market noise" and "model ignorance."

## 3. The Hidden States (The "Real" Market)
An institutional-grade FWM must represent:
1.  **Inventory Risk (Positioning):** The aggregate exposure of market participants (Dealers, CTAs, Hedge Funds). Crowded trades are the primary source of liquidity shocks.
2.  **Liquidity Reflexivity:** How liquidity provision contracts as volatility increases, creating feedback loops.
3.  **Information Asymmetry:** The latent flow of information from informed to uninformed participants.
4.  **Policy Feedback Loops:** The causal link between macro data (CPI/Employment) and Central Bank reaction functions.

## 4. Conceptual Design Principles
*   **Adversarial Multi-Agent Foundation:** Treat the market as a game where participants have competing objectives and constraints.
*   **Hierarchical Latent Dynamics:** Model the market at two speeds:
    *   *Microstructure Speed:* Millisecond-level order book dynamics.
    *   *Macro-Regime Speed:* Monthly-level structural shifts.
*   **Uncertainty Decomposition:** Always output both Aleatoric (Market Randomness) and Epistemic (Model Ignorance) uncertainty scores.
*   **Simulation-in-the-Loop:** Every decision is the result of thousands of counterfactual simulations ("If I buy 10k lots, what is the expected dealer response across 100 scenarios?").
