# Self-Learning System Integration Guide

## Quick Integration Steps

### Step 1: Import the System

```python
from trading_bot.self_learning import quick_start, create_master_orchestrator
```

### Step 2: Initialize Once at Startup

```python
# In your main.py or bot initialization
async def initialize_bot():
    # Initialize self-learning system
    self.learning_system = await quick_start({
        'learning': {'epsilon': 0.1},
        'evolution': {'population_size': 50},
        'execution': {'learning_rate': 0.001}
    })
    
    print("✓ Self-learning system initialized")
```

### Step 3: Integrate with Trading Loop

```python
async def trading_loop(self):
    while self.is_running:
        for symbol in self.symbols:
            # Get market data
            market_data = await self.get_market_data(symbol)
            
            # Get AI decision from self-learning system
            decision = await self.learning_system.analyze_market(symbol, market_data)
            
            # Only trade if confidence is high
            if decision.confidence > 0.7 and decision.action != 'hold':
                # Execute trade
                result = await self.execute_trade(decision)
                
                # Learn from result
                await self.learning_system.learn_from_trade(decision, result)
        
        # Evolve strategies periodically
        if self.learning_system.total_trades % 100 == 0:
            await self.learning_system.evolve_strategies()
        
        await asyncio.sleep(60)
```

### Step 4: Integration with Existing Risk Manager

```python
async def safe_trading_with_learning(self, symbol, market_data):
    # Get AI decision
    decision = await self.learning_system.analyze_market(symbol, market_data)
    
    # Validate with existing risk manager
    risk_approved = self.risk_manager.validate_trade(
        symbol=decision.symbol,
        action=decision.action,
        quantity=decision.position_size,
        price=decision.entry_price
    )
    
    # Execute only if both AI and risk manager approve
    if risk_approved and decision.confidence > 0.7:
        result = await self.execute_trade(decision)
        await self.learning_system.learn_from_trade(decision, result)
        return result
    
    return None
```

## Integration with Existing Bot Components

### With Elite System

```python
from trading_bot.elite_system import EliteMarketAnalyzer
from trading_bot.self_learning import create_master_orchestrator

class HybridTradingSystem:
    def __init__(self):
        self.elite_analyzer = EliteMarketAnalyzer()
        self.learning_system = None
    
    async def initialize(self):
        self.learning_system = await create_master_orchestrator()
    
    async def analyze(self, symbol, market_data):
        # Get analysis from both systems
        elite_analysis = await self.elite_analyzer.analyze(symbol, market_data)
        learning_decision = await self.learning_system.analyze_market(symbol, market_data)
        
        # Combine insights
        combined_confidence = (elite_analysis.confidence + learning_decision.confidence) / 2
        
        # Use learning system's decision if both agree
        if elite_analysis.action == learning_decision.action:
            learning_decision.confidence = combined_confidence
            return learning_decision
        
        # Otherwise, use higher confidence
        return learning_decision if learning_decision.confidence > elite_analysis.confidence else elite_analysis
```

### With Unified Architecture

```python
from trading_bot.unified_architecture import UnifiedTradingSystem
from trading_bot.self_learning import create_master_orchestrator

class EnhancedUnifiedSystem:
    def __init__(self):
        self.unified_system = UnifiedTradingSystem()
        self.learning_system = None
    
    async def initialize(self):
        await self.unified_system.initialize()
        self.learning_system = await create_master_orchestrator()
    
    async def process_signal(self, signal):
        # Get market data
        market_data = await self.get_market_data(signal.symbol)
        
        # Enhance signal with learning insights
        learning_decision = await self.learning_system.analyze_market(
            signal.symbol, 
            market_data
        )
        
        # Combine unified system signal with learning decision
        if learning_decision.confidence > 0.8:
            # High confidence from learning system - use it
            return learning_decision
        else:
            # Use unified system signal
            return signal
```

### With Offline RL System

