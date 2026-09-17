# LIFECYCLE_AND_STATE_OWNERSHIP.md

This document defines the lifecycle, state ownership, and synchronization constraints for all Tier-0 subsystems inside AlphaAlgo. It explicitly diagnoses the singleton "reset()" architectural problem and defines proper lifecycle management patterns.

---

## 1. Core Lifecycle Ownership Model

To prevent state races, cross-loop leakage, and concurrent write locks, AlphaAlgo enforces a strict hierarchy of component lifecycle ownership.

```
       ┌───────────────────────────┐
       │   UnifiedDecisionBus      │  (Global Event Backbone - Owner of Events)
       └─────────────┬─────────────┘
                     │  publishes to
                     ▼
       ┌───────────────────────────┐
       │ CognitiveSystemController │  (Strategic Brain - Owner of Planning/Reasoning)
       └─────────────┬─────────────┘
                     │  accesses
                     ▼
       ┌───────────────────────────┐
       │ HierarchicalMemorySystem  │  (Transactive Memory - Owner of SAGE/AutoMem)
       └───────────────────────────┘
```

---

## 2. Diagnosis of the Singleton "reset()" Architectural Problem

### Why do "UnifiedDecisionBus", "CognitiveSystemController", and "HierarchicalMemorySystem" require global state?
1. **UnifiedDecisionBus**: Operates as a shared LogAct backbone. Since multiple asynchronous tasks across disparate modules must publish actions to a single audited queue to achieve Byzantine consensus, a single globally referenceable transaction bus is required.
2. **CognitiveSystemController (CSC)**: Implements the "One Brain" invariant. If multiple strategic brains run concurrently in production, they will issue conflicting trade directions, leading to transaction collision, doubled exposure, and capital depletion.
3. **HierarchicalMemorySystem (HMS)**: Acts as a transactive memory store. It must preserve a single consistent copy of the SAGE graph schema to avoid database locking, dirty reads, and schema corruption under high-concurrency writes.

### Why do tests require "reset()"?
Tests are designed to run in complete isolation. Because Python's test runner executes sequentially or concurrently in the same process, global singleton states leak between tests. Specifically, outstanding tasks on the `UnifiedDecisionBus` or modified schemas in `HierarchicalMemorySystem` corrupt the initial state of subsequent tests, leading to non-deterministic failures.

### The Architectural Hazard of Mock Resets
Simply deleting a class instance pointer (`_instance = None`) to pass a test creates severe production bugs:
- It leaves background processing tasks (like `_process_log`) running in the event loop, causing thread leakage and CPU exhaustion.
- It leaves file write-locks unclosed.
- It causes cross-loop leakage, where a component bound to a previous asyncio event loop tries to interact with a new loop, triggering `RuntimeError: Task <Task> pending cleanup`.

---

## 3. The Lifecycle Management Pattern (Safe Resets)

If a reset API is required for test isolation, it must be implemented as an explicit lifecycle operation with:
- **Task Cancellation**: Active background worker tasks must be gracefully cancelled and awaited.
- **Resource Cleanup**: Active file descriptors, network connections, and database locks must be safely closed.
- **State Invalidation**: Volatile state variables (queues, caches, logs) must be cleared.
- **Synchronization**: Thread locks must be re-initialized to prevent concurrent race conditions.

### A. Safe Reset Implementation for UnifiedDecisionBus
```python
class UnifiedDecisionBus:
    ...
    @classmethod
    async def reset(cls):
        """Explicit, safe class-level lifecycle reset."""
        with cls._lock:
            if cls._instance is not None:
                # 1. Gracefully stop active loops
                await cls._instance.stop()
                # 2. Clear volatile logs
                cls._instance._log.clear()
                # 3. Clean instance pointer
                cls._instance = None
        logger.info("UnifiedDecisionBus successfully reset with complete task cancellation.")
```

### B. Safe Reset Implementation for CognitiveSystemController
```python
class CognitiveSystemController:
    ...
    @classmethod
    async def reset(cls):
        """Gracefully invalidates CSC state, stopping any active active reasoning loops."""
        if cls._instance is not None:
            # Cancel any internal loops, reset surprise histories
            cls._instance.discrete_channel.clear()
            cls._instance.continuous_state.clear()
            cls._instance.vfe_history.clear()
            cls._instance = None
        logger.info("CognitiveSystemController successfully reset.")
```

### C. Safe Reset Implementation for HierarchicalMemorySystem
```python
class HierarchicalMemorySystem:
    ...
    @classmethod
    def reset(cls):
        """Safe memory system reset closing graph write locks."""
        with cls._lock:
            if cls._instance is not None:
                # Flush schema writes and clear in-memory cache
                cls._instance._save_schema()
                cls._instance = None
        logger.info("HierarchicalMemorySystem successfully reset with schema synchronization.")
```

This explicit lifecycle pattern guarantees that test isolation is achieved cleanly, without introducing race conditions, file corruption, or asyncio cross-loop leakage.
