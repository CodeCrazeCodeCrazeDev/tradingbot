# Observability System Implementation

## Overview

Complete implementation of 5 production-ready observability and control modules for the AlphaAlgo trading system.

## Modules Implemented

### 1. Unified Observability Hub (`unified_observability_hub.py`)
**~550 lines** - Centralized monitoring, metrics aggregation, alerting, and system health tracking.

**Features:**
- Real-time metrics collection (Counter, Gauge, Histogram, Rate, Timer)
- Multi-level alerting with escalation (CRITICAL → INFO)
- Component health monitoring with heartbeats
- Anomaly detection using z-score analysis
- Audit trail logging
- Rate limiting per component

**Key Classes:**
- `UnifiedObservabilityHub` - Main orchestrator
- `MetricPoint` - Single metric data point
- `Alert` - System alert with acknowledgment
- `ComponentStatus` - Component health status
- `AlertManager` - Alert lifecycle management
- `AnomalyDetector` - Statistical anomaly detection

**Usage:**
```python
from trading_bot.observability import UnifiedObservabilityHub, MetricType, AlertSeverity

hub = UnifiedObservabilityHub()

# Register components
hub.register_component("strategy_engine", version="1.0.0")

# Record metrics
hub.record_gauge("pnl", 1500.50, component="strategy_engine")
hub.record_counter("trades", 1, component="strategy_engine")
hub.record_timer("execution_time", 45.2, component="execution")

# Create alerts
hub.create_alert(
    title="High Drawdown",
    message="Drawdown exceeded 5%",
    severity=AlertSeverity.HIGH,
    component="risk_manager"
)

# Get dashboard data
dashboard = hub.get_dashboard_data()
```

---

### 2. Pre-Trade Gate Orchestrator (`pre_trade_gate.py`)
**~550 lines** - Multi-layer validation system that must pass before any trade execution.

**Gate Types:**
- `RISK_LIMIT` - Position size, exposure limits
- `SIGNAL_QUALITY` - Signal confidence threshold
- `DRAWDOWN` - Drawdown limits
- `LIQUIDITY` - Sufficient liquidity check
- `DATA_QUALITY` - Data freshness and quality
- `BROKER_STATUS` - Broker connectivity
- `CIRCUIT_BREAKER` - Circuit breaker status
- `VOLATILITY` - Volatility within bounds
- `STRATEGY_HEALTH` - Strategy performance check

**Key Classes:**
- `PreTradeGateOrchestrator` - Main orchestrator
- `PreTradeCheck` - Trade validation request
- `GateResult` - Result of gate check
- `Gate` - Base class for gates

**Usage:**
```python
from trading_bot.observability import PreTradeGateOrchestrator, PreTradeCheck

orchestrator = PreTradeGateOrchestrator()

# Create trade check
trade = PreTradeCheck(
    check_id="CHK001",
    symbol="BTCUSDT",
    direction="BUY",
    quantity=0.1,
    price=50000,
    strategy_id="momentum_v1",
    signal_confidence=0.75,
)

# Validate through all gates
context = {
    "portfolio_value": 100000,
    "current_drawdown": 0.03,
    "broker_connected": True,
}

passed, results = orchestrator.validate(trade, context)

if passed:
    # Execute trade
    pass
else:
    # Log rejection reasons
    for r in results:
        if not r.passed:
            print(f"Gate {r.gate_name} failed: {r.reason}")
```

---

### 3. Trade Quality Grader (`trade_quality_grader.py`)
**~650 lines** - Comprehensive trade quality scoring and grading system.

**Quality Dimensions:**
- `ENTRY_TIMING` - How well timed was the entry
- `EXIT_TIMING` - How well timed was the exit
- `POSITION_SIZING` - Was position size appropriate
- `RISK_REWARD` - Risk/reward ratio quality
- `SIGNAL_STRENGTH` - Underlying signal quality
- `EXECUTION_QUALITY` - Slippage, fill quality
- `MARKET_ALIGNMENT` - Alignment with market conditions

**Grades:** A+ → F (with GPA calculation)

**Key Classes:**
- `TradeQualityGrader` - Main grader
- `TradeScore` - Complete trade quality score
- `TradeGrade` - Letter grade enum
- `DimensionScore` - Score for single dimension

