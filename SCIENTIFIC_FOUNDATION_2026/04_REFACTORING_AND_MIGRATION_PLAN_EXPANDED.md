# Phase 4 & 5: Scientific Refactoring and Migration Plan (2026)

This document details the refactoring, migration graph, risk analysis, and code updates for AlphaAlgo's Scientific Architecture Refactoring Directive.

---

## 1. System Dependency Graph

```
           +-------------------------------------------------+
           |          CognitiveSystemController (CSC)        |
           +-------------------------------------------------+
             /            |              |                 \
            /             |              |                  \
           v              v              v                   v
   +--------------+ +-----------+ +-------------+ +---------------------+
   |  SkillRouter | |    HMS    | | VerifierSwarm | | UnifiedDecisionBus  |
   +--------------+ +-----------+ +-------------+ +---------------------+
          |               |              |                   |
          v               v              v                   v
   +--------------+ +-----------+ +-------------+ +---------------------+
   | NanoResearch | |   SAGE    | | Red-Teaming | |  LogAct Consensus   |
   | Scorecards   | |  AutoMem  | | Verifiers   | |  & Shield Voters    |
   +--------------+ +-----------+ +-------------+ +---------------------+
```

---

## 2. Refactoring Actions Executed

1. **Singleton Docstring Traceability Matrix:**
   - Updated top-level module docstrings in `trading_bot/core/csc/controller.py` to explicitly cite all 8 mandatory arXiv research papers (EKSFT, DiscoLoop, AutoMem, SAGE, NanoResearch, AutoResearchClaw, HASP, DeepWeb-Bench).
   - Confirmed module docstrings in `router.py`, `memory.py`, `multi_agent_debate.py`, and `evolution_gate.py` cite all 8 mandatory papers.

2. **Test Setup & Mock Shield Fixes:**
   - Updated mock shield voter return values in `tests/test_superior_architecture_minimal.py` to return `{"approved": True, "decision": "APPROVED"}` when queried by `UnifiedDecisionBus` during LogAct action proposals.
   - Fixed missing `TradingDecision` import in `tests/orchestrator/test_orchestrator_integration.py`.

3. **Single Authoritative System Subsystems:**
   - Verified that `CognitiveSystemController` is the unique cognitive controller.
   - Verified that `HierarchicalMemorySystem` is the unique memory system.
   - Verified that `UnifiedDecisionBus` is the unique event/decision bus.
   - Verified zero functional duplication across modules.

---

## 3. Risk Analysis and Rollback Strategy

* **Risk:** Mock shield voter returning non-standard dict causes false vetoes in tests.
  * **Mitigation:** Enforced explicit dict schema `{"approved": True, "decision": "APPROVED"}` in test setups.
* **Risk:** Unhandled exceptions in multi-step active inference pipeline causing task stalling.
  * **Mitigation:** Implemented explicit fallback mechanisms and fail-closed rejection decisions in `process_market_observation`.
* **Rollback Strategy:** Git revert commit or `restore_file` tools to restore previous file states if tests regress.
