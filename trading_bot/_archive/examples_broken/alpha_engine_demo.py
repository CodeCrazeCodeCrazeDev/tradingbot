"""
AlphaEngine Enhanced Trading System - Demo
==========================================

Demonstrates the full AlphaEngine system capabilities:
    pass
- Directional Change detection
- Deep Learning predictions
- Sentiment analysis
- Multi-brain architecture
- Risk management
- Execution algorithms
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AlphaEngine components
from trading_bot.alpha_engine import (
    # Core
    AlphaEngineOrchestrator,
    DirectionalChangeEngine,
    quick_start,
    
    # Deep Learning
    PricePredictionModel,
    DeepLOBPredictor,
    
    # Sentiment
    SentimentAggregator,
    FinBERTAnalyzer,
    
    # Risk
    MLRiskManager,
    KellyCriterion,
    
    # Execution
    SmartOrderRouter,
    VWAPExecutor,
    
    # Multi-Brain
    MultiBrainArchitecture,
    BrainCoordinator,
    
    # Monitoring
    PerformanceDashboard,
    AlertSystem,
    
    # Backtesting
    AdvancedBacktester,
    MonteCarloSimulator,
)


def generate_sample_data(num_points: int = 1000) -> dict:
    pass
    """Generate sample market data for demonstration"""
    np.random.seed(42)
    
    # Generate price series with trend and noise
    base_price = 100
    returns = np.random.normal(0.0001, 0.02, num_points)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate volumes
    volumes = np.random.uniform(1000, 10000, num_points)
    
    # Generate timestamps
    start_time = datetime.now() - timedelta(days=num_points // 24)
    timestamps = [start_time + timedelta(hours=i) for i in range(num_points)]
    
    return {
        'symbol': 'BTCUSD',
        'prices': prices.tolist(),
        'volumes': volumes.tolist(),
        'timestamps': timestamps,
        'price': prices[-1],
        'volume': volumes[-1],
        'timestamp': timestamps[-1],
    }


async def demo_dc_engine():
    pass
    """Demonstrate Directional Change Engine"""
    print("\n" + "="*60)
    print("DIRECTIONAL CHANGE ENGINE DEMO")
    print("="*60)
    
    # Initialize DC Engine
    dc_engine = DirectionalChangeEngine(thresholds=[0.01, 0.02, 0.03])
    
    # Generate sample data
    data = generate_sample_data(500)
    
    # Process prices
    for i, price in enumerate(data['prices']):
    pass
        dc_engine.process_price(price, data['timestamps'][i])
    
    # Get events
    events = dc_engine.get_recent_events(10)
    
    print(f"\nProcessed {len(data['prices'])} price points")
    print(f"Detected {len(events)} DC events")
    
    if events:
    pass
        print("\nRecent DC Events:")
        for event in events[-5:]:
    pass
            print(f"  - {event.direction.upper()} at {event.price:.2f} (threshold: {event.threshold*100:.1f}%)")
    
    # Get consensus signal
    signal = dc_engine.get_consensus_signal()
    print(f"\nConsensus Signal: {signal}")


async def demo_sentiment_analysis():
    pass
    """Demonstrate Sentiment Analysis"""
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS DEMO")
    print("="*60)
    
    # Initialize sentiment analyzer
    finbert = FinBERTAnalyzer()
    
    # Sample financial texts
    texts = [
        "Apple reports record quarterly revenue, beating analyst expectations",
        "Fed signals potential rate hike amid inflation concerns",
        "Tech stocks tumble as recession fears grow",
        "Strong job growth suggests economy remains resilient",
        "Company announces major layoffs amid restructuring",
    ]
    
    print("\nAnalyzing financial texts:")
    for text in texts:
    pass
        result = finbert.analyze(text)
        print(f"\n  Text: {text[:50]}...")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Label: {result['label']}")
        print(f"  Confidence: {result['confidence']:.2f}")


async def demo_risk_management():
    pass
    """Demonstrate Risk Management"""
    print("\n" + "="*60)
    print("RISK MANAGEMENT DEMO")
    print("="*60)
    
    # Initialize risk manager
    risk_manager = MLRiskManager({
        'max_daily_loss': 0.03,
        'max_drawdown': 0.15,
    })
    
    # Set initial equity
    risk_manager.update_equity(100000)
    
    # Simulate some P&L
    daily_pnls = [500, -200, 300, -800, 150, -1500, 200]
    
    print("\nSimulating daily P&L:")
    for i, pnl in enumerate(daily_pnls):
    pass
        risk_manager.update_daily_pnl(pnl)
        status = risk_manager.check_risk_limits()
        
        print(f"\n  Day {i+1}: P&L = ${pnl:+.2f}")
        print(f"  Should Trade: {status['should_trade']}")
        if status['breaches']:
    pass
            print(f"  Breaches: {status['breaches']}")
    
    # Get position recommendation
    signal = {'win_prob': 0.6, 'confidence': 0.7}
    recommendation = risk_manager.get_position_recommendation('BTCUSD', signal)
    
    print(f"\nPosition Recommendation for BTCUSD:")
    print(f"  Base Size: ${recommendation.base_size:.2f}")
    print(f"  Adjusted Size: ${recommendation.adjusted_size:.2f}")
    print(f"  Kelly Fraction: {recommendation.kelly_fraction:.2%}")
    print(f"  Reason: {recommendation.reason}")


async def demo_multi_brain():
    pass
    """Demonstrate Multi-Brain Architecture"""
    print("\n" + "="*60)
    print("MULTI-BRAIN ARCHITECTURE DEMO")
    print("="*60)
    
    # Initialize multi-brain
    multi_brain = MultiBrainArchitecture({
        'require_approval': False,
    })
    
    # Generate sample data
    data = generate_sample_data(200)
    
    # Get decision
    decision = await multi_brain.analyze_and_decide(data)
    
    print("\nMulti-Brain Decision:")
    print(f"  Direction: {decision['direction']}")
    print(f"  Confidence: {decision['confidence']:.2%}")
    print(f"  Regime: {decision['regime']}")
    print(f"  Should Trade: {decision['should_trade']}")
    print(f"  Contributing Brains: {decision['contributing_brains']}")
    print(f"  Reasoning: {decision['reasoning']}")
    
    # Get status
    status = multi_brain.get_status()
    print(f"\nSystem Status:")
    print(f"  Active Strategies: {status['coordinator']['active_strategies']}")
    print(f"  Brain Weights: {status['coordinator']['brain_weights']}")


async def demo_execution():
    pass
    """Demonstrate Execution Algorithms"""
    print("\n" + "="*60)
    print("EXECUTION ALGORITHMS DEMO")
    print("="*60)
    
    # Initialize components
    router = SmartOrderRouter()
    vwap = VWAPExecutor()
    
    # Create sample order
    from trading_bot.alpha_engine.execution import Order, OrderType
    
    order = Order(
        order_id="ORD_001",
        symbol="BTCUSD",
        side="buy",
        order_type=OrderType.LIMIT,
        quantity=10000,
        price=50000,
    )
    
    # Route order
    routing = router.route_order(order)
    
    print("\nSmart Order Routing:")
    print(f"  Order: {order.side.upper()} {order.quantity} {order.symbol}")
    print(f"  Routing:")
    for venue, qty in routing:
    pass
        print(f"    - {venue}: {qty:.2f}")
    
    # Create VWAP schedule
    schedule = vwap.create_schedule(order, duration_minutes=60, num_slices=12)
    
    print(f"\nVWAP Execution Schedule ({len(schedule)} slices):")
    for i, slice_info in enumerate(schedule[:5]):
    pass
        print(f"  Slice {i+1}: {slice_info['quantity']:.2f} @ {slice_info['scheduled_time'].strftime('%H:%M:%S')}")
    if len(schedule) > 5:
    pass
        print(f"  ... and {len(schedule) - 5} more slices")


async def demo_backtesting():
    pass
    """Demonstrate Backtesting"""
    print("\n" + "="*60)
    print("BACKTESTING DEMO")
    print("="*60)
    
    # Generate sample data
    data = generate_sample_data(500)
    
    # Create DataFrame
    import pandas as pd
    df = pd.DataFrame({
        'open': data['prices'],
        'high': [p * 1.01 for p in data['prices']],
        'low': [p * 0.99 for p in data['prices']],
        'close': data['prices'],
        'volume': data['volumes'],
    }, index=data['timestamps'])
    
    # Simple strategy
    def simple_strategy(data):
    pass
        if len(data) < 20:
    pass
            return None
        
        sma_fast = data['close'].iloc[-10:].mean()
        sma_slow = data['close'].iloc[-20:].mean()
        
        if sma_fast > sma_slow * 1.01:
    pass
            return {'symbol': 'BTCUSD', 'direction': 'long', 'size': 100}
        elif sma_fast < sma_slow * 0.99:
    pass
            return {'symbol': 'BTCUSD', 'direction': 'short', 'size': 100}
        return None
    
    # Run backtest
    from trading_bot.alpha_engine.backtesting import BacktestConfig
from typing import Set
import numpy
    
    config = BacktestConfig(
        start_date=data['timestamps'][0],
        end_date=data['timestamps'][-1],
        initial_capital=100000,
    )
    
    backtester = AdvancedBacktester(config)
    backtester.set_strategy(simple_strategy)
    result = backtester.run(df)
    
    print("\nBacktest Results:")
    print(f"  Total Return: {result.total_return:.2%}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {result.max_drawdown:.2%}")
    print(f"  Total Trades: {result.total_trades}")
    print(f"  Win Rate: {result.win_rate:.2%}")
    print(f"  Profit Factor: {result.profit_factor:.2f}")
    
    # Monte Carlo simulation
    if result.trades:
    pass
        mc = MonteCarloSimulator({'num_simulations': 1000})
        mc_result = mc.simulate(result.trades)
        
        print(f"\nMonte Carlo Simulation ({mc_result.num_simulations} runs):")
        print(f"  Mean Return: {mc_result.mean_return:.2%}")
        print(f"  5th Percentile: {mc_result.percentile_5:.2%}")
        print(f"  95th Percentile: {mc_result.percentile_95:.2%}")
        print(f"  Probability of Profit: {mc_result.probability_profit:.2%}")


async def demo_full_system():
    pass
    """Demonstrate Full AlphaEngine System"""
    print("\n" + "="*60)
    print("FULL ALPHAENGINE SYSTEM DEMO")
    print("="*60)
    
    # Initialize orchestrator
    config = {
        'mode': 'paper',
        'dc_thresholds': [0.01, 0.02, 0.03],
        'risk': {
            'max_daily_loss': 0.03,
            'max_drawdown': 0.15,
        },
    }
    
    orchestrator = AlphaEngineOrchestrator(config)
    await orchestrator.start()
    
    # Generate sample data
    data = generate_sample_data(200)
    
    # Process market data
    print("\nProcessing market data...")
    signal = await orchestrator.process_market_data(data)
    
    if signal:
    pass
        print(f"\nGenerated Trading Signal:")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Direction: {signal.direction}")
        print(f"  Strength: {signal.strength.value}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Recommended Size: ${signal.recommended_size:.2f}")
        print(f"  Entry Price: ${signal.entry_price:.2f}")
        print(f"  Stop Loss: ${signal.stop_loss:.2f}")
        print(f"  Take Profit: ${signal.take_profit:.2f}")
        print(f"  Execution Algo: {signal.execution_algo}")
        print(f"  Reasoning: {signal.reasoning}")
        
        # Create execution plan
        plan = orchestrator.create_execution_plan(signal)
        print(f"\nExecution Plan:")
        print(f"  Algorithm: {plan.algorithm}")
        print(f"  Venues: {plan.venues}")
        print(f"  Estimated Cost: ${plan.estimated_cost:.2f}")
    else:
    pass
        print("\nNo trading signal generated (conditions not met)")
    
    # Get system status
    status = orchestrator.get_status()
    print(f"\nSystem Status:")
    print(f"  Mode: {status['mode']}")
    print(f"  Running: {status['is_running']}")
    print(f"  Signals Generated: {status['signals_generated']}")
    print(f"  Trades Executed: {status['trades_executed']}")
    
    await orchestrator.stop()


async def main():
    pass
    """Run all demos"""
    print("\n" + "="*60)
    print("ALPHAENGINE ENHANCED TRADING SYSTEM")
    print("Comprehensive Demo")
    print("="*60)
    
    try:
    pass
        # Run individual component demos
        await demo_dc_engine()
        await demo_sentiment_analysis()
        await demo_risk_management()
        await demo_multi_brain()
        await demo_execution()
        await demo_backtesting()
        
        # Run full system demo
        await demo_full_system()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("\nAll AlphaEngine components demonstrated successfully!")
        print("The system is ready for production use.")
        
    except Exception as e:
    pass
        logger.error(f"Demo error: {e}")
        raise


if __name__ == "__main__":
    pass
    asyncio.run(main())
