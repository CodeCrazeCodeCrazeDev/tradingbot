# 09. WORLD MODEL RESEARCH
## World Model Research Division & Active Inference Architecture

### 1. Architectural Mission
The **World Model Research Division (WMRD)** is the cognitive planning and simulation engine of ASRS. Its sole responsibility is to maintain, refine, and evolve the **Generative World Model (GWM)** of AlphaAlgo.

The GWM represents the system's internal beliefs about the market. It performs three crucial functions: predictive planning, causal reasoning, and future trajectory generation. The WMRD uses the mathematical framework of **Active Inference** to minimize **Variational Free Energy (VFE)**, ensuring that AlphaAlgo's internal world representations remain highly calibrated to reality.

---

### 2. Active Inference & Variational Free Energy Minimization
Active inference conceptualizes the trading agent as a self-organizing system that minimizes surprise (Variational Free Energy) by updating its internal beliefs (perception) or executing trades that align the market state with its preferred bounds (action).

```mermaid
graph LR
    %% Active Inference loop
    A[Market Observations] -->|Surprise / VFE| B[Belief Update (Perception)]
    B -->|Generative Model Updates| C[Generative World Model]
    C -->|Expected Free Energy Optimization| D[Policy Execution (Action)]
    D -->|Trades / Market Orders| A

    classDef main fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    class B,C,D main;
```

#### Variational Free Energy (VFE)
The GWM represents the joint probability of latent market states $x$ and observed price data $y$ as $P(y, x)$. Given a variational distribution $Q(x)$ representing the agent's posterior belief over hidden states, the Variational Free Energy is defined as:

$$F(Q, y) = \mathbb{E}_{Q(x)}\left[\ln \frac{Q(x)}{P(y, x)}\right] = D_{\text{KL}}\left(Q(x) \parallel P(x \mid y)\right) - \ln P(y)$$

By minimizing $F$, the agent achieves two goals:
1. It minimizes the Kullback-Leibler (KL) divergence between its internal beliefs $Q(x)$ and the true distribution of the market $P(x \mid y)$ (accuracy).
2. It maximizes the evidence lower bound (ELBO) of observations, reducing surprise.

#### Expected Free Energy (EFE)
When planning future action trajectories (trading policies $\pi$), the GWM evaluates policies based on their **Expected Free Energy (EFE)** over a future planning horizon $\tau$:

$$G(\pi, \tau) \approx \sum_{\tau} \left( \mathbb{E}_{Q(y_{\tau} \mid \pi)} [ D_{\text{KL}} ( Q(x_{\tau} \mid y_{\tau}, \pi) \parallel Q(x_{\tau}) ) ] + \mathbb{E}_{Q(y_{\tau} \mid \pi)} [ \ln Q(y_{\tau} \mid \pi) - \ln P(y_{\tau}) ] \right)$$

* The first term represents **epistemic value** (information gain): policies are selected to resolve ambiguity about latent market regimes.
* The second term represents **pragmatic value** (preference satisfaction): policies are selected to keep the portfolio state within safe, profitable boundary conditions (e.g., avoiding drawdowns).

---

### 3. Causal Reasoning & Counterfactual Simulations
To prevent simple correlation-chasing and ensure robust decision making, the WMRD integrates **Structural Causal Models (SCMs)** and Judea Pearl's **do-calculus** into the planning loop.

The GWM can perform counterfactual simulations (asking "What if?") to test causal stability:

$$\text{SCM: } \quad y_t = f_y(x_{t-1}, u_{t, y}) \qquad z_t = f_z(y_t, u_{t, z})$$

Where $y_t$ is the market state, $z_t$ is the strategy response, and $u_t$ represents exogenous noise.

By executing a $do$-intervention (e.g., $do(\text{Volatility} = \text{High})$), the GWM breaks incoming causal links and simulates how the strategy would behave under completely different conditions without running actual trades. This permits rigorous test-time simulation of tail risk scenarios.

---

### 4. Future Trajectory Generation
Before a trading signal is sent to the Unified Decision Bus, the GWM runs 100+ parallel multi-step monte carlo trajectory rollouts.

```text
       +--------------------------------------------+
       |   GWM 10-Step Trajectory Rollout (M15)     |
       +--------------------------------------------+
       |                                            |
       |  T0 (Now) ---> T1 ---> T2 ---> T3 ... T10  |
       |    |                                       |
       |    +-[Rollout 1: Trend continues]          |
       |    +-[Rollout 2: Mean-reversion trigger]   |
       |    +-[Rollout N: Sharp Volatility Spike]   |
       |                                            |
       |  * Measure Shannon Entropy of Rollouts:    |
       |    H(Y) = - Sum( P(y) * log(P(y)) )        |
       |  * If Entropy > Threshold, reduce sizing.   |
       +--------------------------------------------+
```

If the predictive entropy (uncertainty) of future price trajectories exceeds the dynamic boundary condition, the GWM signals the Risk Sentinel to reduce position sizing, preventing over-leveraged exposure in highly unpredictable regimes.