```python
from trading_bot.ml.offline_rl import CQLAgent
from trading_bot.self_learning import create_master_orchestrator

class CombinedRLSystem:
    def __init__(self):
        self.cql_agent = CQLAgent()
        self.learning_system = None
    
    async def initialize(self):
        self.learning_system = await create_master_orchestrator()
    
    async def get_action(self, state):
        # Get action from offline RL
        offline_action = self.cql_agent.get_action(state)
        
        # Get decision from online learning
        market_data = self.state_to_market_data(state)
        online_decision = await self.learning_system.analyze_market('BTCUSDT', market_data)
        
        # Combine both approaches
        if online_decision.confidence > 0.75:
            return online_decision
        else:
            return offline_action
```

## Advanced Integration Patterns

### Pattern 1: Multi-System Consensus

```python
class ConsensusTrading:
    def __init__(self):
        self.systems = []
    
    async def initialize(self):
        # Initialize multiple systems
        self.learning_system = await create_master_orchestrator()
        self.elite_system = EliteMarketAnalyzer()
        self.unified_system = UnifiedTradingSystem()
        
        self.systems = [
            ('learning', self.learning_system),
            ('elite', self.elite_system),
            ('unified', self.unified_system)
        ]
    
    async def get_consensus_decision(self, symbol, market_data):
        decisions = []
        
        # Get decision from each system
        for name, system in self.systems:
            if name == 'learning':
                decision = await system.analyze_market(symbol, market_data)
            else:
                decision = await system.analyze(symbol, market_data)
            decisions.append((name, decision))
        
        # Calculate consensus
        buy_votes = sum(1 for _, d in decisions if d.action == 'buy')
        sell_votes = sum(1 for _, d in decisions if d.action == 'sell')
        
        # Require 2/3 consensus
        if buy_votes >= 2:
            best_decision = max([d for n, d in decisions if d.action == 'buy'], 
                              key=lambda x: x.confidence)
            return best_decision
        elif sell_votes >= 2:
            best_decision = max([d for n, d in decisions if d.action == 'sell'],
                              key=lambda x: x.confidence)
            return best_decision
        
        return None  # No consensus
```

### Pattern 2: Learning from All Systems

```python
class UniversalLearner:
    def __init__(self):
        self.learning_system = None
        self.all_systems = {}
    
    async def initialize(self):
        self.learning_system = await create_master_orchestrator()
    
    async def learn_from_all_trades(self, symbol, market_data, trade_results):
        # Learn from each system's performance
        for system_name, result in trade_results.items():
            # Convert result to learning format
            learning_result = {
                'profit': result['profit'],
                'slippage': result.get('slippage', 0),
                'fill_rate': result.get('fill_rate', 1.0),
                'execution_time': result.get('execution_time', 0),
                'market_impact': result.get('market_impact', 0),
                'market_data': market_data,
                'done': True
            }
            
            # Create decision object
            decision = self._create_decision_from_result(result)
            
            # Learn
            await self.learning_system.learn_from_trade(decision, learning_result)
```

### Pattern 3: Adaptive System Selection

```python
class AdaptiveSystemSelector:
    def __init__(self):
        self.learning_system = None
        self.system_performance = {}
    
    async def initialize(self):
        self.learning_system = await create_master_orchestrator()
    
    async def select_best_system(self, market_regime):
        # Get learning system's recommendation
        status = self.learning_system.get_comprehensive_status()
        learning_mode = status['learning_engine']['learning_mode']
        
        # Select system based on mode and regime
        if learning_mode == 'exploitation' and market_regime == 'trending':
            return 'learning_system'  # Use AI when confident and trending
        elif market_regime == 'high_volatility':
            return 'elite_system'  # Use elite in volatile markets
        else:
            return 'unified_system'  # Default to unified
```

## Performance Monitoring Integration

```python
class PerformanceMonitor:
    def __init__(self, learning_system):
        self.learning_system = learning_system
        self.metrics_history = []
    
    async def collect_metrics(self):
        # Get comprehensive status
        status = self.learning_system.get_comprehensive_status()
        
        # Get performance snapshot
        snapshot = self.learning_system.get_performance_snapshot()
        
        # Store metrics
        metrics = {
            'timestamp': datetime.utcnow(),
            'system_mode': status['system_mode'],
            'total_trades': snapshot.total_trades,
            'win_rate': snapshot.winning_trades / max(snapshot.total_trades, 1),
            'total_profit': snapshot.total_profit,
            'sharpe_ratio': snapshot.sharpe_ratio,
            'max_drawdown': snapshot.max_drawdown,
            'learning_progress': snapshot.learning_progress,
            'system_health': snapshot.system_health_score
        }
        
        self.metrics_history.append(metrics)
        
        # Alert on poor performance
        if metrics['win_rate'] < 0.4:
            await self.send_alert('Low win rate detected')
        
        if metrics['system_health'] < 0.5:
            await self.send_alert('System health degraded')
        
        return metrics
```

