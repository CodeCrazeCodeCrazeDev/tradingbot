# Scientific Mathematical Justification

## Bayesian Inference
We use the formal update rule:
$P(H|E) = \frac{P(E|H)P(H)}{P(E)}$
where:
- $P(H)$ is the prior belief in the hypothesis.
- $P(E|H)$ is the likelihood of observing evidence $E$ if $H$ is true.
- $P(E)$ is the evidence probability (marginal likelihood).

## Uncertainty and Ambiguity
- **Uncertainty (Aleatoric)**: Measured via Shannon Entropy of the posterior distribution.
- **Ambiguity (Epistemic)**: Measured via the width of the Credal set (interval probability) when evidence is conflicting.

## Causal Intervention
Using Pearl's Do-calculus:
$P(Y | do(X))$
To differentiate correlation from causation, we simulate interventions in the CausalWorldModel.
