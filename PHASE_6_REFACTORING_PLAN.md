# Phase 6: UCA V5 Refactoring Plan

This plan outlines the structural changes required to complete the transition to Unified Cognitive Architecture (UCA) V5, backed by scientific evidence from the 2026 research package.

## 1. Subsystem Categorization

### 1.1 Keep (Maintain with minor updates)
*   **Immutable Shield** (`trading_bot/core/immutable_shield.py`): The core logic is sound but must be integrated as a mandatory Voter in the LogAct backbone.
*   **Verification Swarm** (`trading_bot/core/verification/`): Infrastructure is solid; needs grounding in the LogAct total ordering.

### 1.2 Redesign (Structural overhaul)
*   **Unified Event Bus** (`trading_bot/core/unified_event_bus.py`):
    - **Change**: Complete the transition from a "Notification Bus" to a "Shared-Log Backbone" (LogAct).
    - **Evidence**: *LogAct: Enabling Agentic Reliability via Shared Logs* (Balakrishnan, et al., 2026).
*   **Hierarchical Memory System** (`trading_bot/core/hms/`):
    - **Change**: Fully implement the SAGE Reader-Writer feedback loop and QKG context-dependent validity.
    - **Evidence**: *SAGE: A Self-Evolving Agentic Graph-Memory Engine* (Wang, et al., 2026).
*   **Cognitive System Controller** (`trading_bot/core/csc/controller.py`):
    - **Change**: Implement the 12-step Active Inference pipeline as the governing loop, replacing heuristic branching. Integrate DiscoLoop mixed-channel reasoning.
    - **Evidence**: *DiscoLoop* (Fu, et al., 2026); *Active Inference & Free Energy* (Ludik, 2025).

### 1.3 Merge (Consolidate duplicated systems)
*   **Evolution & Governance** (`trading_bot/governance/`):
    - **Change**: Merge `evolution_gate.py` with `RSEA` monotone-safe checks and `EKSFT` masking logic.
    - **Evidence**: *RSEA: Recursive Self-Evolving Agents* (2026); *EKSFT* (2026).

### 1.4 Replace (Complete substitution)
*   **Skill Management**:
    - **Change**: Replace MD prompts in `trading_bot/skills/` with executable **HASP Skill Programs** managed by a `SkillRouter`.
    - **Evidence**: *HASP: Harnessing LLM Agents with Skill Programs* (2026).

### 1.5 Remove (Dead code/Legacy)
*   **Legacy Agents**: Remove fragmented agent implementations in `trading_bot/agents/` that do not follow the "One Brain" CSC model.
*   **Stateless RAG**: Remove codepaths that use naive vector search without graph grounding.

## 2. Scientific Mapping & Citations

| Component | Target Architecture | Scientific Citation |
| :--- | :--- | :--- |
| **Reliability** | LogAct Shared Log | arXiv:2604.07988 |
| **Reasoning** | DiscoLoop | arXiv:2607.00341 |
| **Memory** | SAGE / QKG | arXiv:2605.12061 / arXiv:2604.23972 |
| **Skills** | HASP | arXiv:2605.17734 |
| **Governance** | RSEA | arXiv:2606.28374 |
| **Objective** | Active Inference | Friston, et al. (2025) |

## 3. Implementation Roadmap (Tiered)

1.  **Phase A (Reliability)**: LogAct Backbone transition in `unified_event_bus.py`.
2.  **Phase B (Memory)**: SAGE evolution loop in `hms/memory.py`.
3.  **Phase C (Intelligence)**: CSC Active Inference & HASP Router implementation.
4.  **Phase D (Validation)**: CL-Bench "Gain Metric" and FIRE benchmark integration.
