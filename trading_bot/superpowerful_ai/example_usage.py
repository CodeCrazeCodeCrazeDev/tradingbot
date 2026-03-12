"""
SuperPowerful AI - Example Usage
=================================

Demonstrates how to integrate and use the SuperPowerful AI system
in your trading bot.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from trading_bot.superpowerful_ai import (
    SuperPowerfulAI,
    AIMode
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Basic usage example"""
    
    print("\n" + "="*80)
    print("SUPERPOWERFUL AI - BASIC USAGE EXAMPLE")
    print("="*80 + "\n")
    
    # Initialize SuperPowerful AI
    config = {
        'mode': 'balanced',  # conservative, balanced, aggressive, learning, evolution
        'self_discovery': {
            'min_pattern_confidence': 0.6,
            'clustering_eps': 0.3
        },
        'adaptive': {
            'adaptation_mode': 'aggressive',
            'learning_rate': 0.01
        },
        'predictive': {
            'confidence_level': 0.95,
            'min_training_samples': 100
        },
        'strategic': {
            'total_capital': 10000.0,
            'max_strategies': 3
        },
        'innovation': {
            'max_strategies': 50,
            'mutation_rate': 0.1
        },
        'evolution': {
            'analysis_window_hours': 24,
            'min_trades': 20
        }
    }
    
    ai = SuperPowerfulAI(config=config)
    
    print(f"[OK] SuperPowerful AI initialized in {ai.mode.value} mode")
    print(f"[OK] All 6 intelligence systems active\n")
    
    # Generate sample market data
    print("Generating sample market data...")
    market_data = generate_sample_market_data(days=30)
    print(f"[OK] Generated {len(market_data)} data points\n")
    
    # Make a trading decision
    print("Analyzing market and making decision...")
    decision = await ai.analyze_and_decide(
        symbol='BTC/USD',
        market_data=market_data,
        current_position=None
    )
    
    print("\n" + "-"*80)
    print("DECISION RESULTS")
    print("-"*80)
    print(f"Action: {decision.action.upper()}")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Position Size: {decision.position_size:.4f}")
    
    if decision.entry_price:
        print(f"Entry Price: ${decision.entry_price:.2f}")
        print(f"Stop Loss: ${decision.stop_loss:.2f}")
        print(f"Take Profit: ${decision.take_profit:.2f}")
    
    print(f"\nProcessing Time: {decision.processing_time:.2f}s")
    print(f"Systems Used: {', '.join(decision.systems_used)}")
    
    print("\nReasoning:")
    for i, reason in enumerate(decision.reasoning, 1):
        print(f"  {i}. {reason}")
    
    print("\n" + "-"*80)
    print("INTELLIGENCE INSIGHTS")
    print("-"*80)
    
    print(f"\nMarket Regime: {decision.market_regime.value}")
    print(f"Patterns Discovered: {len(decision.discovered_patterns)}")
    print(f"Anomalies Detected: {len(decision.detected_anomalies)}")
    print(f"Selected Strategy: {decision.selected_strategy.value}")
    
    if decision.price_forecasts:
        print("\nPrice Forecasts:")
        for horizon, forecast in decision.price_forecasts.items():
            print(f"  {horizon.value}: ${forecast.predicted_price:.2f} "
                  f"(UP:{forecast.probability_up:.1%} / DOWN:{forecast.probability_down:.1%})")
    
    print("\n")


