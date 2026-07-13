# Scientific Redesign: Institutional-Grade Autonomous Scientific Reasoning

## 1. The 19-Step Recursive Scientific Lifecycle
All system reasoning must follow this deterministic path, with explicit state transitions and logging.

1.  **Observation**: Ingest raw multi-modal market data.
2.  **Anomaly Detection**: Compare observation against World Model predictions.
3.  **Question Generation**: Formulate causal questions for detected anomalies.
4.  **Hypothesis Generation**: Propose falsifiable explanations (Latent Beliefs).
5.  **Evidence Collection**: Gather supporting/refuting cross-domain artifacts.
6.  **World Model Simulation**: Run predictive 'dreaming' scenarios.
7.  **Counterfactual Generation**: Test causal stability using Pearl's 'do' operator.
8.  **Adversarial Debate**: Subject hypothesis to Verification Swarm challenge.
9.  **Experiment Design**: Define statistical test parameters (Backtest/Paper).
10. **Execution**: Run the experiment in a sandbox or paper environment.
11. **Evaluation**: Statistical analysis of outcomes vs. expectations.
12. **Bayesian Update**: Update posterior probabilities $P(H|E)$.
13. **Confidence Calibration**: Adjust for uncertainty and ambiguity (Credal Bounds).
14. **Knowledge Integration**: Abstract findings into Semantic Memory.
15. **Memory Consolidation**: Move to long-term Institutional Tier (HMS Tier 5).
16. **Policy Improvement**: Update trading/research policies (SkillRouter).
17. **Continuous Monitoring**: Track for drift, decay, or regime change.
18. **Hypothesis Retirement**: Transition to one of 10 authoritative end-states.
19. **Automatic Discovery**: Meta-learning to find new research directions.

## 2. Authoritative End-States
Every hypothesis MUST end in one of these states; it can never be "deleted" without provenance.

- **Confirmed**: Validated, high posterior, in production.
- **Rejected**: Falsified by experiment or adversarial debate.
- **Inconclusive**: Insufficient evidence, requires more experimentation.
- **Merged**: Combined with another hypothesis for greater explanatory power.
- **Split**: Found to contain multiple distinct phenomena.
- **Dormant**: Valid but regime-incompatible (waiting for regime shift).
- **Reactivated**: Moved from Dormant back to active testing.
- **Deprecated**: Replaced by a more efficient but not strictly superior model.
- **Superseded**: Replaced by a demonstrably superior hypothesis.
- **Institutionalized**: Promoted to foundational system invariant.

## 3. Mathematical Justification
The SRE operates on the principle of **Variational Free Energy (VFE) Minimization**:

$$F = E_{q(\phi)}[\ln q(\phi) - \ln p(\omega, \phi)]$$

Where:
- $q(\phi)$ is the agent's internal belief (the hypothesis).
- $p(\omega, \phi)$ is the generative world model.
- Minimizing $F$ ensures both **Accuracy** (fitting the data) and **Complexity Control** (Occam's Razor).

Ambiguity is managed using **Credal Bounds** $[P_{lower}, P_{upper}]$, representing the range of valid posteriors under model uncertainty.

## 4. Validation Framework
- **ECE (Expected Calibration Error)**: Must be $< 0.05$ for production promotion.
- **Falsifiability Score**: Every hypothesis must have at least 3 defined triggers that would prove it wrong.
- **Ablation Sensitivity**: Measuring performance impact when the hypothesis is removed.

## 5. Migration Roadmap
- **Phase A**: Base Type consolidation (Standardizing `ScientificHypothesis`).
- **Phase B**: Core Engine refactor (Implementing the 19 steps).
- **Phase C**: Integration (Linking Alpha Research, CSC, and HMS).
- **Phase D**: Productionization (Enforcing the Scientific Audit Gate).
