# Mathematical Foundation: Unified Cognitive Architecture (UCA)

This document provides the formal mathematical grounding for the AlphaAlgo UCA, integrating principles from Active Inference, Causal Inference, and Information Theory.

---

## 1. Agent Decision Making: Active Inference (FEP)

The Persistent Cognitive Agent (PCA) is modeled as a process minimizing **Variational Free Energy** ($\mathcal{F}$) under the Free Energy Principle.

### 1.1 The Generative Model
An agent possesses a generative model $P(o, s, \pi)$ over observations $o$, hidden states $s$, and policies $\pi$.

### 1.2 Variational Free Energy
The agent minimizes $\mathcal{F}$, which is an upper bound on surprise (negative log-evidence):
$$\mathcal{F} = D_{KL}[Q(s) || P(s | o)] - \ln P(o)$$
Where $Q(s)$ is the agent's approximate posterior (belief) about the state. This can be decomposed into:
$$\mathcal{F} = \underbrace{D_{KL}[Q(s) || P(s)]}_{\text{Complexity}} - \underbrace{E_{Q(s)}[\ln P(o | s)]}_{\text{Accuracy}}$$

### 1.3 Expected Free Energy (EFE)
For future planning, the agent selects policies $\pi$ that minimize **Expected Free Energy** ($G$):
$$G(\pi, \tau) = \underbrace{E_{Q(o_\tau, s_\tau | \pi)}[\ln Q(s_\tau | \pi) - \ln Q(s_\tau | o_\tau, \pi)]}_{\text{Epistemic Value (Information Gain)}} + \underbrace{E_{Q(o_\tau | \pi)}[\ln Q(o_\tau | \pi) - \ln P(o_\tau | C)]}_{\text{Pragmatic Value (Goal Seeking)}}$$
- **Epistemic Value**: Reduces uncertainty by seeking informative observations (Exploration).
- **Pragmatic Value**: Minimizes the divergence between predicted outcomes and desired goals $C$ (Exploitation).

---

## 2. World Model: Causal Structural Models & Do-Calculus

The Generative World Model (GWM) enables agents to reason about the consequences of their actions using **Causal Structural Models (SCM)**.

### 2.1 Causal Interventions
A standard prediction is $P(y | x)$, but a causal intervention (a "do-operation") is $P(y | do(x))$.
The GWM implements **Pearl's Backdoor Criterion** to estimate interventions from historical data:
$$P(y | do(x)) = \sum_z P(y | x, z) P(z)$$
Where $Z$ is a set of sufficient adjustment variables (confounders) like market regime or liquidity state.

### 2.2 Counterfactuals
The GWM supports the "Third Rung" of the Causal Ladder: **Counterfactuals**.
Given an event that occurred ($X=x, Y=y$), the GWM estimates what would have happened if $X$ had been $x'$:
$$P(Y_{x'} = y' | X=x, Y=y)$$
This allows the agent to compute **Counterfactual Regret** ($\mathcal{R}$):
$$\mathcal{R} = E[Y_{do(x_{opt})} - Y_{realized}]$$
This regret signal is used to update the agent's procedural policies.

---

## 3. Memory & Learning: Information Bottleneck

The Hierarchical Memory System (HMS) employs the **Information Bottleneck (IB)** principle for knowledge distillation.

### 3.1 Objective Function
To compress episodic experiences into semantic knowledge, the HMS minimizes:
$$\mathcal{L}_{IB} = I(S; Z) - \beta I(Z; R)$$
- $I(S; Z)$: Mutual information between raw states $S$ and compressed representation $Z$ (Compression).
- $I(Z; R)$: Mutual information between $Z$ and future rewards/outcomes $R$ (Sufficiency).
- $\beta$: Trade-off parameter (The "Memory Horizon").

This ensures that only information relevant to *future decision-making* is preserved in long-term memory.

---

## 4. Uncertainty: Bayesian Belief Updating

Beliefs are updated using a **Recursive Bayesian Filter**:
$$P(s_t | o_{1:t}) \propto P(o_t | s_t) \int P(s_t | s_{t-1}, a_{t-1}) P(s_{t-1} | o_{1:t-1}) ds_{t-1}$$
The UCA implements this via a **Variational Autoencoder (VAE)** architecture where the encoder approximates the posterior and the GWM (SSM/Transformer) represents the transition dynamics.

---

## 5. Summary of Mathematical Requirements for UCA

| Component | Formalism | Objective |
| :--- | :--- | :--- |
| **Agent Action** | Active Inference | Minimize Expected Free Energy ($G$). |
| **World Model** | SCM / Do-Calculus | Estimate $P(y | do(x))$ and Counterfactuals. |
| **Memory** | Information Bottleneck | Maximize Predictive Information ($I(Z; R)$). |
| **Learning** | Bayesian Inference | Minimize Surprise (Variational Free Energy $\mathcal{F}$). |
| **Communication** | Game Theory | Achieve Nash Equilibrium in Multi-Agent Debate. |
