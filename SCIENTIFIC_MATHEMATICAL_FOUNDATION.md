# Scientific Reasoning Engine: Mathematical Foundation

## 1. Active Inference & Variational Free Energy

The SRE is grounded in **Active Inference**, where the agent minimizes **Variational Free Energy (VFE)** to maintain an accurate internal model of the world.

$$F = E_{q(\psi)}[\ln q(\psi) - \ln p(o, \psi)]$$

Where:
- $\psi$ is the hidden state (Market Hypothesis).
- $o$ is the observation.
- $q(\psi)$ is the internal belief (posterior).
- $p(o, \psi)$ is the generative model (World Model).

The 18-step loop is an implementation of **Expected Free Energy** minimization, where "Evidence Collection" and "Experiment Design" serve to reduce epistemic uncertainty (information gain).

## 2. Bayesian Evidence Synthesis

For every piece of evidence $E_i$ collected for hypothesis $H$, we update the posterior $P(H|E)$:

$$P(H|E_i) = \frac{P(E_i|H) P(H)}{P(E_i)}$$

The SRE maintains a **Cumulative Evidence Score (CES)**:

$$CES = \sum_{i=1}^{n} w_i \cdot \mathcal{L}(E_i, H)$$

Where $w_i$ is the source reliability and $\mathcal{L}$ is the Likelihood Ratio (Bayes Factor).

## 3. Entropy-Based Uncertainty

We quantify the "Scientific Value" of a hypothesis by the reduction in Shannon Entropy $H(\psi)$:

$$\Delta H = H(q_{prior}) - H(q_{posterior})$$

A hypothesis is only promoted to **INSTITUTIONALIZED** if:
1. $P(H|E) > \tau_{prob}$ (High confidence).
2. $H(q_{posterior}) < \tau_{entropy}$ (Low uncertainty).
3. $\text{Robustness} > \tau_{regime}$ (Performance holds across simulated counterfactual regimes).

## 4. Falsification Logic

Falsification is treated as a hard constraint. If $\exists E_i$ such that $P(E_i|H) < \epsilon$ and $Confidence(E_i) > \tau_{veto}$, the hypothesis is transitioned to **REJECTED** regardless of supporting evidence. This prevents confirmation bias.
