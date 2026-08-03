# ISSUE_TRACKER.md

# AlphaAlgo Audit - Comprehensive Issue Tracker

This document tracks all 30+ production-grade issues discovered, prioritized, and fixed during the Production Engineering Audit.

---

## Issue Summary Matrix

| Issue ID | Subsystem | Severity | Category | Description | Status |
|---|---|---|---|---|---|
| **ISS-001** | Memory | Critical | Architecture | Fragmented dual-constructors in HMS (`memory.py`) | **FIXED** |
| **ISS-002** | Memory | High | Reliability | Missing `Tuple` import in HMS causing runtime failure | **FIXED** |
| **ISS-003** | Memory | Medium | Performance | `nx.MultiDiGraph` edge operations using incorrect key lookups | **FIXED** |
| **ISS-004** | Memory | High | Intelligence | Lack of task-driven edge pruning in SAGE graph | **FIXED** |
| **ISS-005** | Controller | Critical | Architecture | Double-initialization in CognitiveSystemController (CSC) | **FIXED** |
| **ISS-006** | Controller | High | Reliability | Undefined `FoldingOperator` causing `NameError` | **FIXED** |
| **ISS-007** | Controller | High | Concurrency | Thread-safety violations during CSC instantiation | **FIXED** |
| **ISS-008** | Controller | High | Performance | Unbounded `discrete_channel` and state buffers (memory leak) | **FIXED** |
| **ISS-009** | Controller | Medium | Maintainability| Hardcoded consensus threshold in CSC loop | **FIXED** |
| **ISS-010** | Controller | Medium | Intelligence | Unimplemented Pivot/Refine logic on verifier failure | **FIXED** |
| **ISS-011** | Event Bus | High | Reliability | Subscriber registration fails pre-start in UnifiedEventBus | **FIXED** |
| **ISS-012** | Event Bus | Medium | Performance | Blocking synchronous subscriber dispatches | **FIXED** |
| **ISS-013** | Router | Critical | Architecture | Duplicated `SkillRouter` classes in `router.py` | **FIXED** |
| **ISS-014** | Router | High | Concurrency | Thread safety missing in `SkillRouter` registry | **FIXED** |
| **ISS-015** | Router | Medium | Maintainability| Syntax error (unterminated string literal) in `router.py` | **FIXED** |
| **ISS-016** | Security | Critical | Security | Unsafe `eval` inside market analysis examples (RCE risk) | **FIXED** |
| **ISS-017** | Security | Critical | Security | Dangerous OS system call `rm -rf` inside helper scripts | **FIXED** |
| **ISS-018** | Security | High | Security | Unsecure `pickle` deserialization fallback in CacheManager | **FIXED** |
| **ISS-019** | Security | High | Security | Unsecured `pickle` fallback in APICache utility | **FIXED** |
| **ISS-020** | Swarm | Medium | Reliability | AttributeError (`ResearchLedgerEntry.get()`) in Verifier | **FIXED** |
| **ISS-021** | Evolution | High | Reliability | TypeError (`gain_threshold` parameter) in EvolutionGate | **FIXED** |
| **ISS-022** | Sandbox | Medium | Build | Missing execution packages (`psutil`, `networkx`, etc.) | **FIXED** |
| **ISS-023** | System | Low | Maintainability| Leftover fragmented or competing orchestrators | **FIXED** |
| **ISS-024** | Tests | Medium | Testing | Lack of high-concurrency stress test harness | **FIXED** |
| **ISS-025** | Tests | Medium | Testing | Absence of long-term memory leak / endurance checks | **FIXED** |
| **ISS-026** | Tests | Medium | Testing | Absence of decision reproducibility/replay validations | **FIXED** |
| **ISS-027** | Evolution | Low | Maintainability| Hardcoded validation benchmarks in EvolutionGate | **FIXED** |
| **ISS-028** | Memory | Low | Performance | Redundant dictionary-to-JSON serialization in HMS | **FIXED** |
| **ISS-029** | Logging | Low | Telemetry | Missing validation logs during EvolutionGate checks | **FIXED** |
| **ISS-030** | Controller | Low | Telemetry | Silenced verification warnings during Pivot/Refine loop | **FIXED** |

---

## Detailed Breakdown of Top 5 Issues

### ISS-001: Fragmented dual-constructors in HMS
- **Severity**: Critical
- **Files Affected**: `trading_bot/core/hms/memory.py`
- **Root Cause**: Two different `__init__` methods defined on the HierarchicalMemorySystem class. Python overrides the first definition, leaving half of the initialization state (e.g., `self.tiers`) completely undefined, causing system crashes on boot.
- **Solution**: Consolidated them into a single authoritative constructor, fully defining the 6 cognitive tiers.

### ISS-005: Double-initialization in CSC
- **Severity**: Critical
- **Files Affected**: `trading_bot/core/csc/controller.py`
- **Root Cause**: The singleton pattern implemented on the Cognitive System Controller lacked proper initialization locks, leading to the loop initializer being executed twice, resetting the internal channels.
- **Solution**: Enforced `_initialized` boolean states alongside thread-safe locking during instantiation.

### ISS-013: Duplicated `SkillRouter` classes
- **Severity**: Critical
- **Files Affected**: `trading_bot/core/csc/router.py`
- **Root Cause**: An accidental concatenation of a legacy SkillRouter definition and a new UCA-2026 definition occurred in the same module file.
- **Solution**: Streamlined the file by consolidating all routing and registration mechanics into a single, clean class.

### ISS-016: Unsafe `eval` inside market analysis
- **Severity**: Critical
- **Files Affected**: `examples/advanced_market_analysis_demo.py`
- **Root Cause**: Unsafe string evaluation using Python's standard `eval()` was being performed on unverified market data responses, presenting a massive remote code execution (RCE) vector.
- **Solution**: Substituted with safe abstract syntax tree literal parsing (`ast.literal_eval`).

### ISS-018: Unsecure `pickle` deserialization fallback
- **Severity**: High
- **Files Affected**: `persistence/cache.py`
- **Root Cause**: Cache values were falling back to unsafe `pickle.loads()` without schema/hash verification.
- **Solution**: Wrapped the deserializer to enforce JSON-first decoding, completely restricting pickle fallback options to verified internal domains only.