**Usage:**
```python
from trading_bot.observability import TradeQualityGrader

grader = TradeQualityGrader()

# Grade a completed trade
trade_data = {
    "symbol": "EURUSD",
    "strategy_id": "trend_v1",
    "direction": "BUY",
    "entry_price": 1.1000,
    "exit_price": 1.1050,
    "quantity": 10000,
    "pnl": 50,
    "pnl_percent": 0.0045,
    "signal_confidence": 0.8,
    "slippage_bps": 2.0,
}

context = {
    "high_during_trade": 1.1060,
    "low_during_trade": 1.0990,
    "market_trend": "UP",
}

score = grader.grade_trade("TRADE001", trade_data, context)

print(f"Grade: {score.grade.value} ({score.overall_score:.1f})")
print(f"Strengths: {score.strengths}")
print(f"Weaknesses: {score.weaknesses}")
print(f"Recommendations: {score.recommendations}")
```

---

### 4. Correlation Breakdown Detector (`correlation_breakdown_detector.py`)
**~500 lines** - Detects when historical correlations between assets break down.

**Breakdown Types:**
- `DECORRELATION` - Correlation dropped significantly
- `CORRELATION_FLIP` - Correlation changed sign
- `VOLATILITY_SPIKE` - Correlation unstable due to volatility
- `REGIME_CHANGE` - Correlation changed due to regime shift
- `STRUCTURAL_BREAK` - Permanent structural change
- `TEMPORARY_DIVERGENCE` - Short-term divergence

**Key Classes:**
- `CorrelationBreakdownDetector` - Main detector
- `PairCorrelation` - Correlation data for a pair
- `CorrelationAlert` - Alert for breakdown
- `CorrelationCalculator` - Rolling correlation calculator

**Usage:**
```python
from trading_bot.observability import CorrelationBreakdownDetector

detector = CorrelationBreakdownDetector()

# Add pairs to monitor
detector.add_pair("BTCUSDT", "ETHUSDT", expected_correlation=0.85)
detector.add_pair("EURUSD", "GBPUSD", expected_correlation=0.75)

# Update with returns
alerts = detector.update("BTCUSDT", 0.02)  # 2% return
alerts = detector.update("ETHUSDT", -0.01)  # -1% return

# Check for breakdowns
for alert in alerts:
    print(f"BREAKDOWN: {alert.pair_id} - {alert.breakdown_type.name}")
    print(f"  Current: {alert.current_correlation:.2f}")
    print(f"  Expected: {alert.expected_correlation:.2f}")

# Get correlation matrix
matrix = detector.get_correlation_matrix(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
```

---

### 5. Strategy Kill Switch Registry (`strategy_kill_switch.py`)
**~600 lines** - Centralized registry for strategy enable/disable control.

**Kill Reasons:**
- `MANUAL` - Manual kill by operator
- `DRAWDOWN_LIMIT` - Exceeded drawdown threshold
- `LOSS_LIMIT` - Exceeded loss limit
- `WIN_RATE_DECAY` - Win rate dropped below threshold
- `CORRELATION_BREAKDOWN` - Correlation assumptions violated
- `REGIME_MISMATCH` - Strategy not suited for current regime
- `EXECUTION_ISSUES` - Execution quality problems
- `EMERGENCY` - Emergency shutdown

**Strategy Statuses:**
- `ACTIVE` - Fully operational
- `KILLED` - No trading allowed
- `PROBATION` - Re-enabled with restrictions
- `PAUSED` - Temporarily paused
- `WARMING_UP` - Warming up after restart

**Key Classes:**
- `StrategyKillSwitchRegistry` - Main registry
- `KillSwitch` - Kill switch state
- `StrategyHealth` - Health metrics
- `AutoKillMonitor` - Auto-kill condition checker

