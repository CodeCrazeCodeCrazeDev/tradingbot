# ISSUE TRACKER - POST-AUDIT (COMPLETED JULY 2026)

| ID | Title | Severity | Category | Status |
|---|---|---|---|---|
| SEC-001 | Unsafe `pickle` Deserialization | Critical | Security | RESOLVED |
| SEC-002 | `shell=True` in Subprocess Calls | High | Security | RESOLVED |
| SEC-003 | Hardcoded Credentials | High | Security | RESOLVED |
| SEC-004 | Unsafe `eval()` Usage | High | Security | RESOLVED |
| SEC-005 | Insecure Randomness for Quant | Medium | Security | RESOLVED |
| SEC-006 | Credential Exposure in Compose | High | Security | RESOLVED |
| REL-001 | Naked `except:` Blocks | Medium | Reliability | RESOLVED |
| REL-002 | Signal Safety in Main Loop | Medium | Reliability | RESOLVED |
| REL-003 | Async Task Resource Cleanup | Medium | Reliability | RESOLVED |
| REL-004 | Inconsistent Error Recovery | Medium | Reliability | IMPROVED |
| REL-005 | Network Retry Failures | Medium | Reliability | RESOLVED |
| PERF-001 | Blocking I/O in Async Context | High | Performance | RESOLVED |
| PERF-002 | O(n^2) Data Processing Loops | Medium | Performance | RESOLVED |
| PERF-003 | Redundant Model Loading | High | Performance | RESOLVED |
| PERF-004 | Blocking `time.sleep` in Async Latency Benchmark | High | Performance | RESOLVED |
| DATA-001 | Missing Schema Validation | Medium | Data | RESOLVED |
| DATA-002 | Stale Data in Cache | Medium | Data | RESOLVED |
| ARCH-001 | Competing Orchestrators | High | Architecture | RESOLVED |
| ARCH-002 | Circular Dependencies | Medium | Architecture | RESOLVED |
| ARCH-004 | Excessive Coupling in Core | High | Architecture | RESOLVED |
| ARCH-005 | God Module `core/__init__.py` | Medium | Architecture | RESOLVED |
| ARCH-006 | Duplicate `aamis_v3` System | Low | Architecture | RESOLVED |
| INT-001 | "Delusion Loop" (Reality Gate) | Critical | Intelligence | RESOLVED |
| INT-002 | Simulated Superintelligence Stubs | High | Intelligence | RESOLVED |
| PROD-001 | Windows-only MT5 Lock-in | High | Production | RESOLVED |
| PROD-002 | Configuration Validation | Medium | Production | VERIFIED |
| MAINT-001 | "God Class" / Massive Legacy File | Low | Maintainability | RESOLVED |
| MAINT-002 | Excessive Print Statements | Low | Maintainability | RESOLVED |
| MAINT-003 | Duplicated Logic in `_archive` | High | Maintainability | ARCHIVED |
| MAINT-004 | Magic Numbers in Risk Models | Medium | Maintainability | RESOLVED |
| MAINT-005 | Missing Docstrings in Core APIs | Low | Maintainability | RESOLVED |
| SYN-001 | Syntax and duplicate stub definitions in `trading_bot/data/__init__.py` | Critical | Maintainability | RESOLVED |
| SYN-002 | Unterminated triple quotes in `trading_bot/data/mt5.py` | Critical | Maintainability | RESOLVED |
| SYN-003 | Unterminated triple quotes in `trading_bot/data/validate.py` | Critical | Maintainability | RESOLVED |
| SYN-004 | Syntax unclosed triple quote block in `trading_bot/core/csc/router.py` | Critical | Maintainability | RESOLVED |
| SYN-005 | Repeated Keyword Argument `confidence` in `trading_bot/core/csc/hypothesis.py` | Critical | Maintainability | RESOLVED |
| REL-006 | `UnboundLocalError` local variable name conflict in `tests/uca_v5/test_csc_v5.py` | High | Reliability | RESOLVED |

---

## Detailed Audit Specifications for New & Verified Issues

### SYN-001 to SYN-005: Compiler-Blocking Syntax Errors
- **Reproduction steps**: Attempting to run `poetry run pytest` resulted in multiple compilation crashes preventing any test execution.
- **Root cause**: Merged file fragments containing raw unresolved string boundaries, repeated constructor params (`confidence`), and stray legacy stub blocks.
- **Affected components**: `trading_bot/data/`, `trading_bot/core/csc/hypothesis.py`, `trading_bot/core/csc/router.py`.
- **Architectural impact**: Blocked all continuous integration pipelines and static analysis tools.
- **Production impact**: Prevents production deployment and system launch.
- **Proposed solution**: Cleanly refactor the stubs and resolve the unclosed boundaries.
- **Implemented solution**: Restored and validated the clean, authoritative interface contracts from the UCA stable branch.
- **Verification evidence**: Python syntax compiler test passes on all target directories.
- **Remaining risks**: None.

### REL-006: Local Name Shadowing in Test Suite
- **Reproduction steps**: Run `poetry run pytest tests/uca_v5/test_csc_v5.py`.
- **Root cause**: Shorthand local `from ... import decision_bus` inside `test_csc_pivot_loop` shadowed the global `decision_bus` accessed at the function start.
- **Affected components**: `tests/uca_v5/test_csc_v5.py`.
- **Architectural impact**: Led to runtime test execution failures.
- **Production impact**: False negatives in verification pipelines.
- **Proposed solution**: Remove local scope duplicate imports.
- **Implemented solution**: Cleaned up the function import scoping.
- **Verification evidence**: Test runs 100% clean and green.
- **Remaining risks**: None.

### PERF-004: Blocking Async Event Loop via Synchronous sleep
- **Reproduction steps**: Run static audit scan or execute validation.
- **Root cause**: Use of synchronous `time.sleep` blocking the single-threaded asyncio event loop inside the latency benchmark function.
- **Affected components**: `trading_bot/core/validation.py`.
- **Architectural impact**: Stops other running concurrent coroutines, creating lock contention and timeout regressions.
- **Production impact**: Slows down performance to 10+ ms per step.
- **Proposed solution**: Replace with asynchronous non-blocking wait.
- **Implemented solution**: Replaced `time.sleep` with `await asyncio.sleep`.
- **Verification evidence**: High-resolution latency benchmarking runs successfully.
- **Remaining risks**: None.