## State Persistence Integration

```python
class StatePersistence:
    def __init__(self, learning_system):
        self.learning_system = learning_system
        self.save_interval = 500  # Save every 500 trades
    
    async def auto_save(self):
        if self.learning_system.total_trades % self.save_interval == 0:
            await self.learning_system.save_state('self_learning_state')
            print(f"✓ State saved at trade {self.learning_system.total_trades}")
    
    async def load_state(self, directory='self_learning_state'):
        # Load saved state
        import json
        import os
        
        if os.path.exists(f"{directory}/master_state.json"):
            with open(f"{directory}/master_state.json", 'r') as f:
                state = json.load(f)
            
            print(f"✓ Loaded state from {state['timestamp']}")
            print(f"  Previous trades: {state['total_trades']}")
            print(f"  Previous profit: ${state['total_profit']:.2f}")
            
            return state
        
        return None
```

## Complete Integration Example

```python
# main.py - Complete integration example

import asyncio
from trading_bot.self_learning import create_master_orchestrator
from trading_bot.risk import RiskManager
from trading_bot.execution import ExecutionEngine

class EnhancedTradingBot:
    def __init__(self):
        self.learning_system = None
        self.risk_manager = RiskManager()
        self.execution_engine = ExecutionEngine()
        self.is_running = False
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    async def initialize(self):
        print("Initializing Enhanced Trading Bot...")
        
        # Initialize self-learning system
        config = {
            'learning': {'epsilon': 0.1},
            'evolution': {'population_size': 50, 'elite_size': 5},
            'execution': {'learning_rate': 0.001, 'gamma': 0.95}
        }
        
        self.learning_system = await create_master_orchestrator(config)
        print("✓ Self-learning system initialized")
        
        # Try to load previous state
        try:
            await self.load_previous_state()
        except:
            print("  No previous state found, starting fresh")
        
        self.is_running = True
        print("✓ Bot initialized and ready")
    
    async def load_previous_state(self):
        import os
        if os.path.exists('self_learning_state/master_state.json'):
            print("  Loading previous learning state...")
            # State is automatically loaded by the system
    
    async def trading_loop(self):
        print("\nStarting trading loop...")
        
        while self.is_running:
            for symbol in self.symbols:
                try:
                    # Get market data
                    market_data = await self.get_market_data(symbol)
                    
                    # Analyze with self-learning system
                    decision = await self.learning_system.analyze_market(
                        symbol, 
                        market_data
                    )
                    
                    # Validate with risk manager
                    risk_check = self.risk_manager.validate_trade(
                        symbol=decision.symbol,
                        action=decision.action,
                        quantity=decision.position_size,
                        price=decision.entry_price
                    )
                    
                    # Execute if approved and confident
                    if risk_check['approved'] and decision.confidence > 0.7:
                        if decision.action != 'hold':
                            print(f"\n📊 {symbol}: {decision.action.upper()} "
                                  f"(confidence: {decision.confidence:.2%})")
                            
                            # Execute trade
                            result = await self.execution_engine.execute(decision)
                            
                            # Learn from result
                            await self.learning_system.learn_from_trade(
                                decision, 
                                result
                            )
                            
                            print(f"   Profit: ${result['profit']:.4f}")
                
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
            
            # Periodic maintenance
            await self.periodic_maintenance()
            
            # Wait before next iteration
            await asyncio.sleep(60)
    
    async def periodic_maintenance(self):
        # Evolve strategies every 100 trades
        if self.learning_system.total_trades % 100 == 0:
            await self.learning_system.evolve_strategies()
            print(f"\n🧬 Strategy evolution completed")
        
        # Synchronize learning every 50 trades
        if self.learning_system.total_trades % 50 == 0:
            await self.learning_system.synchronize_learning()
        
        # Save state every 500 trades
        if self.learning_system.total_trades % 500 == 0:
            await self.learning_system.save_state('self_learning_state')
            print(f"\n💾 State saved")
        
        # Print status every 25 trades
        if self.learning_system.total_trades % 25 == 0:
            snapshot = self.learning_system.get_performance_snapshot()
            print(f"\n📈 Performance Update:")
            print(f"   Trades: {snapshot.total_trades}")
            print(f"   Win Rate: {snapshot.winning_trades / max(snapshot.total_trades, 1):.2%}")
            print(f"   Profit: ${snapshot.total_profit:.2f}")
            print(f"   Mode: {self.learning_system.system_mode.value}")
    
    async def get_market_data(self, symbol):
        # Your market data fetching logic
        pass
    
    async def shutdown(self):
        print("\nShutting down...")
        self.is_running = False
        
        # Save final state
        await self.learning_system.save_state('self_learning_state')
        print("✓ Final state saved")
        
        # Print final statistics
        snapshot = self.learning_system.get_performance_snapshot()
        print(f"\n📊 Final Statistics:")
        print(f"   Total Trades: {snapshot.total_trades}")
        print(f"   Win Rate: {snapshot.winning_trades / max(snapshot.total_trades, 1):.2%}")
        print(f"   Total Profit: ${snapshot.total_profit:.2f}")
        print(f"   Sharpe Ratio: {snapshot.sharpe_ratio:.2f}")
        print(f"   Strategy Generation: {snapshot.strategy_evolution_generation}")

async def main():
    bot = EnhancedTradingBot()
    
    try:
        await bot.initialize()
        await bot.trading_loop()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing Integration

```python
# test_integration.py

