# AlphaAlgo Agent Audit & Classification Report - July 2026

This report classifies all agent systems within the AlphaAlgo repository to enforce the "One Brain" architecture and eliminate redundancy.

## 1. Authoritative System: Core Agent System (CAS)
**Location:** `trading_bot/core_agent_system/`
**Purpose:** Primary UCA-2026 authoritative controller (CSC).
**Status:** **AUTHORITATIVE**

| Agent | Purpose | Scientific Justification | Decision |
|-------|---------|--------------------------|----------|
| `IntegratedAgentSystem` | Orchestrates all components | Unified system integration | **KEEP** |
| `PlannerAgent` | Proposes trades via ReAct loop | Structured reasoning (OpenAI) | **KEEP** |
| `ExecutorAgent` | Handles trade execution | Action grounding | **KEEP** |
| `SafetyAgent` | Constitutional safety checks | Institutional governance (Anthropic) | **KEEP** |
| `ResearchAgent` | Discovers new alpha/patterns | Continuous discovery | **KEEP** |
| `USIS` | Swarm intelligence system | Collective intelligence | **KEEP** |

---

## 2. Legacy Strategy Layer: Agents2
**Location:** `agents 2/`, `trading_bot/agents2/`
**Purpose:** Traditional strategy implementations (Trend Following, Mean Reversion).
**Status:** **LEGACY**

| Agent | Capability Overlap | Recommendation |
|-------|--------------------|----------------|
| `TrendFollowingAgent` | Replaced by `TrendFollowingPlanner` in CAS | **REPLACE** |
| `MeanReversionAgent` | Replaced by `MeanReversionPlanner` in CAS | **REPLACE** |
| `RiskManagerAgent` | Replaced by `SafetyAgent` + `ImmutableShield` | **ARCHIVE** |
| `MultiAgentCoordinator` | Replaced by `MasterOrchestrator` | **ARCHIVE** |

---

## 3. Redundant Core Layer: AI Core
**Location:** `trading_bot/ai_core/`
**Purpose:** Duplicate implementation of Planner/Executor patterns.
**Status:** **REDUNDANT**

| Agent | Capability Overlap | Recommendation |
|-------|--------------------|----------------|
| `planner_agent.py` | 100% overlap with CAS `PlannerAgent` | **MERGE & ARCHIVE** |
| `executor_agent.py` | 100% overlap with CAS `ExecutorAgent` | **MERGE & ARCHIVE** |
| `safety_validator.py` | Overlap with `ImmutableShield` | **MERGE & ARCHIVE** |

---

## 4. Specialized Research: RadarAI
**Location:** `trading_bot/radar_ai/`
**Purpose:** Ontology-driven market analysis.
**Status:** **SPECIALIZED**

| Agent | Purpose | Recommendation |
|-------|---------|----------------|
| `OntologyAgent` | Manages market knowledge graph | **KEEP & BRIDGE** to HMS |
| `DataFusionAgent` | Cross-source validation | **KEEP & BRIDGE** to USIS |
| `StrategyAgent` | High-level strategy design | **MERGE** into CAS `ResearchAgent` |

---

## 5. Foundation & Research: Foundation Agents
**Location:** `trading_bot/foundation_agents/`
**Purpose:** Basic cognitive building blocks and experimental MAS.
**Status:** **EXPERIMENTAL BASE**

| Agent/Protocol | Status | Recommendation |
|----------------|--------|----------------|
| `AgentSwarm` | Grounded in agent performance | **KEEP** as experimental base |
| `DebateProtocol` | Used for conflict resolution | **KEEP** |
| `CausalEngine` | Grounds evidence relationships | **PROMOTE** to CAS Core |

---

## 6. Self-Improvement: Autonomous Superintelligence
**Location:** `trading_bot/autonomous_superintelligence/`
**Purpose:** Recursive improvement and infrastructure expansion.
**Status:** **EXPERIMENTAL**

| Agent | Purpose | Recommendation |
|-------|---------|----------------|
| `AgentSpawner` | Dynamically creates agents | **MERGE** into CAS `DynamicAgentFactory` |
| `SelfModifier` | Safely updates code/parameters | **MERGE** into `EvolutionGate` |

## 7. Action Plan

1.  **Immediate**: Continue bridging RadarAI and specialized Foundation agents to CAS.
2.  **Phase 1**: Move `agents 2/` and `trading_bot/agents2/` to `_archive/` once `LegacyAgentWrapper` verification is complete.
3.  **Phase 2**: Consolidate `ai_core` into `core_agent_system` and archive.
4.  **Phase 3**: Standardize all "Research" agents into the `ResearchAgent` interface in CAS.
