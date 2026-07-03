# Stage 6: Mathematical Foundations

## 1. World Modeling: JEPA + SCM + Bayesian Filtering
The unified world model shall be grounded in three mathematical pillars:
*   **Joint-Embedding Predictive Architecture (JEPA)**: Minimizing prediction error in latent space rather than pixel/tick space. This allows for noise-robust representation learning.
*   **Structural Causal Models (SCM)**: Representing market relationships as a Directed Acyclic Graph (DAG) with Pearl's **do-calculus** for counterfactual interventions.
*   **Recursive Bayesian Filtering**: Maintaining a belief state $b_t = P(s_t | o_{1:t}, a_{1:t})$ with explicit uncertainty (Entropy $H(b_t)$) to quantify epistemic ignorance.

## 2. Decision Making: Active Inference & Expected Information Gain
The agent's objective function shall be the **Free Energy Principle**:
$$F = \mathbb{E}_{q(s)}[\ln q(s) - \ln p(s, o)]$$
Where agents act to minimize variational free energy, balancing exploitation (utility maximization) with exploration (Expected Information Gain - EIG).

## 3. Risk & Sizing: Information-Theoretic Kelly Criterion
The Kelly fraction $f^*$ shall be adjusted by the model's **Epistemic Uncertainty** $U$:
$$f_{adj} = f^* \cdot (1 - \frac{U}{U_{max}})$$
Where $U$ is derived from the variance of the World Model ensemble and the Information Bottleneck's noise estimate.

## 4. Strategy Evolution: Information Bottleneck (IB) & MDL
*   **Information Bottleneck**: Optimizing the trade-off between compression and prediction: $\min [I(X; Z) - \beta I(Z; Y)]$.
*   **Minimum Description Length (MDL)**: Using Kolmogorov complexity as a regularization term for strategy discovery to prevent overfitting (Occam's Razor for alpha).

## 5. Swarm Intelligence: Consensus via Dempster-Shafer Theory
Combining evidence from specialized swarm experts using **Dempster's Rule of Combination** to handle conflicting signals and non-additive probabilities (representing "unknown unknowns").

## 6. Learning: Meta-Learning & Causal Attribution
*   **Model-Agnostic Meta-Learning (MAML)**: Optimizing for rapid adaptation to new market regimes with few-shot updates.
*   **Causal Attribution**: Using Shapley values and counterfactual paths to attribute PnL to specific model components or internet data sources.
