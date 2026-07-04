# Phase 5 (Part 2): Mathematical Foundation of UCA-2026

This document formalizes the mathematical objectives and optimization frameworks for the AlphaAlgo Unified Scientific Architecture.

---

## 1. Global Agentic Objective: Active Inference

The entire system is governed by the minimization of **Variational Free Energy (VFE)**, which provides a unified framework for both perception (state estimation) and action (policy selection).

### 1.1 Variational Free Energy
For an observation $o$, latent state $s$, and model parameters $\phi$:
$$\mathcal{F} = \mathbb{E}_{q_{\phi}(s)}[\ln q_{\phi}(s) - \ln p(o, s)]$$
$$\mathcal{F} = \mathcal{D}_{KL}[q_{\phi}(s) \| p(s | o)] - \ln p(o)$$
*   Minimizing $\mathcal{F}$ with respect to $q(s)$ results in **Active Perception** (updating beliefs to match reality).
*   Minimizing $\mathcal{F}$ with respect to the model parameters $\phi$ results in **Self-Improvement**.

### 1.2 Expected Free Energy (Policy Selection)
The CSC selects the policy $\pi$ that minimizes the **Expected Free Energy** over the future horizon:
$$\mathcal{G}(\pi) = \sum_{\tau} \mathcal{G}(\pi, \tau)$$
$$\mathcal{G}(\pi, \tau) = \underbrace{\mathbb{E}_{q(o_\tau, s_\tau | \pi)}[\ln q(s_\tau | \pi) - \ln p(s_\tau | o_\tau)]}_{\text{Epistemic Value (Uncertainty Reduction)}} + \underbrace{\mathbb{E}_{q(o_\tau | \pi)}[\ln q(o_\tau) - \ln p(o_\tau | C)]}_{\text{Pragmatic Value (Goal Seeking)}}$$
This objective naturally balances **Exploration** (Epistemic) and **Exploitation** (Pragmatic).

---

## 2. World Model: Structural Causal Model (SCM)

The World Model is formalized as an SCM allowing for **Structural Interventions**.

### 2.1 The SCM Formulation
$$\mathcal{M} = \{ \mathcal{F}, P(U) \}$$
$$V_i = f_i(Pa_i, U_i)$$
Where $V_i$ are market variables, $Pa_i$ are their causal parents, and $U_i$ are unobserved noise.

### 2.2 Do-Calculus (The Intervention Engine)
To predict the outcome of a trade $do(X=x)$ on return $Y$:
$$P(Y | do(X=x), Z) = \sum_{z} P(Y | X=x, Z=z) P(z)$$
This allows the system to simulate tail-risks and market impact without relying on historical correlations that might break during a crash.

---

## 3. Planning: Information Folding & Information Bottleneck

The **Information Folding** mechanism is justified by the **Information Bottleneck (IB)** principle.

### 3.1 The Folding Objective
We want to find a compressed representation $F_t$ of history $H_t$ that minimizes the information about the past while maximizing the information about the future strategic goal $G$:
$$\min I(F_t, H_t) - \beta I(F_t, G)$$
This ensures the context window only contains the "Sufficient Statistics" required for the long-horizon task.

---

## 4. Learning: Socratic Policy Optimization (SocraticPO)

The learning dynamics follow a modified Policy Gradient with **Reward Decay**.

### 4.1 Decay-Weighted Reward
$$\hat{R} = R \cdot e^{-\lambda n}$$
Where $R$ is the outcome reward (profit/loss), $\lambda$ is the decay constant, and $n$ is the number of teacher-assisted corrections.

### 4.2 Optimization (Reinforce++)
$$\nabla_{\theta} J(\theta) = \mathbb{E}_{\pi_{\theta}} \left[ \sum_{t=0}^T \nabla_{\theta} \log \pi_{\theta}(a_t | s_t, g_{teacher}) \hat{R} \right]$$
This forces the policy to prioritize **Self-Correction** over **Teacher-Correction**.

---

## 5. Decision Intelligence: Bayesian EV Optimization

Decisions are wrapped in **Bayesian Decision Theory**.

### 5.1 Calibrated Expected Value (EV)
$$\text{EV}(a) = \int \text{Utility}(s, a) P(s | a, \text{context}) ds$$
Where $P(s | a, \text{context})$ is the **Calibrated Posterior** from the World Model and PCA Epistemic Cores.
$$\text{Decision} = \arg \max_{a} \text{EV}(a)$$
The system will only act if $\text{EV}(a) > \text{Threshold} + \text{Cost of Action}$.
