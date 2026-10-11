# Comprehensive Issue Tracker — Production Engineering Audit

| Issue ID | Severity | Domain | Module / Files Affected | Description & Root Cause | Status |
|---|---|---|---|---|---|
| **ISSUE-001** | High | Architecture / Scientific Traceability | `trading_bot/core/csc/controller.py` | Missing arXiv paper citations in CognitiveSystemController docstring failing traceability tests. | **RESOLVED** |
| **ISSUE-002** | High | Testing / Orchestrator | `tests/orchestrator/test_orchestrator_integration.py` | `NameError: name 'TradingDecision' is not defined` in ML-to-execution integration test flow. | **RESOLVED** |
| **ISSUE-003** | High | Governance / Event Bus | `tests/test_superior_architecture_minimal.py` | `mock_shield.audit_log_action` returning `None`, triggering fail-closed veto on decision bus. | **RESOLVED** |
| **ISSUE-004** | High | Concurrency / I/O | `trading_bot/intel/news_pipeline.py` | Synchronous `requests.get` inside `async def _fetch_from_newsapi` blocking event loop. | **RESOLVED** |
| **ISSUE-005** | High | Concurrency / I/O | `trading_bot/neuros_evolution/plotcode_integration.py` | Synchronous `requests.post` inside `async def _execute_plotcode_test` blocking event loop. | **RESOLVED** |
| **ISSUE-006** | High | Security | `examples/advanced_market_analysis_demo.py` | Unsafe `eval()` calls parsing JSON-like liquidity and order flow string outputs. | **RESOLVED** |
| **ISSUE-007** | Critical | Security / Sandboxing | `trading_bot/aads/core/alpha_evolve_engine.py` | `exec()` call executing evolved signal code without `SecureASTVisitor` validation check. | **RESOLVED** |
| **ISSUE-008** | High | Multi-Agent / Reasoning | `trading_bot/agents/multi_agent_debate.py` | Duplicate `DevilsAdvocate` class definition with undefined `state['reasoning']` reference. | **RESOLVED** |
| **ISSUE-009** | Medium | Risk Management | `trading_bot/orchestrator/risk_manager.py` | Trade dollar position size scaling error in `validate_trade` rejecting valid trades. | **RESOLVED** |
| **ISSUE-010** | Low | Risk Management | `trading_bot/orchestrator/risk_manager.py` | Fallback concentration risk value missing when `min_hhi >= 1`. | **RESOLVED** |
| **ISSUE-011..035** | Medium | Script Runners / Validation | `scripts/runners/run_deepseek_*.py`, `scripts/launchers/*.py` | Blocking `time.sleep` calls inside async loops and silent exception swallowing. | **RESOLVED** |
