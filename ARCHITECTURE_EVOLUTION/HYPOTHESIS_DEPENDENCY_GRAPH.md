# Hypothesis Dependency Graph - AlphaAlgo UCA 2026

This document maps the flow of hypotheses from raw market observations to institutionalized knowledge across all subsystems.

## High-Level Lifecycle Flow

```mermaid
graph TD
    %% 1. Discovery & Observation
    Obs[Market Observation] --> AD[Anomaly Detection]
    AD --> QG[Question Generation]
    QG --> HG[Hypothesis Generation]

    %% 2. Scientific Reasoning Core (SRE)
    HG --> EC[Evidence Collection]
    EC --> WM[World Model Simulation]
    WM --> CF[Counterfactual Generation]
    CF --> ADeb[Adversarial Debate]
    ADeb --> ED[Experiment Design]

    %% 3. Validation & Testing
    ED --> EXE[Execution/Backtest]
    EXE --> EVAL[Evaluation/Ranking]

    %% 4. Decision & Governance
    EVAL --> PHCE[PHCE-D Decision Policy]
    PHCE --> Aletheia[Aletheia Verification]
    Aletheia --> CSC[CSC Execution Proposal]

    %% 5. Refinement & Memory
    EVAL --> BU[Bayesian Update]
    BU --> CC[Confidence Calibration]
    CC --> HMS[HMS Semantic Memory]
    HMS --> PI[Policy Improvement]

    %% 6. Final End-States
    PI --> RET[Hypothesis Retirement]

    subgraph "Authoritative End-States"
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

    %% Key Dependencies
    CSC -.-> |Failure Feedback| PHCE
    Aletheia -.-> |Audit Trace| HMS
    PHCE -.-> |Regime Update| HMS
```

## Subsystem Roles in the Ecosystem

### 1. The Proposers (Generation)
- **AlphaMiningEngine**: Discovers statistical signals ($alpha$) via genetic programming.
- **CuriosityEngine**: Generates "Why" questions from market anomalies.
- **StrategyGenerator**: Evolves strategy DNAs (hypotheses) in `self_evolving_researcher.py`.
- **CognitiveSystemController (CSC)**: Generates competing reasoning branches for immediate execution.

### 2. The Auditors (Validation)
- **ScientificReasoningEngine (SRE)**: The 19-step orchestrator of the hypothesis lifecycle.
- **PHCE-D**: Parallel Hypothesis Correction Engine; provides conservative gatekeeping and refusal logic.
- **Aletheia**: Formal verification and browser-based research auditing of claims.
- **VerificationSwarm**: Multi-agent "Red Team" that attempts to falsify trade ideas.

### 3. The Repository (Memory)
- **Hierarchical Memory System (HMS)**: Stores the "Scientific Ledger" and semantic graph of all beliefs.
- **Unified Alpha Brain**: Aggregates weights and performance for all active strategies.
- **TALOS**: Manages the research evidence bridge and long-term research memory.

### 4. The Policy (Evolution)
- **SkillRouter**: Routes tasks based on the "Earned Work" logic of validated hypotheses.
- **ImmutableShield**: Enforces constitutional constraints on all accepted policies.
