# Hypothesis Dependency Graph - AlphaAlgo UCA 2026

This document maps the flow of hypotheses from raw market observations to institutionalized knowledge.

## High-Level Flow

```mermaid
graph TD
    Obs[Market Observation] --> AD[Anomaly Detection]
    AD --> QG[Question Generation]
    QG --> HG[Hypothesis Generation]
    HG --> EC[Evidence Collection]
    EC --> WM[World Model Simulation]
    WM --> CF[Counterfactual Generation]
    CF --> ADeb[Adversarial Debate]
    ADeb --> ED[Experiment Design]
    ED --> EXE[Execution]
    EXE --> EVAL[Evaluation]
    EVAL --> BU[Bayesian Update]
    BU --> CC[Confidence Calibration]
    CC --> KI[Knowledge Integration]
    KI --> MC[Memory Consolidation]
    MC --> PI[Policy Improvement]
    PI --> CM[Continuous Monitoring]
    CM --> RET[Retirement/End-States]

    subgraph "End-States"
        RET --> Conf[Confirmed]
        RET --> Rej[Rejected]
        RET --> Inc[Inconclusive]
        RET --> Mer[Merged]
        RET --> Spl[Split]
        RET --> Dor[Dormant]
        RET --> Rea[Reactivated]
        RET --> Dep[Deprecated]
        RET --> Sup[Superseded]
        RET --> Inst[Institutionalized]
    end
```

## Propagation Paths

1.  **Research-Led Path**:
    `ResearchObject` -> `HypothesisExtractionEngine` -> `Hypothesis` -> `ScientificReasoningEngine`.
2.  **Market-Led Path**:
    `MarketObservation` -> `CuriosityEngine` -> `HypothesisGenerator` -> `ReasoningBranch` -> `ScientificReasoningEngine`.
3.  **Discovery-Led Path**:
    `AlphaMiningEngine` -> `AlphaCandidate` -> `GeneticAlphaSearch` -> `ScientificReasoningEngine`.
4.  **Governance-Led Path**:
    `PHCE-D` -> `Hypothesis` -> `ValidationGateway` -> `DecisionRecord` -> `ScientificReasoningEngine`.

## Data Model Dependencies

- `ScientificHypothesis` (Core)
  - depends on `ScientificEvidence` (HMS)
  - depends on `HypothesisLineage` (SRE)
  - influences `CoreDecision` (CSC)
  - persists as `ScientificMemoryObject` (HMS)
