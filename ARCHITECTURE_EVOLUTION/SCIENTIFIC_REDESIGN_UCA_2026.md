# Scientific Redesign - Unified Cognitive Architecture 2026

## 1. Executive Summary
The AlphaAlgo UCA 2026 refactor consolidates all intelligence subsystems into a single, authoritative **Scientific Reasoning Engine (SRE)**. This engine governs the entire hypothesis lifecycle—from raw observation to institutionalized policy—ensuring mathematical consistency, causal stability, and immutable provenance.

## 2. The 19-Step SRE Lifecycle
Every hypothesis in the system must progress through these formal stages:

1.  **Observation**: Unified ingestion of market, macro, and alternative data.
2.  **Anomaly Detection**: Identify deviations from the World Model's predicted state.
3.  **Question Generation**: Formulate causal questions (e.g., "Why did liquidity $L$ drop during event $E$?").
4.  **Hypothesis Generation**: Propose falsifiable causal or predictive claims $H$.
5.  **Evidence Collection**: Gather supporting/refuting data $E$ from cross-domain sources.
6.  **World Model Simulation**: Run parallel futures in the GWM to test $H$.
7.  **Counterfactual Generation**: Perform Pearl's $do(X)$ interventions to verify causal stability.
8.  **Adversarial Debate**: Subject $H$ to the `VerificationSwarm` (Red Team).
9.  **Experiment Design**: Select the optimal test (Backtest, Monte Carlo, Paper Trade).
10. **Execution**: Execute the experiment in a secure sandbox.
11. **Evaluation**: Perform statistical evaluation of outcomes (Sharpe, IC, ECE).
12. **Bayesian Update**: Formal update of the posterior $P(H|E)$.
13. **Confidence Calibration**: Adjust confidence based on uncertainty and ambiguity metrics.
14. **Knowledge Integration**: Abstract findings into the HMS Semantic layer.
15. **Memory Consolidation**: Move important patterns to Institutional Memory.
16. **Policy Improvement**: Update the `SkillRouter` and `RL` agents with validated insights.
17. **Continuous Monitoring**: Track $H$ in production for alpha decay or regime drift.
18. **Hypothesis Retirement**: Transition $H$ to an authoritative end-state.
19. **Automatic Discovery**: Recursive meta-discovery of new research paths based on $H$'s lifecycle.

## 3. Authoritative End-States
Hypotheses are never deleted; they terminate in one of ten states:
- `CONFIRMED`: High posterior, low uncertainty, proven in production.
- `REJECTED`: Falsified by evidence or experiment.
- `INCONCLUSIVE`: Insufficient evidence to confirm or reject.
- `MERGED`: Combined with another hypothesis to form a stronger model.
- `SPLIT`: Divided into sub-hypotheses (e.g., regime-specific versions).
- `DORMANT`: Valid but not currently applicable to the market regime.
- `REACTIVATED`: Moved from Dormant to Active due to regime shift.
- `DEPRECATED`: Replaced by a more modern or efficient model.
- `SUPERSEDED`: Formally replaced by a direct successor.
- `INSTITUTIONALIZED`: Incorporated into the core system logic/constraints.

## 4. Mathematical Justification

### A. Variational Active Inference (VAI)
The SRE objective is the minimization of **Variational Free Energy (VFE)**. For a hypothesis $h$, we evaluate the expected free energy $G(h)$:
$$G(h) \approx \sum_{\tau} E_{q(s_\tau, o_\tau | h)} [\ln q(s_\tau | h) - \ln p(s_\tau, o_\tau)]$$
This ensures the system balances **Epistemic Value** (searching for new information) and **Extrinsic Value** (maximizing utility/PnL).

### B. Recursive Bayesian Synthesis
Updating belief $H$ given evidence $E$:
$$P(H|E) = \frac{P(E|H)P(H)}{P(E)}$$
We use a Recursive Bayesian Filter to ensure every new data packet in the HMS contributes to the global posterior.

### C. Causal Stability (Do-Calculus)
To avoid spurious correlations, we utilize Pearl's **Do-Calculus** in Step 7:
$$P(Y | do(X)) \neq P(Y | X)$$
If a hypothesis $X \rightarrow Y$ fails to hold when $X$ is intervened upon in the simulation, it is flagged for causal instability.

### D. Uncertainty Quantification
We use **Credal Sets** $[\underline{P}, \overline{P}]$ to distinguish between:
- **Aleatoric Uncertainty**: Inherent randomness (high variance).
- **Epistemic Uncertainty**: Lack of knowledge (large credal interval).

## 5. Validation Framework
The SRE implements a three-tier validation gate:
1.  **Logical Consistency**: Formal proof search for model invariants.
2.  **Adversarial Robustness**: Survival against the `VerificationSwarm`.
3.  **Empirical Calibration**: Out-of-sample performance matching the predicted posterior.
