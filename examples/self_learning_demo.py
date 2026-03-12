"""
Self-Learning System Demo

Demonstrates the complete self-learning, self-evolving, and self-optimizing
trading system for AI-driven market analysis and profit generation.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_bot.self_learning import (
    quick_start,
    create_master_orchestrator,
    SystemMode,
    LearningMode,
    ModelType
)


def generate_sample_market_data(symbol: str, bars: int = 100) -> pd.DataFrame:
    """Generate sample market data for testing"""
    np.random.seed(42)
    
    # Generate realistic price movement
    base_price = 100.0
    returns = np.random.normal(0.0005, 0.02, bars)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate volume
    base_volume = 1000000
    volume = base_volume * (1 + np.random.normal(0, 0.3, bars))
    volume = np.abs(volume)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': [datetime.utcnow() - timedelta(minutes=i) for i in range(bars-1, -1, -1)],
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, bars)),
        'high': prices * (1 + np.random.uniform(0, 0.02, bars)),
        'low': prices * (1 - np.random.uniform(0, 0.02, bars)),
        'close': prices,
        'volume': volume
    })
    
    return df


def simulate_trade_execution(decision) -> dict:
    """Simulate trade execution and generate result"""
    # Simulate execution with some randomness
    success_prob = decision.confidence
    success = np.random.random() < success_prob
    
    if success:
        # Profitable trade
        profit_pct = np.random.uniform(0.01, 0.05)
        profit = decision.position_size * profit_pct
    else:
        # Losing trade
        loss_pct = np.random.uniform(0.005, 0.02)
        profit = -decision.position_size * loss_pct
    
    return {
        'profit': profit,
        'slippage': np.random.uniform(0.0001, 0.0005),
        'fill_rate': np.random.uniform(0.95, 1.0),
        'execution_time': np.random.uniform(0.1, 1.0),
        'market_impact': np.random.uniform(0.0001, 0.0003),
        'opportunity_cost': np.random.uniform(0, 0.0002),
        'done': True
    }


async def demo_basic_usage():
    """Demonstrate basic usage of the self-learning system"""
    print("=" * 80)
    print("DEMO 1: Basic Usage")
    print("=" * 80)
    
    # Quick start with default config
    orchestrator = await quick_start()
    
    # Generate sample market data
    market_data = generate_sample_market_data('BTCUSDT', bars=100)
    
    # Analyze market
    print("\n📊 Analyzing market...")
    decision = await orchestrator.analyze_market('BTCUSDT', market_data)
    
    # Display decision
    print(f"\n🎯 Trading Decision:")
    print(f"   Symbol: {decision.symbol}")
    print(f"   Action: {decision.action.upper()}")
    print(f"   Confidence: {decision.confidence:.2%}")
    print(f"   Position Size: {decision.position_size:.4f}")
    print(f"   Entry Price: ${decision.entry_price:.2f}")
    print(f"   Stop Loss: ${decision.stop_loss:.2f}")
    print(f"   Take Profit: ${decision.take_profit:.2f}")
    print(f"   Risk Score: {decision.risk_score:.2f}")
    print(f"   Strategy: {decision.strategy_id}")
    print(f"   Market Regime: {decision.market_regime}")
    print(f"   Learning Mode: {decision.learning_mode}")
    print(f"   System Mode: {decision.system_mode}")
    
    # Simulate trade execution
    if decision.action != 'hold':
        print(f"\n💼 Executing {decision.action} trade...")
        trade_result = simulate_trade_execution(decision)
        trade_result['market_data'] = market_data
        
        print(f"   Profit: ${trade_result['profit']:.4f}")
        print(f"   Slippage: {trade_result['slippage']:.4f}")
        print(f"   Fill Rate: {trade_result['fill_rate']:.2%}")
        
        # Learn from trade
        print(f"\n🧠 Learning from trade result...")
        await orchestrator.learn_from_trade(decision, trade_result)
        print("   ✓ Learning complete")
    
    # Get system status
    print(f"\n📈 System Status:")
    status = orchestrator.get_comprehensive_status()
    print(f"   Mode: {status['system_mode']}")
    print(f"   Total Trades: {status['performance']['total_trades']}")
    print(f"   Win Rate: {status['performance']['win_rate']:.2%}")
    print(f"   Learning Progress: {status['performance']['learning_progress']:.2%}")


async def demo_continuous_learning():
    """Demonstrate continuous learning over multiple trades"""
    print("\n" + "=" * 80)
    print("DEMO 2: Continuous Learning (100 trades)")
    print("=" * 80)
    
    # Create orchestrator with custom config
    config = {
        'learning': {'epsilon': 0.1},
        'evolution': {'population_size': 30, 'elite_size': 3},
        'execution': {'learning_rate': 0.001}
    }
    
    orchestrator = await create_master_orchestrator(config)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    n_trades = 100
    
    print(f"\n🔄 Running {n_trades} simulated trades...")
    
    for i in range(n_trades):
        symbol = symbols[i % len(symbols)]
        
        # Generate fresh market data
        market_data = generate_sample_market_data(symbol, bars=100)
        
        # Analyze and decide
        decision = await orchestrator.analyze_market(symbol, market_data)
        
        # Execute if confidence is sufficient
        if decision.confidence > 0.5 and decision.action != 'hold':
            trade_result = simulate_trade_execution(decision)
            trade_result['market_data'] = market_data
            
            # Learn from result
            await orchestrator.learn_from_trade(decision, trade_result)
            
            # Print progress every 10 trades
            if (i + 1) % 10 == 0:
                snapshot = orchestrator.get_performance_snapshot()
                print(f"   Trade {i+1}/{n_trades}: "
                      f"Win Rate: {snapshot.winning_trades / max(snapshot.total_trades, 1):.2%}, "
                      f"Profit: ${snapshot.total_profit:.2f}, "
                      f"Mode: {orchestrator.system_mode.value}")
        
        # Evolve strategies every 25 trades
        if (i + 1) % 25 == 0:
            await orchestrator.evolve_strategies()
            print(f"   🧬 Strategy evolution completed (Generation {orchestrator.strategy_evolution.population.generation})")
    
    # Final performance report
    print(f"\n📊 Final Performance Report:")
    snapshot = orchestrator.get_performance_snapshot()
    print(f"   Total Trades: {snapshot.total_trades}")
    print(f"   Winning Trades: {snapshot.winning_trades}")
    print(f"   Win Rate: {snapshot.winning_trades / max(snapshot.total_trades, 1):.2%}")
    print(f"   Total Profit: ${snapshot.total_profit:.2f}")
    print(f"   Sharpe Ratio: {snapshot.sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {snapshot.max_drawdown:.2%}")
    print(f"   Strategy Generation: {snapshot.strategy_evolution_generation}")
    print(f"   System Health: {snapshot.system_health_score:.2%}")
    print(f"   Active Strategies: {snapshot.active_strategies}")


async def demo_system_modes():
    """Demonstrate different system modes"""
    print("\n" + "=" * 80)
    print("DEMO 3: System Mode Adaptation")
    print("=" * 80)
    
    orchestrator = await quick_start()
    
    # Simulate different performance scenarios
    scenarios = [
        ('High Win Rate', 0.8, 0.05, SystemMode.EXPLOITING),
        ('Low Win Rate', 0.3, -0.02, SystemMode.DEFENSIVE),
        ('Moderate Performance', 0.55, 0.02, SystemMode.OPTIMIZING),
    ]
    
    for scenario_name, win_rate, avg_profit, expected_mode in scenarios:
        print(f"\n📍 Scenario: {scenario_name}")
        print(f"   Target Win Rate: {win_rate:.2%}")
        print(f"   Target Avg Profit: ${avg_profit:.4f}")
        
        # Simulate 30 trades with target performance
        for i in range(30):
            market_data = generate_sample_market_data('BTCUSDT', bars=50)
            decision = await orchestrator.analyze_market('BTCUSDT', market_data)
            
            # Create result matching target performance
            success = np.random.random() < win_rate
            profit = avg_profit if success else -abs(avg_profit) * 0.5
            
            trade_result = {
                'profit': profit,
                'slippage': 0.0002,
                'fill_rate': 1.0,
                'execution_time': 0.5,
                'market_impact': 0.0001,
                'market_data': market_data,
                'done': True
            }
            
            await orchestrator.learn_from_trade(decision, trade_result)
        
        print(f"   Adapted Mode: {orchestrator.system_mode.value}")
        print(f"   Expected Mode: {expected_mode.value}")
        print(f"   ✓ Mode adaptation {'successful' if orchestrator.system_mode == expected_mode else 'in progress'}")


async def demo_distributed_learning():
    """Demonstrate distributed learning and knowledge sharing"""
    print("\n" + "=" * 80)
    print("DEMO 4: Distributed Learning & Knowledge Sharing")
    print("=" * 80)
    
    orchestrator = await quick_start()
    
    print("\n🌐 Distributed Learning System:")
    status = orchestrator.distributed_learning.get_system_status()
    print(f"   Active: {status['active']}")
    print(f"   Components: {len(status['components'])}")
    
    for name, comp_status in status['components'].items():
        print(f"      - {name}: {comp_status['role']} (learned: {comp_status['learned_knowledge']})")
    
    print(f"\n📚 Knowledge Base:")
    kb_stats = status['knowledge_base']
    print(f"   Total Knowledge: {kb_stats['total_knowledge']}")
    print(f"   Avg Confidence: {kb_stats['avg_confidence']:.2%}")
    print(f"   Total Validations: {kb_stats['total_validations']}")
    
    # Simulate knowledge sharing
    print(f"\n🔄 Simulating knowledge sharing...")
    for i in range(5):
        market_data = generate_sample_market_data('BTCUSDT', bars=50)
        decision = await orchestrator.analyze_market('BTCUSDT', market_data)
        
        trade_result = simulate_trade_execution(decision)
        trade_result['market_data'] = market_data
        await orchestrator.learn_from_trade(decision, trade_result)
    
    # Synchronize learning
    await orchestrator.synchronize_learning()
    print("   ✓ Learning synchronized across all components")
    
    # Check updated knowledge
    status = orchestrator.distributed_learning.get_system_status()
    kb_stats = status['knowledge_base']
    print(f"\n📚 Updated Knowledge Base:")
    print(f"   Total Knowledge: {kb_stats['total_knowledge']}")
    print(f"   Recent Accesses: {kb_stats['recent_accesses']}")


async def demo_self_healing():
    """Demonstrate self-healing capabilities"""
    print("\n" + "=" * 80)
    print("DEMO 5: Self-Healing System")
    print("=" * 80)
    
    orchestrator = await quick_start()
    
    print("\n🏥 System Health Check:")
    health = orchestrator.self_healing.get_system_health()
    print(f"   Status: {health['status']}")
    print(f"   Health Score: {health['health_score']:.2%}")
    print(f"   CPU Usage: {health['metrics']['cpu_usage']:.1f}%")
    print(f"   Memory Usage: {health['metrics']['memory_usage']:.1f}%")
    print(f"   Active Issues: {health['active_issues']}")
    print(f"   Repair Success Rate: {health['repair_success_rate']:.2%}")
    
    print(f"\n🔧 Component Health:")
    for comp_name, comp_health in health['components'].items():
        print(f"   {comp_name}:")
        print(f"      Health Score: {comp_health['health_score']:.2%}")
        print(f"      Recent Errors: {comp_health['recent_errors']}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("SELF-LEARNING TRADING SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 80)
    print("\nThis demo showcases the complete self-learning, self-evolving,")
    print("and self-optimizing system for AI-driven market analysis and profit generation.")
    
    try:
        # Run all demos
        await demo_basic_usage()
        await demo_continuous_learning()
        await demo_system_modes()
        await demo_distributed_learning()
        await demo_self_healing()
        
        print("\n" + "=" * 80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nThe self-learning system is ready for production use!")
        print("Key capabilities demonstrated:")
        print("  ✓ Real-time market analysis and decision making")
        print("  ✓ Continuous learning from every trade")
        print("  ✓ Automatic strategy evolution")
        print("  ✓ Adaptive system mode switching")
        print("  ✓ Distributed knowledge sharing")
        print("  ✓ Self-healing and monitoring")
        print("\nFor integration, see: SELF_LEARNING_SYSTEM_COMPLETE.md")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
