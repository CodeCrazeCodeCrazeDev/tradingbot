# Quick Start Guide - Newly Integrated Modules

## Overview

This guide shows you how to immediately start using the newly integrated modules in AlphaAlgo.

---

## 1. Orchestrator System

### Basic Usage

```python
from trading_bot import MasterOrchestrator, TradingMode
from trading_bot.data import MT5Interface

# Initialize MT5
mt5 = MT5Interface()

# Create orchestrator
orchestrator = MasterOrchestrator(
    mt5_interface=mt5,
    symbol="EURUSD",
    trading_mode=TradingMode.BALANCED  # or AGGRESSIVE, CONSERVATIVE, DEFENSIVE
)

# Run the orchestrator
await orchestrator.run()
```

### Available Trading Modes

- `TradingMode.AGGRESSIVE` - High risk, high reward
- `TradingMode.BALANCED` - Moderate risk/reward
- `TradingMode.CONSERVATIVE` - Low risk, steady gains
- `TradingMode.DEFENSIVE` - Capital preservation
- `TradingMode.SCALPING` - Quick in/out trades
- `TradingMode.SWING` - Multi-day positions
- `TradingMode.POSITION` - Long-term holds

### Advanced Features

```python
from trading_bot.orchestrator import (
    ExecutionEngine,
    ExecutionAlgorithm,
    PortfolioRiskManager
)

# Smart execution
execution_engine = ExecutionEngine(
    algorithm=ExecutionAlgorithm.VWAP  # or TWAP, ADAPTIVE, SNIPER
)

# Advanced risk management
risk_manager = PortfolioRiskManager(
    max_portfolio_risk=0.02,  # 2% max risk
    max_correlated_exposure=0.5,  # 50% max in correlated assets
    use_kelly_criterion=True
)
```

---

## 2. Opportunity Scanner

### Scan for All Opportunities

```python
from trading_bot.opportunity_scanner import (
    MarketInefficiencyScanner,
    NewsImpactAnalyzer,
    MomentumBurstDetector,
    VolatilityArbitrage
)

# Initialize scanners
scanners = [
    MarketInefficiencyScanner(),
    NewsImpactAnalyzer(api_key="your_newsapi_key"),
    MomentumBurstDetector(),
    VolatilityArbitrage()
]

# Scan for opportunities
all_opportunities = []
for scanner in scanners:
    opportunities = await scanner.scan(market_data)
    all_opportunities.extend(opportunities)

# Filter high-confidence opportunities
best_opps = [
    opp for opp in all_opportunities 
    if opp.confidence > 0.7 and opp.expected_return > 0.02
]

# Sort by expected value
best_opps.sort(key=lambda x: x.confidence * x.expected_return, reverse=True)

# Take top 5
top_opportunities = best_opps[:5]
```

### Specific Opportunity Types

```python
# Market Inefficiency
from trading_bot.opportunity_scanner import MarketInefficiencyScanner, InefficiencyType

scanner = MarketInefficiencyScanner()
inefficiencies = await scanner.scan(market_data)

for ineff in inefficiencies:
    if ineff.type == InefficiencyType.PRICE_DISLOCATION:
        print(f"Price dislocation: {ineff.symbol} - Expected return: {ineff.expected_return:.2%}")

# Arbitrage
from trading_bot.opportunity_scanner import CrossExchangeArbitrage

arbitrage = CrossExchangeArbitrage(
    exchanges=["binance", "coinbase", "kraken"]
)
arb_opportunities = await arbitrage.find_opportunities()

# News Trading
from trading_bot.opportunity_scanner import NewsImpactAnalyzer

news_analyzer = NewsImpactAnalyzer(api_key="your_key")
news_opportunities = await news_analyzer.analyze_recent_news(
    symbols=["EURUSD", "GBPUSD", "USDJPY"]
)

# Momentum
from trading_bot.opportunity_scanner import MomentumBurstDetector

momentum = MomentumBurstDetector()
momentum_signals = await momentum.detect_bursts(market_data)
```

---

## 3. Exit Strategies

### Basic Exit Management

