# UCA V5 Refactoring Blueprint (July 2026)

This document provides the detailed engineering blueprint for refactoring AlphaAlgo into the UCA V5 architecture, backed by scientific evidence.

---

## 1. Core Component Redesign

### 1.1 The LogAct Shared-Log Backbone
*   **Target**: `trading_bot/core/unified_event_bus.py`
*   **Refactor**: Convert the singleton bus into a totally ordered action log.
*   **Mechanism**: `ActionEntry` serialization; `VoterRegistry` for decoupled approval.
*   **Scientific Justification**: *LogAct: Enabling Agentic Reliability via Shared Logs* (Balakrishnan, et al., 2026).
*   **Citations**: arXiv:2604.07988.

### 1.2 HMS-SAGE (Dynamic Graph Memory)
*   **Target**: `trading_bot/core/hms/memory.py`
*   **Refactor**: Implement a self-evolving graph-memory substrate.
*   **Mechanism**: `MemoryWriter` (graph construction) and `MemoryReader` (GFM-based retrieval) with feedback loops.
*   **Scientific Justification**: *SAGE: A Self-Evolving Agentic Graph-Memory Engine* (Wang, et al., 2026).
*   **Citations**: arXiv:2605.12061.

### 1.3 The HASP Skill Program Router
*   **Target**: `trading_bot/core/csc/router.py` (New File)
*   **Refactor**: Implement executable state-action intervention functions.
*   **Mechanism**: `SkillRouter` maps task states to either `SkillPrograms` (HASP) or `LoRA Adapters` (S2L).
*   **Scientific Justification**: *HASP: Harnessing LLM Agents with Skill Programs* (arXiv:2605.17734); *Skill-to-LoRA* (arXiv:2606.16769).

### 1.4 The CSC Active Inference Loop
*   **Target**: `trading_bot/core/csc/controller.py`
*   **Refactor**: Wrap reasoning in a Variational Free Energy (VFE) objective.
*   **Mechanism**: **DiscoLoop** multi-hop reasoning; Bayesian belief updates.
*   **Scientific Justification**: *DiscoLoop* (Fu, et al., 2026); *Active Inference and the Free Energy Principle* (Ludik, 2025).

---

## 2. Refactoring Priority & Implementation Order

1.  **Phase A: Foundational Reliability (Tier 0)**
    *   Deploy LogAct Backbone in `unified_event_bus.py`.
    *   Integrate `ImmutableShield` as the primary LogAct Voter.
2.  **Phase B: Cognitive Memory (Tier 0)**
    *   Implement SAGE dynamic graph memory in `hms/memory.py`.
    *   Update `hms/models.py` with QKG context-aware triplet schema.
3.  **Phase C: Agent Intelligence (Tier 1)**
    *   Deploy `SkillRouter` and migrate prompts to `HASP` programs.
    *   Implement `DiscoLoop` reasoning in `controller.py`.
4.  **Phase D: Validation (Tier 2)**
    *   Implement "Gain Metric" and HORIZON diagnostics in `tests/uca_v5_validation.py`.
