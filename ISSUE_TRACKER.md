# Production Engineering Issue Tracker (2026)

This document contains the granular registry of all 34 engineering-significant issues identified and remediated during the 2026 Production Engineering Audit.

---

## Issue Registry Table

| Issue ID | Severity | Category | Affected File(s) | Short Description | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **SEC-001** | Critical | Security | `trading_bot/ml/automl_pipeline.py` | Unsafe `pickle.load` deserialization risk | Resolved |
| **SEC-002** | Critical | Security | `trading_bot/distributed/parallel_backtester.py` | Unsanitized `exec` strategy evaluation | Resolved |
| **SEC-003** | High | Security | `trading_bot/core/security/sandbox.py` | Incomplete module import whitelist | Resolved |
| **REL-001** | High | Reliability | `trading_bot/foundation_agents/causal_engine/causal_discovery.py` | Bare `except:` catching SystemExit in lstsq | Resolved |
| **REL-002** | High | Reliability | `trading_bot/foundation_agents/causal_engine/causal_discovery.py` | Bare `except:` in independence test | Resolved |
| **REL-003** | High | Reliability | `trading_bot/foundation_agents/causal_engine/granger_causality.py` | Silent exception swallowing in optimal VAR lag search | Resolved |
| **REL-004** | High | Reliability | `trading_bot/foundation_agents/cognitive_core/attention_mechanism.py` | Bare exception swallowing in novelty z-score calculation | Resolved |
| **REL-005** | Medium | Reliability | `trading_bot/foundation_agents/knowledge_pipeline/citation_network.py` | Bare `except:` swallow in PageRank network calculations | Resolved |
| **REL-006** | Medium | Reliability | `trading_bot/foundation_agents/knowledge_pipeline/citation_network.py` | Bare `except:` swallow in degree centrality calculation | Resolved |
| **REL-007** | High | Reliability | `trading_bot/foundation_agents/multi_agent/collective_intelligence.py` | Silent fallback in logit extremization | Resolved |
| **REL-008** | Critical | Reliability | `trading_bot/autonomous/alpha_factor_discovery.py` | Mutable default argument `nodes=[]` causing cross-call state leak | Resolved |
| **REL-009** | High | Reliability | `trading_bot/ai_core/forecasting/temporal_fusion_transformer.py` | Mutable default argument in prediction function | Resolved |
| **REL-010** | High | Reliability | `trading_bot/ai_core/rl/offline_policy_evaluation.py` | Mutable default argument in offline policy evaluation | Resolved |
| **SYN-001** | High | Syntax/Build | `trading_bot/agents/multi_agent_debate.py` | Unexpected indentation in falsification gate check | Resolved |
| **SYN-002** | Medium | Syntax/Build | `trading_bot/agents/multi_agent_debate.py` | Missing quotes in dict keys (`agent_contributions`) | Resolved |
| **SYN-003** | Medium | Syntax/Build | `trading_bot/agents/multi_agent_debate.py` | Missing quotes in dict keys (`consensus_record`) | Resolved |
| **PERF-001** | Medium | Performance | `trading_bot/world_model/causal_model.py` | Un-memoized cycle finding in causal DAGs | Resolved |
| **PERF-002** | Medium | Performance | `trading_bot/core/hms/memory.py` | Uncached multi-hop SAGE graph traversal | Resolved |
| **DATA-001** | High | Data Integrity | `trading_bot/unified_architecture/layer1_data_foundation.py` | Silent exception swallowing during tick ingestion | Resolved |
| **DATA-002** | Medium | Data Integrity | `trading_bot/database/production_database.py` | Unhandled transaction aborts during high-concurrency writes | Resolved |
| **CONC-001** | High | Concurrency | `trading_bot/core/unified_event_bus.py` | Unhandled task cancellation during shutdown | Resolved |
| **CONC-002** | High | Concurrency | `trading_bot/core/csc/controller.py` | Potential lock race during fast strategy pivots | Resolved |
| **ARCH-001** | Medium | Architecture | `trading_bot/core/service_registry.py` | Duplicate fallback handlers | Resolved |
| **ARCH-002** | Medium | Architecture | `trading_bot/core_agent_system/master_orchestrator.py` | Misplaced import statements in error recovery | Resolved |
| **GOV-001** | Critical | Governance | `trading_bot/governance/orchestrator.py` | Missing governance orchestrator export | Resolved |
| **GOV-002** | High | Governance | `trading_bot/core/security/defense.py` | Unenforced risk parameter immutability in emergency mode | Resolved |
| **SEC-004** | Low | Security | `trading_bot/distributed/parallel_backtester.py` | Missing input validation for backtest config dictionary | Resolved |
| **REL-011** | Low | Reliability | `trading_bot/neuros_evolution/code_evolution_engine.py` | Incomplete string stripping on coverage calculation | Resolved |
| **PERF-003** | Low | Performance | `trading_bot/ml/automl_pipeline.py` | Redundant model re-loading on evaluation calls | Resolved |
| **MAINT-001** | Low | Maintainability | `trading_bot/agents/multi_agent_debate.py` | Duplicate docstrings in HeadAI class | Resolved |
| **MAINT-002** | Low | Maintainability | `trading_bot/foundation_agents/causal_engine/causal_discovery.py` | Unused local import inside function body | Resolved |
| **MAINT-003** | Low | Maintainability | `trading_bot/foundation_agents/cognitive_core/attention_mechanism.py` | Magic number `0.3` for moderate novelty fallback | Resolved |
| **MAINT-004** | Low | Maintainability | `trading_bot/world_model/causal_model.py` | Missing type hint annotations on path strengths | Resolved |
| **MAINT-005** | Low | Maintainability | `trading_bot/distributed/parallel_backtester.py` | Print statements instead of logger invocations | Resolved |

---

## Detailed Technical Breakdowns

### Issue SEC-001: Unsafe Deserialization
* **Severity**: Critical
* **Root Cause**: Use of standard `pickle.load` without class filtering allowed arbitrary code execution.
* **Solution**: Switched to `safe_load` from `trading_bot.security.safe_pickle` which checks module/class origin against an explicit safety whitelist.

### Issue SEC-002: Dynamic Code Execution
* **Severity**: Critical
* **Root Cause**: In `parallel_backtester.py`, strategy code submitted as strings was executed directly with `exec()`.
* **Solution**: Integrated `SecureASTVisitor().validate_code(strategy_code)` before executing strategy blocks.

### Issue REL-008: Shared Mutable Default Argument State
* **Severity**: Critical
* **Root Cause**: `def get_random_node(expr, nodes=[]):` accumulated nodes across successive function calls.
* **Solution**: Modified function signature to `def get_random_node(expr, nodes=None):` and instantiated `nodes = []` if `None`.
