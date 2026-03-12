# Reality Gates - Preventing AI Stupidity in Live Trading

## Overview

Successfully implemented **6 hard gates** that prevent the trading bot from making decisions based on unrealistic assumptions, bad data, or overfitted models.

**Philosophy**: "AI is a genius in backtest, an idiot in live trading. These gates ensure the idiot never gets to trade."

## Location

```
trading_bot/reality_gates/
├── __init__.py                  # Module exports
├── data_integrity_gate.py       # Gate 1: Data validation
├── walk_forward_gate.py         # Gate 2: Strategy validation
├── execution_realism_gate.py    # Gate 3: Execution costs
├── multiple_testing_gate.py     # Gate 4: P-hacking prevention
├── drift_detection_gate.py      # Gate 5: Regime change detection
├── kill_switch_gate.py          # Gate 6: Emergency stops
└── master_reality_gate.py       # Master orchestrator
```

## The 6 Reality Gates

### Gate 1: Data Integrity Gate
**Purpose**: Validate all incoming data before any decision is made.

**Checks**:
- Completeness - No missing values
- Freshness - Data not stale
- Validity - No impossible values (negative prices, High < Low)
- Consistency - No logical contradictions
- Outliers - Extreme values flagged
- Duplicates - No repeated data

**Anomaly Types Detected**:
- Missing values
- Stale data
- Impossible values
- Extreme outliers
- Timestamp gaps
- Price jumps
- Volume anomalies
- Bid/ask crossed
- Negative prices
- Duplicate data

```python
from trading_bot.reality_gates import DataIntegrityGate

gate = DataIntegrityGate()
result = gate.validate(market_data, 'ohlcv')

if not result.is_usable:
    print("BAD DATA - NO TRADE")
```

### Gate 2: Walk-Forward Validation Gate
**Purpose**: Ensure strategies are properly validated out-of-sample.

**Requirements**:
- Minimum 4 walk-forward periods
- Positive OOS Sharpe ratio (> 0.5)
- Maximum OOS drawdown (< 20%)
- Minimum OOS win rate (> 45%)
- IS/OOS Sharpe ratio < 2.0 (no overfitting)
- Minimum trades per period (30+)

**Detects**:
- Overfitting (large IS/OOS gap)
- Inconsistent performance
- Insufficient validation
- Performance degradation

```python
from trading_bot.reality_gates import WalkForwardGate

gate = WalkForwardGate()
result = gate.validate_strategy('my_strategy', walk_forward_results)

if not result.is_approved:
    print(f"STRATEGY REJECTED: {result.failure_reasons}")
```

### Gate 3: Execution Realism Gate
**Purpose**: Account for real-world execution costs.

**Adjustments**:
- Slippage (based on volatility and size)
- Spread costs (bid/ask)
- Market impact (square-root model)
- Latency costs (price movement during execution)
- Commission costs

**Key Metric**: Minimum edge after costs (10 bps)

```python
from trading_bot.reality_gates import ExecutionRealismGate

gate = ExecutionRealismGate()
result = gate.analyze_trade(
    symbol='EURUSD',
    size=10000,
    price=1.0850,
    expected_return=0.5,
    volatility=0.15,
    spread=0.0002,
    avg_daily_volume=5000000000
)

if not result.is_viable:
    print(f"TRADE NOT VIABLE: {result.adjusted_return}% after costs")
```

### Gate 4: Multiple Testing Correction Gate
**Purpose**: Prevent p-hacking and data snooping.

**Methods**:
- Bonferroni correction
- Holm step-down procedure
- Benjamini-Hochberg FDR
- Deflated Sharpe Ratio (Bailey & Lopez de Prado)

**Tracks**:
- Number of strategies tested
- Parameter combinations tried
- Data reuse count
- Search space size

```python
from trading_bot.reality_gates import MultipleTestingGate

gate = MultipleTestingGate()

# Register test BEFORE running backtest
gate.register_test(
    strategy_id='my_strategy',
    num_parameters=10,
    parameter_ranges={'fast_ma': (5, 50), 'slow_ma': (20, 200)},
    data_hash='dataset_001'
)

# Correct results AFTER backtest
result = gate.correct_results(
    strategy_id='my_strategy',
    observed_sharpe=2.5,
    observed_pvalue=0.01,
    num_trades=100,
    backtest_years=3
)

print(f"Deflated Sharpe: {result.deflated_sharpe}")  # Much lower!
```

### Gate 5: Drift Detection Gate
**Purpose**: Detect when market conditions have changed.

**Drift Types**:
- **Concept Drift** - Feature-target relationship changed
- **Data Drift** - Input distribution changed
- **Regime Drift** - Market regime changed
- **Correlation Drift** - Asset correlations changed
- **Volatility Drift** - Volatility regime changed
- **Performance Drift** - Strategy performance degraded

**Actions**:
- Minor drift: Log and monitor
- Moderate drift: Reduce position sizes
- Severe drift: Halt new trades
- Critical drift: Close all positions

