# 🗺️ Phase 4: Capability Mapping & Strategic Prioritization (2026)

This document maps every canonical engineering principle to specific AlphaAlgo subsystems, assigning execution priority, dependencies, ROI estimation, complexity, and target benchmark metrics.

---

## 1. Principle to Subsystem Mapping Matrix

| Engineering Principle | Target Subsystem Path | Priority | Dependencies | Expected ROI | Complexity | Target Benchmark Metric |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Subgoal Planning (HIPIF)** | `trading_bot/core/csc/folding.py` | **High** | `HierarchicalMemorySystem` | **Very High** | Medium | Context token size reduction of $>50\%$ |
| **Multi-Hop Reasoning (DiscoLoop)** | `trading_bot/core/csc/controller.py` | **High** | `DiscoLoopCell` | **High** | High | Multi-hop causal reasoning precision improvement of $>35\%$ |
| **Dynamic Causal Worlds (CWMI)** | `trading_bot/world_model/causal/scm.py` | **High** | None | **High** | High | Slippage and order impact prediction error $<5\%$ |
| **Self-Evolving Memories (SAGE)** | `trading_bot/core/hms/memory.py` | **Medium** | `SAGEGraphMemory` | **Medium** | Medium | SAGE graph retrieval lookup latency $<5\text{ms}$ |
| **Non-Bypassable Compliance (HASP)** | `trading_bot/core/csc/router.py` | **Critical** | `SkillRouter` | **Unlimited** | Low | 100% compliance gate enforcement under volatility spikes |

---

## 2. Rejection of Redundant / Non-Value Principles

To preserve architectural elegance and prevent unnecessary complexity, the following research principles from our 100-paper corpus are explicitly **rejected**:

1. **Category 9 - Self-Replicating Agent Classes (MAS-026)**:
   - *Rationale for Rejection*: Unstructured population cloning of models inside trading desks introduces high risk of chaotic coordination drift, resource exhaustion, and "Policy Contagion."
   - *Alternative*: Retain our strict single-brain (CSC) workflow model acting on LogAct shared logs.
2. **Category 8 - Recursive Self-Repair Sockets (SAF-022)**:
   - *Rationale for Rejection*: Writing self-repair websocket wrapper scripts in real-time opens major security vulnerability windows.
   - *Alternative*: Rely on static, verified, and compiled connection-recovery routines.
3. **Category 5 - Cross-Domain Analogical Mappings (SCI-025)**:
   - *Rationale for Rejection*: Mapping biological/physical models (e.g. cellular division) to financial series has zero out-of-sample statistical backing and introduces high risk of conceptual hallucinations.
   - *Alternative*: Constrain SAGE graph relations strictly to causal and empirical financial data links.
