# Dependency Analysis Report

**Generated**: 2026-07-07T13:37:31.290245

## Summary

| Metric | Value |
|--------|-------|
| Total Modules | 7,991 |
| Total Dependencies | 8,825 |
| Avg Dependencies/Module | 1.1 |
| Circular Dependencies | 0 |
| Hub Modules | 50 |
| Leaf Modules | 50 |

## Domain Dependency Matrix

This shows how many imports flow from one domain to another:

| Source Domain | Target Domains |
|---------------|----------------|
| D01_data_infrastructure | D07_infrastructure: 162, D05_ai_ml: 16, D04_signal_generation: 16, D08_governance: 9, D03_execution: 9 |
| D02_risk_management | D07_infrastructure: 174, D05_ai_ml: 33, D04_signal_generation: 14, D03_execution: 10, D01_data_infrastructure: 10 |
| D03_execution | D07_infrastructure: 169, D04_signal_generation: 37, D02_risk_management: 33, D05_ai_ml: 22, D01_data_infrastructure: 16 |
| D04_signal_generation | D07_infrastructure: 263, D05_ai_ml: 33, D02_risk_management: 18, D03_execution: 18, D01_data_infrastructure: 15 |
| D05_ai_ml | D07_infrastructure: 721, D02_risk_management: 48, D04_signal_generation: 47, D03_execution: 33, D01_data_infrastructure: 33 |
| D06_security_compliance | D07_infrastructure: 18 |
| D07_infrastructure | D05_ai_ml: 124, D02_risk_management: 108, D04_signal_generation: 98, D01_data_infrastructure: 94, D03_execution: 70 |
| D08_governance | D07_infrastructure: 82, D05_ai_ml: 9, D02_risk_management: 5, D06_security_compliance: 4, D10_integration: 2 |
| D09_performance | D07_infrastructure: 134, D05_ai_ml: 16, D01_data_infrastructure: 15, D03_execution: 13, D02_risk_management: 12 |
| D10_integration | D07_infrastructure: 50, D01_data_infrastructure: 8, D06_security_compliance: 2, D04_signal_generation: 2, D08_governance: 1 |
| D11_testing | D07_infrastructure: 2517, D05_ai_ml: 267, D04_signal_generation: 184, D02_risk_management: 180, D03_execution: 172 |
| D12_documentation | D07_infrastructure: 160, D05_ai_ml: 37, D04_signal_generation: 13, D03_execution: 11, D02_risk_management: 10 |

## Hub Modules (Most Dependents)

These modules are imported by many others and should be integrated first:

| Module | Dependents | Domain |
|--------|------------|--------|
| `trading/__init__.py` | 5358 | D07_infrastructure |
| `trading/order_execution.py` | 5358 | D03_execution |
| `trading/order_fill_tracker.py` | 5358 | D03_execution |
| `trading/position_manager.py` | 5358 | D02_risk_management |
| `trading/risk_calculator.py` | 5358 | D02_risk_management |
| `trading_bot/__init__.py` | 5322 | D07_infrastructure |
| `trading_bot/a2a.py` | 5322 | D07_infrastructure |
| `trading_bot/adaptive.py` | 5322 | D07_infrastructure |
| `trading_bot/adaptive_systems.py` | 5322 | D07_infrastructure |
| `trading_bot/advanced_exits.py` | 5322 | D07_infrastructure |
| `trading_bot/aean_meta_intelligence_layer.py` | 5322 | D05_ai_ml |
| `trading_bot/agents.py` | 5322 | D07_infrastructure |
| `trading_bot/agents2.py` | 5322 | D07_infrastructure |
| `trading_bot/alphaalgo_5star.py` | 5322 | D05_ai_ml |
| `trading_bot/analysis.py` | 5322 | D04_signal_generation |
| `trading_bot/analysis_orchestrator.py` | 5322 | D04_signal_generation |
| `trading_bot/api.py` | 5322 | D10_integration |
| `trading_bot/approval.py` | 5322 | D08_governance |
| `trading_bot/arbitrage.py` | 5322 | D07_infrastructure |
| `trading_bot/archive_orchestrator.py` | 5322 | D03_execution |

## Integration Order (First 20)

Start integration with these modules:

| Level | Module |
|-------|--------|
| 1 | `tests/alpha_engine/test_compliance_xai.py` |
| 1 | `tests/test_human_gateway.py` |
| 1 | `tests/test_algorithms_updated.py` |
| 1 | `tests/test_simple_collector.py` |
| 1 | `trading_bot/complete_implementation.py` |
| 1 | `tests/deepseek_engineer/test_guardrails.py` |
| 1 | `tests/market_teacher/test_curiosity_engine.py` |
| 1 | `tests/test_system_health.py` |
| 1 | `tests/test_journal_manager.py` |
| 1 | `trading_bot/adversarial_decision/confidence_vector.py` |
| 1 | `trading_bot/_archive/event_monitoring/economic_calendar.py` |
| 1 | `tests/test_performance.py` |
| 1 | `tests/brain/test_tier6_macro.py` |
| 1 | `tests/ml/federated/test_global_model.py` |
| 1 | `trading_bot/self_learning/master_orchestrator.py` |
| 1 | `tests/core/test_shared.py` |
| 1 | `examples/intelligence_core_demo.py` |
| 1 | `tests/market_student/test_reward_system.py` |
| 1 | `tests/dashboard/test_performance_attribution.py` |
| 1 | `tests/test_multilayerriskmanager.py` |

## Recommended Integration Strategy

### Phase 1: Foundation (Level 1-2)
- Core utilities and constants
- Logging and configuration
- Base classes and interfaces

### Phase 2: Infrastructure (Level 3-5)
- Database connections
- Message bus
- Health monitoring

### Phase 3: Domain Services (Level 6-10)
- Risk management
- Data pipelines
- Execution engine

### Phase 4: Business Logic (Level 11-15)
- Strategies
- ML models
- Signal generation

### Phase 5: Integration (Level 16-20)
- APIs
- External adapters
- Orchestration

## Next Steps

1. **Fix Circular Dependencies**: Resolve all circular imports before proceeding
2. **Start with Hub Modules**: Integrate high-dependency modules first
3. **Follow Level Order**: Integrate modules level by level
4. **Test Each Level**: Verify integration before moving to next level
5. **Document as You Go**: Update integration status for each module
