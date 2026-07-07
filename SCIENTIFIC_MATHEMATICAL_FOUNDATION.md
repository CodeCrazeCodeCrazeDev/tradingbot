# Scientific Mathematical Foundation - SRE 2026

The Scientific Reasoning Engine (SRE) is grounded in four mathematical pillars.

## 1. Variational Active Inference (VAI)
The global objective is the minimization of **Variational Free Energy (VFE)**.
A hypothesis $h$ is evaluated by the expected free energy $G(h)$ of its outcomes:
$$G(h) \approx \sum_{\tau} E_{q(s_\tau, o_\tau | h)} [\ln q(s_\tau | h) - \ln p(s_\tau, o_\tau)]$$
This balances **Epistemic Value** (information gain) and **Extrinsic Value** (expected utility).

## 2. Bayesian Evidence Synthesis
Updating hypothesis $H$ given evidence $E$:
$$P(H|E) = \frac{P(E|H)P(H)}{P(E)}$$
We use a **Recursive Bayesian Filter** for continuous updates as new evidence packets arrive in the HMS.

## 3. Causal Stability (Do-Calculus)
To distinguish correlation from causation, we utilize Pearl's **Do-Calculus**:
$$P(Y | do(X)) \neq P(Y | X)$$
Step 7 (Counterfactuals) simulates interventions $do(X)$ in the GWM to verify the mechanism $X \rightarrow Y$ remains stable even when $X$ is forced.

## 4. Uncertainty Calibration (Credal Sets)
We move beyond single-point probabilities to **Credal Intervals** $[\underline{P}, \overline{P}]$ to handle ambiguity:
- **Ambiguity**: $\overline{P} - \underline{P}$
- **Confidence**: Inverse of uncertainty/ambiguity.
High-ambiguity hypotheses are routed for further "Evidence Collection" (Step 5) rather than "Execution" (Step 10).
