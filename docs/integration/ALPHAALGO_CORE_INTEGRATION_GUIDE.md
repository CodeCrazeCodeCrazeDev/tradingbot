# AlphaAlgo Core Integration Guide

**Version**: 1.0  
**Date**: 2026-01-27  
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Integration Patterns](#integration-patterns)
4. [MSOS Integration](#msos-integration)
5. [SurvivalCore Integration](#survivalcore-integration)
6. [Signal Generator Integration](#signal-generator-integration)
7. [Risk Manager Integration](#risk-manager-integration)
8. [Main Loop Integration](#main-loop-integration)
9. [Configuration](#configuration)
10. [Monitoring & Debugging](#monitoring--debugging)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview

AlphaAlgo Core is a **hostile capital-preserving quantitative decision engine** that evaluates all trades through a 7-stage adversarial pipeline:

1. **Market Hostility Check** - Block trading in hostile markets
2. **Claim Graph Construction** - Decompose trades into falsifiable claims
3. **Orthogonal Evaluation** - Independent perspective validation
4. **Adversarial Committee** - Internal agents challenge the trade
5. **Confidence Vector** - Multi-dimensional confidence (no single scores)
6. **Decision Gate** - Unified approval gate
7. **Position Sizing** - Confidence-weighted sizing

### Core Principles

- **Markets are adversarial** - Assume hostility
- **Alpha decays** - Time degrades edge
- **Most trades are bad** - Bias toward rejection
- **Overconfidence is lethal** - Minimum confidence dominates
- **Inaction is preferred** - No trade > bad trade

---

## Quick Start

### Installation

AlphaAlgo Core is already included in the trading bot. No additional installation required.

### Basic Usage

```python
from trading_bot.core.alphaalgo_core_integration import (
    create_core_integration,
    IntegratedTradeRequest
)

# Initialize
core = create_core_integration(
    confidence_threshold=0.6,
    enable_strict_mode=True
)

# Create trade request
request = IntegratedTradeRequest(
    request_id="trade_001",
    symbol="BTCUSDT",
    direction="long",
    quantity=1.0,
    entry_price=50000.0,
    stop_loss=49000.0,
    signal_strength=0.75,
    current_equity=100000.0,
    current_drawdown=0.05
)

# Evaluate
decision = await core.evaluate_trade_request(request)

if decision.approved:
    print(f"✅ APPROVED: {decision.approved_quantity} units")
else:
    print(f"❌ REJECTED: {decision.rejection_reason}")
```

---

## Integration Patterns

### Pattern 1: Pre-Execution Gate

Use AlphaAlgo Core as a **final gate** before execution:

```python
async def execute_trade(signal):
    # Convert signal to request
    request = IntegratedTradeRequest(
        request_id=signal['id'],
        symbol=signal['symbol'],
        direction=signal['direction'],
        quantity=signal['quantity'],
        entry_price=signal['price'],
        stop_loss=signal['stop_loss'],
        signal_strength=signal['confidence'],
        current_equity=portfolio.equity,
        current_drawdown=portfolio.drawdown
    )
    
    # Evaluate through AlphaAlgo Core
    decision = await core.evaluate_trade_request(request)
    
    if not decision.approved:
        logger.warning(f"Trade rejected: {decision.rejection_reason}")
        return None
    
    # Execute with approved size
    return broker.execute(
        symbol=signal['symbol'],
        direction=signal['direction'],
        quantity=decision.approved_quantity
    )
```

### Pattern 2: Signal Validation

Use AlphaAlgo Core to **validate signals** before they enter the system:

```python
async def validate_signal(signal):
    request = convert_signal_to_request(signal)
    decision = await core.evaluate_trade_request(request)
    
    if decision.approved:
        signal['validated'] = True
        signal['approved_quantity'] = decision.approved_quantity
        signal['confidence_breakdown'] = decision.confidence_breakdown
        return signal
    else:
        logger.info(f"Signal rejected: {decision.rejection_reason}")
        return None
```

### Pattern 3: Multi-Layer Defense

Use AlphaAlgo Core as **one layer** in a multi-layer defense:

```python
async def multi_layer_validation(signal):
    # Layer 1: MSOS
    msos_result = await msos.evaluate(signal)
    if not msos_result.can_trade:
        return REJECT("MSOS rejected")
    
    # Layer 2: AlphaAlgo Core (Adversarial)
    request = convert_signal_to_request(signal)
    core_decision = await core.evaluate_trade_request(request)
    if not core_decision.approved:
        return REJECT(f"Core rejected: {core_decision.rejection_reason}")
    
    # Layer 3: Risk Manager
    risk_result = risk_manager.validate(signal, core_decision.approved_quantity)
    if not risk_result.approved:
        return REJECT("Risk manager rejected")
    
    # All layers passed
    return APPROVE(core_decision.approved_quantity)
```

---

## MSOS Integration

### Using MSOSAdapter

```python
from trading_bot.core.alphaalgo_core_integration import create_msos_adapter

# Initialize
msos_adapter = create_msos_adapter()

# Evaluate MSOS signal
approved, position_size, reason = await msos_adapter.evaluate_msos_signal(
    symbol="EURUSD",
    signal_data={
        'direction': 'long',
        'quantity': 1.0,
        'price': 1.0850,
        'stop_loss': 1.0800,
        'confidence': 0.75,
        'regime': 'trending',
        'volatility': 0.15,
        'liquidity_score': 0.8
    },
    strategy_config={
        'strategy_id': 'trend_follower_v1'
    },
    equity=100000.0
)

if approved:
    execute_trade(symbol, position_size)
else:
    logger.info(f"MSOS signal rejected: {reason}")
```

### Integration with MSOS Orchestrator

```python
from trading_bot.msos import MSOSOrchestrator
from trading_bot.core.alphaalgo_core_integration import create_msos_adapter

class EnhancedMSOSOrchestrator(MSOSOrchestrator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alphaalgo_adapter = create_msos_adapter()
    
    async def evaluate(self, strategy_id, symbol, market_data, strategy_config, equity):
        # Original MSOS evaluation
        msos_result = await super().evaluate(
            strategy_id, symbol, market_data, strategy_config, equity
        )
        
        if not msos_result.is_tradable:
            return msos_result
        
        # Additional AlphaAlgo Core evaluation
        approved, size, reason = await self.alphaalgo_adapter.evaluate_msos_signal(
            symbol=symbol,
            signal_data={
                'direction': 'long',  # Extract from msos_result
                'quantity': msos_result.max_exposure,
                'price': market_data['close'].iloc[-1],
                'confidence': 0.7,  # Extract from msos_result
                'regime': 'trending',  # Extract from regime detector
                'volatility': market_data['returns'].std(),
                'liquidity_score': 0.7
            },
            strategy_config=strategy_config,
            equity=equity
        )
        
        if not approved:
            logger.warning(f"AlphaAlgo Core rejected MSOS signal: {reason}")
            msos_result.can_trade = False
            msos_result.max_exposure = 0.0
        else:
            msos_result.max_exposure = min(msos_result.max_exposure, size)
        
        return msos_result
```

---

## SurvivalCore Integration

### Using SurvivalCoreAdapter

```python
from trading_bot.core.alphaalgo_core_integration import create_survival_core_adapter

# Initialize
survival_adapter = create_survival_core_adapter()

# Validate signal
approved, reason = await survival_adapter.validate_survival_signal(
    signal={
        'signal_id': 'sig_001',
        'symbol': 'BTCUSDT',
        'direction': 'long',
        'quantity': 1.0,
        'price': 50000.0,
        'stop_loss': 49000.0,
        'confidence': 0.75,
        'strategy': 'momentum_v1'
    },
    portfolio_state={
        'equity': 100000.0,
        'drawdown': 0.05
    }
)

if approved:
    execute_signal(signal)
else:
    logger.info(f"Signal rejected: {reason}")
```

### Integration with SurvivalCore

```python
from trading_bot.core.survival_core import SurvivalCore
from trading_bot.core.alphaalgo_core_integration import create_survival_core_adapter

class EnhancedSurvivalCore(SurvivalCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alphaalgo_adapter = create_survival_core_adapter()
    
    async def process_signal(self, signal):
        # Original SurvivalCore validation
        if not self.validate_signal(signal):
            return None
        
        # Additional AlphaAlgo Core validation
        approved, reason = await self.alphaalgo_adapter.validate_survival_signal(
            signal=signal,
            portfolio_state={
                'equity': self.get_equity(),
                'drawdown': self.get_drawdown()
            }
        )
        
        if not approved:
            logger.warning(f"AlphaAlgo Core rejected signal: {reason}")
            return None
        
        return signal
```

---

## Signal Generator Integration

### Wrapping Signal Generators

```python
from trading_bot.core.alphaalgo_core_integration import (
    create_core_integration,
    IntegratedTradeRequest
)

class AlphaAlgoSignalGenerator:
    """Wrapper for any signal generator"""
    
    def __init__(self, base_generator, core_integration=None):
        self.base_generator = base_generator
        self.core = core_integration or create_core_integration()
    
    async def generate_signal(self, symbol, market_data, portfolio):
        # Generate base signal
        base_signal = self.base_generator.generate(symbol, market_data)
        
        if base_signal is None:
            return None
        
        # Convert to request
        request = IntegratedTradeRequest(
            request_id=f"{symbol}_{datetime.utcnow().timestamp()}",
            symbol=symbol,
            direction=base_signal['direction'],
            quantity=base_signal['quantity'],
            entry_price=base_signal['price'],
            stop_loss=base_signal.get('stop_loss'),
            take_profit=base_signal.get('take_profit'),
            signal_strength=base_signal.get('confidence', 0.5),
            signal_source='signal_generator',
            strategy_id=self.base_generator.name,
            current_equity=portfolio.equity,
            current_drawdown=portfolio.drawdown
        )
        
        # Evaluate through AlphaAlgo Core
        decision = await self.core.evaluate_trade_request(request)
        
        if not decision.approved:
            logger.info(f"Signal rejected: {decision.rejection_reason}")
            return None
        
        # Return enhanced signal
        return {
            **base_signal,
            'validated': True,
            'approved_quantity': decision.approved_quantity,
            'confidence_breakdown': decision.confidence_breakdown,
            'risk_score': decision.risk_score
        }
```

### Example: Wrapping Existing Generators

```python
# Original generator
from trading_bot.signals import TrendFollowingSignalGenerator

trend_generator = TrendFollowingSignalGenerator()

# Wrap with AlphaAlgo Core
enhanced_generator = AlphaAlgoSignalGenerator(trend_generator)

# Use enhanced generator
signal = await enhanced_generator.generate_signal(
    symbol='BTCUSDT',
    market_data=df,
    portfolio=portfolio
)

if signal:
    execute(signal)
```

---

## Risk Manager Integration

### Using RiskManagerAdapter

```python
from trading_bot.core.alphaalgo_core_integration import create_risk_manager_adapter

# Initialize
risk_adapter = create_risk_manager_adapter()

# Validate trade
approved, adjusted_size, reason = await risk_adapter.validate_risk_limits(
    trade_request={
        'id': 'trade_001',
        'symbol': 'EURUSD',
        'direction': 'long',
        'quantity': 1.0,
        'price': 1.0850,
        'stop_loss': 1.0800
    },
    portfolio={
        'equity': 100000.0,
        'drawdown': 0.05,
        'correlation': 0.3
    }
)

if approved:
    execute_trade(adjusted_size)
else:
    logger.info(f"Risk check failed: {reason}")
```

---

## Main Loop Integration

### Complete Main Loop Example

```python
import asyncio
from trading_bot.core.alphaalgo_core_integration import create_core_integration

async def main_trading_loop():
    # Initialize AlphaAlgo Core
    core = create_core_integration(
        confidence_threshold=0.6,
        enable_strict_mode=True,
        enable_msos=True,
        enable_survival_core=True
    )
    
    while True:
        try:
            # Get market data
            market_data = await get_market_data()
            
            # Generate signals from multiple sources
            signals = []
            signals.extend(await trend_generator.generate(market_data))
            signals.extend(await momentum_generator.generate(market_data))
            signals.extend(await mean_reversion_generator.generate(market_data))
            
            # Evaluate each signal through AlphaAlgo Core
            for signal in signals:
                request = convert_signal_to_request(signal)
                decision = await core.evaluate_trade_request(request)
                
                if decision.approved:
                    logger.info(f"✅ Signal approved: {signal['symbol']}")
                    await execute_trade(signal, decision.approved_quantity)
                else:
                    logger.debug(f"❌ Signal rejected: {decision.rejection_reason}")
            
            # Get statistics
            stats = core.get_statistics()
            logger.info(f"Core stats: {stats}")
            
            # Wait for next iteration
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_trading_loop())
```

### Integration with Existing Main.py

```python
# Add to existing main.py

from trading_bot.core.alphaalgo_core_integration import create_core_integration

# In main() function, after initialization:
alphaalgo_core = create_core_integration(
    confidence_threshold=config.get('alphaalgo_threshold', 0.6),
    enable_strict_mode=config.get('alphaalgo_strict', True)
)

# In signal processing loop, before execution:
async def process_signal(signal):
    # Convert signal to request
    request = IntegratedTradeRequest(
        request_id=signal.signal_id,
        symbol=signal.symbol,
        direction=signal.direction,
        quantity=signal.quantity,
        entry_price=signal.price,
        stop_loss=signal.stop_loss,
        signal_strength=signal.confidence,
        current_equity=portfolio_manager.get_equity(),
        current_drawdown=portfolio_manager.get_drawdown()
    )
    
    # Evaluate through AlphaAlgo Core
    decision = await alphaalgo_core.evaluate_trade_request(request)
    
    if not decision.approved:
        logger.warning(f"AlphaAlgo Core rejected: {decision.rejection_reason}")
        return None
    
    # Update signal with approved quantity
    signal.quantity = decision.approved_quantity
    
    # Execute
    return await execution_manager.execute(signal)
```

---

## Configuration

### Core Configuration

```python
from trading_bot.core.alphaalgo_core_integration import create_core_integration

core = create_core_integration(
    # Confidence threshold (0.0 to 1.0)
    # Higher = more conservative
    confidence_threshold=0.6,  # Default: 0.6
    
    # Strict mode
    # True = All checks enforced
    # False = Some checks may be relaxed
    enable_strict_mode=True,  # Default: True
    
    # MSOS integration
    enable_msos=True,  # Default: True
    
    # SurvivalCore integration
    enable_survival_core=True  # Default: True
)
```

### Engine Configuration

```python
from trading_bot.core.alphaalgo_core_engine import create_alphaalgo_core

engine = create_alphaalgo_core(
    # Minimum confidence threshold
    required_confidence_threshold=0.6,
    
    # Strict mode
    enable_strict_mode=True
)
```

### Market Context Configuration

```python
market_context = {
    # Recent performance (list of returns)
    'recent_performance': [0.02, -0.01, 0.03, -0.005, 0.01],
    
    # Regime stability (0.0 to 1.0)
    'regime_stability': 0.7,
    
    # Liquidity stress (0.0 to 1.0)
    'liquidity_stress': 0.2,
    
    # Cross-strategy dispersion (0.0 to 1.0)
    'cross_strategy_dispersion': 0.3
}

decision = await core.evaluate_trade_request(request, market_context)
```

---

## Monitoring & Debugging

### Getting Statistics

```python
# Get core statistics
stats = core.get_statistics()

print(f"Total evaluations: {stats['core_engine']['total_evaluations']}")
print(f"Approved: {stats['core_engine']['approved']}")
print(f"Rejected: {stats['core_engine']['rejected']}")
print(f"Market hostile: {stats['core_engine']['market_hostile']}")
print(f"Approval rate: {stats['core_engine']['approval_rate']:.2%}")
print(f"Top rejection reasons: {stats['core_engine']['top_rejection_reasons']}")
```

### Logging Configuration

```python
import logging

# Enable detailed logging
logging.getLogger('trading_bot.core.alphaalgo_core_engine').setLevel(logging.DEBUG)
logging.getLogger('trading_bot.core.alphaalgo_core_integration').setLevel(logging.DEBUG)

# Log to file
handler = logging.FileHandler('alphaalgo_core.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger('trading_bot.core').addHandler(handler)
```

### Decision Inspection

```python
decision = await core.evaluate_trade_request(request)

# Inspect decision details
print(f"Outcome: {decision.outcome.value}")
print(f"Approved: {decision.approved}")
print(f"Rejection reason: {decision.rejection_reason}")
print(f"Min confidence: {decision.min_confidence}")
print(f"Confidence breakdown: {decision.confidence_breakdown}")
print(f"Market hostility: {decision.market_hostility}")
print(f"Risk score: {decision.risk_score}")
print(f"Evaluation time: {decision.evaluation_time_ms:.1f}ms")

# Inspect stage results
print(f"Failed claims: {decision.stage_results['failed_claims']}")
print(f"Killer verdict: {decision.stage_results['killer_verdict']}")
print(f"Agent verdicts: {decision.stage_results['agent_verdicts']}")
```

---

## Best Practices

### 1. Always Use Market Context

```python
# ✅ GOOD: Provide market context
decision = await core.evaluate_trade_request(request, {
    'recent_performance': performance_tracker.get_recent(),
    'regime_stability': regime_detector.stability,
    'liquidity_stress': liquidity_monitor.stress,
    'cross_strategy_dispersion': strategy_monitor.dispersion
})

# ❌ BAD: No market context
decision = await core.evaluate_trade_request(request)
```

### 2. Use Minimum Confidence, Not Average

```python
# ✅ GOOD: Use minimum confidence
if decision.confidence_breakdown:
    min_conf = min(decision.confidence_breakdown.values())
    if min_conf < 0.6:
        reject()

# ❌ BAD: Use average confidence
avg_conf = sum(decision.confidence_breakdown.values()) / len(decision.confidence_breakdown)
```

### 3. Respect Killer Verdicts

```python
# ✅ GOOD: Killer verdict is absolute
if decision.stage_results.get('killer_verdict'):
    logger.warning(f"Killer rejected: {decision.stage_results['killer_verdict']}")
    return REJECT

# ❌ BAD: Override killer verdict
if decision.stage_results.get('killer_verdict'):
    if signal_strength > 0.9:  # DON'T DO THIS
        return APPROVE
```

### 4. Log All Rejections

```python
# ✅ GOOD: Log rejection details
if not decision.approved:
    logger.warning(
        f"Trade rejected: {decision.rejection_reason}\n"
        f"Failed claims: {decision.stage_results['failed_claims']}\n"
        f"Min confidence: {decision.min_confidence}\n"
        f"Market hostility: {decision.market_hostility}"
    )

# ❌ BAD: Silent rejection
if not decision.approved:
    return None
```

### 5. Use Approved Quantity, Not Original

```python
# ✅ GOOD: Use approved quantity
if decision.approved:
    execute_trade(symbol, decision.approved_quantity)

# ❌ BAD: Use original quantity
if decision.approved:
    execute_trade(symbol, request.quantity)  # May be too large
```

---

## Troubleshooting

### Issue: All Trades Rejected

**Symptoms**: Approval rate < 10%

**Possible Causes**:
1. Confidence threshold too high
2. Market hostility too sensitive
3. Signal quality too low

**Solutions**:
```python
# Lower confidence threshold (temporarily)
core = create_core_integration(confidence_threshold=0.5)

# Check market hostility
stats = core.get_statistics()
hostile_rate = stats['core_engine']['market_hostile'] / stats['core_engine']['total_evaluations']
if hostile_rate > 0.5:
    # Market hostility detector too sensitive
    pass

# Check rejection reasons
top_reasons = stats['core_engine']['top_rejection_reasons']
print(top_reasons)  # Identify most common rejection
```

### Issue: Killer Always Rejects

**Symptoms**: All rejections from Killer agent

**Possible Causes**:
1. Signals have failed claims
2. Confidence too low
3. Drawdown too high

**Solutions**:
```python
# Inspect killer verdicts
for decision in recent_decisions:
    if decision.stage_results.get('killer_verdict'):
        print(f"Killer reason: {decision.stage_results['killer_verdict']}")

# Common killer rejections:
# - "Failed claims: [...]" → Fix signal quality
# - "Minimum confidence below threshold" → Improve confidence
# - "Current drawdown too high" → Reduce trading during drawdown
```

### Issue: Integration Not Working

**Symptoms**: AlphaAlgo Core not being called

**Solutions**:
```python
# Verify integration
import logging
logging.getLogger('trading_bot.core.alphaalgo_core_integration').setLevel(logging.DEBUG)

# Check if evaluate_trade_request is called
decision = await core.evaluate_trade_request(request)
# Should see DEBUG logs

# Verify adapters are used
msos_adapter = create_msos_adapter()
approved, size, reason = await msos_adapter.evaluate_msos_signal(...)
# Should see evaluation logs
```

### Issue: Performance Degradation

**Symptoms**: Evaluation time > 100ms

**Solutions**:
```python
# Check evaluation time
decision = await core.evaluate_trade_request(request)
print(f"Evaluation time: {decision.evaluation_time_ms:.1f}ms")

# If > 100ms:
# 1. Reduce market context complexity
# 2. Cache regime detection results
# 3. Optimize claim evaluation
# 4. Consider async parallelization
```

---

## Advanced Usage

### Custom Adversarial Agents

```python
from trading_bot.core.alphaalgo_core_engine import (
    AdversarialCommittee,
    AgentVerdict,
    AgentRole
)

class CustomAdversarialCommittee(AdversarialCommittee):
    def _custom_agent_evaluate(self, proposal):
        """Add custom adversarial agent"""
        # Custom logic to challenge trade
        if proposal.symbol in high_risk_symbols:
            return AgentVerdict(
                agent=AgentRole.KILLER,
                approved=False,
                reason="Symbol on high-risk list",
                severity=1.0
            )
        return AgentVerdict(
            agent=AgentRole.KILLER,
            approved=True,
            reason="Custom check passed",
            severity=0.0
        )
```

### Custom Claim Types

```python
from trading_bot.core.alphaalgo_core_engine import Claim, ClaimType
from enum import auto

class CustomClaimType(ClaimType):
    NEWS_SENTIMENT = auto()
    SOCIAL_SENTIMENT = auto()

# Add custom claims
custom_claim = Claim(
    claim_type=CustomClaimType.NEWS_SENTIMENT,
    description="News sentiment is positive",
    testable=True,
    historical_reference="news_sentiment_history"
)
```

---

## Summary

AlphaAlgo Core provides **hostile capital-preserving** decision-making through:

1. ✅ **7-stage adversarial evaluation**
2. ✅ **Multi-dimensional confidence** (no single scores)
3. ✅ **Adversarial committee** (Killer has veto power)
4. ✅ **Market hostility detection**
5. ✅ **Unified decision gate**
6. ✅ **Confidence-weighted position sizing**

### Integration Checklist

- [ ] Initialize AlphaAlgo Core in main loop
- [ ] Route all signals through `evaluate_trade_request`
- [ ] Use `MSOSAdapter` for MSOS integration
- [ ] Use `SurvivalCoreAdapter` for SurvivalCore integration
- [ ] Replace single confidence scores with vectors
- [ ] Use approved quantity, not original
- [ ] Log all rejections with details
- [ ] Monitor statistics regularly
- [ ] Respect Killer verdicts (no override)
- [ ] Provide market context for all evaluations

### Next Steps

1. **Integrate with main loop** - Add to `main.py`
2. **Wrap signal generators** - Use `AlphaAlgoSignalGenerator`
3. **Monitor performance** - Track approval rates and rejection reasons
4. **Tune thresholds** - Adjust confidence threshold based on results
5. **Review rejections** - Analyze top rejection reasons weekly

---

**Documentation Complete**  
**Status**: Ready for Production Integration
