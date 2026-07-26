# ISSUE TRACKER - AlphaAlgo Production Audit

This document tracks all 30+ engineering-significant issues, their classifications, files affected, and resolved status.

| Issue ID | Severity | Category | Description | Files Affected | Status |
|---|---|---|---|---|---|
| **SEC-001** | Critical | Security | Unsafe Deserialization via `pickle.load` | `model_registry.py` | Resolved |
| **SEC-002** | High | Security | Command Injection via `shell=True` | `legacy_orchestrators.py` | Resolved |
| **SEC-003** | High | Security | Unsafe Evaluation via `eval()` | `safe_eval.py`, `code_evolver.py` | Resolved |
| **SEC-004** | Medium | Security | Clear-text API tokens exposed in logs | `logging_config.py` | Resolved |
| **SEC-005** | Medium | Security | Weak Hashing / Insecure Randomness | `secrets` overrides | Resolved |
| **REL-001** | Critical | Reliability | MagicMock TypeError in csc process | `tests/uca_v5/test_csc_v5.py` | Resolved |
| **REL-002** | High | Reliability | Missing required `trade_id` on `CoreDecision` | `trading_bot/core/csc/controller.py` | Resolved |
| **REL-003** | High | Reliability | Redundant duplicate un-awaited LogActions | `trading_bot/core/csc/controller.py` | Resolved |
| **REL-004** | High | Reliability | Inconsistent exception recovery in Event Bus | `trading_bot/core/unified_event_bus.py` | Resolved |
| **REL-005** | Medium | Reliability | Naked `except:` blocks in Network Calls | `api_client.py` | Resolved |
| **REL-006** | Medium | Reliability | Missing cleanup of async background tasks | `module_registry.py` | Resolved |
| **REL-007** | Medium | Reliability | Infinite retry loops on rate limits | `rate_limiter.py` | Resolved |
| **PERF-001** | High | Performance | Blocking File I/O inside graph storage | `trading_bot/core/hms/memory.py` | Resolved |
| **PERF-002** | Medium | Performance | O(n^2) unindexed memory searches | `experience_replay.py` | Resolved |
| **PERF-003** | High | Performance | Redundant strategy parameter checkpoint loads | `module_registry.py` | Resolved |
| **PERF-004** | Low | Performance | High GC allocations in active inference loop | `controller.py` | Resolved |
| **PERF-005** | Medium | Performance | Slow startup via un-deferred plotting imports | `elite_brain.py` | Resolved |
| **PERF-006** | Medium | Performance | High priority queue latency jitter | `unified_event_bus.py` | Resolved |
| **ARCH-001** | High | Architecture | Competing constructors in `EvolutionGate` | `evolution_gate.py` | Resolved |
| **ARCH-002** | High | Architecture | Inconsistent SkillRouter Routing return shapes | `trading_bot/core/csc/router.py` | Resolved |
| **ARCH-003** | Medium | Architecture | Redundant competed Registries | `unified_registry.py` | Resolved |
| **ARCH-004** | Medium | Architecture | Circular inline imports between HMS and CSC | `controller.py`, `memory.py` | Resolved |
| **ARCH-005** | Low | Architecture | Legacy scripts running raw system code on import| `tests/research/*` | Resolved |
| **ARCH-006** | Medium | Architecture | Hardcoded dynamic leverage risk limits | `acpe.py`, `controller.py` | Resolved |
| **INT-001** | Critical | Intelligence | Delusion Loops in World Model | `world_model.py` | Resolved |
| **INT-002** | High | Intelligence | Zero default confidence in generated branches | `trading_bot/core/csc/hypothesis.py` | Resolved |
| **INT-003** | High | Intelligence | Volatility guardrail lookup bypass | `trading_bot/core/csc/controller.py` | Resolved |
| **INT-004** | Medium | Intelligence | Hallucinated target parameters on regime shift | `controller.py` | Resolved |
| **MAINT-001**| Medium | Maintainability| Inconsistent spelling in task routing | `trading_bot/core/csc/router.py` | Resolved |
| **MAINT-002**| Medium | Maintainability| NameError in Free Research and Innovation tests | `tests/research/*` | Resolved |
| **DATA-001** | High | Data | Missing Schema Versioning on persistent memories| `trading_bot/core/hms/memory.py` | Resolved |
| **DATA-002** | Medium | Data | Stale data caching in order flow evaluations | `rate_limiter.py` | Resolved |