**Usage:**
```python
from trading_bot.observability import StrategyKillSwitchRegistry, KillReason, StrategyHealth

registry = StrategyKillSwitchRegistry()

# Register strategies
registry.register_strategy("momentum_v1")
registry.register_strategy("mean_reversion_v1")

# Check if allowed to trade
allowed, reason = registry.is_allowed("momentum_v1")
if not allowed:
    print(f"Trading blocked: {reason}")

# Manual kill
registry.kill(
    "momentum_v1",
    KillReason.MANUAL,
    message="Performance review required",
    killed_by="operator",
)

# Update health for auto-kill monitoring
health = StrategyHealth(
    strategy_id="mean_reversion_v1",
    is_healthy=True,
    health_score=75.0,
    win_rate=0.52,
    profit_factor=1.3,
    sharpe_ratio=1.2,
    max_drawdown=0.08,
    current_drawdown=0.04,
    daily_pnl=0.005,
    weekly_pnl=0.02,
    trade_count=50,
)

kill_reason = registry.update_health("mean_reversion_v1", health)
if kill_reason:
    print(f"Strategy auto-killed: {kill_reason.name}")

# Re-enable with probation
success, msg = registry.reenable("momentum_v1", with_probation=True)

# Global kill (emergency)
registry.global_kill("Market crash detected", killed_by="risk_system")
```

---

## Integration Example

```python
from trading_bot.observability import (
    UnifiedObservabilityHub,
    PreTradeGateOrchestrator,
    TradeQualityGrader,
    CorrelationBreakdownDetector,
    StrategyKillSwitchRegistry,
    PreTradeCheck,
    StrategyHealth,
    AlertSeverity,
    KillReason,
)

# Initialize all components
hub = UnifiedObservabilityHub()
gates = PreTradeGateOrchestrator()
grader = TradeQualityGrader()
correlation = CorrelationBreakdownDetector()
kill_switch = StrategyKillSwitchRegistry()

# Register components with hub
hub.register_component("gates", version="1.0")
hub.register_component("grader", version="1.0")
hub.register_component("correlation", version="1.0")
hub.register_component("kill_switch", version="1.0")

# Connect kill switch to correlation alerts
def on_correlation_breakdown(alert):
    if alert.severity.name == "CRITICAL":
        # Kill affected strategies
        kill_switch.kill(
            "pairs_trading",
            KillReason.CORRELATION_BREAKDOWN,
            f"Correlation breakdown: {alert.pair_id}",
        )

# Trading loop integration
async def process_signal(signal):
    strategy_id = signal["strategy_id"]
    
    # 1. Check kill switch
    allowed, reason = kill_switch.is_allowed(strategy_id)
    if not allowed:
        hub.record_counter("signals_blocked", 1, component="kill_switch")
        return None
    
    # 2. Pre-trade validation
    trade = PreTradeCheck(
        check_id=signal["id"],
        symbol=signal["symbol"],
        direction=signal["direction"],
        quantity=signal["quantity"],
        price=signal["price"],
        strategy_id=strategy_id,
        signal_confidence=signal["confidence"],
    )
    
    passed, results = gates.validate(trade, get_context())
    if not passed:
        hub.record_counter("trades_rejected", 1, component="gates")
        return None
    
    # 3. Execute trade
    execution_result = await execute_trade(trade)
    
    # 4. Grade trade quality
    score = grader.grade_trade(
        trade.check_id,
        {**signal, **execution_result},
        get_market_context(),
    )
    
    hub.record_gauge("trade_quality", score.overall_score, component="grader")
    
    # 5. Update strategy health
    health = calculate_strategy_health(strategy_id)
    kill_switch.update_health(strategy_id, health)
    
    return execution_result
```

---

## Summary

| Module | Lines | Purpose |
|--------|-------|---------|
| `unified_observability_hub.py` | ~550 | Centralized monitoring & alerting |
| `pre_trade_gate.py` | ~550 | Multi-layer pre-trade validation |
| `trade_quality_grader.py` | ~650 | Trade quality scoring (A+ to F) |
| `correlation_breakdown_detector.py` | ~500 | Correlation breakdown detection |
| `strategy_kill_switch.py` | ~600 | Strategy enable/disable control |
| **Total** | **~2,850** | |

## Files Created

```
trading_bot/observability/
├── __init__.py
├── unified_observability_hub.py
├── pre_trade_gate.py
├── trade_quality_grader.py
├── correlation_breakdown_detector.py
└── strategy_kill_switch.py
```

## Status

**100% COMPLETE** - All 5 modules implemented, documented, and ready for production use.
