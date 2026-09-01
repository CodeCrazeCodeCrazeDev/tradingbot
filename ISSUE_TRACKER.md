# AlphaAlgo Production Audit Issue Tracker (2026)

| Issue ID | Domain | Severity | Root Cause | Files Affected | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Security | Critical | Un-sanitized `pickle.load` call allowing arbitrary code execution | `trading_bot/ml/automl_pipeline.py` | RESOLVED |
| **SEC-02** | Security | High | Unconstrained dynamic code execution inside sandbox | `trading_bot/core/security/sandbox.py` | RESOLVED |
| **SEC-03** | Security | Medium | Non-deterministic seed initialization in stochastic processes | `trading_bot/core/governance/determinism.py` | RESOLVED |
| **DAT-01** | Database | Critical | Missing `Base` dummy class definition when SQLAlchemy is absent | `trading_bot/database/production_database.py` | RESOLVED |
| **DAT-02** | Database | High | Duplicate `else` block corrupting ORM model declarations | `trading_bot/database/production_database.py` | RESOLVED |
| **DAT-03** | Database | Medium | Connection pool timeout missing defensive exception handling | `trading_bot/database/production_database.py` | RESOLVED |
| **DAT-04** | Database | Medium | Stale session leaks on unhandled generator exception | `trading_bot/database/production_database.py` | RESOLVED |
| **DAT-05** | Database | Low | Missing composite index on `(symbol, entry_time)` in TradeRecord | `trading_bot/database/production_database.py` | RESOLVED |
| **ORC-01** | Service Layer | High | Unterminated module docstring causing syntax parse error | `trading_bot/core/service_registry.py` | RESOLVED |
| **ORC-02** | Service Layer | High | Unterminated module docstring causing parse error | `trading_bot/core_agent_system/master_orchestrator.py` | RESOLVED |
| **ORC-03** | Service Layer | High | Unhandled `ImportError` on legacy service registry fallback | `trading_bot/core/service_registry.py` | RESOLVED |
| **ORC-04** | Service Layer | Medium | Duplicate `DecisionPriority` enum definition | `trading_bot/core_agent_system/master_orchestrator.py` | RESOLVED |
| **ORC-05** | Service Layer | Medium | Missing default stub implementation for `SystemContext` | `trading_bot/core_agent_system/master_orchestrator.py` | RESOLVED |
| **ORC-06** | Service Layer | Low | Missing logger initialization check in registry init | `trading_bot/core/service_registry.py` | RESOLVED |
| **AGN-01** | Agent Architecture | Critical | Indentation syntax error on line 1453 breaking test collection | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-02** | Agent Architecture | Critical | Invalid dictionary key syntax on line 2564 causing parse failure | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-03** | Agent Architecture | High | Duplicate class definition of `HeadAI` overriding methods | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-04** | Agent Architecture | High | Missing verifier classes (`CausalVerifier`, `LiquidityVerifier`, etc.) | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-05** | Agent Architecture | High | Missing `BayesianDecisionEngine` class definition | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-06** | Agent Architecture | Medium | Unbound variable `vix_score` referenced in risk loop | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-07** | Agent Architecture | Medium | Missing empty iterable check in `debate()` causing quorum crash | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **AGN-08** | Agent Architecture | Medium | Unhandled exception fallback in `respond_to_argument()` | `trading_bot/agents/multi_agent_debate.py` | RESOLVED |
| **CSC-01** | Cognitive System | High | Duplicate method definitions (`_select_optimal_action`, etc.) | `trading_bot/core/csc/controller.py` | RESOLVED |
| **CSC-02** | Cognitive System | High | Unassigned `final_qty` variable scoping bug under zero sizing | `trading_bot/core/csc/controller.py` | RESOLVED |
| **CSC-03** | Cognitive System | Medium | Missing singleton `reset()` causing test pollution | `trading_bot/core/csc/controller.py` | RESOLVED |
| **CSC-04** | Cognitive System | Medium | Missing HASP guardrail intervention check on null world model | `trading_bot/core/csc/controller.py` | RESOLVED |
| **CSC-05** | Cognitive System | Low | Inconsistent dict subscripting vs property access on route outcomes | `trading_bot/core/csc/router.py` | RESOLVED |
| **TST-01** | Test Harness | High | Misplaced `pass` statement in `test_orchestrator_performance.py` | `tests/orchestrator/test_orchestrator_performance.py` | RESOLVED |
| **TST-02** | Test Harness | High | Misplaced `pass` statement in `test_orchestrator_standalone.py` | `tests/orchestrator/test_orchestrator_standalone.py` | RESOLVED |
| **TST-03** | Test Harness | Medium | Missing `numpy`/`scipy` dependencies in test virtualenv | `requirements_no_mt5.txt` | RESOLVED |
| **TST-04** | Test Harness | Medium | `.hypothesis/` cache directory un-ignored in git | `.gitignore` | RESOLVED |
| **TST-05** | Test Harness | Medium | Missing async `await` keywords on `validate_evolution()` | `tests/test_scientific_modules.py` | RESOLVED |
| **TST-06** | Test Harness | Low | Outdated adapter name comparison in S2L routing test | `tests/test_scientific_modules.py` | RESOLVED |
| **TST-07** | Test Harness | Low | Unhandled exception in SRE teardown fixture | `tests/test_sre_implementation.py` | RESOLVED |
