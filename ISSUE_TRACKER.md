# AlphaAlgo Production Issue Tracker — 2026 Audit

| Issue ID | Domain | Severity | Root Cause | Affected File(s) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | Risk Management | High | Parenthesized list comprehension unpacking syntax error. | `risk/risk_manager.py` | **RESOLVED** |
| **ISSUE-002** | Operations | Medium | Unexpected indentation error in script definition. | `scripts/fixes/auto_fix_critical_issues_v2.py` | **RESOLVED** |
| **ISSUE-003** | Deployment | High | Indentation/scoping error in deploy loop. | `scripts/deployment/deploy_5star_production.py` | **RESOLVED** |
| **ISSUE-004** | Launchers | Medium | Indentation error in data generation block. | `scripts/launchers/run_alphaalgo_5star.py` | **RESOLVED** |
| **ISSUE-005** | Validation / Benchmarks | High | Blocking `time.sleep` in async benchmark method. | `trading_bot/core/validation.py` | **RESOLVED** |
| **ISSUE-006** | Realtime Dependencies | High | Sync `fix_package` blocking async loop. | `trading_bot/realtime_dependency_manager.py` | **RESOLVED** |
| **ISSUE-007** | Security / AADS | Critical | Unsanitized `exec()` invocation without AST security check. | `trading_bot/aads/core/alpha_evolve_engine.py` | **RESOLVED** |
| **ISSUE-008** | Security / Backtester | Critical | Unchecked strategy code `exec()` execution. | `trading_bot/distributed/parallel_backtester.py` | **RESOLVED** |
| **ISSUE-009** | Security / Sandbox | Medium | Missing `validate_code` helper on `SecureASTVisitor`. | `trading_bot/core/security/sandbox.py` | **RESOLVED** |
| **ISSUE-010** | Core Brain (CSC) | Medium | Silent exception swallowing in evidence/simulation. | `trading_bot/core/csc/controller.py` | **RESOLVED** |
| **ISSUE-011** | Memory System (HMS) | Medium | Silent exception swallowing during reset schema save. | `trading_bot/core/hms/memory.py` | **RESOLVED** |
| **ISSUE-012** | Security Credentials | Low | Silent exception swallowing during file decryption. | `trading_bot/security/secure_credentials.py` | **RESOLVED** |
| **ISSUE-013** | Rate Limiter | High | Synchronous sleep in `wait_for_token_async`. | `trading_bot/utils/api_rate_limiter.py` | **RESOLVED** |
| **ISSUE-014** | Resilience | Medium | Synchronous retry loop in circuit breaker. | `trading_bot/resilience/circuit_breaker.py` | **RESOLVED** |
| **ISSUE-015** | Data Management | Medium | Synchronous background cleanup in shared memory manager. | `trading_bot/database/shared_memory_manager.py` | **RESOLVED** |
| **ISSUE-016** | Brain Controller | High | Blocking sleep in central controller loop. | `trading_bot/brain/central_controller.py` | **RESOLVED** |
| **ISSUE-017** | Brain Architecture | High | Synchronous loop delay in brain architecture. | `trading_bot/brain/brain_architecture.py` | **RESOLVED** |
| **ISSUE-018** | COS Core | Medium | Blocking sleep in COS core execution loop. | `trading_bot/cos/cos_core.py` | **RESOLVED** |
| **ISSUE-019** | Exception Handler | High | Synchronous sleep in async exception handler. | `trading_bot/core/exception_handler.py` | **RESOLVED** |
| **ISSUE-020** | Liquidity Analysis | High | Blocking sleep in realtime liquidity streamer. | `trading_bot/analysis/realtime_liquidity.py` | **RESOLVED** |
| **ISSUE-021** | Eternal Evolution | High | Blocking sleep in architecture evolution. | `trading_bot/eternal_evolution/architecture_evolution.py` | **RESOLVED** |
| **ISSUE-022** | Distributed Systems | High | Blocking sleep in task distributor. | `trading_bot/distributed/task_distributor.py` | **RESOLVED** |
| **ISSUE-023** | Self Coordinating AI | Critical | Unsandboxed `exec()` in sandbox executor. | `trading_bot/self_coordinating_ai/sandbox_executor.py` | **RESOLVED** |
| **ISSUE-024** | Autonomous Organism | Critical | Unchecked `exec()` in sandbox environment. | `trading_bot/autonomous_research_organism/sandbox_environment.py` | **RESOLVED** |
| **ISSUE-025** | Advanced AI | Critical | Unchecked `exec()` in code synthesis. | `trading_bot/advanced_ai/code_synthesis.py` | **RESOLVED** |
| **ISSUE-026** | Survival Core | Medium | Bare exception swallowing in survival core. | `trading_bot/core/survival_core.py` | **RESOLVED** |
| **ISSUE-027** | Error Recovery | Medium | Bare exception swallowing in error recovery. | `trading_bot/core/error_recovery.py` | **RESOLVED** |
| **ISSUE-028** | Compute Budget | Medium | Bare exception swallowing in budget controller. | `trading_bot/autonomous_research_organism/compute_budget_controller.py` | **RESOLVED** |
| **ISSUE-029** | Unified Approvals | Low | Bare exception swallowing in notifications. | `trading_bot/unified_approval/notification_system.py` | **RESOLVED** |
| **ISSUE-030** | Safety Systems | High | Bare exception swallowing in connectivity monitor. | `trading_bot/safety/connectivity_monitor.py` | **RESOLVED** |
| **ISSUE-031** | Integration | Medium | Bare exception swallowing in cTrader integration. | `trading_bot/ctrader/ctrader_integration.py` | **RESOLVED** |
| **ISSUE-032** | Monitoring | Medium | Bare exception swallowing in live monitor. | `trading_bot/monitoring/live_monitor.py` | **RESOLVED** |
| **ISSUE-033** | Operational Utilities | High | Mis-indented try block in autonomous operator. | `scripts/utilities/alphaalgo_autonomous_operator.py` | **RESOLVED** |
| **ISSUE-034** | Indicator Calculations | Medium | Un-vectorized loop computation in liquidity heatmap. | `trading_bot/indicators/advanced_liquidity.py` | **RESOLVED** |
| **ISSUE-035** | ML Model Monitoring | Medium | Un-vectorized metric computation in model monitor. | `trading_bot/ml/model_monitoring.py` | **RESOLVED** |
