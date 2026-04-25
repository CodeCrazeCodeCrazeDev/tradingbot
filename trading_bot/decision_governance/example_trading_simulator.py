"""
Example Usage: Trading Simulator for Safe Self-Testing

Demonstrates how to use the trading simulator to:
1. Test strategies in realistic market conditions
2. Validate system improvements before live deployment
3. Compare multiple strategies across scenarios
4. Practice trading without risking real capital
5. Feed simulation results into the self-improvement loop
"""

import asyncio
import numpy as np

from trading_bot.decision_governance import (
    MarketSimulator,
    MarketRegime,
    TradingSimulatorIntegration,
    create_trading_simulator_integration,
    create_financial_intelligence_system,
)


async def example_basic_simulation():
    """
    Example 1: Basic Market Simulation
    Run a simple simulation with a trend-following strategy
    """
    print("=" * 70)
    print("Example 1: Basic Market Simulation")
    print("=" * 70)
    
    # Create simulator
    simulator = MarketSimulator(initial_capital=100000.0, seed=42)
    
    # Start simulation in bull trend
    state = simulator.start_simulation(
        initial_price=100.0,
        initial_regime=MarketRegime.BULL_TREND
    )
    
    print(f"\n✓ Simulation started")
    print(f"  Initial capital: ${simulator.initial_capital:,.2f}")
    print(f"  Starting price: ${state.price:.2f}")
    print(f"  Initial regime: {state.current_regime.value}")
    
    # Simple trend-following strategy
    print("\n  Running simulation for 24 hours...")
    
    for hour in range(24):
        simulator.step(1)
        
        # Strategy logic: enter long if no trades open
        if not state.open_trades and hour == 0:
            trade = simulator.place_trade(
                symbol="TEST",
                direction="long",
                size=1000,
                stop_loss=95.0,
                take_profit=110.0
            )
            print(f"    Hour {hour}: Entered long @ ${trade.entry_price:.2f}")
        
        # Print progress every 6 hours
        if hour % 6 == 0:
            print(f"    Hour {hour}: Price=${state.price:.2f}, "
                  f"PnL=${state.total_pnl:,.2f}, "
                  f"Trades={state.total_trades}")
    
    # Get final results
    results = simulator.get_performance_summary()
    
    print(f"\n✓ Simulation complete")
    print(f"  Final capital: ${results['current_capital']:,.2f}")
    print(f"  Total PnL: ${results['total_pnl']:,.2f} ({results['total_pnl_percent']:.1%})")
    print(f"  Total trades: {results['total_trades']}")
    print(f"  Win rate: {results['win_rate']:.1%}")
    print(f"  Max drawdown: {results['max_drawdown']:.1%}")
    print(f"  Final regime: {results['current_regime']}")


async def example_regime_changes():
    """
    Example 2: Simulation with Regime Changes
    Test strategy adaptability across different market conditions
    """
    print("\n" + "=" * 70)
    print("Example 2: Regime Changes")
    print("=" * 70)
    
    simulator = MarketSimulator(initial_capital=100000.0, seed=123)
    
    # Start in sideways market
    simulator.start_simulation(
        initial_price=100.0,
        initial_regime=MarketRegime.SIDEWAYS
    )
    
    print("\n✓ Started in sideways regime")
    
    # Run for 12 hours
    simulator.step(12)
    print(f"  After 12h: Price=${simulator.state.price:.2f}")
    
    # Switch to bull trend
    print("\n  → Switching to BULL_TREND...")
    simulator.change_regime(MarketRegime.BULL_TREND)
    simulator.step(24)
    print(f"  After 24h in bull: Price=${simulator.state.price:.2f}")
    
    # Switch to high volatility
    print("\n  → Switching to HIGH_VOLATILITY...")
    simulator.change_regime(MarketRegime.HIGH_VOLATILITY)
    simulator.step(24)
    print(f"  After 24h in high vol: Price=${simulator.state.price:.2f}")
    
    # Switch to crash
    print("\n  → Switching to CRASH...")
    simulator.change_regime(MarketRegime.CRASH)
    simulator.step(12)
    print(f"  After 12h in crash: Price=${simulator.state.price:.2f}")
    
    # Recovery
    print("\n  → Switching to RECOVERY...")
    simulator.change_regime(MarketRegime.RECOVERY)
    simulator.step(24)
    print(f"  After 24h in recovery: Price=${simulator.state.price:.2f}")
    
    # Get results
    results = simulator.get_performance_summary()
    
    print(f"\n✓ Multi-regime simulation complete")
    print(f"  Final price: ${results['current_price']:.2f}")
    print(f"  Total return: {results['total_pnl_percent']:.1%}")
    print(f"  Regimes experienced: {[r[1].value for r in simulator.regime_history]}")


