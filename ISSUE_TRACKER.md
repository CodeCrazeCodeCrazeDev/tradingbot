# ISSUE TRACKER — Complete Audit Defect Ledger 2026

| Issue ID | Severity | Category | Root Cause File | Brief Description | Remediation Status |
|---|---|---|---|---|---|
| **ISS-001** | High | Concurrency | `trading_bot/intel/news_pipeline.py` | Blocking `requests.get` call in `_fetch_from_newsapi` inside async function | RESOLVED |
| **ISS-002** | High | Concurrency | `trading_bot/neuros_evolution/plotcode_integration.py` | Blocking `requests.post` call in `_execute_plotcode_test` inside async function | RESOLVED |
| **ISS-003** | Critical | Security | `examples/advanced_market_analysis_demo.py` | Unsafe `eval()` calls in Dash callback rendering routines | RESOLVED |
| **ISS-004** | Critical | Security | `trading_bot/aads/core/alpha_evolve_engine.py` | Direct `exec()` invocation without AST security validation | RESOLVED |
| **ISS-005** | High | Security | `trading_bot/core/security/sandbox.py` | Direct `exec()` call inside worker process missing pre-AST check | RESOLVED |
| **ISS-006** | Critical | Testing | `tests/test_superior_architecture_minimal.py` | Mock shield voter missing `audit_log_action` causing pipeline trade rejection | RESOLVED |
| **ISS-007** | High | Testing | `tests/orchestrator/test_orchestrator_integration.py` | Missing `TradingDecision` import in `TestMLToExecutionFlow` | RESOLVED |
| **ISS-008** | High | Risk Management | `trading_bot/orchestrator/risk_manager.py` | Position risk calculation unscaled for trades with size > 1.0 | RESOLVED |
| **ISS-009** | Medium | Risk Management | `trading_bot/orchestrator/risk_manager.py` | Zero division fallback in `_calculate_new_concentration` when capital is zero | RESOLVED |
| **ISS-010** | High | Architecture | `trading_bot/agents/multi_agent_debate.py` | Duplicate `DevilsAdvocate` class definition | RESOLVED |
| **ISS-011** | High | Concurrency | `trading_bot/core/unified_event_bus.py` | Non-thread-safe `__new__` singleton initialization in `UnifiedDecisionBus` | RESOLVED |
| **ISS-012** | Medium | Performance | `trading_bot/indicators/advanced_liquidity.py` | Unvectorized nested loop in `VolumeDeltaHeatmap.create_heatmap` | RESOLVED |
| **ISS-013** | Medium | Concurrency | `scripts/validation/comprehensive_validation.py` | Blocking `requests` call inside async function | RESOLVED |
| **ISS-014** | Medium | Concurrency | `scripts/launchers/run_comprehensive_system_test.py` | Blocking `time.sleep` call inside async routine | RESOLVED |
| **ISS-015** | Medium | Concurrency | `scripts/runners/run_deepseek_safe_24_7.py` | Blocking `time.sleep` call inside async runner loop | RESOLVED |
| **ISS-016** | Medium | Security | `tests/security/test_safe_eval.py` | Direct `eval()` invocation in safe eval tests | RESOLVED |
| **ISS-017** | Low | Reliability | `scripts/full_system_audit.py` | Silent exception swallowing in file auditing | RESOLVED |
| **ISS-018** | Low | Reliability | `scripts/security_audit.py` | Bare `except:` catch block swallowing operational errors | RESOLVED |
| **ISS-019** | Low | Reliability | `scripts/monitoring/check_alphaalgo_status.py` | Bare `except:` catch block in status reporting | RESOLVED |
| **ISS-020** | Medium | AI Core | `trading_bot/ai_core/agents/__init__.py` | Unexported agent components in AI core module | RESOLVED |
| **ISS-021** | High | Reliability | `trading_bot/intel/news_pipeline.py` | Missing NaN date parsing check in RSS feed handler | RESOLVED |
| **ISS-022** | Medium | Production | `trading_bot/neuros_evolution/plotcode_integration.py` | Hardcoded localhost port fallback in Selenium driver setup | RESOLVED |
| **ISS-023** | Low | Maintainability | `trading_bot/indicators/advanced_liquidity.py` | Unused import alias `numpy` in advanced liquidity | RESOLVED |
| **ISS-024** | High | Security | `tests/run_system_imports.py` | Direct `exec()` without AST sandboxing during dynamic import checks | RESOLVED |
| **ISS-025** | Medium | Reliability | `scripts/launchers/thinking_bot.py` | Bare `except:` block in process cleanup routines | RESOLVED |
| **ISS-026** | Medium | Reliability | `scripts/runners/run_deepseek_comprehensive.py` | Blocking `time.sleep` inside async runner loop | RESOLVED |
| **ISS-027** | Medium | Concurrency | `scripts/runners/run_deepseek_autonomous_24_7.py` | Blocking `time.sleep` inside async runner loop | RESOLVED |
| **ISS-028** | Medium | Concurrency | `scripts/runners/run_deepseek_evolution.py` | Blocking `time.sleep` inside async runner loop | RESOLVED |
| **ISS-029** | Low | Reliability | `scripts/utilities/watchdog.py` | Silent exception swallowing in watchdog loop | RESOLVED |
| **ISS-030** | Low | Reliability | `scripts/utilities/autonomous_operator.py` | Silent exception swallowing in operator status check | RESOLVED |
| **ISS-031** | High | Concurrency | `trading_bot/core/unified_event_bus.py` | Potential event loop queue mismatch during loop restarts | RESOLVED |
| **ISS-032** | Critical | Testing | `tests/orchestrator/test_agent_orchestrator.py` | String format KeyError during orchestrator test setup | RESOLVED |
| **ISS-033** | High | Architecture | `trading_bot/orchestrator/agent_orchestrator.py` | Missing orchestrator factory helper export | RESOLVED |
| **ISS-034** | Medium | Security | `trading_bot/core/security/sandbox.py` | Missing AST validation before compiling strategy string | RESOLVED |
| **ISS-035** | High | Risk Management | `risk/risk_manager.py` | Syntax error in parenthesized list comprehension unpacking | RESOLVED |
