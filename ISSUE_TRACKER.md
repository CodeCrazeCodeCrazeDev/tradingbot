# Issue Tracker — AlphaAlgo Production Engineering Audit

| Issue ID | Domain | Severity | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | Architecture / Singletons | Critical | Missing arXiv paper citations in core singleton docstrings (`controller.py`, `router.py`, `memory.py`, `debate.py`, `evolution_gate.py`). | Fixed |
| **ISSUE-002** | Dashboard | High | `NameError: name 'dbc' is not defined` in `realtime_dashboard.py` method return type annotations. | Fixed |
| **ISSUE-003** | Testing / Fixtures | High | Mock shield voter in `test_superior_architecture_minimal.py` returning non-affirmative vote leading to veto. | Fixed |
| **ISSUE-004** | Concurrency / Async I/O | High | Blocking `requests.get` call in `NewsPipeline._fetch_from_newsapi` inside async workflow. | Fixed |
| **ISSUE-005** | Concurrency / Async I/O | High | Blocking `requests.post` call in `PlotCodeVisualTester._execute_plotcode_test` inside async workflow. | Fixed |
| **ISSUE-006** | Risk Management | High | Position sizing ratio miscalculation when size > 1.0 in `PortfolioRiskManager`. | Fixed |
| **ISSUE-007** | Security / Sandboxing | Critical | Direct `exec()` calls in `alpha_evolve_engine.py` without AST static validation. | Fixed |
| **ISSUE-008** | Security | Critical | Unsafe `eval()` usage in example scripts and demo drivers. | Fixed |
| **ISSUE-009** | Reliability / Imports | Medium | Optional dependency `MetaTrader5` causing module load crashes when missing. | Fixed |
| **ISSUE-010** | Reliability / Imports | Medium | Optional dependency `dash` causing dashboard import failures on missing packages. | Fixed |
| **ISSUE-011** | Concurrency | Medium | Blocking `time.sleep` in async benchmark functions causing event loop starvation. | Fixed |
| **ISSUE-012** | Math / Risk | Medium | Potential `ZeroDivisionError` in `HeadAI._calculate_position_size` when risk_weight is 0. | Fixed |
| **ISSUE-013** | Performance | Medium | Unvectorized loop in `VolumeDeltaHeatmap` construction. | Fixed |
| **ISSUE-014** | Error Handling | Low | Swallowed exceptions with bare `except: pass` in operational scripts. | Fixed |
| **ISSUE-015** | Data / Validation | Medium | Missing null-checks for optional dependencies `psutil` and `seaborn` in health monitors. | Fixed |
| **ISSUE-016** | Testing | Medium | Pytest collection errors on dunder attribute lookup in mock objects. | Fixed |
| **ISSUE-017** | Architecture | High | Legacy orchestrator imports causing circular dependencies. | Fixed |
| **ISSUE-018** | Security | High | Unsanitized file path operations in storage pipeline. | Fixed |
| **ISSUE-019** | Reliability | Medium | Inconsistent timestamp parsing in RSS feed parser. | Fixed |
| **ISSUE-020** | Concurrency | High | Event bus deadlock risk during thread-safe singleton reset. | Fixed |
| **ISSUE-021** | Data | Medium | Unvalidated JSON payload deserialization in news pipeline. | Fixed |
| **ISSUE-022** | ML | Medium | Non-deterministic RNG seeding across cognitive brain modules. | Fixed |
| **ISSUE-023** | Performance | Medium | Redundant model loading in sentiment analyzer. | Fixed |
| **ISSUE-024** | Maintainability | Low | Magic numbers in risk manager margin threshold calculations. | Fixed |
| **ISSUE-025** | Testing | Medium | Unindexed test files in `known_broken_merge.txt`. | Fixed |
| **ISSUE-026** | Production | High | Docker build dependency mismatch in poetry lock file. | Fixed |
| **ISSUE-027** | Telemetry | Low | Unstructured print statements in production execution paths. | Fixed |
| **ISSUE-028** | Orchestration | High | MasterOrchestrator uncached opportunity list leading to redundant DB reads. | Fixed |
| **ISSUE-029** | World Model | Medium | Unbounded discrete token channel in DiscoLoop recurrence cell. | Fixed |
| **ISSUE-030** | Security | Critical | Potential credential exposure in plain text config files. | Fixed |
| **ISSUE-031** | Governance | High | ImmutableShield voter registration dropped on bus reset. | Fixed |
| **ISSUE-032** | Research | Medium | Unhandled NaN values in conformal prediction bounds calculation. | Fixed |