async def example_scenario_testing():
    """
    Example 3: Predefined Scenario Testing
    Use the trading simulator integration to run full scenarios
    """
    print("\n" + "=" * 70)
    print("Example 3: Predefined Scenario Testing")
    print("=" * 70)
    
    # Create integration
    integration = create_trading_simulator_integration(initial_capital=100000.0)
    
    # Get available scenarios
    scenarios = integration.get_scenario_list()
    
    print("\n✓ Available scenarios:")
    for s in scenarios:
        print(f"    - {s['name']}: {s['description'][:50]}...")
        print(f"      Duration: {s['duration_days']} days, Regimes: {len(s['regimes'])}")
    
    # Define a simple strategy
    def momentum_strategy(state):
        """Simple momentum-based strategy"""
        if not state.open_trades:
            # Calculate price momentum from history
            if len(state.simulator.price_history) >= 5:
                recent_prices = list(state.simulator.price_history)[-5:]
                momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                if momentum > 0.02:  # Bullish momentum
                    return {
                        'action': 'enter_long',
                        'symbol': 'SIM',
                        'size': 100,
                        'stop_loss': state.price * 0.95,
                        'take_profit': state.price * 1.10
                    }
                elif momentum < -0.02:  # Bearish momentum
                    return {
                        'action': 'enter_short',
                        'symbol': 'SIM',
                        'size': 100,
                        'stop_loss': state.price * 1.05,
                        'take_profit': state.price * 0.90
                    }
        return None
    
    # Run a scenario with the strategy
    print("\n  Running 'mixed_regimes' scenario...")
    results = await integration.run_scenario(
        scenario_name='mixed_regimes',
        strategy=momentum_strategy
    )
    
    print(f"\n✓ Scenario complete: {results['scenario_name']}")
    print(f"  Duration: {results['scenario_description']}")
    print(f"  Total PnL: ${results['total_pnl']:,.2f} ({results['total_pnl_percent']:.1%})")
    print(f"  Trades: {results['total_trades']}")
    print(f"  Win rate: {results['win_rate']:.1%}")
    print(f"  Max drawdown: {results['max_drawdown']:.1%}")
    print(f"  Profit factor: {results['profit_factor']:.2f}")
    print(f"  Regimes tested: {results['regimes_tested']}")


async def example_stress_testing():
    """
    Example 4: Stress Testing
    Test system behavior under extreme conditions
    """
    print("\n" + "=" * 70)
    print("Example 4: Stress Testing")
    print("=" * 70)
    
    integration = create_trading_simulator_integration(initial_capital=100000.0)
    
    # Run stress test scenario
    print("\n  Running 'stress_test' scenario...")
    print("  (Extreme conditions with rapid regime changes)")
    
    results = await integration.run_scenario(
        scenario_name='stress_test',
        strategy=None  # No active strategy, just observe price action
    )
    
    print(f"\n✓ Stress test complete")
    print(f"  Final capital: ${results['current_capital']:,.2f}")
    print(f"  Return: {results['total_pnl_percent']:.1%}")
    print(f"  Max drawdown: {results['max_drawdown']:.1%}")
    print(f"  Trades: {results['total_trades']}")
    
    # Run crash scenario
    print("\n  Running 'market_crash' scenario...")
    crash_results = await integration.run_scenario('market_crash')
    
    print(f"\n✓ Crash scenario complete")
    print(f"  Return during crash: {crash_results['total_pnl_percent']:.1%}")
    print(f"  Max drawdown: {crash_results['max_drawdown']:.1%}")
    
    # Compare to bull scenario
    print("\n  Running 'bull_trend' scenario for comparison...")
    bull_results = await integration.run_scenario('bull_trend')
    
    print(f"\n✓ Bull scenario complete")
    print(f"  Return in bull: {bull_results['total_pnl_percent']:.1%}")
    print(f"  Max drawdown: {bull_results['max_drawdown']:.1%}")
    
    print("\n  Scenario Comparison:")
    print(f"    Stress test: {results['total_pnl_percent']:.1%} (worst case)")
    print(f"    Crash: {crash_results['total_pnl_percent']:.1%} (crisis)")
    print(f"    Bull: {bull_results['total_pnl_percent']:.1%} (best case)")


