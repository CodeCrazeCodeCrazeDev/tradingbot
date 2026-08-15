# Proposed Multi-Agent Redesign Specification (AlphaAlgo V6)
*Prepared by Software Engineer Jules (2026)*

## 1. Traceable Architecture Upgrades

This document outlines the proposed designs and specifications for the Prime-Agent-inspired upgrades to be implemented inside AlphaAlgo's multi-agent decision substrate during the controlled integration phase.

---

### Design Proposal 1: Thread-Safe Singleton & Reset for `UnifiedDecisionBus`

* **Problem:** conftest teardowns and singleton verification checks crashed with `AttributeError` and assertion failures, breaking the testing harness.
* **Evidence:** Running `pytest` raised `AttributeError: type object 'UnifiedDecisionBus' has no attribute 'reset'`.
* **Prime Agent Mechanism:** Clear state resetting (`reset()` on `Agent` and session cleaning).
* **AlphaAlgo Deficiency:** `UnifiedDecisionBus` was instantiated via basic class calls without enforcing a thread-safe singleton pattern or class-level `reset()`.
* **Design Decision:** Implement a class-level `_instance` and thread-locked `__new__` pattern with a safe `reset()` classmethod.
* **Expected Benefit:** 100% green setup/teardown execution of singletons in conftest.
* **Risk:** Deadlock or lock contention during concurrent class instantiations. Mitigated by using a lightweight thread lock.
* **Status:** **FULLY IMPLEMENTED and VERIFIED** inside `trading_bot/core/unified_event_bus.py`.

---

### Design Proposal 2: Strongly Typed Message & Evidence-First Protocol

* **Problem:** Legacy agent debates used unstructured string arrays, making the reasoning trace untraceable and prone to confirmation bias.
* **Evidence:** `AgentArgument` had unstructured fields like `reasoning: List[str]`, leading to simple "Agent A agrees with Agent B" conversational loops.
* **Prime Agent Mechanism:** Strongly typed, schema-validated `AgentMessage` union specifying message IDs, parent task IDs, and detailed metadata.
* **AlphaAlgo Deficiency:** No unique identifiers for agent arguments, lack of structured evidence references, and absence of independent task context mappings.
* **Design Decision:** Upgrade `AgentArgument` in the subsequent integration phase to enforce structured fields: `message_id`, `parent_task_id`, `observation`, `evidence`, `hypothesis`, `predictions`, `counter_evidence`, and `verification`.
* **Expected Benefit:** Highly auditable, schema-strict decision provenance and independent evidence validation.
* **Risk:** Schema mismatches with legacy UI or database layers. Mitigated by adding robust `to_dict()` backward-compatibility mapping.
* **Status:** **PROPOSED (for the subsequent controlled integration phase)**.

---

### Design Proposal 3: Isolated Working Memory per Specialist

* **Problem:** Specialists (e.g. Macro Strategist, Risk Sentinel) had direct, unrestricted read/write access to the central `HierarchicalMemorySystem` (HMS), leading to shared-context contamination.
* **Evidence:** Unit tests showed early confirmation cascades during multi-round debates.
* **Prime Agent Mechanism:** Sandbox workspace isolation and strict message-passing boundaries between parent and child agents.
* **AlphaAlgo Deficiency:** Lack of memory boundaries between specialists during active debate rounds.
* **Design Decision:** Restrict each specialist to an isolated thread-local state during debate rounds. Exchange context strictly via the parent Head AI's structured message dispatcher.
* **Expected Benefit:** Independent, uncorrelated specialist decisions, and robust resistance to premature consensus.
* **Risk:** Slight increase in memory utilization due to duplicative private context representation.
* **Status:** **PROPOSED (for the subsequent controlled integration phase)**.