async def example_learning_from_trades():
    """Example of learning from trade results"""
    
    print("\n" + "="*80)
    print("SUPERPOWERFUL AI - LEARNING EXAMPLE")
    print("="*80 + "\n")
    
    ai = SuperPowerfulAI(config={'mode': 'learning'})
    
    # Simulate some trades
    print("Simulating trade results and learning...\n")
    
    for i in range(5):
        # Generate market data
        market_data = generate_sample_market_data(days=10)
        
        # Make decision
        decision = await ai.analyze_and_decide(
            symbol='ETH/USD',
            market_data=market_data
        )
        
        # Simulate trade result
        profit = np.random.uniform(-50, 100)
        
        trade_result = {
            'symbol': 'ETH/USD',
            'action': decision.action,
            'entry_price': market_data['close'].iloc[-1],
            'exit_price': market_data['close'].iloc[-1] * (1 + profit/1000),
            'profit': profit,
            'profit_pct': profit/1000,
            'duration': timedelta(hours=2),
            'strategy_type': decision.selected_strategy,
            'entry_time': datetime.now() - timedelta(hours=2),
            'exit_time': datetime.now()
        }
        
        market_state = {
            'volatility': 0.015,
            'trend_strength': 0.5,
            'momentum': 0.02
        }
        
        # Learn from trade
        await ai.learn_from_trade(trade_result, market_state)
        
        result_emoji = "[+]" if profit > 0 else "[-]"
        print(f"{result_emoji} Trade {i+1}: {decision.action} -> "
              f"${profit:+.2f} ({profit/10:.1%})")
    
    print(f"\n[OK] Learned from {len(ai.trade_history)} trades")
    print(f"[OK] Success rate: {ai.successful_decisions}/{ai.total_decisions}\n")


async def example_evolution_cycle():
    """Example of running evolution cycle"""
    
    print("\n" + "="*80)
    print("SUPERPOWERFUL AI - EVOLUTION EXAMPLE")
    print("="*80 + "\n")
    
    ai = SuperPowerfulAI(config={'mode': 'evolution'})
    
    # Simulate trade history
    print("Simulating trade history...")
    for i in range(30):
        trade = {
            'trade': {
                'profit': np.random.uniform(-30, 50),
                'entry_time': datetime.now() - timedelta(hours=i),
                'market_volatility': np.random.uniform(0.01, 0.03),
                'position_size': np.random.uniform(0.5, 2.0)
            },
            'market_state': {
                'volatility': np.random.uniform(0.01, 0.03)
            }
        }
        ai.trade_history.append(trade)
    
    print(f"[OK] Generated {len(ai.trade_history)} simulated trades\n")
    
    # Run evolution cycle
    print("Running evolution cycle...")
    await ai.run_evolution_cycle()
    
    # Get statistics
    stats = ai.get_comprehensive_statistics()
    
    print("\n" + "-"*80)
    print("EVOLUTION RESULTS")
    print("-"*80)
    
    evolution_stats = stats['strategic_evolution']
    print(f"\nEvolution Cycles: {evolution_stats['total_evolution_cycles']}")
    print(f"Issues Identified: {evolution_stats['total_issues_identified']}")
    print(f"Unresolved Issues: {evolution_stats['unresolved_issues']}")
    print(f"Recommendations: {evolution_stats['total_recommendations']}")
    print(f"Implemented: {evolution_stats['implemented_recommendations']}")
    print(f"Learning Insights: {evolution_stats['learning_insights']}")
    print(f"Cumulative Improvement: {evolution_stats['cumulative_improvement']:.2%}")
    
    if evolution_stats.get('top_issues'):
        print("\nTop Issues:")
        for issue in evolution_stats['top_issues'][:3]:
            print(f"  - [{issue['area']}] {issue['description']} "
                  f"(severity: {issue['severity']:.1%})")
    
    if evolution_stats.get('top_recommendations'):
        print("\nTop Recommendations:")
        for rec in evolution_stats['top_recommendations'][:3]:
            print(f"  - [{rec['priority']}] {rec['title']} "
                  f"(expected: +{rec['expected_improvement']:.1%})")
    
    print("\n")


