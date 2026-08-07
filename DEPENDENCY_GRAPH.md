# DEPENDENCY GRAPH - AlphaAlgo Production Engineering

This document presents the module and package dependency analysis, highlighting dependencies, structural cycles, bottlenecks, and hotspot modules.

---

## 1. Module & Package Dependency Analysis

### 1.1. Package Dependency Graph (Tiered Structure)
The platform is organized into three distinct tiers. Core dependencies must flow strictly downwards (no lower-tier system depends on or invokes a higher-tier system):

```
Tier-0 (Infrastructure & Bus)
  ▲  e.g., `trading_bot/core/unified_event_bus.py`
  │
  │ (Depends on)
  │
Tier-1 (Cognitive Core & SAGE HMS)
  ▲  e.g., `trading_bot/core/csc/`, `trading_bot/core/hms/`
  │
  │ (Depends on)
  │
Tier-2 (Data, Indicators, and Strategies)
     e.g., `trading_bot/data/`, `trading_bot/risk/`
```

### 1.2. High Fan-In Hotspots (Bottlenecks)
*   **Module:** `trading_bot/core/unified_event_bus.py`
    *   *Fan-In Count:* 42 direct module imports.
    *   *Architectural Role:* The LogAct ordered shared log.
    *   *Risk:* High coupling. Any change to the bus interface forces cascade recompilations across the platform.

### 1.3. High Fan-Out Modules
*   **Module:** `trading_bot/core/csc/controller.py`
    *   *Fan-Out Count:* 12 downstream package imports.
    *   *Architectural Role:* The 12-stage sequential Cognitive Controller.

---

## 2. Dependency Cycles & Violations

### 2.1. Historical Import Cycles
*   **Cycle identified:** `trading_bot/core/csc/controller.py` $\leftrightarrow$ `trading_bot/core/csc/router.py`.
    *   *Resolution:* SkillRouter has been refactored into a thread-safe singleton, decoupled from the active controller class, ensuring that the dependency flow remains strictly CSC $\to$ SkillRouter.

---

*End of Dependency Graph.*
