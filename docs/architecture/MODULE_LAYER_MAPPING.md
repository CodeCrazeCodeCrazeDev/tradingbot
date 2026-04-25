# Module to Layer Mapping

This document maps all 177 modules in the trading bot codebase to the 11-layer unified architecture.

## Summary

| Layer | Name | Modules | Files | Lines |
|-------|------|---------|-------|-------|
| 0 | Infrastructure | 3 | 33 | ~9,233 |
| 1 | Observability | 4 | 45 | ~14,781 |
| 2 | Connectivity | 4 | 58 | ~26,921 |
| 3 | Data Foundation | 4 | 66 | ~18,647 |
| 4 | Intelligence | 12 | 280 | ~95,000 |
| 5 | Signal Generation | 6 | 58 | ~15,000 |
| 6 | Risk & Safety | 6 | 88 | ~32,000 |
| 7 | Decision Verification | 3 | 31 | ~7,389 |
| 8 | Execution | 3 | 73 | ~25,738 |
| 9 | Orchestration | 5 | 60 | ~28,000 |
| 10 | Governance | 6 | 38 | ~15,000 |
| Cross-cutting | Utilities & Support | 121 | ~2,300 | ~1,200,000 |

**Total: 177 modules, 3,121 files, ~1,494,642 lines**

---

## Layer 0: Infrastructure & Hardware

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `infrastructure/` | 21 | 8,097 | Cloud, auto-scaling, health, Kubernetes |
| `performance/` | 10 | 4,904 | Memory, profiling, optimization |
| `profiling/` | 2 | 572 | Async profiler |

---

## Layer 1: Observability & Health

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `monitoring/` | 21 | 8,558 | Prometheus, alerting, dashboards |
| `observability/` | 8 | 3,677 | Metrics, tracing, pre-trade gate |
| `log_system/` | 9 | 2,546 | Structured logging, audit |
| `telemetry/` | 7 | - | Metrics collection |

---

## Layer 2: Connectivity & Ingestion

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `connectivity/` | 22 | 9,243 | WebSocket, REST, rate limiting |
| `connectors/` | 8 | 4,215 | Exchange connectors |
| `brokers/` | 17 | 7,311 | Broker adapters (MT5, Alpaca, Binance) |
| `ingestion/` | 11 | 6,152 | Event collection, normalization |

---

## Layer 3: Data Foundation

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `data/` | 35 | 9,447 | Market data, feeds, databases |
| `database/` | 23 | 7,384 | Persistence, caching, streaming |
| `data_feeds/` | 6 | 1,816 | Multi-source feeds |
| `data_sources/` | 2 | 429 | Free data providers |

---

## Layer 4: Intelligence Core

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `ml/` | 139 | 42,392 | ML models, RL, transformers |
| `ai_core/` | 59 | - | AI systems |
| `cognitive_architecture/` | 12 | 3,932 | 10-layer cognitive system |
| `alpha_engine/` | 28 | 23,098 | Alpha generation |
| `alpha_research/` | 11 | 8,500 | Research systems |
| `deepchart/` | 22 | 13,727 | Chart intelligence |
| `deepseek_architecture/` | 9 | 6,412 | DeepSeek integration |
| `market_intelligence/` | 19 | 10,539 | Market analysis |
| `meta_learning/` | 2 | 108 | MAML |
| `innovations/` | 19 | 11,987 | Experimental features |
| `indicators/` | 9 | 3,705 | Technical indicators |
| `analysis/` | - | - | Analysis tools |

---

## Layer 5: Signal Generation

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `signals/` | 12 | - | Signal generation |
| `strategies/` | 9 | - | Trading strategies |
| `strategy/` | 13 | - | Strategy engine |
| `opportunity_scanner/` | 12 | 5,903 | Opportunity detection |
| `institutional_entry/` | 5 | 3,449 | Institutional signals |
| `sentiment/` | - | - | Sentiment analysis |

---

