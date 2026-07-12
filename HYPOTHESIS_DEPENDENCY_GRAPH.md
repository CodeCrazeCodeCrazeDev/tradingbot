# Hypothesis Dependency Graph

```mermaid
graph TD
    Obs[Observation / Market Data] --> Anomaly[Anomaly Detection]
    Anomaly --> QG[Question Generation]
    QG --> HG[Hypothesis Generation]

    HG --> PHCE_D[PHCE-D Hypothesis]
    HG --> SRE_Hyp[Scientific Hypothesis]
    HG --> CSC_Branch[Reasoning Branch]

    PHCE_D --> Verifier[Deterministic/Statistical Verifiers]
    SRE_Hyp --> SRE_Cycle[19-Step SRE Cycle]
    CSC_Branch --> GWM[Global World Model Simulation]

    Verifier --> Gateway[Validation Gateway]
    SRE_Cycle --> Bayesian[Bayesian Update]
    GWM --> Counterfactual[Counterfactual Engine]

    Gateway --> PaperTrade[Paper Trade Promotion]
    Bayesian --> Knowledge[Knowledge Integration]
    Counterfactual --> Adversarial[Adversarial Debate]

    PaperTrade --> Production[Production Strategy]
    Knowledge --> HMS[Hierarchical Memory System]
    Adversarial --> Refine[Hypothesis Refinement]

    Production --> Drift[Drift Monitor]
    Drift --> Retire[Hypothesis Retirement]
    Retire --> Institutional[Institutionalized Knowledge]
    Retire --> Rejected[Rejected / Forgotten]
```

## Flow Description

1.  **Origination**: Hypotheses originate from `HypothesisGenerator` modules (in PHCE-D and CSC) or via the `observe()` method in the `ScientificReasoningEngine`. They are triggered by anomalies or research objectives.
2.  **Propagation**: Hypotheses are wrapped in `ReasoningBranch` objects in CSC for parallel simulation, or passed as `Hypothesis` data structures through the `ValidationGateway` in PHCE-D.
3.  **Evolution**: Hypotheses evolve through the 19-step cycle in the SRE, where they are refined based on experiment results and counterfactual reasoning.
4.  **Evaluation**: Primary evaluation occurs in `trading_bot/phce_d/verifier.py` (performance metrics) and `trading_bot/core_agent_system/cds/epistemology_engine.py` (epistemic quality).
5.  **Death**: Hypotheses "die" when they are moved to `REJECTED` or `RETIRED` states due to drift detection, failed validation, or being superseded.
6.  **Knowledge**: Successful hypotheses are abstracted into Semantic or Institutional memory tiers within the HMS.
7.  **Policies**: Validated hypotheses influence trading policies via the `SkillRouter` and `PolicyImprovement` steps.
8.  **Strategies**: Hypotheses become active trading strategies after passing the Paper Trade promotion gate.
9.  **Feedback**: Retired or failed hypotheses influence future generation by providing negative examples in the `FailureMemory`.
