# Scientific Redesign - Unified Cognitive Architecture 2026

## The "One Brain" Philosophy
The redesign eliminates fragmented "islands" of intelligence and replaces them with a single, authoritative **Scientific Reasoning Engine (SRE)** that governs the hypothesis lifecycle for the entire system.

## The 19-Step SRE Lifecycle

1.  **Observation**: Unified ingestion of market, macro, and alternative data.
2.  **Anomaly Detection**: Identify deviations from the World Model's expected state.
3.  **Question Generation**: Formulate "Why" questions (e.g., "Why did liquidity drop during the breakout?").
4.  **Hypothesis Generation**: Propose falsifiable causal or predictive claims.
5.  **Evidence Collection**: Gather multi-domain evidence (Market, Sentiment, Order Flow).
6.  **World Model Simulation**: Run parallel futures to test the hypothesis in the GWM.
7.  **Counterfactual Generation**: Perform "Do-calculus" interventions to test causal stability.
8.  **Adversarial Debate**: Subject the hypothesis to the `VerificationSwarm` and `EpistemologyEngine`.
9.  **Experiment Design**: Select the optimal test (Backtest, Monte Carlo, Paper Trade).
10. **Execution**: Execute the experiment in a secure sandbox.
11. **Evaluation**: Perform statistical evaluation of results (Sharpe, IC, Robustness).
12. **Bayesian Update**: Formal update of the hypothesis's posterior probability.
13. **Confidence Calibration**: Adjust confidence based on uncertainty and ambiguity metrics.
14. **Knowledge Integration**: Abstract findings into the HMS Semantic layer.
15. **Memory Consolidation**: Move important patterns to Institutional Memory.
16. **Policy Improvement**: Update the `SkillRouter` and `RL` agents with new strategic insights.
17. **Continuous Monitoring**: Track the hypothesis in production for drift or decay.
18. **Hypothesis Retirement**: Transition to one of 10 authoritative end-states.
19. **Automatic Discovery**: Meta-discovery of new research paths based on the results.

## Unified Data Model: `ScientificHypothesis`
Located in `trading_bot/core_agent_system/scientific_reasoning/core.py`.
- **Posterior**: The primary belief score.
- **Uncertainty**: Quantified entropy/variance.
- **Lineage**: Immutable record of parent/child relationships (provenance).
- **Boundary Conditions**: Regimes where the hypothesis is valid.

## End-States
No hypothesis is ever deleted. They must terminate in:
- `CONFIRMED`, `REJECTED`, `INCONCLUSIVE`, `MERGED`, `SPLIT`, `DORMANT`, `REACTIVATED`, `DEPRECATED`, `SUPERSEDED`, `INSTITUTIONALIZED`.