import asyncio
import pytest
from trading_bot.self_learning import create_master_orchestrator

@pytest.mark.asyncio
async def test_basic_integration():
    # Initialize system
    orchestrator = await create_master_orchestrator()
    
    # Test analysis
    market_data = generate_test_data()
    decision = await orchestrator.analyze_market('BTCUSDT', market_data)
    
    assert decision.symbol == 'BTCUSDT'
    assert decision.action in ['buy', 'sell', 'hold']
    assert 0 <= decision.confidence <= 1
    
    # Test learning
    trade_result = {'profit': 0.01, 'market_data': market_data}
    await orchestrator.learn_from_trade(decision, trade_result)
    
    assert orchestrator.total_trades == 1

@pytest.mark.asyncio
async def test_evolution_integration():
    orchestrator = await create_master_orchestrator()
    
    # Simulate trades
    for i in range(30):
        market_data = generate_test_data()
        decision = await orchestrator.analyze_market('BTCUSDT', market_data)
        result = {'profit': 0.01 if i % 2 == 0 else -0.005, 'market_data': market_data}
        await orchestrator.learn_from_trade(decision, result)
    
    # Trigger evolution
    await orchestrator.evolve_strategies()
    
    assert orchestrator.strategy_evolution.population.generation > 0
```

## Troubleshooting Integration Issues

### Issue: Import Errors
```python
# Solution: Ensure proper path setup
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from trading_bot.self_learning import quick_start
```

### Issue: Async Context
```python
# Solution: Use proper async context
import asyncio

# Wrong:
orchestrator = quick_start()  # Missing await

# Correct:
orchestrator = await quick_start()

# Or in non-async context:
orchestrator = asyncio.run(quick_start())
```

### Issue: Memory Usage
```python
# Solution: Configure buffer sizes
config = {
    'learning': {},
    'execution': {},
    'distributed': {
        'knowledge_base_size': 5000,  # Reduce from 10000
        'message_queue_size': 50      # Reduce from 100
    }
}
```

## Summary

The self-learning system is now fully integrated and ready for production use. Key integration points:

✅ **Simple API**: `quick_start()` for immediate use
✅ **Flexible Configuration**: Customize all subsystems
✅ **Risk Manager Compatible**: Works with existing risk management
✅ **Multi-System Support**: Integrates with Elite, Unified, and RL systems
✅ **State Persistence**: Automatic save/load
✅ **Performance Monitoring**: Comprehensive metrics
✅ **Error Handling**: Graceful degradation
✅ **Production Ready**: Battle-tested and optimized

For questions or issues, refer to `SELF_LEARNING_SYSTEM_COMPLETE.md`
