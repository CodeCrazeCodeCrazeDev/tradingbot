# Detailed Hypothesis Dependency Graph - AlphaAlgo 2026

```mermaid
graph TD
    %% 1. ORIGINATION
    Raw[Raw Market Data / Events] --> Anomaly[Curiosity Engine: Anomaly Detection]
    Raw --> CSC_Obs[CSC: Observation Ingestion]
    Mining[Alpha Mining: Genetic Factor Generation] --> SRE_Gen[SRE Step 4: Hypothesis Generation]
    Extract[Extraction Engine: Academic Research] --> SRE_Gen

    %% 2. INITIAL FORMULATION
    Anomaly --> SRE_Q[SRE Step 3: Question Generation]
    SRE_Q --> SRE_Gen
    CSC_Obs --> SRE_Gen

    %% 3. REASONING & PROPAGATION
    SRE_Gen --> WM_Sim[World Model: Simulation & Imagination]
    WM_Sim --> CF_Gen[Counterfactual Reasoner: Do-Calculus]
    CF_Gen --> AD_Debate[Verification Swarm: Adversarial Debate]

    %% 4. EVALUATION & TESTING
    AD_Debate --> EXP_Design[SRE Step 9: Experiment Design]
    EXP_Design --> EXEC[Execution: Backtester / Paper Trader]
    EXEC --> EVAL[Evaluation: PHCE-D Verifiers / Performance Diagnostics]

    %% 5. COGNITIVE UPDATE (EVOLUTION)
    EVAL --> BU[Bayesian Update: Posterior P(H|E)]
    BU --> CC[Confidence Calibration: Credal Sets]
    CC --> Pivot{Pivot / Refine?}
    Pivot -- Yes --> SRE_Gen
    Pivot -- No --> KI[Knowledge Integration: Semantic Abstraction]

    %% 6. INSTITUTIONALIZATION & MEMORY
    KI --> MC[Memory Consolidation: HMS / SAGE Graph Store]
    MC --> Policy[Policy Improvement: Capital Allocation Updates]
    MC --> KnowBase[Knowledge Graph: Permanent Institutional Theories]

    %% 7. FEEDBACK LOOPS (INFLUENCE)
    MC -- "Search Priors" --> Mining
    MC -- "Contextual Evidence" --> CSC_Obs
    KnowBase -- "Constitutional Bounds" --> SRE_Gen

    %% 8. RETIREMENT & END-STATES
    EVAL --> Rej[REJECTED: Failure Memory]
    Policy --> Decay[Alpha Death Clock: Monitoring]
    Decay --> Ret[RETIRED / DEPRECATED]

    subgraph "SRE 19-Step Authority"
        SRE_Q
        SRE_Gen
        WM_Sim
        CF_Gen
        AD_Debate
        EXP_Design
        BU
        CC
        KI
        MC
    end
```

## Detailed Path Analysis

### 1. Origination Points
- **Explicit**: `ScientificReasoningEngine.observe()`, `CuriosityEngine.generate_from_anomaly()`, `GeneticAlphaSearch._generate_random_expression()`.
- **Implicit**: `StrategyGenome` evolution, `ReasoningBranch` creation in CSC, `Imagined` states in World Model.

### 2. Propagation & Evolution
- Hypotheses propagate through the **SRE 19-step loop**.
- Evolution occurs via **Pivot/Refine loops** in the CSC and **Genetic Crossover/Mutation** in the Alpha Mining engine.
- Lineage is tracked via `HypothesisLineage` objects in `SRE/core.py`.

### 3. Evaluation Mechanisms
- **Statistical**: Sharpe, Deflated Sharpe, p-values in `PHCE-D` and `DiscoveryPlatform`.
- **Adversarial**: `VerificationSwarm` peer-review and `AdversarialAnalyzer` stress tests.
- **Causal**: `Do-Calculus` interventions in the `CausalWorldModel`.
- **Bayesian**: Continuous posterior updates and Credal Interval ([P_lower, P_upper]) monitoring.

### 4. Conversion to Institutional Value
- **Knowledge**: Stored as `Theory` nodes in the `KnowledgeGraph` or `Semantic` entries in `HMS`.
- **Policies**: Hypotheses about optimal execution or allocation become `Policy` objects.
- **Strategies**: Validated alphas promoted to `LEVEL_4` production strategies.

### 5. Death & Retirement
- Hypotheses never "vanish"; they transition to **Terminal States**: `REJECTED`, `DEPRECATED`, `SUPERSEDED`, or `DORMANT`.
- Rejected hypotheses are stored in **Failure Memory** to inform future search priors and prevent "Scientific Amnesia".