```python
from trading_bot.exit_strategies import (
    ExitSignalGenerator,
    AdaptiveExitStrategy,
    ProfitMaximizer
)

# Create exit signal generator
exit_gen = ExitSignalGenerator(
    strategies=[
        AdaptiveExitStrategy(),
        ProfitMaximizer()
    ]
)

# Generate exit signals for current position
exit_signals = exit_gen.generate_signals(
    position=current_position,
    market_data=latest_data,
    trade_history=recent_trades
)

# Process signals
for signal in exit_signals:
    if signal.strength > 0.8:  # Very strong signal
        await executor.close_position(
            position_id=signal.position_id,
            size=signal.exit_size,
            reason=signal.reason
        )
```

### Dynamic Trade Management

```python
from trading_bot.exit_strategies import DynamicTradeManager, TradeHealth

# Create trade manager
trade_manager = DynamicTradeManager()

# Monitor trade health
health = trade_manager.assess_trade_health(
    position=current_position,
    market_data=latest_data
)

if health == TradeHealth.CRITICAL:
    # Exit immediately
    await executor.close_position(current_position.id)
elif health == TradeHealth.POOR:
    # Reduce position size
    await executor.reduce_position(current_position.id, by_percent=50)
elif health == TradeHealth.EXCELLENT:
    # Consider adding to position
    await executor.increase_position(current_position.id, by_percent=25)
```

### Profit Maximization

```python
from trading_bot.exit_strategies import ProfitMaximizer, RiskRewardOptimizer

# Create profit maximizer
profit_max = ProfitMaximizer()

# Optimize exit levels
optimal_exits = profit_max.calculate_optimal_exits(
    entry_price=current_position.entry_price,
    current_price=latest_price,
    market_conditions=market_analysis
)

print(f"Take Profit 1: {optimal_exits.tp1} (30% position)")
print(f"Take Profit 2: {optimal_exits.tp2} (40% position)")
print(f"Take Profit 3: {optimal_exits.tp3} (30% position)")
print(f"Trailing Stop: {optimal_exits.trailing_stop}")
```

---

## 4. Complete Integration Example

### Full Trading System with All Modules

```python
import asyncio
from trading_bot import (
    MasterOrchestrator,
    TradingMode,
    MarketInefficiencyScanner,
    NewsImpactAnalyzer,
    MomentumBurstDetector,
    ExitSignalGenerator,
    AdaptiveExitStrategy,
    ProfitMaximizer
)
from trading_bot.data import MT5Interface

async def run_integrated_trading_system():
    """Complete trading system using all integrated modules."""
    
    # 1. Initialize MT5
    mt5 = MT5Interface()
    
    # 2. Initialize Opportunity Scanners
    scanners = [
        MarketInefficiencyScanner(),
        NewsImpactAnalyzer(api_key="your_key"),
        MomentumBurstDetector()
    ]
    
    # 3. Initialize Exit Management
    exit_generator = ExitSignalGenerator(
        strategies=[
            AdaptiveExitStrategy(),
            ProfitMaximizer()
        ]
    )
    
    # 4. Initialize Orchestrator
    orchestrator = MasterOrchestrator(
        mt5_interface=mt5,
        symbol="EURUSD",
        trading_mode=TradingMode.BALANCED,
        opportunity_scanners=scanners,
        exit_generator=exit_generator
    )
    
    # 5. Run the system
    print("Starting integrated trading system...")
    await orchestrator.run()

# Run
if __name__ == "__main__":
    asyncio.run(run_integrated_trading_system())
```

---

## 5. Command-Line Usage

### Run with Orchestrator Mode

```bash
# Basic orchestrator mode
py main.py --symbol EURUSD --mode paper --orchestrator-mode

# With specific trading mode
py main.py --symbol EURUSD --mode paper --orchestrator-mode --trading-mode aggressive

# With opportunity scanning
py main.py --symbol EURUSD --mode paper --orchestrator-mode --enable-scanners

# With advanced exits
py main.py --symbol EURUSD --mode paper --orchestrator-mode --advanced-exits

# Full integration
py main.py --symbol EURUSD --mode paper --orchestrator-mode --enable-scanners --advanced-exits --trading-mode balanced
```

