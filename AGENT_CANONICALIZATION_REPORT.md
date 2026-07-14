# Agent Canonicalization Report - UCA-2026 One Brain

## Executive Summary
This report audits all specialized agents within the AlphaAlgo ecosystem to enforce the "One Brain" principle. Redundant, obsolete, or fragmented agents have been categorized for consolidation into the canonical Cognitive System Controller (CSC) or archived.

## 1. Core Reasoning & Planning (CSC Candidates)
| Agent | Source Path | Recommendation | Justification |
|-------|-------------|----------------|---------------|
| `PlannerAgent` | `trading_bot/agents/planner_agent.py` | **Canonical** | Integrated into IAS as a core Skill. |
| `VerifierAgent` | `trading_bot/agents/verifier_agent.py` | **Canonical** | Core part of the CSC Verification Swarm. |
| `ExecutorAgent` | `trading_bot/agents/executor_agent.py` | **Canonical** | Integrated with `TradeExecutor`. |
| `MigratedPlannerAgent` | `trading_bot/core_agent_system/migrated_agents/` | **Merge** | Merge into `PlannerAgent`. |
| `MultiAgentDebate` | `trading_bot/agents/multi_agent_debate.py` | **Merge** | Protocol to be handled by CSC/VerificationSwarm. |

## 2. Specialized Strategy Agents
| Agent | Source Path | Recommendation | Justification |
|-------|-------------|----------------|---------------|
| `TrendFollowingAgent` | `trading_bot/agents2/specialized_agents.py` | **Merge into Skill** | Port logic to TrendFollowing Skill (HASP). |
| `MeanReversionAgent` | `trading_bot/agents2/specialized_agents.py` | **Merge into Skill** | Port logic to MeanReversion Skill (HASP). |
| `VolatilityAgent` | `trading_bot/agents2/specialized_agents.py` | **Merge into Skill** | Port logic to Volatility Skill (HASP). |
| `MarketMakerAgent` | `trading_bot/agents2/specialized_agents.py` | **Merge into Skill** | Port logic to MarketMaking Skill (HASP). |
| `RiskManagerAgent` | `trading_bot/agents2/specialized_agents.py` | **Archive** | Redundant; logic handled by `ImmutableShield`. |

## 3. Swarm & Intelligence Experts
| Agent | Source Path | Recommendation | Justification |
|-------|-------------|----------------|---------------|
| `MarketScientist` | `trading_bot/core_agent_system/swarm/experts.py` | **Canonical** | High-level research specialist in the Swarm. |
| `QuantAnalyst` | `trading_bot/core_agent_system/swarm/experts.py` | **Canonical** | Domain specialist for quantitative verification. |
| `SwarmRiskManager` | `trading_bot/core_agent_system/swarm/experts.py` | **Rewrite** | Refactor as `RiskVerifier` for the Verification Swarm. |

## 4. Foundation & Research Agents (Radar AI / Foundation)
| Agent | Source Path | Recommendation | Justification |
|-------|-------------|----------------|---------------|
| `CausalDiscovery` | `trading_bot/foundation_agents/causal_engine/` | **Canonical** | Strategic capability for World Model V2. |
| `HypothesisGenerator`| `trading_bot/foundation_agents/curiosity_engine/`| **Merge** | Logic moved to `trading_bot/core/csc/hypothesis.py`. |
| `ArxivConnector` | `trading_bot/foundation_agents/knowledge_pipeline/`| **Skill** | External tool accessible by Research Skills. |
| `StrategyAgent` | `trading_bot/radar_ai/agents/` | **Archive** | Overlaps with PlannerAgent; violates singularity. |
| `OntologyAgent` | `trading_bot/radar_ai/agents/` | **Merge** | Merge into HMS Semantic Memory management. |

## 5. Conclusion
All surviving agents must function as **Skills** or **Domain Experts** coordinated by the `CognitiveSystemController` via the `CapabilityRouter`. Direct, uncoordinated trade execution or independent event-bus bypasses are prohibited.
