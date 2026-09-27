# Codebase Mapping & Research Alignment Audit (2026 Edition)

## Executive Summary
This document establishes the bidirectional traceability matrix mapping the 8 canonical peer-reviewed research papers (EKSFT, LogAct, CORAL, Search-R1, AutoMem, S2L, HASP, DeepWeb-Bench) to AlphaAlgo's active production subsystems.

---

## Codebase Subsystem Mapping Matrix

### 1. Core Cognitive System Controller (`trading_bot/core/csc/controller.py`)
- **Supporting Literature**:
  - **CORAL (arXiv:2607.01224)**: Provides the mathematical foundation for Variational Free Energy (VFE) state estimation and elastic weight regularization to prevent cognitive drift.
  - **S2L (arXiv:2605.20025)**: Supplies active inference principles for continuous belief updating in $O(N)$ time.
- **Architectural Status**: Fully Aligned. Single authoritative controller managing global brain state.

### 2. Multi-Agent Debate & Bayesian Decision Engine (`trading_bot/agents/multi_agent_debate.py`)
- **Supporting Literature**:
  - **DeepWeb-Bench (arXiv:2605.21482)**: Drives the 4-tier verifier topology (`CausalVerifier`, `LiquidityVerifier`, `RegimeVerifier`, `HallucinationDetector`).
  - **Quiet-STaR**: Informs the `thought_tokens` scratchpad reasoning field in `AgentArgument`.
  - **S2L (arXiv:2605.20025)**: Formulates epistemic uncertainty bounds ($\sigma_{\text{epi}}^2$) inside `BayesianDecisionEngine`.
- **Architectural Status**: Fully Aligned. Single canonical implementation.

### 3. Hierarchical Memory System (`trading_bot/memory/hms/memory.py`)
- **Supporting Literature**:
  - **AutoMem (arXiv:2605.10813)**: Establishes SHA-256 provenance hash tracking, memory consolidation, and 3-tier Working/Episodic/Semantic memory hierarchy.
- **Architectural Status**: Fully Aligned.

### 4. Shared Event Bus & Log Backbone (`trading_bot/core/unified_event_bus.py`)
- **Supporting Literature**:
  - **LogAct (arXiv:2607.00341)**: Shared-Log event sourcing architecture for zero-data-loss event broadcasting.
- **Architectural Status**: Fully Aligned.

### 5. AlphaEvolve & AST Security Visitor (`trading_bot/aads/core/alpha_evolve_engine.py`)
- **Supporting Literature**:
  - **EKSFT (arXiv:2605.29303)**: Mandates AST-level security sandboxing (`SecureASTVisitor`) before dynamic code compilation (`exec`).
- **Architectural Status**: Fully Aligned.