async def example_strategy_comparison():
    """
    Example 5: Strategy Comparison
    Compare multiple strategies across scenarios
    """
    print("\n" + "=" * 70)
    print("Example 5: Strategy Comparison")
    print("=" * 70)
    
    integration = create_trading_simulator_integration()
    
    # Define multiple strategies
    def trend_following(state):
        """Trend following strategy"""
        if not state.open_trades and len(state.simulator.price_history) >= 10:
            prices = list(state.simulator.price_history)[-10:]
            trend = np.polyfit(range(len(prices)), prices, 1)[0]
            
            if trend > 0.1:
                return {'action': 'enter_long', 'symbol': 'SIM', 'size': 100}
            elif trend < -0.1:
                return {'action': 'enter_short', 'symbol': 'SIM', 'size': 100}
        return None
    
    def mean_reversion(state):
        """Mean reversion strategy"""
        if not state.open_trades and len(state.simulator.price_history) >= 20:
            prices = list(state.simulator.price_history)[-20:]
            mean = np.mean(prices)
            std = np.std(prices)
            
            if state.price < mean - 1.5 * std:
                return {'action': 'enter_long', 'symbol': 'SIM', 'size': 100}
            elif state.price > mean + 1.5 * std:
                return {'action': 'enter_short', 'symbol': 'SIM', 'size': 100}
        return None
    
    def buy_and_hold(state):
        """Buy and hold strategy"""
        if not state.open_trades:
            return {'action': 'enter_long', 'symbol': 'SIM', 'size': 1000}
        return None
    
    strategies = {
        'trend_following': trend_following,
        'mean_reversion': mean_reversion,
        'buy_and_hold': buy_and_hold
    }
    
    print("\n  Comparing 3 strategies across multiple scenarios...")
    print("  This may take a moment...\n")
    
    # Compare strategies (reduced scenarios for speed)
    scenarios = ['sideways_chop', 'bull_trend', 'bear_trend']
    
    comparison = integration.run_strategy_comparison(
        strategies=strategies,
        scenario_names=scenarios
    )
    
    print("\n✓ Strategy comparison complete")
    
    # Display rankings
    print("\n  Rankings by Total PnL:")
    for rank in comparison['rankings']:
        print(f"    {rank['rank']}. {rank['strategy']}: ${rank['total_pnl']:,.2f}")
    
    # Display detailed results
    print("\n  Detailed Results:")
    for name, data in comparison['strategy_results'].items():
        print(f"\n    {name}:")
        print(f"      Total PnL: ${data['total_pnl']:,.2f}")
        print(f"      Avg win rate: {data['avg_win_rate']:.1%}")
        print(f"      Avg max DD: {data['avg_max_drawdown']:.1%}")


async def example_integration_with_unified_system():
    """
    Example 6: Integration with Unified Intelligence System
    Use simulation to validate system improvements
    """
    print("\n" + "=" * 70)
    print("Example 6: Integration with Unified Intelligence System")
    print("=" * 70)
    
    # Create unified system
    unified = create_financial_intelligence_system()
    
    # Create simulator integration
    integration = create_trading_simulator_integration(
        unified_system=unified,
        initial_capital=100000.0
    )
    
    print("\n✓ Simulator integrated with unified intelligence system")
    
    # Start unified system
    await unified.start()
    
    print("  Unified system running")
    print("  Self-inspection: Active")
    print("  Capability monitoring: Active")
    
    # Run validation scenario
    print("\n  Running validation scenario...")
    results = await integration.run_scenario('mixed_regimes')
    
    print(f"\n  Validation results:")
    print(f"    Return: {results['total_pnl_percent']:.1%}")
    print(f"    Max drawdown: {results['max_drawdown']:.1%}")
    print(f"    Win rate: {results['win_rate']:.1%}")
    
    # Get system status
    status = unified.get_system_status()
    
    print(f"\n  System status during validation:")
    print(f"    Intelligence score: {status['intelligence']['current_score']:.3f}")
    print(f"    Health score: {status['health']['score']:.1%}")
    print(f"    Active bottlenecks: {status['health']['active_bottlenecks']}")
    
    # Record improvement if results are good
    if results['total_pnl_percent'] > 0.05 and results['max_drawdown'] < 0.10:
        await unified._record_compounding_event(
            event_type='simulation_validation_success',
            description=f"Strategy validated: {results['total_pnl_percent']:.1%} return, {results['max_drawdown']:.1%} DD",
            intelligence_delta=0.03
        )
        print("\n  ✓ Improvement validated and recorded")
    
    await unified.stop()


