# Dependency Analysis Report

**Generated**: 2026-03-07T15:58:13.443764

## Summary

| Metric | Value |
|--------|-------|
| Total Modules | 21,471 |
| Total Dependencies | 21,418 |
| Avg Dependencies/Module | 1.0 |
| Circular Dependencies | 0 |
| Hub Modules | 50 |
| Leaf Modules | 50 |

## Domain Dependency Matrix

This shows how many imports flow from one domain to another:

| Source Domain | Target Domains |
|---------------|----------------|
| D01_data_infrastructure | D07_infrastructure: 448, D04_signal_generation: 61, D03_execution: 40, D05_ai_ml: 34, D02_risk_management: 22 |
| D02_risk_management | D07_infrastructure: 530, D05_ai_ml: 116, D03_execution: 65, D04_signal_generation: 61, D01_data_infrastructure: 49 |
| D03_execution | D07_infrastructure: 653, D04_signal_generation: 249, D02_risk_management: 207, D05_ai_ml: 140, D01_data_infrastructure: 101 |
| D04_signal_generation | D07_infrastructure: 783, D05_ai_ml: 200, D03_execution: 112, D02_risk_management: 87, D01_data_infrastructure: 79 |
| D05_ai_ml | D07_infrastructure: 1483, D04_signal_generation: 198, D02_risk_management: 156, D03_execution: 153, D01_data_infrastructure: 85 |
| D06_security_compliance | D07_infrastructure: 26 |
| D07_infrastructure | D01_data_infrastructure: 367, D05_ai_ml: 288, D02_risk_management: 269, D04_signal_generation: 238, D03_execution: 215 |
| D08_governance | D07_infrastructure: 163, D02_risk_management: 27, D05_ai_ml: 12, D10_integration: 4 |
| D09_performance | D07_infrastructure: 468, D01_data_infrastructure: 88, D05_ai_ml: 65, D02_risk_management: 30, D03_execution: 29 |
| D10_integration | D07_infrastructure: 93, D01_data_infrastructure: 44, D04_signal_generation: 11, D06_security_compliance: 1, D02_risk_management: 1 |
| D11_testing | D07_infrastructure: 2939, D05_ai_ml: 600, D04_signal_generation: 430, D01_data_infrastructure: 404, D03_execution: 397 |
| D12_documentation | D07_infrastructure: 555, D05_ai_ml: 102, D04_signal_generation: 74, D03_execution: 49, D01_data_infrastructure: 43 |

## Hub Modules (Most Dependents)

These modules are imported by many others and should be integrated first:

| Module | Dependents | Domain |
|--------|------------|--------|
| `trading\__init__.py` | 11647 | D07_infrastructure |
| `trading\order_execution.py` | 11647 | D03_execution |
| `trading\order_fill_tracker.py` | 11647 | D03_execution |
| `trading\position_manager.py` | 11647 | D02_risk_management |
| `trading\risk_calculator.py` | 11647 | D02_risk_management |
| `trading_bot\__init__.py` | 11555 | D07_infrastructure |
| `trading_bot\adaptive.py` | 11555 | D07_infrastructure |
| `trading_bot\adaptive_systems.py` | 11555 | D07_infrastructure |
| `trading_bot\advanced_exits.py` | 11555 | D07_infrastructure |
| `trading_bot\agents.py` | 11555 | D07_infrastructure |
| `trading_bot\agents2.py` | 11555 | D07_infrastructure |
| `trading_bot\alphaalgo_5star.py` | 11555 | D05_ai_ml |
| `trading_bot\analysis.py` | 11555 | D04_signal_generation |
| `trading_bot\analysis_orchestrator.py` | 11555 | D04_signal_generation |
| `trading_bot\api.py` | 11555 | D10_integration |
| `trading_bot\approval.py` | 11555 | D08_governance |
| `trading_bot\arbitrage.py` | 11555 | D07_infrastructure |
| `trading_bot\archive_orchestrator.py` | 11555 | D03_execution |
| `trading_bot\audit.py` | 11555 | D06_security_compliance |
| `trading_bot\auto_dependency_installer.py` | 11555 | D07_infrastructure |

## Integration Order (First 20)

Start integration with these modules:

| Level | Module |
|-------|--------|
| 1 | `tests\ai_core\execution\test_market_impact.py` |
| 1 | `autonomous_backups\20251209_062525\trading_bot\complete_implementation.py` |
| 1 | `tests\test_orderblockpanel.py` |
| 1 | `trading_bot.egg-info\trading_bot\monitoring\__init__.py` |
| 1 | `trading_bot.egg-info\trading_bot\improvements\forecast_improvements\master_orchestrator.py` |
| 1 | `tests\test_resilient_connection.py` |
| 1 | `tests\adversarial_decision\test_adversarial_core.py` |
| 1 | `trading_bot.egg-info\trading_bot\schemas\trading.py` |
| 1 | `tests\analysis\test_wyckoff.py` |
| 1 | `tests\test_signal_lifecycle.py` |
| 1 | `trading_bot\wealth\__init__.py` |
| 1 | `autonomous_backups\20251209_062611\trading_bot\elite_integration.py` |
| 1 | `tests\ai_core\meta_learning\test_maml.py` |
| 1 | `tests\analysis\test_pattern_failure_detection.py` |
| 1 | `tests\data\test_market_data.py` |
| 1 | `trading_bot.egg-info\trading_bot\_archive\skills\alternative_data\__init__.py` |
| 1 | `tests\test_auto_pause.py` |
| 1 | `autonomous_backups\20251209_062525\trading_bot\deepseek_engineer\live_engineer.py` |
| 1 | `tests\event_pipeline\test_event_consumer.py` |
| 1 | `tests\connectivity\test_async_fetcher.py` |

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
