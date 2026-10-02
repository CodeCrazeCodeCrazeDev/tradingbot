# AlphaAlgo Master Issue Tracker

| Issue ID | Category | Severity | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| ISS-001 | Risk Management | Critical | `PortfolioRiskManager.validate_trade` rejected valid trades due to absolute dollar position scaling | Fixed |
| ISS-002 | Risk Management | High | Single-asset concentration limit defaulted to restrictive 20% for 3-asset portfolios | Fixed |
| ISS-003 | Orchestration | High | Missing import `TradingDecision` in `test_orchestrator_integration.py` causing `NameError` | Fixed |
| ISS-004 | Orchestration | Medium | Uncached candidate opportunity predictions in `MasterOrchestrator.orchestrate_trading` | Fixed |
| ISS-005 | Connectors | Critical | Direct `import MetaTrader5` in `mt5_connector.py` causing import crashes on Linux/macOS | Fixed |
| ISS-006 | Dashboard | Critical | Unhandled top-level `import dash` in `performance_dashboard.py` crashing core brain singletons | Fixed |
| ISS-007 | Security | Critical | Dynamic `exec()` in `alpha_evolve_engine.py` without AST security validation | Fixed |
| ISS-008 | Security | Critical | Unsafe `eval()` calls in `examples/advanced_market_analysis_demo.py` | Fixed |
| ISS-009 | Performance | High | Blocking `requests.get` inside async `_fetch_from_newsapi` blocking event loop | Fixed |
| ISS-010 | Maintainability | Medium | Unresolved `import data_fetcher` in `ultimate_alphaalgo.py` | Fixed |
| ISS-011 | Concurrency | High | Unsynchronized singleton instantiation potential race in `UnifiedDecisionBus` | Fixed |
| ISS-012 | Intelligence | High | Zero-division potential in `HeadAI._calculate_position_size` when `risk_weight` is zero | Fixed |
| ISS-013 | System | High | Missing null-check for optional `psutil` dependency in `health_check.py` | Fixed |
| ISS-014 | Performance | Medium | Unvectorized orderbook heatmap construction in `VolumeDeltaHeatmap` | Fixed |
| ISS-015 | Maintainability | Low | Uncaught warnings in `task_scheduler` coroutines during test teardown | Fixed |
| ISS-016 | Maintainability | Low | Legacy script indentation and bare exception handling in operational scripts | Fixed |
| ISS-017 | ML | Medium | Missing fallback for optional sentiment analyzer dependencies | Fixed |
| ISS-018 | Intelligence | Medium | Unbounded epistemic variance penalty in Bayesian decision posterior calculations | Fixed |
| ISS-019 | Data | Low | Missing parquet export fallback in analytics data warehouse when `pyarrow` is absent | Fixed |
| ISS-020 | Data | Low | Unhandled socket resource cleanup on rapid health probing | Fixed |
| ISS-021 | Production | Medium | Unprotected thermal path check on containerized non-Linux environments | Fixed |
| ISS-022 | Security | High | Missing Fernet secret key fallback in credential vault module | Fixed |
| ISS-023 | Telemetry | Low | Lock contention in event logging dictionary updates | Fixed |
| ISS-024 | Maintainability | Low | Unhandled Markdown rendering exception when `markdown` package is missing | Fixed |
| ISS-025 | Orchestration | Medium | Redundant market data re-fetching across multi-agent debate rounds | Fixed |
| ISS-026 | Intelligence | Medium | Missing calibration fallback when calibrator model is uninitialized | Fixed |
| ISS-027 | Concurrency | Medium | Unawaited coroutine warnings in workflow manager event loops | Fixed |
| ISS-028 | Risk | Medium | Drawdown controller equity peak reset on system restart | Fixed |
| ISS-029 | ML | High | Non-deterministic RNG seeding in parallel strategy sandbox workers | Fixed |
| ISS-030 | Security | Critical | Dynamic code string execution without isolated scope restricted builtins | Fixed |
| ISS-031 | System | Medium | Missing connection pool shutdown hooks in timeseries database module | Fixed |
| ISS-032 | Documentation | Low | Incomplete paper traceability matrices across singletons | Fixed |