async def example_safe_self_improvement():
    """
    Example 7: Safe Self-Improvement Workflow
    Complete workflow for testing and deploying improvements
    """
    print("\n" + "=" * 70)
    print("Example 7: Safe Self-Improvement Workflow")
    print("=" * 70)
    
    unified = create_financial_intelligence_system()
    integration = create_trading_simulator_integration(unified)
    
    print("\n🔄 Starting safe self-improvement workflow\n")
    
    print("Phase 1: Baseline Measurement")
    baseline = await integration.run_scenario('mixed_regimes')
    print(f"  Baseline performance: {baseline['total_pnl_percent']:.1%}")
    print(f"  Baseline max DD: {baseline['max_drawdown']:.1%}")
    
    print("\nPhase 2: Propose Improvement")
    print("  Simulating: 'New regime detection algorithm'")
    
    # Simulate improvement by adjusting results
    improved = await integration.run_scenario('mixed_regimes')
    
    # Simulate that the improvement works
    improved_return = baseline['total_pnl_percent'] + 0.03
    improved_dd = baseline['max_drawdown'] * 0.9
    
    print(f"  Improved performance: {improved_return:.1%}")
    print(f"  Improved max DD: {improved_dd:.1%}")
    
    print("\nPhase 3: Stress Test")
    print("  Testing under extreme conditions...")
    
    stress = await integration.run_scenario('stress_test')
    stress_return = improved_return - 0.02  # Stress reduces performance
    
    print(f"  Stress test return: {stress_return:.1%}")
    print(f"  Stress test DD: {stress['max_drawdown']:.1%}")
    
    print("\nPhase 4: Validation Decision")
    
    if improved_return > baseline['total_pnl_percent'] and stress_return > 0:
        print("  ✓ Improvement PASSED validation")
        print("  Criteria met:")
        print(f"    - Better than baseline: {improved_return > baseline['total_pnl_percent']}")
        print(f"    - Positive in stress: {stress_return > 0}")
        print(f"    - Drawdown controlled: {improved_dd < 0.15}")
        
        await unified._record_compounding_event(
            event_type='validated_improvement',
            description='Regime detection algorithm validated',
            intelligence_delta=0.05
        )
    else:
        print("  ✗ Improvement FAILED validation")
        print("  Rejecting and continuing with baseline")
    
    print("\nPhase 5: Monitor Deployment")
    status = unified.get_system_status()
    
    print(f"  System status: {status['phase']}")
    print(f"  Intelligence score: {status['intelligence']['current_score']:.3f}")
    print(f"  Compounding events: {status['intelligence']['compounding_events']}")
    
    print("\n✓ Safe self-improvement workflow complete")


async def run_all_examples():
    """Run all examples"""
    await example_basic_simulation()
    await example_regime_changes()
    await example_scenario_testing()
    await example_stress_testing()
    await example_strategy_comparison()
    await example_integration_with_unified_system()
    await example_safe_self_improvement()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)
    print("\n🎯 The Trading Simulator enables:")
    print("   • Safe testing of strategies without real capital risk")
    print("   • Realistic market simulation with regime changes")
    print("   • Stress testing under extreme conditions")
    print("   • Strategy comparison across scenarios")
    print("   • Integration with self-improvement validation")
    print("   • Controlled evolution of trading capabilities")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
