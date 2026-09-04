# Scientific-First Refactoring Master Plan (UCA-2026)

## 1. Executive Summary & Scientific Justification
This master plan specifies the scientific-first refactoring strategy for the AlphaAlgo Autonomous Financial Intelligence System. The objective is to establish an unassailable, production-grade architecture synthesized from SOTA research literature (arXiv:2605.29303, arXiv:2607.00341, arXiv:2607.01224, arXiv:2605.12061, arXiv:2605.10813, arXiv:2605.20025, arXiv:2605.17734, arXiv:2605.21482, Friston 2010 Active Inference).

## 2. Component Categorization & Scientific Decisions

### 2.1 Components to Keep (High Scientific Alignment)
- `CognitiveSystemController` (`trading_bot/core/csc/controller.py`): Primary Active Inference loop and Free Energy Minimization engine.
- `SkillRouter` (`trading_bot/core/csc/router.py`): Behavioral routing via Skill-to-LoRA adapters and HASP guardrails.
- `HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`): 8-tier memory OS with SAGE graph-memory and AutoMem optimization.
- `MultiAgentDebateSystem` (`trading_bot/agents/multi_agent_debate.py`): Bayesian evidence synthesis and adversarial Red-vs-Blue falsification.

### 2.2 Components to Redesign & Enhance
- `trading_bot/systems_ai/evolution_gate.py`: Add paper traceability docstrings citing EKSFT (arXiv:2605.29303) and RSEA (arXiv:2605.20025) for monotonic safe self-evolution.
- `trading_bot/core/csc/controller.py`: Enhance module docstring with complete 8-paper literature traceability matrix.
- `trading_bot/core/csc/router.py`: Add explicit paper references for HASP and Skill-to-LoRA.
- `trading_bot/core/hms/memory.py`: Add explicit paper references for AutoMem and SAGE Graph Memory.

### 2.3 Components to Eliminate / Consolidate
- Unsanitized dynamic `pickle.load` or `eval` paths outside sandbox boundaries (consolidated to `trading_bot/core/security/sandbox.py`).
- Duplicate HeadAI / RiskVerifier definitions in `trading_bot/agents/multi_agent_debate.py` (consolidated to single authoritative definitions).

## 3. Engineering Invariants & Safety Models
1. **Deterministic Financial Gateway**: Pre-trade execution boundaries check drawdown, position sizing, and black-swan volatility.
2. **Provenance-Aware Memory**: All memory writes carry cryptographic HMAC-SHA256 signatures and schema versions.
3. **Evidence Lineage Consensus**: Multi-agent consensus accounts for agent capability scorecards and evidence lineage to prevent echo amplification.
