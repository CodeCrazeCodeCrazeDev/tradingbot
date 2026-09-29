# Multi-Agent Logic Consolidation Report - July 2026

## 1. Redundant Systems Identified

| System | Location | Status | Action |
|--------|----------|--------|--------|
| Multi-Agent Debate V1 | `trading_bot/agents/` | Deprecated | Moved to `_archive/agents/` |
| Decision Governance Debate | `trading_bot/decision_governance/` | Duplicate | Moved to `_archive/decision_governance/` |
| Foundation Multi-Agent | `trading_bot/foundation_agents/multi_agent/` | Research | Retain as experimental research base |
| Agents2 Coordinator | `trading_bot/agents2/` | Deprecated | Marked for removal |
| RadarAI Swarm | `trading_bot/radar_ai/` | Specialized | Bridge to USIS |
| **Unified Swarm Intelligence (USIS)** | `trading_bot/core_agent_system/swarm/` | **AUTHORITATIVE** | Primary production brain |

## 2. Consolidation Actions Taken

- **Archived** `trading_bot/decision_governance/multi_agent_debate.py` to prevent confusion with the primary debate system.
- **Grounded** `trading_bot/foundation_agents/multi_agent/agent_swarm.py` by replacing random confidence with agent-proficiency metrics.
- **Integrated** `trading_bot/agents/multi_agent_debate.py` with `UnifiedDecisionBus` to ensure debate outcomes are visible to the CSC.
- **Refactored** `HeadAI` to use structured evidence (uncertainty, assumptions, causal links) rather than simple weighted voting.

## 3. Recommended Next Steps

- Move all remaining production-critical logic from `trading_bot/agents/` to `trading_bot/core_agent_system/swarm/`.
- Standardize all agent communication on `UnifiedDecisionBus`.
- Remove `trading_bot/agents2/` after verifying that its specialized agents are fully supported by `IntegratedAgentSystem`.
