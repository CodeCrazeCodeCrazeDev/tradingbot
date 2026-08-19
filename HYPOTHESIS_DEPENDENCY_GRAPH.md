# Hypothesis Dependency Graph (Complete System Audit 2026)

## Overview
This document outlines the complete multi-horizon dependency and propagation graph of hypotheses across the AlphaAlgo Autonomous Scientific System. In AlphaAlgo, every signal, prediction, regime belief, trade idea, world model projection, and parameter mutation is treated as a falsifiable hypothesis.

---

## 1. Multi-Horizon Dependency Flow Graph

```mermaid
graph TD
    %% Fast Loop: Tactical Operations (< 1 minute)
    subgraph Fast_Loop ["Fast Tactical Horizon (< 1 min)"]
        Obs["1. Market Observation / Tick Feed"] --> CSC["2. Cognitive System Controller (CSC)"]
        CSC --> SigHyp["3. Tactical Signal Hypothesis"]
        SigHyp --> Exec["4. Pre-Trade Execution Boundary"]
        Exec --> Realized["5. Trade Execution / PnL Feedback"]
    end

    %% Slow Loop: Strategic Reasoning (1 min - 1 day)
    subgraph Slow_Loop ["Slow Strategic Horizon (1 min - 1 day)"]
        Realized --> Anomaly["6. Anomaly / Volatility Shock Detection"]
        Anomaly --> SRE["7. Scientific Reasoning Engine (SRE 19-Step Cycle)"]
        SRE --> WM_Sim["8. Unified World Model (Interventional Simulation)"]
        WM_Sim --> Deb["9. Swarm Adversarial Debate (LogAct Consensus)"]
        Deb --> RegBelief["10. Calibrated Regime Belief Hypothesis"]
    end

    %% Research Loop: Continuous Meta-Learning (> 1 day)
    subgraph Research_Loop ["Research & Evolution Horizon (> 1 day)"]
        RegBelief --> Mining["11. Alpha Mining & Extraction Engine"]
        Mining --> SymDiscovery["12. Symbolic Discovery & Genetic Mutator"]
        SymDiscovery --> FactorHyp["13. Strategic Factor Expression Hypothesis"]
        FactorHyp --> Backtest["14. Out-of-Sample Backtest / Stress Test"]
        Backtest --> HMS_Store["15. Hierarchical Memory System (HMS T6/T7)"]
        HMS_Store --> Institutional["16. Institutionalized Knowledge Base"]
    end

    %% Cross-Horizon Feedback Lines
    Institutional --> CSC
    RegBelief --> CSC
    HMS_Store --> SRE
```

---

## 2. Propagation & Transition Pathways

| Horizon Stage | Subsystem Owner | Input Evidence | Transformation Output | Propagation Target |
| :--- | :--- | :--- | :--- | :--- |
| **Observation** | Data Pipelines / Tick Stream | Raw Orderbook & Trades | Anomaly Metric ($z$-score $> 2.5$) | `SRE.observe()` |
| **Tactical Hypothesis** | `CognitiveSystemController` | Price Action & Latent Features | Position Candidate Vector | `DeterministicFinancialGateway` |
| **World Model Simulation** | `UnifiedWorldModel` | Structural Causal Graph & $do(X)$ | Tri-Horizon Futures (Nominal, Stressed, Black Swan) | `AdversarialDebate` |
| **Adversarial Debate** | `GovernanceOrchestrator` | Risk Vetoes & Verifier Scores | Evidence-Weighted Consensus | `SRE.update_bayesian()` |
| **Memory Consolidation** | `HierarchicalMemorySystem` | Evaluated Performance Ledger | Knowledge Subgraph Entry (SAGE Graph) | `SkillRouter` |

---

## 3. Propagation to Downstream Action Layers

1. **Knowledge Conversion**: Validated hypotheses accumulate epistemic weight and transition to permanent nodes in `HierarchicalMemorySystem` (Level T6/T7).
2. **Policy Conversion**: Confirmed strategic hypotheses update the action space routing probabilities in `SkillRouter` and execution weights in `CognitiveSystemController`.
3. **Trading Strategy Conversion**: Factor hypotheses passing out-of-sample stress testing are promoted to active execution candidates managed by the `PHCE-D` deterministic engine.
4. **Future Reasoning Influence**: Historical failures are recorded with full invalidation DAGs, preventing repeated discovery of rejected structures.
