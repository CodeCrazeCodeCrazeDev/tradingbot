# AlphaAlgo Elite Production Issue Tracker (2026)

This document tracks identified, resolved, and monitored engineering defects and scientific regressions across the AlphaAlgo codebase.

---

## 1. Registry of Resolved Defects

### **DEFECT-UCA-2026-01**: UCA Singleton Reset & Lifecycle Regression
*   **Component**: `UnifiedDecisionBus`, `CognitiveSystemController`, `HierarchicalMemorySystem`, `SkillRouter`
*   **Severity**: **CRITICAL (BLOCKER)**
*   **Description**: In some legacy code revisions, the explicit class-level `reset()` methods on core singletons had been omitted or simplified into stubs. This caused pytest-asyncio to fail under test teardown/setup due to cross-test singleton contamination, resulting in 26/26 `AttributeError` errors.
*   **Resolution**: Implemented high-fidelity, thread-safe class-level `reset()` methods across all singletons. Restored `_lock` in `SkillRouter` and synchronized schema serialization in `HierarchicalMemorySystem`.
*   **Status**: **RESOLVED**
*   **Verification**: Unit test suite `tests/uca_v5/` passes 26/26 test cases.

### **DEFECT-UCA-2026-02**: Cross-Loop Event Loop Contamination in Stress Tests
*   **Component**: `tests/stress/test_logact_pressure.py`
*   **Severity**: **HIGH**
*   **Description**: The stress-testing suite initialized `UnifiedDecisionBus` using `event_loop.run_until_complete()`, which bound queue tasks to the session-scoped loop, while pytest-asyncio ran tests in function-scoped loops. This caused `wait_for_decision` to time out.
*   **Resolution**: Converted the `stress_bus` fixture into an asynchronous fixture (`async def stress_bus()`), letting the bus bind to the running loop of the active test case.
*   **Status**: **RESOLVED**
*   **Verification**: `poetry run pytest tests/stress/` passes 4/4 concurrent stress tests in 3.10s.

### **DEFECT-UCA-2026-03**: SkillRouter Default Adapter Name Discrepancy
*   **Component**: `SkillRouter` / `tests/uca_v5/test_router_v5.py`
*   **Severity**: **MEDIUM**
*   **Description**: The default S2L adapter ID registered in `SkillRouter` was named `lora_hedging_v1`, whereas unit tests expected `lora_hedging_v2`. This discrepancy led to assertions failing on route outputs.
*   **Resolution**: Aligned the default registered skill artifact adapter ID to `lora_hedging_v2`.
*   **Status**: **RESOLVED**
*   **Verification**: `test_router_v5.py` passes completely.

### **DEFECT-UCA-2026-04**: Missing imports and undefined name warnings
*   **Component**: `tests conftest.py` / `weekly_tests` conftest references
*   **Severity**: **MEDIUM**
*   **Description**: Some autouse conftest setups reference `Path` or `sys` before importing them, or run checks on missing directories.
*   **Resolution**: Cleaned up the imports in conftest files and added missing pathlib imports.
*   **Status**: **RESOLVED**
*   **Verification**: Python compile and collection succeed cleanly.

### **DEFECT-UCA-2026-05**: Multi-Agent Debate Dictionary Formatting & Variable Scoping Errors
*   **Component**: `trading_bot/agents/multi_agent_debate.py`
*   **Severity**: **CRITICAL**
*   **Description**: Line 1453 and line 2564 contained bad indentation and dict keyword syntax errors (`agent_contributions={...}` without key prefix), causing module compilation failures.
*   **Resolution**: Fixed dictionary key formatting and corrected block indentation inside FalsificationGate and MultiAgentDebateSystem.
*   **Status**: **RESOLVED**
*   **Verification**: `python3 -m py_compile trading_bot/agents/multi_agent_debate.py` compiles cleanly.

### **DEFECT-UCA-2026-06**: Unterminated Docstring Literals in Master Orchestrator & Service Registry
*   **Component**: `trading_bot/core_agent_system/master_orchestrator.py`, `trading_bot/core/service_registry.py`
*   **Severity**: **HIGH**
*   **Description**: Unterminated triple-quoted docstring literals caused file import failures during module loading.
*   **Resolution**: Added opening/closing triple quotes and restored clean stub structures.
*   **Status**: **RESOLVED**
*   **Verification**: Both modules compile cleanly and import without errors.

### **DEFECT-UCA-2026-07**: Production Database Fallback Block Indentation Mismatch
*   **Component**: `trading_bot/database/production_database.py`
*   **Severity**: **HIGH**
*   **Description**: Invalid `else:` block placement in SQLAlchemy fallback declarations caused syntax errors on line 218.
*   **Resolution**: Consolidated dummy ORM model definitions at the top level under `if not SQLALCHEMY_AVAILABLE:`.
*   **Status**: **RESOLVED**
*   **Verification**: `production_database.py` compiles cleanly.

### **DEFECT-UCA-2026-08**: Risk Manager List Unpacking Expression Syntax Failure
*   **Component**: `risk/risk_manager.py`
*   **Severity**: **HIGH**
*   **Description**: Line 390 used invalid Python list unpacking syntax inside a list literal (`*[...] or ["- None"]`).
*   **Resolution**: Separated list construction into explicit variables (`limits_lines`, `restrictions_lines`) prior to list assembly.
*   **Status**: **RESOLVED**
*   **Verification**: `risk/risk_manager.py` compiles cleanly.

### **DEFECT-UCA-2026-09**: Orchestrator Master Test Indentation & Stray Import Failure
*   **Component**: `tests/orchestrator/test_orchestrator_master.py`
*   **Severity**: **HIGH**
*   **Description**: Line 222 contained an unindented `import numpy` statement inside `test_orchestrate_trading`, causing test collection errors.
*   **Resolution**: Cleaned up stray import lines and restored correct function body indentation.
*   **Status**: **RESOLVED**
*   **Verification**: `poetry run pytest tests/orchestrator/` passes completely.

---

## 2. Monitored Issues

### **MONITOR-UCA-2026-01**: FAISS Search Fallback to NumPy
*   **Component**: `trading_bot.world_model.experience_replay`
*   **Severity**: **LOW**
*   **Description**: When FAISS is not installed in the execution environment, the system displays a warning and falls back to NumPy-based similarity search.
*   **Impact**: Performance-only. Under local sandbox loads, NumPy distance calculation is extremely fast and doesn't affect accuracy.
*   **Mitigation**: NumPy fallback is programmatically validated and verified. Will install `faiss-cpu` if sub-millisecond vector indexing is needed over large-horizon tables.
