# Issue Tracker

| Issue ID | Severity | Priority Rank | Status | Dependencies | Root Cause |
|----------|----------|---------------|--------|--------------|------------|
| RELI-03 | High | 1 | Pending | None | Committing unverified/unformatted code to production directories. |
| SEC-01 | Critical | 2 | Pending | None | Use of `pickle.loads()` on untrusted cache data. |
| SEC-02 | Critical | 3 | Pending | None | Use of `eval()` in simulation logic. |
| ARCH-01 | Critical | 4 | Pending | RELI-03 | Successive architecture overlays without decommissioning. |
| INTELL-01| Critical | 5 | Pending | ARCH-01 | RL reward signal grounded in noise instead of data. |
| RELI-01 | High | 6 | Pending | ARCH-01 | Improper use of `asyncio.run()` in library methods. |
| RELI-02 | High | 7 | Pending | ARCH-01 | Swallowing `ImportError` in critical paths. |
| SEC-03 | High | 8 | Pending | None | Command injection in `pipeline_approval.py`. |
| SEC-05 | High | 9 | Pending | None | Unsafe PyTorch model loading. |
| ARCH-05 | High | 10 | Pending | ARCH-01 | Fragmented development of execution layers. |
| MAINT-01 | High | 11 | Pending | ARCH-01 | 240+ subdirectories without a cleanup strategy. |
| ARCH-02 | High | 12 | Pending | ARCH-01 | Fragmented development of World Models. |
| ARCH-03 | High | 13 | Pending | ARCH-01 | No unified agent lifecycle management. |
| SEC-04 | High | 14 | Pending | None | MD5 collisions in high-volume systems. |
| TEST-01 | High | 15 | Pending | ARCH-01 | Test development lagging behind features. |
| PROD-01 | High | 16 | Pending | None | Platform-specific terminal commands in core logic. |
| RELI-06 | Medium | 17 | Pending | ARCH-01 | Use of generic `except Exception`. |
| RELI-07 | Medium | 18 | Pending | None | Missing `finally` blocks for DB connections. |
| ARCH-07 | Medium | 19 | Pending | ARCH-01 | Too many specialized registries. |
| PERF-01 | Medium | 20 | Pending | ARCH-01 | Redundant polling for market data. |
| PROD-02 | Medium | 21 | Pending | ARCH-07 | Missing distributed heartbeats. |
| RELI-04 | Medium | 22 | Pending | ARCH-04 | Unbounded memory growth in `MemorySystem`. |
| ARCH-04 | Medium | 23 | Pending | ARCH-01 | Memory system overlap between WM and IAS. |
| ARCH-06 | Medium | 24 | Pending | None | Conflicting config files. |
| RELI-05 | Medium | 25 | Pending | None | Hardcoded Redis dependency. |
| INTELL-02| Medium | 26 | Pending | ARCH-01 | Hardcoded reasoning traces. |
| PERF-02 | Medium | 27 | Pending | ARCH-01 | Unoptimized async polling loops. |
| ARCH-08 | Medium | 28 | Pending | ARCH-01 | Tight coupling between components. |
| PROD-03 | Medium | 29 | Pending | None | Broker-specific logic leakage. |
| RELI-08 | Medium | 30 | Pending | None | Redis key collisions in multi-instance setups. |
| MAINT-02 | Low | 31 | Pending | None | Archival bloat in the main repo. |

## Dependency Analysis
- **RELI-03 (Syntax Errors)** is the absolute first priority as it prevents the system from being correctly analyzed or tested by automated tools.
- **ARCH-01 (Orchestration Consolidation)** is the "Architectural Keystone". Most other issues (RELI-01, RELI-02, ARCH-05, etc.) are symptoms of the fragmented orchestration. Fixing ARCH-01 first simplifies the resolution of at least 15 other issues.
- **Security Issues (SEC-*)** are high priority but can be fixed in parallel or immediately after the Keystones.
- **INTELL-01 (Delusion Loop)** is a scientific priority; without fixing this, any "improvement" the bot makes is statistically invalid.

## Root Cause Mapping
1. **Pillar 1: Lack of Refactoring Discipline** -> Leads to ARCH-01, ARCH-05, MAINT-01, ARCH-03, ARCH-07.
2. **Pillar 2: Insufficient Secure Coding Standards** -> Leads to SEC-01, SEC-02, SEC-03, SEC-04, SEC-05.
3. **Pillar 3: Async Programming Misunderstandings** -> Leads to RELI-01, PERF-02.
4. **Pillar 4: Simulated vs Grounded Reality Gap** -> Leads to INTELL-01, INTELL-02.
