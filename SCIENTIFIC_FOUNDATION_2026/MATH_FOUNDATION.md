# Mathematical Foundation: Unified Foresight-Conditioned Intelligence
**Date:** March 16, 2026

## 1. Unified Agentic Objective

The core objective is to internalize the future directly into the policy $\pi_\theta$. Instead of a reactive mapping $s \to a$, we optimize for a predictive mapping $s \to (\tau, \hat{Q}, a)$, where $\tau$ is a prospective trajectory and $\hat{Q}$ is a self-estimated success probability.

### 1.1 The Foresight-Conditioned Loss
The model is trained on a three-term composite objective:

$$ \mathcal{L}(\theta) = \mathcal{L}_{\text{policy}} + \alpha \mathcal{L}_{\text{dynamics}} + \beta \mathcal{L}_{\text{calibration}} $$

#### Term 1: Predictive Policy Loss ($\mathcal{L}_{\text{policy}}$)
Standard cross-entropy over actions, but conditioned on the model's own generated foresight:
$$ \mathcal{L}_{\text{policy}} = -\sum_{t} \log \pi_\theta(a_t^* | s_t, \hat{\tau}_t, \hat{Q}_t) $$

#### Term 2: Latent Dynamics Loss ($\mathcal{L}_{\text{dynamics}}$)
Forces the internal representation to be predictive of future states (V-JEPA / DreamerV3 style):
$$ \mathcal{L}_{\text{dynamics}} = \sum_{h=1}^H \| z_{t+h} - \text{Predictor}(z_t, a_{t:t+h-1}) \|^2 $$
where $z$ are the latent embeddings from the multimodal perception encoder.

#### Term 3: Foresight Calibration Loss ($\mathcal{L}_{\text{calibration}}$)
Ensures that the verbalized success estimate $\hat{Q}$ matches the actual cumulative discounted reward $G_t$:
$$ \mathcal{L}_{\text{calibration}} = \| \hat{Q}_t - G_t \|^2 $$

## 2. World Model V3: Causal State-Space

The World Model $M$ is a digital twin representing the transition function:
$$ P(s_{t+1} | s_t, a_t, \xi_t) $$
where $\xi_t$ represents the latent participant inventory risk and liquidity reflexivity.

### 2.1 Uncertainty Decomposition
We decompose total predictive uncertainty $\sigma^2$ into:
1.  **Aleatoric ($\sigma_a^2$):** Stochastic market noise, irreducible.
2.  **Epistemic ($\sigma_e^2$):** Model ignorance, reducible with data.

Using the ensemble variance $\text{Var}_{\phi \in \text{Ensemble}} [ f_\phi(z_t, a_t) ]$ to gate the planning horizon $H$.

## 3. Active Inference & Variational Free Energy
The agent minimizes Variational Free Energy $\mathcal{F}$ to maintain a coherent belief state $q(s)$:
$$ \mathcal{F} = \text{DKL}[q(s) \| p(s | o)] - \mathbb{E}_{q(s)}[\log p(o | s)] $$
This ensures that the "One Brain" always updates its internal market model upon receiving new observations $o$, effectively "Internalizing the Future" through constant alignment with the past.
