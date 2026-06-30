# RSIE Subsystem Map

The Unified Recursive Self-Improvement Engine (RSIE) manages the following improvable subsystems, categorized by Tier and Criticality.

## Tier 0: Critical to Profitability & Reliability
| Subsystem | Owner Loop | Max Level | Primary Validation Gates |
|-----------|------------|-----------|--------------------------|
| **Validation Reliability** | EvaluationLoop | 5 | Leakage Check, Walk-Forward, Regime Stability |
| **Trading Strategies** | StrategyLoop | 5 | OOS Performance, Sharpe Ratio, Max Drawdown |
| **Risk Management** | RiskLoop | 4 | Robustness Testing, Drawdown Bounds, VaR |
| **Feature Engineering** | FeatureLoop | 5 | Statistical Significance, Feature Stability |

## Tier 1: Critical to Intelligence
| Subsystem | Owner Loop | Max Level | Primary Validation Gates |
|-----------|------------|-----------|--------------------------|
| **Improvement Discovery** | MetaLoop | 4 | Meta-Hypothesis Success Rate, Discovery Speed |
| **Agent Coordination** | AgentLoop* | 4 | Latency, Accuracy, Conflict Resolution |
| **Workflow Policies** | WorkflowLoop* | 3 | Process Efficiency, Execution Trace Success |
| **Model Architecture** | ModelLoop* | 6 | Training Loss, Inference Latency, Accuracy |

## Tier 2: Scalability & Research
| Subsystem | Owner Loop | Max Level | Primary Validation Gates |
|-----------|------------|-----------|--------------------------|
| **World Model** | ResearchLoop* | 5 | Predictive Error, Latent Dynamics Consistency |
| **Swarm Intelligence** | ResearchLoop* | 4 | Consensus Accuracy, Diversification Score |
| **Reasoning Frameworks**| ResearchLoop* | 4 | Logic Consistency, Audit Trail Quality |

*\* Architecture support implemented; full autonomous loop implementation pending Tier 0 stability.*

## Improvement Levels (0-7)
- **Level 0:** No modification.
- **Level 1:** Configuration optimization.
- **Level 2:** Hyperparameter optimization.
- **Level 3:** Workflow optimization.
- **Level 4:** Agent coordination optimization.
- **Level 5:** Model architecture proposals.
- **Level 6:** Code generation proposals (Requires Human Approval).
- **Level 7:** Core architecture modifications (Requires Human Approval).

## Governance
All improvements must pass the **ImprovementValidationPipeline** and comply with **GovernanceSystem** boundaries. Levels 6 and 7, or any proposal flagged by the Anti-Reward Hacking system, require explicit approval via `pending_approvals.json`.
