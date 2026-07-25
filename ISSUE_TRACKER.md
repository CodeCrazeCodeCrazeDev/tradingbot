# ISSUE TRACKER

| ID | Title | Severity | Category | Impact | Status |
|---|---|---|---|---|---|
| SYN-001 | Broker Interface Syntax Error | Critical | Reliability | Syntax Failure | Resolved |
| SYN-002 | Binance Broker Indentation and dangling except | Critical | Reliability | Syntax Failure | Resolved |
| SYN-003 | Interactive Brokers Syntax Error | High | Reliability | Syntax Failure | Resolved |
| ARCH-001 | Data Layer Initializer Fragmentation | High | Architecture | Missing Imports | Resolved |
| ARCH-002 | Brain Layer Initializer NameError | High | Architecture | Missing Imports | Resolved |
| ARCH-003 | Directory Suffix and Space Artifacts | High | Architecture | Unimportable Root | Resolved |
| DATA-001 | Production Database NameError | Critical | Data | Load Failure | Resolved |
| PERF-001 | Optional Visualization Dependency Leak | Medium | Performance | Memory Load | Resolved |
| SEC-001 | Unsafe `pickle` Deserialization | Critical | Security | RCE Risk | Audited |
| SEC-002 | `shell=True` in Subprocess Calls | High | Security | Command Injection | Audited |
| SEC-003 | Hardcoded Credentials | High | Security | Credential Leak | Audited |
| REL-001 | Naked `except:` Blocks | Medium | Reliability | Silent Failures | Audited |
| REL-002 | Infinite Loops without Exit Signals | Medium | Reliability | Zombie Processes | Audited |
| PERF-002 | Blocking I/O in Async Context | High | Performance | Loop Starvation | Audited |
| INT-001 | "Delusion Loop" (Random Simulation) | Critical | Intelligence | Hallucinated Alpha | Audited |
| MAINT-001 | "God Class" / Massive Files | Low | Maintainability | Hard to Audit | Audited |
| MAINT-002 | Excessive Print Statements | Low | Maintainability | Log Pollution | Audited |
| PROD-001 | Windows-only MT5 Lock-in | High | Production | Deployment Limit | Audited |
| REL-003 | Missing Cleanup in Async Tasks | Medium | Reliability | Memory Leaks | Audited |
| SEC-004 | Unsafe `eval()` Usage | High | Security | Code Injection | Audited |
| ARCH-004 | Redundant Registry Implementations | Medium | Architecture | Confusion | Audited |
| DATA-002 | Missing Schema Validation | Medium | Data | Corruption Risk | Audited |
| PERF-003 | O(n^2) Data Processing Loops | Medium | Performance | Latency | Audited |
| MAINT-003 | Duplicated Logic in `_archive` | High | Maintainability | Confusion | Audited |
| INT-002 | Simulated Superintelligence Stubs | High | Intelligence | False Capability | Audited |
| CONC-001 | Race Conditions in Event Bus | High | Concurrency | Data Loss | Audited |
| SEC-005 | Weak Hashing / Insecure Randomness | Medium | Security | Crypto Risk | Audited |
| REL-004 | Inconsistent Error Recovery | Medium | Reliability | System Instability | Audited |
| PERF-004 | Redundant Model Loading | High | Performance | Memory Exhaustion | Audited |
| MAINT-004 | Magic Numbers in Risk Models | Medium | Maintainability | Untunable | Audited |
