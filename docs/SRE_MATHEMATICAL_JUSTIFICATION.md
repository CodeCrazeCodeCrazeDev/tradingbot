# Mathematical Justification: AlphaAlgo Scientific Reasoning Engine

## 1. Bayesian Belief Updating
The core of the SRE is a recursive Bayesian update mechanism. For any hypothesis $H$ and incoming evidence $E$:

$$P(H|E) = \frac{P(E|H)P(H)}{P(E)}$$

- **Prior $P(H)$**: Initialized via novelty scores and similarity to existing Level 5 (Institutional) knowledge.
- **Likelihood $P(E|H)$**: Modeled via the **World Model V2** simulation. How likely is the evidence $E$ given the hypothesis state?
- **Posterior $P(H|E)$**: Becomes the new Prior for the next reasoning cycle.

## 2. Information-Theoretic Discovery
Anomaly detection is driven by **Variational Free Energy** (Surprisal) minimization, a concept from Active Inference:

$$F = \text{Surprisal} + \text{Divergence}$$

When the World Model's prediction $\hat{x}$ diverges from observation $x$, the SRE interprets the residual as "Surprisal." High surprisal triggers **Question Generation** to reduce future uncertainty.

## 3. Causal Inference (SCM)
Hypotheses are not just correlations but Structural Causal Models (SCMs):

$$X = f(Pa(X), U_X)$$

Where $Pa(X)$ are the causal parents and $U_X$ is exogenous noise.
- **Merge Logic**: Two hypotheses $H_1, H_2$ are merged if their SCM graphs are isomorphic and their Joint Information Gain is negligible.
- **Split Logic**: A hypothesis $H$ is split if its causal mechanism $f$ shows high variance across disjoint market regimes $R_a, R_b$.

## 4. Uncertainty Decomposition
We decompose uncertainty $\sigma_{total}$ into:
- **Aleatoric ($\sigma_a$)**: Inherent market noise (e.g., high frequency volatility).
- **Epistemic ($\sigma_e$)**: Lack of system knowledge (e.g., unseen regime).

Promotion to Level 5 requires $\sigma_e \to 0$ over $N$ diverse regimes.

---

# Validation Framework

## 1. Calibration Error (ECE)
Measure how well the system's "Confidence" ($P(H|E)$) predicts actual success.
- **Metric**: Expected Calibration Error (ECE).
- **Goal**: $\text{ECE} < 0.1$.

## 2. Hypothesis Survival Analysis
Track the "Half-life" of hypotheses.
- **Metric**: Kaplan-Meier survival curves for different Hypothesis Types.
- **Goal**: Identify which sources (Agents) produce "High-Decay" (Overfitted) hypotheses.

## 3. Robustness via Counterfactuals
Test the hypothesis against "Synthetic Stress" in the World Model.
- **Test**: Does the hypothesis hold under $do(z)$ interventions (e.g., "What if liquidity drops by 50%?")?

## 4. Knowledge Graph Coherence
Measure the density and connectivity of the Institutional Knowledge Graph.
- **Metric**: Clustering coefficient and average path length of the Evidence Graph.
