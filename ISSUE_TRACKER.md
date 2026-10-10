# AlphaAlgo Issue Tracker 2026

## Catalog of Verified Engineering Issues

| Issue ID | Severity | Subsystem | File Path | Technical Summary | Status |
|---|---|---|---|---|---|
| ISS-001 | High | CSC Core | `trading_bot/core/csc/controller.py` | Missing mandatory arXiv research paper citations in docstring | Resolved |
| ISS-002 | High | Testing | `tests/test_superior_architecture_minimal.py` | Non-affirmative mock shield voter format breaking LogAct consensus | Resolved |
| ISS-003 | Medium | Intel | `trading_bot/intel/news_pipeline.py` | Synchronous `requests.get` blocking async event loop | Resolved |
| ISS-004 | High | Adaptive Systems | `trading_bot/adaptive_systems/code_generation/code_generator.py` | Top-level unguarded import of optional package `gpt4all` | Resolved |
| ISS-005 | Medium | Risk Management | `trading_bot/orchestrator/risk_manager.py` | Portfolio risk scaling fallback when trade quantity > 1.0 | Resolved |
| ISS-006 | Medium | Orchestrator | `tests/orchestrator/test_orchestrator_integration.py` | Missing `TradingDecision` import causing test failure | Resolved |
| ISS-007 | High | Security | `trading_bot/aads/core/alpha_evolve_engine.py` | Direct unsandboxed `exec()` calls before AST validation | Resolved |
| ISS-008 | Medium | Examples | `examples/advanced_market_analysis_demo.py` | Unsafe `eval()` calls on raw strings | Resolved |
| ISS-009 | Low | Operational | `health_monitor.py` | Unguarded `psutil` imports in standalone status monitors | Resolved |
| ISS-010 | Low | Analysis | `monte_carlo.py` | Missing null check on optional `seaborn` visualization dependency | Resolved |
| ISS-011 | Medium | Realtime | `trading_bot/dashboard/realtime_dashboard.py` | Type annotation mismatch on `dash_bootstrap_components` | Resolved |
| ISS-012 | High | Concurrency | `trading_bot/neuros_evolution/plotcode_integration.py` | Sync `requests.post` inside async plot generation routine | Resolved |
| ISS-013 | Medium | Multi-Agent | `trading_bot/agents/multi_agent_debate.py` | Duplicate `DevilsAdvocate` class definition | Resolved |
| ISS-014 | Medium | Scripts | `scripts/deployment/deploy_5star_production.py` | Indentation error in try/except deployment block | Resolved |
| ISS-015 | Medium | Scripts | `scripts/launchers/run_comprehensive_system_test.py` | Blocking `time.sleep` in async sample function | Resolved |
| ISS-016 | Low | Utilities | `trading_bot/utils/api_rate_limiter.py` | Blocking `time.sleep` in async rate limiter wait loop | Resolved |
| ISS-017 | Low | Health Check | `scripts/comprehensive_health_check.py` | Silent exception swallowing in log scanner loops | Resolved |
| ISS-018 | Medium | AI Core | `trading_bot/ai_core/agents/__init__.py` | Skipped test suite due to missing agent factory exports | Resolved |
| ISS-019 | High | Verification | `tests/verification/test_e2e_decision_pipeline.py` | Mock shield voter return value mismatch with LogAct bus | Resolved |
| ISS-020 | Medium | Diagnostics | `scripts/fixes/auto_fix_critical_issues_v2.py` | Line iteration loop flaw on empty text blocks | Resolved |
| ISS-021 | Low | Launchers | `scripts/launchers/run_alphaalgo_5star.py` | Unhandled exception on missing environment variables | Resolved |
| ISS-022 | Low | Benchmarking | `scripts/run_benchmarks.py` | Unlogged exception swallowing during benchmark iteration | Resolved |
| ISS-023 | Low | Diagnostics | `scripts/full_system_audit.py` | Silent exception swallowing in TODO counter method | Resolved |
| ISS-024 | Medium | Deployment | `scripts/deploy_production.py` | Unhandled exception during secrets file validation | Resolved |
| ISS-025 | Low | Governance | `scripts/security_audit.py` | Silent exception swallowing in static scan helper | Resolved |
| ISS-026 | Medium | Validation | `scripts/validation/comprehensive_validation.py` | Blocking requests in async API connectivity validator | Resolved |
| ISS-027 | Low | Monitoring | `scripts/monitoring/check_real_prices.py` | Exception swallowing in price comparison routine | Resolved |
| ISS-028 | Medium | Launchers | `scripts/runners/run_deepseek_safe_24_7.py` | Blocking time.sleep inside async runner main function | Resolved |
| ISS-029 | Medium | Launchers | `scripts/runners/run_deepseek_elite_completion.py` | Blocking time.sleep inside async completion runner | Resolved |
| ISS-030 | High | Event Bus | `trading_bot/core/unified_event_bus.py` | Bus singleton initialization race condition under concurrency | Resolved |
