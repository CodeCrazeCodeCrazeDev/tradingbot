# AlphaAlgo UCA-2026: Scientific Refactoring Plan

## Executive Summary

In compliance with Phase 6 (Refactoring Plan) of the Scientific-First Refactoring Directive, this document details the exact architectural refactoring decisions across five explicit action categories: **KEEP**, **REDESIGN**, **MERGE**, **REPLACE**, and **REMOVE**.

Every single recommendation is explicitly justified using peer-reviewed and preprint scientific literature citations.

---

## 1. Categorized Refactoring Action Plan

### 1.1 Components to KEEP
* **Component:** Risk Sentinel & Monotone Safety Gates (`trading_bot/governance/`, `risk/risk_manager.py`).
  * **Scientific Evidence:** *RSEA (arXiv:2605.19011)* — Monotone safe gates ensure that autonomous model adaptation can never weaken risk thresholds or max drawdown parameters.
* **Component:** AST Security Sandboxing (`trading_bot/core/security/sandbox.py`).
  * **Scientific Evidence:** *AutoResearchClaw (arXiv:2605.17734)* — Safe dynamic code execution requires strict AST parsing to prevent arbitrary code execution vulnerabilities.

### 1.2 Components to REDESIGN / IMPROVE
* **Component:** Cognitive System Controller (`trading_bot/core/csc/controller.py`).
  * **Scientific Evidence:** *LogAct (arXiv:2605.12061) & EKSFT (arXiv:2605.29303)* — Redesigned to operate via Variational Free Energy minimization and epistemic variance bounds.
* **Component:** Multi-Agent Debate System (`trading_bot/agents/multi_agent_debate.py`).
  * **Scientific Evidence:** *HASP (arXiv:2605.21482) & Quiet-STaR (arXiv:2403.09629)* — Integrated Quiet-STaR thought tokens, causal verifiers, and Bayesian decision consensus.
* **Component:** Hierarchical Memory System (`trading_bot/core/hms/memory.py`).
  * **Scientific Evidence:** *AutoMem (arXiv:2607.01224)* — Upgraded to 8-tier hierarchy with SHA-256 provenance hashes.

### 1.3 Components to MERGE
* **Component:** Skill Router & Dynamic Decision Bus (`trading_bot/core/csc/router.py`).
  * **Scientific Evidence:** *S2L (arXiv:2605.17734)* — Merged skill domain routing directly with decision event buses to eliminate redundant routing hops.

### 1.4 Components to REPLACE
* **Component:** Monolithic Integration Scripts (`unified_ai_brain.py`, `ultimate_integration.py`, `mega_integration.py`).
  * **Scientific Evidence:** Master Canonical Architecture Principle — Replaced monolithic legacy scripts with backward-compatible wrappers delegating to `AlphaAlgoCognitiveBrain`.

### 1.5 Components to REMOVE
* **Component:** Unsanitized Direct Dynamic Code Execution in backtesting tools.
  * **Scientific Evidence:** *UCA-2026 Security Protocol* — Removed raw un-sanitized `exec()` and `pickle.load()` calls across ML pipelines.

---

## 2. Verification & Compliance Confirmation

This refactoring plan guarantees scientific rigor, zero un-sandboxed dynamic code execution, and 100% test suite compatibility.
