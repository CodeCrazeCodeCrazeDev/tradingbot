# 14. MATHEMATICAL FOUNDATIONS
## Mathematical Foundations, Objective Functions & Statistical Standards

### 1. Document Overview
This document consolidates the complete mathematical foundations of the **Institutional AI-for-AI Research System (ASRS)**. Every division relies on precise, formal equations to govern its behavior, compute performance, evaluate risk, model the market, and validate promotions.

---

### 2. Statistical Analysis & Significance

#### Paired Bootstrap Confidence Intervals
To construct confidence intervals for a performance delta metric $\theta = \mu_{\text{candidate}} - \mu_{\text{baseline}}$:
1. Resample indices $j^* = [i_1^*, \dots, i_N^*]$ with replacement from $[1, \dots, N]$ of historical out-of-sample periods.
2. Calculate the resampled metric delta:
   $$\theta^* = \hat{\mu}_{\text{candidate}}(j^*) - \hat{\mu}_{\text{baseline}}(j^*)$$
3. Repeat $B = 10,000$ times to compile the empirical bootstrap distribution $\theta^{*(1)}, \dots, \theta^{*(B)}$.
4. Compute the percentile confidence interval $[\theta^*_{\alpha/2}, \theta^*_{1-\alpha/2}]$ where $\alpha = 0.05$. Promotion requires:
   $$\theta^*_{\alpha/2} > 0$$

#### False Discovery Rate (FDR) Control
To control the proportion of false positives when running $m$ simultaneous mutations, we apply the Benjamini-Hochberg procedure. Sort p-values:
$$p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$$
Identify the largest index $k$ satisfying:
$$p_{(k)} \le \frac{k}{m} \cdot Q$$
Where $Q = 0.05$. Reject all null hypotheses $H_0^{(i)}$ for $i = 1, \dots, k$.

#### Sequential Probability Ratio Test (SPRT)
For sequential shadow validation of calibration error $x_t$:
$$\Lambda_n = \sum_{i=1}^n \ln \frac{f(x_i \mid H_1)}{f(x_i \mid H_0)}$$
Assuming $x_i \sim \mathcal{N}(\mu, \sigma^2)$:
$$\Lambda_n = \frac{\mu_1 - \mu_0}{\sigma^2} \sum_{i=1}^n x_i - \frac{n(\mu_1^2 - \mu_0^2)}{2\sigma^2}$$
* Reject candidate and halt if $\Lambda_n \ge \ln \frac{1-\beta}{\alpha}$.
* Terminate shadow validation and promote if $\Lambda_n \le \ln \frac{\beta}{1-\alpha}$.

#### Effect Size (Cohen's $d$)
To measure the standardized magnitude of the improvement:
$$d = \frac{\bar{x}_c - \bar{x}_b}{s_{\text{pooled}}} \qquad \text{where} \quad s_{\text{pooled}} = \sqrt{\frac{(n_c-1)s_c^2 + (n_b-1)s_b^2}{n_c + n_b - 2}}$$

---

### 3. Optimization & Search Algorithmic Foundations

#### CMA-ES (Covariance Matrix Adaptation Evolution Strategy)
In generation $g$, search parameters are sampled from a multivariate normal distribution:
$$x_k^{(g+1)} \sim m^{(g)} + \sigma^{(g)} \mathcal{N}\left(0, C^{(g)}\right) \qquad \text{for } k = 1, \dots, \lambda$$
Where:
* $m^{(g)}$: Mean of the distribution.
* $\sigma^{(g)}$: Step size.
* $C^{(g)}$: Covariance matrix.
The parameters are updated using the elite selection weights $w_i$:
$$m^{(g+1)} = \sum_{i=1}^{\mu} w_i x_{i:\lambda}^{(g+1)}$$
Covariance update is adapted using the evolution path $p_c^{(g+1)}$ to capture coordinate dependencies.

#### Multi-Objective Pareto Dominance (NSGA-II)
A candidate $u$ Pareto-dominates candidate $v$ ($u \prec v$) iff:
$$\forall i \in \{1, \dots, D\}, f_i(u) \le f_i(v) \quad \text{and} \quad \exists i \in \{1, \dots, D\}, f_i(u) < f_i(v)$$
For multi-objective metrics (Latency vs. Sharpe), NSGA-II sorts candidates into non-dominated fronts $\mathcal{F}_1, \mathcal{F}_2, \dots$ and uses **crowding distance** to preserve diversity.

