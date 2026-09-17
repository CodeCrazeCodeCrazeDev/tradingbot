# Hypothesis Dependency Graph (Comprehensive Audit 2026)

```mermaid
graph TD
    %% Origination Points
    Obs[Observation / Market Data] --> Anomaly[Anomaly Detection]
    Anomaly --> QG[Question Generation]
    QG --> HG[Hypothesis Generation]
    HG --> EC[Evidence Collection]

    %% Research & Mining
    Mining[Alpha Mining Engine] --> HG
    Extraction[Hypothesis Extraction Engine] --> HG
    Curiosity[Curiosity Engine] --> Anomaly

    %% Evolution & Evaluation
    HG --> WM[World Model Simulation]
    WM --> CF[Counterfactual Generation]
    CF --> ADeb[Adversarial Debate]
    ADeb --> ED[Experiment Design]
    ED --> EXE[Execution / Backtest]
    EXE --> EVAL[Evaluation / Diagnostics]

    %% Cognitive Processing
    EVAL --> BU[Bayesian Update]
    BU --> CC[Confidence Calibration]
    CC --> KI[Knowledge Integration]
    KI --> MC[Memory Consolidation]

    %% Lifecycle States
    MC --> PI[Policy Improvement]
    PI --> CM[Continuous Monitoring]
    CM --> RET[Retirement / End-States]

    %% Subsystem Connections
    CSC[Cognitive System Controller] --> HG
    PHCE_D[PHCE-D Engine] --> EVAL
    HMS[Hierarchical Memory System] <--> MC
    GWM[Global World Model] <--> WM

    %% End-States
    subgraph "Terminal States"
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

## Critical Propagation Paths

1. **The Fast Loop (Tactical)**: `Observation` -> `CSC Reasoning` -> `Signal` -> `Execution` -> `Market Teacher Evaluation`.
2. **The Slow Loop (Strategic)**: `Anomaly` -> `SRE 19-Step Cycle` -> `Validated Hypothesis` -> `HMS Research Ledger` -> `Alpha Promotion`.
3. **The Research Loop**: `Academic Paper` -> `Extraction Engine` -> `Causal Mechanism` -> `Backtest` -> `Knowledge Base`.

## Component Mapping
- **World Model**: `trading_bot/world_model/` (Imagination, Counterfactuals, Causal Model).
- **Research Engine**: `trading_bot/alpha_research/` (Extraction, Mining).
- **Core Reasoning**: `trading_bot/core_agent_system/scientific_reasoning/core.py` (SRE).
- **Decision Layer**: `trading_bot/core/csc/` (Reasoning Branches, Logic Folding).
- **Validation**: `trading_bot/core/phce_d_engine.py` (Deterministic Verifiers).
- **Governance**: `trading_bot/core/unified_event_bus.py` (LogAct Consensus).
