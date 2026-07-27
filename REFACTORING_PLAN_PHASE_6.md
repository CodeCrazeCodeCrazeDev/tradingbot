# Refactoring Plan (Phase 6): AlphaAlgo UCA V5 Implementation

This document specifies the authoritative refactoring strategy for AlphaAlgo, backed by the 24-paper scientific synthesis of July 2026.

---

## 1. Component Categorization & Scientific Justification

### 1.1 Components to KEEP
*   **Subsystem**: `Evidence Models` (`trading_bot/core/hms/models.py`)
    *   **Reason**: The `ResearchLedgerEntry` and `EvidenceGraph` schemas provide a solid foundation for traceability.
*   **Subsystem**: `ImmutableShield` Logic (`trading_bot/core_agent_system/governance_system.py`)
    *   **Reason**: The core risk-bound logic remains valid but will be re-hosted as a LogAct Voter.

### 1.2 Components to REDESIGN
*   **Subsystem**: `CognitiveSystemController` (`trading_bot/core/csc/controller.py`)
    *   **Redesign**: Implement the 12-step Recursive Active Inference pipeline. Integrate **DiscoLoop** mixed-channel reasoning and the **Pivot/Refine** decision loop.
    *   **Evidence**: *DiscoLoop* (Fu et al., 2026); *Active Inference* (Ludik, 2025).
*   **Subsystem**: `HierarchicalMemorySystem` (`trading_bot/core/hms/memory.py`)
    *   **Redesign**: Transform into a **SAGE** Self-evolving Agentic Graph-Memory. Implement the `MemoryWriter` (incremental construction) and `MemoryReader` (Graph-FM) feedback loop.
    *   **Evidence**: *SAGE* (Wang et al., 2026, arXiv:2605.12061).
*   **Subsystem**: `UnifiedDecisionBus` (`trading_bot/core/unified_event_bus.py`)
    *   **Redesign**: Convert from a standard event bus to a **LogAct** Shared-Log Backbone. Ensure total ordering of actions and mandatory voting before execution.
    *   **Evidence**: *LogAct: Enabling Agentic Reliability via Shared Logs* (Balakrishnan et al., 2026, arXiv:2604.07988).

### 1.3 Components to MERGE
*   **Subsystem**: `Risk & Governance`
    *   **Action**: Merge fragmented risk checkers from `risk/`, `compliance/`, and `anti_reward_hacking.py` into the `GovernanceShield` LogAct Voter.
    *   **Evidence**: *Reward Hacking in Autonomous Agents* (2026); *LogAct* (2026).

### 1.4 Components to REPLACE
*   **Subsystem**: `Skill Management`
    *   **Replacement**: Replace static `SKILL.md` prompts with executable **HASP** Skill Programs and **S2L** LoRA adapters.
    *   **Evidence**: *HASP* (arXiv:2605.17734); *Skill-to-LoRA* (arXiv:2606.16769).
*   **Subsystem**: `Knowledge Retrieval`
    *   **Replacement**: Replace static RAG with **SAGE** multi-hop evidence recovery.
    *   **Evidence**: *SAGE* (2026).

### 1.5 Components to REMOVE
*   **Subsystem**: `Redundant Orchestrators`
    *   **Action**: Decommission 82+ fragmented orchestrators (e.g., `SafeOrchestrator`, `MetaOrchestrator`) in favor of the "One Brain" CSC.
    *   **Evidence**: *Building Effective Agents* (Anthropic/DeepMind, 2025 - "Symmetry of Orchestration").
*   **Subsystem**: `Stochastic World Model`
    *   **Action**: Remove Gaussian noise-based simulations (`np.random`) in favor of deterministic backtest replays and **CWMI** causal induction.
    *   **Evidence**: *Causal World Model Induction* (2025).

---

## 2. Implementation Order (Priority)

1.  **Tier 0**: LogAct Backbone & Governance Shield (Transactional Reliability).
2.  **Tier 0**: CSC Active Inference Loop (Core Reasoning).
3.  **Tier 1**: SAGE Graph Memory & QKG (Contextual Knowledge).
4.  **Tier 1**: HASP Skill Router (Efficient Execution).
5.  **Tier 2**: Evolution Gate & CL-Bench (Self-Improvement).
