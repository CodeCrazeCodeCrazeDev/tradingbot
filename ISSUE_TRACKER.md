# AlphaAlgo Issue Tracker (2026 Production Audit)

| Issue ID | Category | Severity | Root Cause | Affected File(s) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | Syntax / Parsing | Critical | Parenthesized list comprehension unpacking error in risk manager | `risk/risk_manager.py` | Fixed |
| **ISSUE-002** | Security | Critical | Dynamic execution of unvalidated code string via `exec()` in backtesting | `trading_bot/distributed/parallel_backtester.py` | Fixed |
| **ISSUE-003** | Concurrency | High | Blocking `time.sleep(0.01)` inside async `benchmark_latency()` | `trading_bot/core/validation.py` | Fixed |
| **ISSUE-004** | Error Handling | High | Swallowed exception handlers and scoping errors during component init | `trading_bot/ultimate_production/core_engine.py` | Fixed |
| **ISSUE-005** | Test Framework | High | Pytest/Hypothesis collection failure from dunder attribute lookup | `tests/test_superior_architecture_minimal.py` | Fixed |
| **ISSUE-006** | Orchestration | High | Missing orchestrator modules in active `trading_bot/orchestrator/` | `trading_bot/orchestrator/` | Fixed |
| **ISSUE-007** | Syntax / Parsing | High | Unexpected indentation in production deployment script | `scripts/deployment/deploy_5star_production.py` | Fixed |
| **ISSUE-008** | Syntax / Parsing | High | Unexpected indentation in automated fix script | `scripts/fixes/auto_fix_critical_issues_v2.py` | Fixed |
| **ISSUE-009** | Syntax / Parsing | High | Unexpected indentation in 5-star operational launcher | `scripts/launchers/run_alphaalgo_5star.py` | Fixed |
| **ISSUE-010** | Orchestration | Medium | IndentationError in master orchestrator async test | `tests/orchestrator/test_orchestrator_master.py` | Fixed |
| **ISSUE-011** | Orchestration | Medium | Syntax indentation errors in standalone orchestrator test | `tests/orchestrator/test_orchestrator_standalone.py` | Fixed |
| **ISSUE-012** | Orchestration | Medium | Syntax indentation errors in performance tracker test | `tests/orchestrator/test_orchestrator_performance.py` | Fixed |
| **ISSUE-013** | Orchestration | Medium | Syntax indentation errors in ML predictor test | `tests/orchestrator/test_orchestrator_ml_predictor.py` | Fixed |
| **ISSUE-014** | Agent Architecture | Medium | Missing thought tokens field in debate agent argument dataclass | `trading_bot/agents/multi_agent_debate.py` | Fixed |
| **ISSUE-015** | Mathematics | Medium | Potential ZeroDivisionError in HeadAI position size calculation | `trading_bot/agents/multi_agent_debate.py` | Fixed |
| **ISSUE-016** | Performance | Medium | Unvectorized liquidity calculation loop in advanced liquidity | `trading_bot/indicators/advanced_liquidity.py` | Fixed |
| **ISSUE-017** | Data / Caching | Low | Lack of `.gitignore` entries for `.hypothesis` test cache artifacts | `.gitignore` | Fixed |
| **ISSUE-018** | Imports | Low | Missing package exports in `trading_bot/ai_core/agents/__init__.py` | `trading_bot/ai_core/agents/__init__.py` | Fixed |
| **ISSUE-019** | Error Handling | Medium | Silent exception swallowing in unified AI brain analysis methods | `trading_bot/unified_ai_brain.py` | Fixed |
| **ISSUE-020** | Error Handling | Medium | Unhandled exceptions in layer 1 data foundation fetch loop | `trading_bot/unified_architecture/layer1_data_foundation.py` | Fixed |
| **ISSUE-021** | Concurrency | Medium | Unawaited coroutine tasks in workflow manager lifecycle | `trading_bot/orchestrator/workflow_manager.py` | Fixed |
| **ISSUE-022** | Concurrency | Medium | Unawaited coroutine tasks in task scheduler initialization | `trading_bot/orchestrator/task_scheduler.py` | Fixed |
| **ISSUE-023** | Error Handling | Low | Silent exception swallowing in unicode fix utility | `trading_bot/unicode_fix.py` | Fixed |
| **ISSUE-024** | Error Handling | Medium | Swallowed exception handlers in decision verification chain | `trading_bot/verification/decision_verification_chain.py` | Fixed |
| **ISSUE-025** | Error Handling | Low | Swallowed exception handlers in approval system init | `trading_bot/ultimate_approval/approval_system.py` | Fixed |
| **ISSUE-026** | Error Handling | Low | Swallowed exception handlers in notification system stop method | `trading_bot/unified_approval/notification_system.py` | Fixed |
| **ISSUE-027** | Error Handling | Medium | Bare pass blocks in data upgrade processors | `trading_bot/upgrades/data_upgrades_301_350.py` | Fixed |
| **ISSUE-028** | Error Handling | Medium | Bare pass blocks in signal upgrade generators | `trading_bot/upgrades/signal_upgrades_501_550.py` | Fixed |
| **ISSUE-029** | Data | Medium | Unhandled cycle break edge case in causal world model | `trading_bot/world_model/causal_model.py` | Fixed |
| **ISSUE-030** | Hardware | Low | Swallowed exception in hardware optimizer detection | `trading_bot/ultimate_system/hardware_optimizer.py` | Fixed |
| **ISSUE-031** | Orchestration | High | Uncached opportunity lookup in master orchestrator | `trading_bot/orchestrator/master_orchestrator.py` | Fixed |
| **ISSUE-032** | Risk | Medium | Scaling factor division error in position risk fraction | `risk/risk_manager.py` | Fixed |
| **ISSUE-033** | Risk | Medium | Sortino ratio zero downside returns handling gap | `trading_bot/orchestrator/performance_tracker.py` | Fixed |
| **ISSUE-034** | Test Suite | Medium | Missing path import causing NameError during test collection | `tests/orchestrator/test_agent_orchestrator.py` | Fixed |
| **ISSUE-035** | Operational | High | Indentation error in autonomous operator loop script | `scripts/launchers/alphaalgo_autonomous_operator.py` | Fixed |
| **ISSUE-036** | Security | High | Unsanitized file path input in data feed ingestion | `trading_bot/data_feeds/csv_feed.py` | Fixed |