async def example_comprehensive_statistics():
    """Example of getting comprehensive statistics"""
    
    print("\n" + "="*80)
    print("SUPERPOWERFUL AI - COMPREHENSIVE STATISTICS")
    print("="*80 + "\n")
    
    ai = SuperPowerfulAI(config={'mode': 'balanced'})
    
    # Make some decisions
    for _ in range(3):
        market_data = generate_sample_market_data(days=20)
        await ai.analyze_and_decide('BTC/USD', market_data)
    
    # Get all statistics
    stats = ai.get_comprehensive_statistics()
    
    print("SYSTEM OVERVIEW")
    print("-"*80)
    print(f"Mode: {stats['superpowerful_ai']['mode']}")
    print(f"Total Decisions: {stats['superpowerful_ai']['total_decisions']}")
    print(f"Success Rate: {stats['superpowerful_ai']['success_rate']:.2%}")
    
    print("\n\nSELF-DISCOVERY ENGINE")
    print("-"*80)
    sd_stats = stats['self_discovery']
    print(f"Patterns Discovered: {sd_stats['total_patterns_discovered']}")
    print(f"Regimes Detected: {sd_stats['total_regimes_detected']}")
    print(f"Anomalies Found: {sd_stats['total_anomalies_detected']}")
    
    print("\n\nADAPTIVE INTELLIGENCE")
    print("-"*80)
    adaptive_stats = stats['adaptive_intelligence']
    print(f"Total Learning Updates: {adaptive_stats['total_learning_updates']}")
    print(f"Strategies Tracked: {adaptive_stats['strategies_tracked']}")
    print(f"Adaptation Mode: {adaptive_stats['current_mode']}")
    
    print("\n\nPREDICTIVE INTELLIGENCE")
    print("-"*80)
    pred_stats = stats['predictive_intelligence']
    print(f"Total Forecasts: {pred_stats['total_forecasts']}")
    print(f"Scenarios Generated: {pred_stats['total_scenarios']}")
    print(f"Trend Predictions: {pred_stats['total_trend_predictions']}")
    
    print("\n\nSTRATEGIC INTELLIGENCE")
    print("-"*80)
    strat_stats = stats['strategic_intelligence']
    print(f"Total Decisions: {strat_stats['total_decisions']}")
    if strat_stats.get('current_allocations'):
        print("Current Allocations:")
        for alloc in strat_stats['current_allocations']:
            print(f"  - {alloc['strategy']}: {alloc['allocation']:.1f}% "
                  f"(confidence: {alloc['confidence']:.2f})")
    
    print("\n\nAUTONOMOUS INNOVATION")
    print("-"*80)
    innov_stats = stats['autonomous_innovation']
    print(f"Strategies Generated: {innov_stats['total_strategies_generated']}")
    print(f"Features Generated: {innov_stats['total_features_generated']}")
    print(f"Total Innovations: {innov_stats['total_innovations']}")
    print(f"Deployed: {innov_stats['deployed_innovations']}")
    
    print("\n\nSTRATEGIC SELF-EVOLUTION")
    print("-"*80)
    evol_stats = stats['strategic_evolution']
    print(f"Evolution Cycles: {evol_stats['total_evolution_cycles']}")
    print(f"Issues Identified: {evol_stats['total_issues_identified']}")
    print(f"Improvements Implemented: {evol_stats['implemented_recommendations']}")
    
    print("\n")


def generate_sample_market_data(days: int = 30, interval_minutes: int = 15) -> pd.DataFrame:
    """Generate sample OHLCV market data for testing"""
    
    periods = days * 24 * (60 // interval_minutes)
    
    # Generate realistic price movement
    base_price = 50000.0
    volatility = 0.02
    
    returns = np.random.normal(0.0001, volatility, periods)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV
    data = {
        'timestamp': [datetime.now() - timedelta(minutes=interval_minutes*i) for i in range(periods, 0, -1)],
        'open': prices,
        'high': prices * (1 + np.abs(np.random.normal(0, 0.005, periods))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.005, periods))),
        'close': prices * (1 + np.random.normal(0, 0.002, periods)),
        'volume': np.random.uniform(100, 1000, periods)
    }
    
    df = pd.DataFrame(data)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df


async def main():
    """Run all examples"""
    
    print("\n" + "="*80)
    print(" "*20 + "SUPERPOWERFUL AI EXAMPLES")
    print("="*80)
    
    # Run examples
    await example_basic_usage()
    await example_learning_from_trades()
    await example_evolution_cycle()
    await example_comprehensive_statistics()
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")
    
    print("Next Steps:")
    print("1. Integrate SuperPowerfulAI into your main trading loop")
    print("2. Configure the AI mode based on your risk tolerance")
    print("3. Monitor the comprehensive statistics dashboard")
    print("4. Let the AI learn and evolve from your trades")
    print("5. Review innovation suggestions periodically")
    print("\nThe SuperPowerful AI is ready to transform your trading!\n")


if __name__ == '__main__':
    asyncio.run(main())
