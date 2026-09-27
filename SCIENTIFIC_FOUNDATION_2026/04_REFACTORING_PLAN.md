# Evidence-Based Refactoring Specification (2026 Edition)

## Executive Summary
This document specifies the scientific refactoring plan for AlphaAlgo. Each action is backed by empirical research evidence and rigorous safety constraints.

---

## Subsystem Categorization & Action Plan

### 1. Components to Keep (Canonical Production Core)
- **`trading_bot.core.csc.controller.CognitiveSystemController`**: Authoritative singleton for active inference state estimation.
- **`trading_bot.agents.multi_agent_debate.MultiAgentDebateSystem`**: Single authoritative multi-agent debate and Bayesian consensus engine.
- **`trading_bot.memory.hms.HierarchicalMemorySystem`**: Single authoritative memory hierarchy with SHA-256 provenance tracking.
- **`trading_bot.core.security.sandbox.SecureASTVisitor`**: Sandboxed AST validator protecting dynamic evolution pipelines.

### 2. Components to Redesign (Optimization & Hardening)
- **`trading_bot/core/csc/controller.py`**:
  - *Action*: Ensure explicit citation matrix in module docstring referencing all 8 mandatory arXiv research papers (EKSFT, LogAct, CORAL, Search-R1, AutoMem, S2L, HASP, DeepWeb-Bench).
  - *Justification*: Citing foundational research ensures 100% scientific audit traceability.
- **`trading_bot/agents/multi_agent_debate.py`**:
  - *Action*: Incorporate epistemic uncertainty bounds ($\sigma_{\text{epi}}^2$) and Quiet-STaR thought scratchpads into debate arguments.
  - *Justification*: Prevents LLM hallucinations under high market noise (supported by DeepWeb-Bench arXiv:2605.21482 and Quiet-STaR).
- **`risk/risk_manager.py`**:
  - *Action*: Parenthesize list comprehension unpacking in `get_risk_report` to ensure Python syntax compliance.
  - *Justification*: Fixes AST compilation failure during static analysis.

### 3. Components to Merge (Consolidation)
- Legacy monolithic brain entrypoints (`unified_ai_brain.py`, `ultimate_integration.py`, `mega_integration.py`) are wrapped as backward-compatible proxies pointing directly to `AlphaAlgoCognitiveBrain`.

### 4. Components to Remove (Deprecation)
- Obsolete temporary fix files and test scripts containing invalid syntax (e.g., broken test functions in `tests/orchestrator/test_orchestrator_master.py`).
