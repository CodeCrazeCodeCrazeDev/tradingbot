# Lifecycle Architecture Map - AlphaAlgo

This document maps the core components responsible for research, experimentation, evolution, and self-improvement.

## 1. Research & Experimentation Infrastructure
**Primary Location**: `trading_bot/research/`

| Component | Class/Module | Responsibility |
|---|---|---|
| **Research Kernel** | `ResearchKernel` | Manages immutable `ResearchObject` states and dependency graphs. |
| **Research OS** | `ResearchWorkspace` | Unified API for research projects, questions, and feature sets. |
| **Experimentation** | `ExperimentRegistry` | Tracks quantitative experiments with strict dataset hashing for reproducibility. |
| **Idea Management** | `IdeaRegistry` | Prioritizes quantitative ideas based on expected Sharpe and implementation cost. |
| **Governance** | `PeerReviewBoard` | Simulates institutional review to prevent overfitting and bias. |

## 2. Recursive Self-Improvement (RSIE)
**Primary Location**: `trading_bot/recursive_improvement/`

| Component | Class/Module | Responsibility |
|---|---|---|
| **RSIE Core** | `RecursiveImprovementCore` | Orchestrates improvement cycles across multiple dimensions (Strategy, Risk, Architecture). |
| **Improvement Loops** | `BaseImprovementLoop` | Specialized loops for focused optimization (RiskLoop, StrategyLoop, etc.). |
| **Proposal System** | `ImprovementProposal` | Formal definitions of changes, expected benefits, and rollback plans. |
| **Meta-Improvement** | `MetaRecursiveController` | Improves the improvement process itself by analyzing past cycle successes. |

## 3. Evolution Layer
**Primary Location**: `trading_bot/evolution_layer/`

| Component | Class/Module | Responsibility |
|---|---|---|
| **Code Evolution** | `CodeEvolver` | Handles code-level changes, bounded by an immutable reward model and human approval. |
| **Optimization** | `SelfOptimizer` | Dynamically tunes system parameters to meet global objectives. |
| **Continuous Learning** | `ContinuousLearner` | Adapts models in real-time as new market data is ingested. |

## 4. Autonomous Intelligence
**Primary Location**: `trading_bot/autonomous_superintelligence/`

| Component | Class/Module | Responsibility |
|---|---|---|
| **Core Intelligence** | `AutonomousCore` | High-level decision making and autonomous loop orchestration. |
| **Consciousness** | `ConsciousnessEngine` | Self-modeling, attention management, and introspective reasoning. |
| **Self-Preservation** | `SelfPreservationSystem` | Monitors system integrity and handles defensive responses to threats. |

## Inter-Component Interaction Flow
1. **Discovery**: `AutonomousCore` identifies an opportunity.
2. **Formulation**: `ResearchWorkspace` creates a project and hypothesis.
3. **Experimentation**: `ExperimentRegistry` executes the test and logs results.
4. **Improvement**: `RecursiveImprovementCore` generates a proposal based on results.
5. **Evolution**: `CodeEvolver` applies the approved change.
6. **Persistence**: `ResearchKernel` updates the dependency graph and archives the knowledge.