---

### 4. Quantitative Trading & Risk Metrics

#### Sharpe, Sortino & Calmar
* **Sharpe**:
  $$S = \frac{\mathbb{E}[R_p - R_f]}{\sqrt{\text{Var}(R_p)}}$$
* **Sortino**:
  $$S_o = \frac{\mathbb{E}[R_p - R_f]}{\sqrt{\mathbb{E}[(\min(0, R_p - R_f))^2]}}$$
* **Calmar**:
  $$C_a = \frac{\text{Annualized Return}}{\max_{t \in [0, T]} \left( \max_{\tau \in [0, t]} P_{\tau} - P_t \right) / \max_{\tau \in [0, t]} P_{\tau}}$$

#### Conditional Value at Risk (CVaR)
For a confidence level $\alpha$ and portfolio loss $L$:
$$\text{CVaR}_{\alpha} = \frac{1}{1-\alpha} \int_{\alpha}^1 \text{VaR}_{u}(L) \, du = \mathbb{E}[L \mid L \ge \text{VaR}_{\alpha}]$$

#### Liquidity-Adjusted Value at Risk (L-VaR)
Integrating execution liquidation delay and order-book depth constraints:
$$\text{L-VaR}_{\alpha} = \text{VaR}_{\alpha} + \sum_{i=1}^M V_i \left( \frac{s_i}{2} + \gamma_i \frac{V_i}{\text{ADV}_i} \right)$$
Where $V_i$ is position volume, $s_i$ is spread, and $\text{ADV}_i$ is average daily volume.

---

### 5. World Model & Active Inference

#### Variational Free Energy (VFE) Minimization
The variational distribution $Q(x)$ approximates the true posterior over latent states $x$ given observations $y$:
$$F(Q, y) = \int Q(x) \ln \frac{Q(x)}{P(y, x)} \, dx$$
This can be decomposed into:
$$F(Q, y) = \underbrace{D_{\text{KL}}\left(Q(x) \parallel P(x \mid y)\right)}_{\text{Ambiguity / Divergence}} - \underbrace{\ln P(y)}_{\text{Surprise}}$$

#### Expected Free Energy (EFE) for Planning
For policy $\pi$ and horizon step $\tau$:
$$G(\pi, \tau) = \mathbb{E}_{Q(y_{\tau}, x_{\tau} \mid \pi)} \left[ \ln Q(x_{\tau} \mid y_{\tau}, \pi) - \ln P(y_{\tau}, x_{\tau}) \right]$$
Expanding this yields:
$$G(\pi, \tau) \approx \underbrace{\mathbb{E}_{Q(y_{\tau} \mid \pi)} \left[ D_{\text{KL}}\left(Q(x_{\tau} \mid y_{\tau}, \pi) \parallel Q(x_{\tau} \mid \pi)\right) \right]}_{\text{Epistemic Value (Information Seek)}} + \underbrace{\mathbb{E}_{Q(x_{\tau} \mid \pi)} \left[ \ln Q(x_{\tau} \mid \pi) - \ln P(x_{\tau}) \right]}_{\text{Pragmatic Value (Preference Satisfaction)}}$$

---

### 6. Multi-Objective Experiment Selection
The **Cost-Aware Research Planner** evaluates candidates using an expected utility framework. The utility function of candidate $j$ is computed as:

$$\mathcal{U}_j = \underbrace{\mathbb{E}[\Delta U_j]}_{\text{Expected Benefit}} \times \underbrace{\mathcal{P}(\text{success}_j)}_{\text{Feasibility}} - \underbrace{\mathcal{C}(\text{compute}_j)}_{\text{Hardware Cost}} + \lambda \cdot \underbrace{\mathcal{H}(j)}_{\text{Novelty / Entropy}}$$

Where:
* $\mathbb{E}[\Delta U_j]$: Weighted linear sum of target metric improvements (Sharpe, ECE, Latency).
* $\mathcal{P}(\text{success}_j)$: Logistic regressor model estimating completion probability based on historic runs.
* $\mathcal{C}(\text{compute}_j)$: Realized electricity and infrastructure dollar cost to run the experiment.
* $\mathcal{H}(j)$: Shannon entropy of the candidate's parameter space compared to the existing knowledge base, representing structural novelty.
