# ISSUE TRACKER

| ID | Title | Severity | Category | Impact | Status |
|---|---|---|---|---|---|
| SEC-001 | Unsafe `pickle` Deserialization | Critical | Security | RCE Risk | Resolved |
| SEC-002 | `shell=True` in Subprocess Calls | High | Security | Command Injection | Resolved |
| SEC-003 | Hardcoded Credentials | High | Security | Credential Leak | Resolved |
| REL-001 | Naked `except:` Blocks | Medium | Reliability | Silent Failures | Resolved |
| REL-002 | Infinite Loops without Exit Signals | Medium | Reliability | Zombie Processes | Resolved |
| PERF-001 | Blocking I/O in Async Context | High | Performance | Loop Starvation | Resolved |
| ARCH-001 | Competing Orchestrators | High | Architecture | Split-Brain Decisions | Resolved |
| ARCH-002 | Circular Dependency Workarounds | Medium | Architecture | Technical Debt | Resolved |
| INT-001 | "Delusion Loop" (Random Simulation) | Critical | Intelligence | Hallucinated Alpha | Resolved |
| MAINT-001 | "God Class" / Massive Files | Low | Maintainability | Hard to Audit | Resolved |
| MAINT-002 | Excessive Print Statements | Low | Maintainability | Log Pollution | Resolved |
| PROD-001 | Windows-only MT5 Lock-in | High | Production | Deployment Limit | Resolved |
| REL-003 | Missing Cleanup in Async Tasks | Medium | Reliability | Memory Leaks | Resolved |
| SEC-004 | Unsafe `eval()` Usage | High | Security | Code Injection | Resolved |
| ARCH-003 | Redundant Registry Implementations | Medium | Architecture | Confusion | Resolved |
| DATA-001 | Missing Schema Validation | Medium | Data | Corruption Risk | Resolved |
| PERF-002 | O(n^2) Data Processing Loops | Medium | Performance | Latency | Resolved |
| MAINT-003 | Duplicated Logic in `_archive` | High | Maintainability | Confusion | Resolved |
| INT-002 | Simulated Superintelligence Stubs | High | Intelligence | False Capability | Resolved |
| CONC-001 | Race Conditions in Event Bus | High | Concurrency | Data Loss | Resolved |
| SEC-005 | Weak Hashing / Insecure Randomness | Medium | Security | Crypto Risk | Resolved |
| REL-004 | Inconsistent Error Recovery | Medium | Reliability | System Instability | Resolved |
| PERF-003 | Redundant Model Loading | High | Performance | Memory Exhaustion | Resolved |
| ARCH-004 | Excessive Coupling in Core | High | Architecture | Rigidity | Resolved |
| MAINT-004 | Magic Numbers in Risk Models | Medium | Maintainability | Untunable | Resolved |
| DATA-002 | Stale Data in Cache | Medium | Data | Bad Decisions | Resolved |
| PROD-002 | Missing Configuration Validation | Medium | Production | Startup Failure | Resolved |
| REL-005 | Retry Failures in Network Calls | Medium | Reliability | Data Gaps | Resolved |
| ARCH-005 | God Module `trading_bot/core/__init__.py` | Medium | Architecture | Performance | Resolved |
| MAINT-005 | Missing Docstrings in Core APIs | Low | Maintainability | Onboarding | Resolved |