## Layer 6: Risk & Safety

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `risk/` | 52 | 15,883 | Risk management |
| `safety/` | 12 | - | Safety systems |
| `reality_gates/` | 8 | 3,982 | Reality validation |
| `hedge_fund_safety/` | 8 | 5,778 | Institutional safety |
| `critical_fixes/` | 10 | 6,880 | Critical validators |
| `msos/` | 17 | 9,173 | Market safety |

---

## Layer 7: Decision Verification

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `adversarial_decision/` | 9 | - | Adversarial validation |
| `agents/` | 5 | - | AI agents |
| `decision_layer/` | 17 | 4,147 | Decision concepts |

---

## Layer 8: Execution

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `execution/` | 56 | 18,427 | Order execution |
| `exit_strategies/` | 6 | 3,665 | Exit management |
| `position/` | 6 | 2,767 | Position tracking |

---

## Layer 9: Orchestration

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `orchestrator/` | 10 | 4,245 | Master orchestration |
| `brain/` | 20 | 10,072 | Trading brain |
| `core/` | 98 | 33,666 | Core systems |
| `realtime/` | 8 | 4,608 | Real-time processing |
| `unified_architecture/` | 7 | - | Previous unified system |

---

## Layer 10: Governance & Human Control

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `governance/` | 3 | 91 | Approval workflows |
| `alphaalgo_core/` | 20 | - | G0/G1/G2 hierarchy |
| `compliance/` | 4 | 1,411 | Compliance monitoring |
| `audit/` | 3 | - | Audit logging |
| `human_layer/` | 5 | 1,609 | Human interface |
| `deepseek_governance/` | 7 | 4,185 | AI governance |

---

## Cross-Cutting Modules

These modules provide utilities and support across multiple layers:

| Module | Files | Lines | Description |
|--------|-------|-------|-------------|
| `config/` | 5 | 1,776 | Configuration |
| `utils/` | - | - | Utilities |
| `models/` | 3 | 476 | Data models |
| `core_api/` | 5 | 2,572 | Core interfaces |
| `bridges/` | 7 | 559 | Layer bridges |
| `integrations/` | 7 | 2,975 | Integration layers |
| `testing/` | - | - | Test utilities |
| `examples/` | - | - | Example code |

---

## New Unified System Files

Created as part of this integration:

| File | Description |
|------|-------------|
| `trading_bot/unified_system/__init__.py` | Package initialization |
| `trading_bot/unified_system/unified_types.py` | Core type definitions |
| `trading_bot/unified_system/layer_interfaces.py` | Layer interface contracts |
| `trading_bot/unified_system/layer_registry.py` | Layer registration |
| `trading_bot/unified_system/unified_config.py` | Configuration management |
| `trading_bot/unified_system/master_system.py` | Master orchestrator |
| `trading_bot/unified_system/layers/layer0_infrastructure.py` | Layer 0 impl |
| `trading_bot/unified_system/layers/layer1_observability.py` | Layer 1 impl |
| `trading_bot/unified_system/layers/layer2_connectivity.py` | Layer 2 impl |
| `trading_bot/unified_system/layers/layer3_data_foundation.py` | Layer 3 impl |
| `trading_bot/unified_system/layers/layer4_intelligence.py` | Layer 4 impl |
| `trading_bot/unified_system/layers/layer5_signal.py` | Layer 5 impl |
| `trading_bot/unified_system/layers/layer6_risk_safety.py` | Layer 6 impl |
| `trading_bot/unified_system/layers/layer7_decision.py` | Layer 7 impl |
| `trading_bot/unified_system/layers/layer8_execution.py` | Layer 8 impl |
| `trading_bot/unified_system/layers/layer9_orchestration.py` | Layer 9 impl |
| `trading_bot/unified_system/layers/layer10_governance.py` | Layer 10 impl |
| `main_unified_system.py` | Main entry point |
| `RUN_UNIFIED_SYSTEM.bat` | Windows launcher |
| `examples/unified_system_demo.py` | Demo script |
| `docs/UNIFIED_SYSTEM_ARCHITECTURE.md` | Architecture docs |
| `docs/DEPLOYMENT_GUIDE.md` | Deployment guide |
| `docs/MODULE_LAYER_MAPPING.md` | This file |

---

**Total New Files:** 23  
**Total New Lines:** ~3,500
