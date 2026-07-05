# 05_MATHEMATICAL_FOUNDATION.md - Formalizing Predictive Planning

## Objective
Provide the rigorous mathematical formulation for the World Model V3, moving beyond simple regression to Active Inference and Causal Planning.

## 1. The Generative World Model (GWM)
The GWM is defined as a transition model $P_\theta$ that governs the evolution of the market state $s$ under an action $a$:

$$P_\theta(s_{t+1}, \dots, s_{t+H} | s_t, a_{t:t+H-1})$$

Unlike JEPA, which minimizes latent error, V3 maximizes the **Evidence Lower Bound (ELBO)** of the market dynamics under Active Inference.

## 2. Active Inference & Expected Free Energy
The World Model's objective is to minimize the **Expected Free Energy (EFE)** for a plan $\pi$:

$$G(\pi, t) \approx \underbrace{\mathbb{E}_{Q(s_{t+\tau}, o_{t+\tau} | \pi)} [\ln Q(s_{t+\tau} | \pi) - \ln Q(s_{t+\tau} | o_{t+\tau}, \pi)]}_{\text{Information Gain (Epistemic)}} + \underbrace{\mathbb{E}_{Q(o_{t+\tau} | \pi)} [\ln Q(o_{t+\tau} | \pi) - \ln P(o_{t+\tau})]}_{\text{Expected Utility (Pragmatic)}}$$

Where:
*   $Q$ is the model's belief.
*   $P(o_{t+\tau})$ represents the institutional "prior" for success (e.g., target Sharpe, risk limits).

## 3. Causal Interventions ($do$-calculus)
We model the market as a Structural Causal Model (SCM). An intervention on a variable $X$ (e.g., our order size) is represented by the $do$ operator:

$$P(Y | do(X = x)) = \int P(Y | x, z) P(z) dz$$

Where $Z$ are the parent variables (pre-intervention market state). The World Model learns the causal adjacency matrix $\mathcal{G}$ to propagate these effects.

## 4. Probabilistic Trajectory Generation (Diffusion)
To generate the distribution of futures, we use a Diffusion-based approach:

$$q(x_0) \to q(x_T) \sim \mathcal{N}(0, I)$$
$$p_\theta(x_{t-1} | x_t) = \mathcal{N}(x_{t-1}; \mu_\theta(x_t, t), \Sigma_\theta(x_t, t))$$

This allows the model to sample diverse, multi-modal trajectories $\tau = \{s_{t+1}, \dots, s_{t+H}\}$ by denoising from a latent prior.

## 5. Execution Dynamics (Microstructure)
We explicitly model the **Slippage Function** $\mathcal{S}$ and **Fill Probability** $\mathcal{F}$:

$$\mathcal{S}(a_t, L_t) = \alpha \cdot \text{Impact}(a_t) + \beta \cdot \text{Volatility}(s_t)$$
$$\mathcal{F}(a_t, Q_{pos}, t) = \sigma(\kappa \cdot (\text{QueueDepth} - Q_{pos}))$$

Where $L_t$ is the L2 liquidity state and $Q_{pos}$ is our queue position.

## 6. Reward & Risk Metric Formulation
The reward $R$ is a multi-objective vector optimized via FC-RL:

$$R = \omega_1 \cdot \text{Sortino} - \omega_2 \cdot \text{CVaR}_\alpha - \omega_3 \cdot \text{CalibrationError} - \omega_4 \cdot \text{TurnoverPenalty}$$

Calibration error is defined as the Kullback-Leibler (KL) divergence between predicted scenario probabilities and realized outcome frequencies.
