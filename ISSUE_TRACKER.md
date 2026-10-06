# AlphaAlgo Production Engineering Audit — Issue Tracker

This issue tracker catalogs all **35 verified production engineering defects** discovered during the codebase-wide audit.

| Issue ID | Severity | Category | Affected File(s) | Description | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | Critical | Architecture | `trading_bot/core/csc/controller.py` | CognitiveSystemController docstring missing mandatory arXiv paper citations | RESOLVED |
| **ISSUE-002** | Critical | Security | `trading_bot/aads/core/alpha_evolve_engine.py` | Unsafe `exec()` execution on generated code without AST sandboxing | RESOLVED |
| **ISSUE-003** | Critical | Reliability | `trading_bot/orchestrator/risk_manager.py` | Position size > 1.0 treated as risk ratio, rejecting valid dollar-sized trades | RESOLVED |
| **ISSUE-004** | High | Testing | `tests/orchestrator/test_orchestrator_integration.py` | `NameError: TradingDecision` in `test_predict_and_execute_flow` | RESOLVED |
| **ISSUE-005** | High | Concurrency | `trading_bot/intel/news_pipeline.py` | Synchronous `requests.get` inside async function blocking event loop | RESOLVED |
| **ISSUE-006** | High | Concurrency | `trading_bot/neuros_evolution/plotcode_integration.py` | Synchronous `requests.post` inside async function blocking event loop | RESOLVED |
| **ISSUE-007** | High | Security | `examples/advanced_market_analysis_demo.py` | Unsafe `eval()` used for parameter parsing instead of `ast.literal_eval()` | RESOLVED |
| **ISSUE-008** | Medium | Reliability | `trading_bot/orchestrator/risk_manager.py` | Default `max_concentration` set too low (0.2), causing trade rejection | RESOLVED |
| **ISSUE-009** | Medium | Architecture | `trading_bot/agents/multi_agent_debate.py` | Duplicate `DevilsAdvocate` class definition causing name collision | RESOLVED |
| **ISSUE-010** | High | Concurrency | `trading_bot/core/unified_event_bus.py` | `UnifiedDecisionBus.__new__` non-thread-safe initialization race condition | RESOLVED |
| **ISSUE-011** | Medium | Concurrency | `scripts/runners/run_deepseek_safe_24_7.py` | Blocking `time.sleep` inside async `main()` | RESOLVED |
| **ISSUE-012** | Medium | Concurrency | `scripts/runners/run_deepseek_elite_completion.py` | Blocking `time.sleep` inside async `main()` | RESOLVED |
| **ISSUE-013** | Medium | Concurrency | `scripts/runners/run_deepseek_comprehensive.py` | Blocking `time.sleep` inside async `main()` | RESOLVED |
| **ISSUE-014** | Medium | Concurrency | `scripts/runners/run_deepseek_complete_work.py` | Blocking `time.sleep` inside async `main()` | RESOLVED |
| **ISSUE-015** | Medium | Concurrency | `scripts/runners/run_deepseek_autonomous_24_7.py` | Blocking `time.sleep` inside async `main()` | RESOLVED |
| **ISSUE-016** | Medium | Concurrency | `scripts/runners/run_deepseek_evolution.py` | Blocking `time.sleep` inside async `main()` | RESOLVED |
| **ISSUE-017** | Medium | Reliability | `trading_bot/realtime_dependency_manager.py` | Unhandled fallback when optional dependencies missing | RESOLVED |
| **ISSUE-018** | Medium | Reliability | `trading_bot/eternal_evolution/architecture_evolution.py` | Unhandled exception swallowing during evolution loop | RESOLVED |
| **ISSUE-019** | Medium | Reliability | `trading_bot/brain/central_controller.py` | Blocking sleep in controller loop | RESOLVED |
| **ISSUE-020** | Medium | Reliability | `trading_bot/brain/brain_architecture.py` | Blocking sleep in brain cycle | RESOLVED |
| **ISSUE-021** | Medium | Reliability | `trading_bot/ultimate_production/core_engine.py` | Bare `except: pass` swallowing core engine initialization errors | RESOLVED |
| **ISSUE-022** | Medium | Reliability | `trading_bot/analytics/data_warehouse.py` | Bare `except: pass` swallowing query execution errors | RESOLVED |
| **ISSUE-023** | Medium | Reliability | `trading_bot/realtime/realtime_data_hub.py` | Bare `except: pass` swallowing WebSocket streamer errors | RESOLVED |
| **ISSUE-024** | Medium | Reliability | `trading_bot/ingestion/event_router.py` | Bare `except: pass` swallowing event dispatch errors | RESOLVED |
| **ISSUE-025** | Medium | Reliability | `trading_bot/strategy/strategy_engine.py` | Bare `except: pass` swallowing strategy signal errors | RESOLVED |
| **ISSUE-026** | Medium | Reliability | `trading_bot/self_diagnostic/diagnostic_engine.py` | Bare `except: pass` swallowing self-diagnostic health errors | RESOLVED |
| **ISSUE-027** | Medium | Reliability | `trading_bot/self_diagnostic/knowledge_gap.py` | Bare `except: pass` swallowing knowledge extraction errors | RESOLVED |
| **ISSUE-028** | Medium | Reliability | `trading_bot/ml/model_monitoring.py` | Bare `except: pass` swallowing model drift monitor errors | RESOLVED |
| **ISSUE-029** | Medium | Reliability | `trading_bot/unified_architecture/layer1_data_foundation.py` | Bare `except: pass` swallowing layer 1 data ingestion errors | RESOLVED |
| **ISSUE-030** | Medium | Reliability | `trading_bot/sentient_core/knowledge_harvester.py` | Bare `except: pass` swallowing web harvester errors | RESOLVED |
| **ISSUE-031** | Medium | Reliability | `trading_bot/sentient_core/ai_learner.py` | Bare `except: pass` swallowing AI learning cycle errors | RESOLVED |
| **ISSUE-032** | Medium | Reliability | `trading_bot/sentient_core/network_sentinel.py` | Bare `except: pass` swallowing network health monitor errors | RESOLVED |
| **ISSUE-033** | Medium | Reliability | `trading_bot/dashboard/web_dashboard.py` | Bare `except: pass` swallowing web dashboard callback errors | RESOLVED |
| **ISSUE-034** | Medium | Reliability | `trading_bot/services/risk_service.py` | Bare `except: pass` swallowing risk service RPC errors | RESOLVED |
| **ISSUE-035** | Medium | Reliability | `trading_bot/services/signals_service.py` | Bare `except: pass` swallowing signal service RPC errors | RESOLVED |
