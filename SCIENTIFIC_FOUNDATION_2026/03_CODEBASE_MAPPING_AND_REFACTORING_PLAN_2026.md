# 03 Codebase Mapping & Refactoring Plan (2026)

## 1. Codebase Scientific Audit & Traceability Mapping (Phase 5)

| AlphaAlgo Subsystem | Source Path | Grounding Research Papers | Current Limitations / Flaws | Refactoring Action | Scientific Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cognitive System Controller** | `trading_bot/core/csc/controller.py` | REF-04 (HASP), REF-06 (DiscoLoop) | Lacked continuous VFE state estimation; relied solely on discrete rule loops. | **REDESIGN & EXPAND** | Grounding continuous active inference reduces regime prediction error and bounded guardrails prevent unsafe trade generation. |
| **Hierarchical Memory System** | `trading_bot/core/hms/memory.py` | REF-02 (SAGE), REF-03 (AutoMem) | Linear vector lookup without temporal decay or SHA-256 graph provenance verification. | **REDESIGN & MERGE** | Dynamic TD-link updates allow memory graph to adapt to shifting market macro regimes without catastrophic forgetting. |
| **Multi-Agent Debate Engine** | `trading_bot/agents/multi_agent_debate.py` | REF-01 (LogAct), REF-07 (AutoResearchClaw), REF-08 (EKSFT) | Lack of explicit epistemic uncertainty bounds on agent arguments. | **REDESIGN & HARDEN** | Epistemic uncertainty bounds prevent overconfident agent hallucination in decision governance. |
| **Adaptive Control Policy Engine** | `trading_bot/core/governance/acpe.py` | REF-05 (Skill-to-LoRA) | Static fallback policy routing. | **KEEP & OPTIMIZE** | Rapid adapter routing lowers operational latency while preserving regime-specific skill execution. |

---

## 2. Scientific Refactoring Execution Roadmap (Phase 6)

### Directive 1: Bounded Active Inference Control
*   **Target File**: `trading_bot/core/csc/controller.py`
*   **Modification**: Implement `calculate_variational_free_energy()` and integrate HASP safety interceptor before plan dispatch.

### Directive 2: SAGE Provenance & Graph-Native Memory
*   **Target File**: `trading_bot/core/hms/memory.py`
*   **Modification**: Integrate SHA-256 provenance hashing into memory node creation and implement `update_graph_edge_weights_td()`.

### Directive 3: Epistemic Uncertainty & AutoResearchClaw Debates
*   **Target File**: `trading_bot/agents/multi_agent_debate.py`
*   **Modification**: Add `epistemic_uncertainty` parameter to agent arguments and verify Bayesian calibration bounds during consensus calculation.
