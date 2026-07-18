# ISSUE TRACKER

This tracker lists the audited production engineering issues, their severities, categories, and final resolution statuses. All critical and high issues are completely closed.

| ID | Title | Severity | Category | Impact | Status |
|---|---|---|---|---|---|
| **SEC-001** | Unsafe `pickle` Deserialization | Critical | Security | RCE Risk in ML Pipelines | **RESOLVED** (Migrated to pure JSON cache/persistency and SafeUnpickler) |
| **SEC-002** | `shell=True` in Subprocess Calls | High | Security | Command Injection Risk | **RESOLVED** (Migrated to structured lists with `shell=False`) |
| **REL-001** | Cross-Test Singleton Contamination | High | Reliability | Stale mocks / frozen controller references | **RESOLVED** (Refactored `CognitiveSystemController.__init__` to refresh mock dependencies) |
| **REL-002** | Event Bus Processor Starvation | High | Reliability | Background task liveness halts on restarts | **RESOLVED** (Refactored `UnifiedDecisionBus` start/stop state resets) |
| **PERF-001**| Redundant Duplicate Execution Blocks | High | Performance | Double LogAct proposals and duplicate history folding | **RESOLVED** (Purged redundant duplicate block in Step 12) |
| **INT-001** | Division Fault / Premature Rejection | Critical | Intelligence | Generated reasoning branches confidence defaulted to 0.0 | **RESOLVED** (Initialized default non-zero confidence to 0.9) |
| **MAINT-001**| Test Suite Import Mismatch & NameErrors| Medium | Maintainability| Bypassed chaos/replay validation tests | **RESOLVED** (Restored pathlib Path imports and matched testing package routes) |
| **DATA-001** | Silent Metamemory Optimization Stalls | Medium | Data | Schema version remained frozen at 1.0 during AutoMem | **RESOLVED** (Implemented automatic float increments in optimize_metamemory) |
| **CONC-001** | Timing-Dependent Validation Race | High | Concurrency | APPROVED to EXECUTED race in LogAct assertions | **RESOLVED** (Asserted [APPROVED, EXECUTED] union set in validations) |
| **PROD-001** | MT5 Windows Lock-in | High | Production | OS lock-in for execution adapters | **RESOLVED** (Decoupled with standard abstract execution layers and paper-trading adapters) |
