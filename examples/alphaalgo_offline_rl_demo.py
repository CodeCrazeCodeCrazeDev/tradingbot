"""
AlphaAlgo Autonomous Offline RL System - Complete Demo

Demonstrates the full autonomous learning cycle with real trading integration.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AlphaAlgo components
from trading_bot.ml.offline_rl import (
import numpy
import pandas
    create_alphaalgo_system,
    AlphaAlgoTradingIntegration,
    MarketStateBuilder,
    ActionMapper,
    RewardCalculator
)


class MockMT5Interface:
    pass
    """Mock MT5 interface for demonstration."""
    
    def __init__(self):
    pass
        self.current_price = 1.1000
        self.equity = 10000.0
        self.margin_level = 1000.0
        self.free_margin = 9000.0
    
    async def get_rates(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
    pass
        """Generate mock market data."""
        dates = pd.date_range(end=datetime.now(), periods=bars, freq='1min')
        
        # Generate realistic price movement
        returns = np.random.randn(bars) * 0.0001
        prices = self.current_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'time': dates,
            'open': prices * (1 + np.random.randn(bars) * 0.0001),
            'high': prices * (1 + np.abs(np.random.randn(bars)) * 0.0002),
            'low': prices * (1 - np.abs(np.random.randn(bars)) * 0.0002),
            'close': prices,
            'volume': np.random.randint(1000, 10000, bars),
            'rsi': np.random.uniform(30, 70, bars),
            'macd': np.random.randn(bars) * 0.0001,
            'macd_signal': np.random.randn(bars) * 0.0001,
            'atr': np.random.uniform(0.0005, 0.0015, bars),
            'bb_upper': prices * 1.002,
            'bb_lower': prices * 0.998,
        })
        
        self.current_price = prices[-1]
        return df
    
    def account_info(self):
    pass
        """Return mock account info."""
        class AccountInfo:
    pass
            def __init__(self, equity, margin_level, margin_free):
    pass
                self.equity = equity
                self.margin_level = margin_level
                self.margin_free = margin_free
        
        return AccountInfo(self.equity, self.margin_level, self.free_margin)


async def demo_basic_usage():
    pass
    """Demonstrate basic AlphaAlgo usage."""
    print("\n" + "="*80)
    print("DEMO 1: BASIC USAGE")
    print("="*80)
    
    # Create mock MT5 interface
    mt5 = MockMT5Interface()
    
    # Create AlphaAlgo trader
    config = {
        'lookback_window': 50,
        'action_space': 'simple',
        'reward_type': 'sharpe',
        'autonomous_config': {
            'buffer_size': 10000,
            'min_buffer_size': 100,  # Low for demo
            'training_interval_hours': 1,
            'training_epochs': 10,  # Low for demo
        }
    }
    
    trader = AlphaAlgoTradingIntegration(
        mt5_interface=mt5,
        symbol="EURUSD",
        config=config
    )
    
    await trader.start()
    
    # Simulate trading loop
    print("\nSimulating 200 trades...")
    for i in range(200):
    pass
        # Get market data
        market_data = await mt5.get_rates("EURUSD", "M15", 100)
        
        # Get account info
        account_info = {
            'equity': mt5.equity,
            'margin_level': mt5.margin_level,
            'free_margin': mt5.free_margin
        }
        
        # Get trading signal
        signal = await trader.get_trading_signal(market_data, account_info)
        
        # Simulate trade execution
        if signal['type'] != 'hold':
    pass
            # Simulate PnL
            pnl = np.random.randn() * 10
            
            # Update equity
            mt5.equity += pnl
            mt5.free_margin = mt5.equity * 0.9
            
            # Create trade result
            trade_result = {
                'pnl': pnl,
                'commission': 0.5,
                'swap': 0.1,
                'position_change': signal['size'],
                'current_position': signal['size'] if signal['type'] == 'buy' else -signal['size'],
                'forced_close': False,
                'account_info': account_info
            }
            
            # Process result
            await trader.process_trade_result(trade_result, market_data)
        
        if (i + 1) % 50 == 0:
    pass
            print(f"  Completed {i+1} trades...")
    
    # Get status
    status = trader.get_status()
    print("\nFinal Status:")
    print(f"  Symbol: {status['symbol']}")
    print(f"  Trades: {status['trades_count']}")
    print(f"  Buffer Size: {status['system_status']['buffer_size']}")
    print(f"  Current Policy: {status['system_status']['deployed_policy']}")
    print(f"  Mean Performance: {status['system_status']['recent_performance']['mean']:.4f}")
    
    # Force training
    print("\nForcing training cycle...")
    success = trader.force_training()
    if success:
    pass
        print("✅ Training completed successfully")
        
        # Get updated status
        status = trader.get_status()
        print(f"  New Policy: {status['system_status']['deployed_policy']}")
    else:
    pass
        print("⚠️ Training failed (may need more data)")
    
    # Stop
    trader.stop()
    print("\n✅ Demo 1 complete!")


async def demo_advanced_features():
    pass
    """Demonstrate advanced features."""
    print("\n" + "="*80)
    print("DEMO 2: ADVANCED FEATURES")
    print("="*80)
    
    # Test state builder
    print("\n[1] Testing State Builder...")
    state_builder = MarketStateBuilder(lookback_window=50)
    
    market_data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
        'rsi': np.random.uniform(30, 70, 100),
        'macd': np.random.randn(100),
        'atr': np.random.uniform(0.5, 2.0, 100)
    })
    
    state = state_builder.build_state(market_data, current_position=0.5)
    print(f"  ✅ State dimension: {len(state)}")
    print(f"  ✅ State sample: {state[:5]}")
    
    # Test action mapper
    print("\n[2] Testing Action Mapper...")
    for action_space in ['simple', 'extended']:
    pass
        mapper = ActionMapper(action_space)
        print(f"  {action_space.upper()} action space ({mapper.action_dim} actions):")
        for i in range(min(3, mapper.action_dim)):
    pass
            action = mapper.map_action(i)
            print(f"    Action {i}: {action}")
    
    # Test reward calculator
    print("\n[3] Testing Reward Calculator...")
    for reward_type in ['simple', 'sharpe', 'sortino']:
    pass
        calc = RewardCalculator(reward_type)
        rewards = []
        for _ in range(10):
    pass
            pnl = np.random.randn() * 10
            reward = calc.calculate_reward(pnl, transaction_cost=0.5)
            rewards.append(reward)
        print(f"  {reward_type.upper()}: mean={np.mean(rewards):.4f}, std={np.std(rewards):.4f}")
    
    # Test autonomous system
    print("\n[4] Testing Autonomous System...")
    system = create_alphaalgo_system(state_dim=20, action_dim=3)
    
    print("  Collecting experience...")
    for i in range(150):
    pass
        state = np.random.randn(20)
        action = system.get_action(state)
        reward = np.random.randn() * 0.1
        next_state = np.random.randn(20)
        done = np.random.rand() < 0.05
        
        system.collect_trade_experience(state, action, reward, next_state, done)
    
    status = system.get_status()
    print(f"  ✅ Buffer size: {status['buffer_size']}")
    print(f"  ✅ Total trades: {status['stats']['total_trades']}")
    print(f"  ✅ Success rate: {status['stats']['successful_trades']/max(1, status['stats']['total_trades'])*100:.1f}%")
    
    print("\n✅ Demo 2 complete!")


async def demo_full_cycle():
    pass
    """Demonstrate complete learning cycle."""
    print("\n" + "="*80)
    print("DEMO 3: COMPLETE LEARNING CYCLE")
    print("="*80)
    
    # Create system
    system = create_alphaalgo_system(
        state_dim=20,
        action_dim=3,
        config={
            'buffer_size': 5000,
            'min_buffer_size': 500,
            'training_epochs': 20,
        }
    )
    
    system.start()
    
    print("\n[Phase 1] Data Collection (500+ samples)...")
    for i in range(600):
    pass
        state = np.random.randn(20)
        action = system.get_action(state)
        reward = np.random.randn() * 0.1 + 0.01  # Slight positive bias
        next_state = np.random.randn(20)
        done = np.random.rand() < 0.05
        
        system.collect_trade_experience(state, action, reward, next_state, done)
        
        if (i + 1) % 200 == 0:
    pass
            print(f"  Collected {i+1} samples...")
    
    print("\n[Phase 2] Training Policies...")
    success = system.force_training()
    
    if success:
    pass
        print("  ✅ Training successful!")
        
        status = system.get_status()
        print(f"  Deployed Policy: {status['deployed_policy']}")
        print(f"  Training Cycles: {status['stats']['total_training_cycles']}")
        print(f"  Deployments: {status['stats']['total_deployments']}")
    else:
    pass
        print("  ⚠️ Training failed")
    
    print("\n[Phase 3] Live Trading with Monitoring...")
    for i in range(100):
    pass
        state = np.random.randn(20)
        action = system.get_action(state)
        
        # Simulate performance degradation after 50 trades
        if i < 50:
    pass
            reward = np.random.randn() * 0.1 + 0.02
        else:
    pass
            reward = np.random.randn() * 0.1 - 0.05  # Worse performance
        
        next_state = np.random.randn(20)
        done = np.random.rand() < 0.05
        
        system.collect_trade_experience(state, action, reward, next_state, done)
    
    print("  ✅ Monitoring complete")
    
    status = system.get_status()
    print(f"  Total Rollbacks: {status['stats']['total_rollbacks']}")
    
    # Export metrics
    print("\n[Phase 4] Exporting Metrics...")
    metrics_df = system.export_metrics()
    print(metrics_df.to_string())
    
    system.stop()
    print("\n✅ Demo 3 complete!")


async def main():
    pass
    """Run all demos."""
    print("\n" + "="*80)
    print("ALPHAALGO AUTONOMOUS OFFLINE RL SYSTEM - COMPLETE DEMO")
    print("="*80)
    print("\nThis demo showcases:")
    print("  1. Basic usage with trading integration")
    print("  2. Advanced features (state, action, reward)")
    print("  3. Complete learning cycle (collect, train, deploy, monitor)")
    print("\n" + "="*80)
    
    # Run demos
    await demo_basic_usage()
    await demo_advanced_features()
    await demo_full_cycle()
    
    print("\n" + "="*80)
    print("ALL DEMOS COMPLETE!")
    print("="*80)
    print("\nNext Steps:")
    print("  1. Run validation: python validate_alphaalgo_offline_rl.py")
    print("  2. Review guide: ALPHAALGO_OFFLINE_RL_DEPLOYMENT_GUIDE.md")
    print("  3. Start trading: python main.py --alphaalgo-offline-rl")
    print("\n" + "="*80)


if __name__ == "__main__":
    pass
    asyncio.run(main())