---

## 6. Configuration Files

### Create orchestrator_config.yaml

```yaml
orchestrator:
  trading_mode: balanced
  max_positions: 5
  max_risk_per_trade: 0.02
  
execution:
  algorithm: vwap
  slippage_tolerance: 0.0005
  
risk_management:
  use_kelly_criterion: true
  max_portfolio_risk: 0.05
  max_correlated_exposure: 0.5
  
performance:
  track_metrics: true
  auto_optimize: true
  optimization_interval: 3600  # 1 hour
```

### Create opportunity_config.yaml

```yaml
scanners:
  market_inefficiency:
    enabled: true
    min_confidence: 0.6
    
  news_trading:
    enabled: true
    api_key: "your_newsapi_key"
    min_impact: 0.7
    
  momentum:
    enabled: true
    lookback_periods: [5, 10, 20]
    
  volatility:
    enabled: true
    min_vol_ratio: 1.5
```

### Create exit_strategies_config.yaml

```yaml
exit_strategies:
  adaptive:
    enabled: true
    volatility_multiplier: 2.0
    
  profit_maximizer:
    enabled: true
    take_profit_levels: [0.02, 0.04, 0.06]
    
  dynamic_management:
    enabled: true
    health_check_interval: 300  # 5 minutes
```

---

## 7. Testing

### Validate Integrations

```bash
# Run validation script
py validate_integrations.py

# Expected output:
# [OK] Orchestrator modules imported successfully
# [OK] Opportunity Scanner modules imported successfully
# [OK] Exit Strategies modules imported successfully
# [OK] Root-level imports working
# [SUCCESS] All integrations validated successfully!
```

### Paper Trading Test

```bash
# Test with paper trading
py main.py --symbol EURUSD --mode paper --orchestrator-mode --bars 1000

# Monitor output for:
# - Opportunity detection logs
# - Trade execution logs
# - Exit signal logs
# - Performance metrics
```

---

## 8. Monitoring

### Check System Status

```python
from trading_bot.orchestrator import MasterOrchestrator

# Get orchestrator status
status = orchestrator.get_status()

print(f"Active Positions: {status.active_positions}")
print(f"Opportunities Scanned: {status.opportunities_scanned}")
print(f"Trades Today: {status.trades_today}")
print(f"Win Rate: {status.win_rate:.2%}")
print(f"Sharpe Ratio: {status.sharpe_ratio:.2f}")
```

### Performance Metrics

```python
from trading_bot.orchestrator import PerformanceTracker

tracker = PerformanceTracker()
metrics = tracker.get_metrics()

print(f"Total Return: {metrics.total_return:.2%}")
print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"Profit Factor: {metrics.profit_factor:.2f}")
print(f"Average Win: ${metrics.avg_win:.2f}")
print(f"Average Loss: ${metrics.avg_loss:.2f}")
```

---

## 9. Troubleshooting

### Import Errors

If you get import errors:

```bash
# Verify integrations
py validate_integrations.py

# Check Python path
py -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
pip install -r requirements.txt
```

### Configuration Errors

If configuration files are missing:

```bash
# Create default configs
py -c "from trading_bot.orchestrator import create_default_config; create_default_config()"
```

### Runtime Errors

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in main.py
py main.py --log-level DEBUG --orchestrator-mode
```

---

## 10. Next Steps

1. **Test in Paper Mode** - Run with `--mode paper` first
2. **Monitor Performance** - Track metrics for at least 1 week
3. **Optimize Parameters** - Tune configurations based on results
4. **Gradual Rollout** - Start with one module, add more incrementally
5. **Live Trading** - Only after thorough paper trading validation

---

## Support

- **Documentation**: See INTEGRATION_STRATEGY.md for detailed implementation
- **Analysis**: See ORPHAN_MODULE_REPORT.md for module details
- **Summary**: See INTEGRATION_COMPLETE_SUMMARY.md for overview

---

**Status**: Ready to Use ✅  
**Validation**: 100% Pass Rate ✅  
**Backward Compatible**: Yes ✅  
**Production Ready**: After paper trading validation ✅