```python
from trading_bot.reality_gates import DriftDetectionGate

gate = DriftDetectionGate()
status = gate.check_drift(
    features={'trend': 0.2, 'momentum': 0.15},
    current_volatility=0.45,
    current_regime='volatile'
)

if status.should_halt_trading:
    print("DRIFT DETECTED - TRADING HALTED")
```

### Gate 6: Kill Switch Gate
**Purpose**: Automatic emergency stops.

**Triggers**:
- Drawdown exceeds threshold (3% daily, 7% weekly, 15% total)
- Loss rate exceeds threshold (50% in 1h, 60% in 24h)
- Consecutive losses (5+)
- Volatility spike (3x normal)
- Execution failures (3+)
- Data feed failures (5+)
- Black swan events (-5% single period)

**Features**:
- Multiple independent triggers
- Automatic position closing
- Cooldown period (30 min)
- Auto-reset (24 hours)
- Manual override capability

```python
from trading_bot.reality_gates import KillSwitchGate

gate = KillSwitchGate()
is_allowed, reasons = gate.check(
    current_equity=100000,
    current_return=-0.03,
    current_volatility=0.45,
    trade_result={'pnl': -500}
)

if not is_allowed:
    print(f"KILL SWITCH TRIGGERED: {reasons}")
```

## Master Reality Gate

The `MasterRealityGate` orchestrates all 6 gates into a single check:

```python
from trading_bot.reality_gates import create_reality_gate

gate = create_reality_gate()

# Register strategy first
gate.register_strategy(
    strategy_id='my_strategy',
    num_parameters=5,
    parameter_ranges={'param1': (1, 10)},
    data_hash='my_data',
    walk_forward_results=[...]
)

# Check before every trade
result = gate.check(
    market_data=market_data,
    strategy_id='my_strategy',
    symbol='EURUSD',
    side='buy',
    size=10000,
    price=1.0860,
    expected_return=0.5,
    current_equity=100000,
    current_volatility=0.15,
    avg_daily_volume=5000000000,
    spread=0.0002
)

if result.is_approved:
    # Apply multipliers
    adjusted_confidence = signal_confidence * result.final_confidence_multiplier
    adjusted_size = position_size * result.final_position_size_multiplier
    execute_trade(adjusted_size)
else:
    print(f"BLOCKED BY: {result.blocking_gates}")
    print(f"REASONS: {result.blocking_reasons}")
```

## Integration with Trading Loop

```python
from trading_bot.reality_gates import create_reality_gate

class TradingBot:
    def __init__(self):
        self.reality_gate = create_reality_gate()
        
    async def on_signal(self, signal):
        # EVERY signal must pass through reality gate
        result = self.reality_gate.check(
            market_data=self.current_market_data,
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            side=signal.side,
            size=signal.size,
            price=signal.price,
            expected_return=signal.expected_return,
            current_equity=self.portfolio.equity,
            current_volatility=self.market.volatility,
            avg_daily_volume=self.market.adv,
            spread=self.market.spread
        )
        
        if not result.is_approved:
            logger.warning(f"Signal blocked: {result.blocking_reasons}")
            return
        
        # Apply reality adjustments
        adjusted_size = signal.size * result.final_position_size_multiplier
        adjusted_confidence = signal.confidence * result.final_confidence_multiplier
        
        if adjusted_confidence < 0.3:
            logger.info("Confidence too low after adjustment")
            return
        
        # Execute with adjusted parameters
        await self.execute(signal, adjusted_size)
```

## Demo

Run the demo to see all gates in action:

```bash
python examples/reality_gates_demo.py
```

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `data_integrity_gate.py` | ~450 | Data validation |
| `walk_forward_gate.py` | ~400 | Strategy validation |
| `execution_realism_gate.py` | ~400 | Execution costs |
| `multiple_testing_gate.py` | ~450 | P-hacking prevention |
| `drift_detection_gate.py` | ~500 | Regime change detection |
| `kill_switch_gate.py` | ~550 | Emergency stops |
| `master_reality_gate.py` | ~450 | Master orchestrator |
| `__init__.py` | ~80 | Module exports |
| **Total** | **~3,280** | **Complete reality gate system** |

## Key Principles

1. **ALL gates must pass** - One failure = No trade
2. **No exceptions** - Even for "obvious" trades
3. **Fail-safe default** - When in doubt, don't trade
4. **Automatic response** - Faster than human reaction
5. **Multiple redundancy** - Many independent checks
6. **Continuous monitoring** - Every tick, every trade

## Why This Matters

| Problem | Without Gates | With Gates |
|---------|---------------|------------|
| Bad data | Trade on garbage | Block immediately |
| Overfit strategy | Deploy and lose | Reject before live |
| Execution costs | Ignore, lose edge | Account for reality |
| P-hacking | False confidence | Deflated Sharpe |
| Regime change | Keep losing | Detect and adapt |
| Drawdown | Blow up account | Auto-stop |

## Status

**COMPLETE** - All 6 reality gates implemented and integrated.

## Next Steps

1. Run demo: `python examples/reality_gates_demo.py`
2. Integrate with main trading loop
3. Configure thresholds for your risk tolerance
4. Monitor gate statistics
5. Tune based on live performance
