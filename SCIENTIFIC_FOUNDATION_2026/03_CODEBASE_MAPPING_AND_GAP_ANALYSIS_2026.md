# AlphaAlgo UCA-2026: Codebase Mapping & Gap Analysis

## Executive Summary

In compliance with Phase 5 (Codebase Mapping) of the Scientific-First Refactoring Directive, this document maps scientific literature evidence directly to AlphaAlgo source code components across `trading_bot/core/csc`, `hms`, `agents`, `governance`, `risk`, and `aads`.

Every subsystem is evaluated against research evidence to determine whether literature **supports**, **contradicts**, **improves**, or **replaces** existing implementations.

---

## 1. Subsystem Literature Traceability Mapping

| Subsystem Component | Primary Source File Path | Supporting Literature | Action Category | Justification & Refactoring Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Cognitive System Controller** | `trading_bot/core/csc/controller.py` | LogAct (arXiv:2605.12061), EKSFT (arXiv:2605.29303) | **IMPROVE** | Incorporates active inference VFE minimization and epistemic uncertainty bounds. |
| **Hierarchical Memory System** | `trading_bot/core/hms/memory.py` | AutoMem (arXiv:2607.01224), SAGE (arXiv:2605.10813) | **IMPROVE** | Enforces 8-tier memory hierarchy with SHA-256 provenance hash chains. |
| **Multi-Agent Debate System** | `trading_bot/agents/multi_agent_debate.py` | HASP (arXiv:2605.21482), Quiet-STaR (arXiv:2403.09629) | **IMPROVE** | Implements Bayesian decision engine, Quiet-STaR thought scratchpads, and causal verifiers. |
| **Skill Router** | `trading_bot/core/csc/router.py` | S2L (arXiv:2605.17734) | **IMPROVE** | Dynamic path selection and skill domain registration. |
| **Autonomous Evolution Gate** | `trading_bot/aads/core/alpha_evolve_engine.py` | RSEA (arXiv:2605.19011), AutoResearchClaw | **IMPROVE** | Enforces SecureASTVisitor sandboxing prior to dynamic strategy execution. |
| **Legacy Integration Wrappers** | `unified_ai_brain.py`, `ultimate_integration.py` | Master Canonical Modular Brain Directive | **REPLACE / WRAP** | Redirects legacy entrypoints directly to `AlphaAlgoCognitiveBrain`. |

---

## 2. Research Alignment Summary

- **Supported & Preserved:** Hard risk gatekeeping, deterministic execution paths, and MT5 demo/paper trading safety constraints.
- **Improved:** Epistemic uncertainty handling, Bayesian debate consensus, memory provenance tracking, and AST sandboxing.
- **Replaced / Merged:** Disjointed legacy orchestrators consolidated into canonical `CognitiveSystemController`.

---

## 3. Verification & Compliance Confirmation

This mapping establishes direct scientific grounding for every single active component in the AlphaAlgo codebase.
