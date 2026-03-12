"""
Real-Time Trading System Demo
=============================

Demonstrates the complete real-time trading system with all components.

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def demo_data_hub():
    """Demo the RealTimeDataHub"""
    print("\n" + "=" * 60)
    print("DEMO: RealTimeDataHub")
    print("=" * 60)
    
    from trading_bot.realtime.realtime_data_hub import (
        RealTimeDataHub, StreamConfig, StreamType
    )
    
    hub = RealTimeDataHub({'use_simulation': True})
    await hub.initialize()
    await hub.start()
    
    # Subscribe to tick stream
    tick_count = 0
    
    def on_tick(symbol, tick):
        nonlocal tick_count
        tick_count += 1
        if tick_count <= 5:
            print(f"  Tick {tick_count}: {symbol} bid={tick.bid:.2f} ask={tick.ask:.2f} "
                  f"spread={tick.spread_bps:.1f}bps")
    
    hub.subscribe(StreamType.TICK, on_tick)
    
    # Subscribe to BTCUSDT
    await hub.subscribe_stream(StreamConfig(
        stream_type=StreamType.TICK,
        symbol='BTCUSDT',
        exchange='binance'
    ))
    
    # Let it run for a bit
    await asyncio.sleep(2)
    
    print(f"\n  Total ticks received: {tick_count}")
    print(f"  Metrics: {hub.get_metrics()}")
    
    await hub.stop()
    print("  DataHub demo complete!")


async def demo_signal_engine():
    """Demo the RealTimeSignalEngine"""
    print("\n" + "=" * 60)
    print("DEMO: RealTimeSignalEngine")
    print("=" * 60)
    
    from trading_bot.realtime.realtime_signal_engine import (
        RealTimeSignalEngine, RealTimeIndicators
    )
    RealTimeDataHub, StreamConfig, StreamType
    )
    
    # Create components
    hub = RealTimeDataHub({'use_simulation': True})
    engine = RealTimeSignalEngine({})
    
    await hub.initialize()
    await hub.start()
    await engine.start()
    
    # Wire up
    hub.subscribe(StreamType.TICK, engine.on_tick)
    
    # Track signals
    signals_received = []
    
    def on_signal(signal):
        signals_received.append(signal)
        print(f"  Signal: {signal.symbol} {signal.direction.value} "
              f"confidence={signal.confidence:.2f} type={signal.signal_type.value}")
    
    engine.subscribe(on_signal)
    
    # Subscribe to data
    await hub.subscribe_stream(StreamConfig(
        stream_type=StreamType.TICK,
        symbol='BTCUSDT',
        exchange='binance'
    ))
    
    # Let it generate signals
    await asyncio.sleep(5)
    
    print(f"\n  Total signals generated: {len(signals_received)}")
    print(f"  Engine metrics: {engine.get_metrics()}")
    
    await engine.stop()
    await hub.stop()
    print("  SignalEngine demo complete!")


async def demo_execution():
    """Demo the RealTimeExecution"""
    print("\n" + "=" * 60)
    print("DEMO: RealTimeExecution")
    print("=" * 60)
    
    from trading_bot.realtime.realtime_execution import (
        RealTimeExecution, OrderSide, OrderType
    )
    
    execution = RealTimeExecution({
        'broker': {'latency_ms': 50, 'slippage_bps': 2}
    })
    
    await execution.start()
    
    # Update price
    execution.update_price('BTCUSDT', 50000)
    
    # Submit orders
    print("\n  Submitting orders...")
    
    order1 = await execution.submit_order(
        symbol='BTCUSDT',
        side=OrderSide.BUY,
        quantity=0.1,
        order_type=OrderType.MARKET
    )
    print(f"  Order 1: {order1.order_id} status={order1.status.value} "
          f"filled={order1.filled_quantity} @ {order1.avg_fill_price:.2f}")
    
    order2 = await execution.submit_order(
        symbol='BTCUSDT',
        side=OrderSide.SELL,
        quantity=0.05,
        order_type=OrderType.MARKET
    )
    print(f"  Order 2: {order2.order_id} status={order2.status.value} "
          f"filled={order2.filled_quantity} @ {order2.avg_fill_price:.2f}")
    
    print(f"\n  Execution metrics: {execution.get_metrics()}")
    
    await execution.stop()
    print("  Execution demo complete!")


async def demo_risk_monitor():
    """Demo the RealTimeRiskMonitor"""
    print("\n" + "=" * 60)
    print("DEMO: RealTimeRiskMonitor")
    print("=" * 60)
    
    from trading_bot.realtime.realtime_risk import RealTimeRiskMonitor
    
    risk = RealTimeRiskMonitor({
        'initial_capital': 100000,
        'max_position_size': 0.02,
        'max_daily_loss': 0.05,
        'max_drawdown': 0.20
    })
    
    await risk.start()
    
    # Simulate fills
    print("\n  Simulating trades...")
    
    await risk.on_fill('BTCUSDT', 'long', 0.1, 50000)
    print(f"  Opened long 0.1 BTC @ 50000")
    
    # Price update
    risk.on_price_update('BTCUSDT', 50500)
    print(f"  Price updated to 50500")
    
    snapshot = risk.get_portfolio_snapshot()
    if snapshot:
        print(f"  Equity: ${snapshot.total_equity:,.2f}")
        print(f"  Unrealized P&L: ${snapshot.unrealized_pnl:,.2f}")
        print(f"  Risk Level: {snapshot.risk_level.value}")
    
    # Check if we can trade
    can_trade, reason = risk.can_trade()
    print(f"\n  Can trade: {can_trade} ({reason})")
    
    # Pre-trade check
    approved, reason = risk.check_order('ETHUSDT', 'long', 0.5, 3000)
    print(f"  Order check: {approved} ({reason})")
    
    print(f"\n  Risk metrics: {risk.get_metrics()}")
    
    await risk.stop()
    print("  RiskMonitor demo complete!")


async def demo_ml_engine():
    """Demo the RealTimeMLEngine"""
    print("\n" + "=" * 60)
    print("DEMO: RealTimeMLEngine")
    print("=" * 60)
    
    from trading_bot.realtime.realtime_ml import RealTimeMLEngine
    
    ml = RealTimeMLEngine({})
    await ml.start()
    
    # Simulate tick stream
    print("\n  Feeding price data...")
    
    import random
    price = 50000
    
    for i in range(50):
        price *= (1 + random.gauss(0, 0.001))
        prediction = await ml.on_tick('BTCUSDT', price, random.uniform(100, 1000))
        
        if i % 10 == 0:
            print(f"  Tick {i}: price={price:.2f} prediction={prediction.value:.3f} "
                  f"confidence={prediction.confidence:.2f}")
    
    print(f"\n  Model accuracies: {ml.get_model_accuracies()}")
    print(f"  ML metrics: {ml.get_metrics()}")
    
    await ml.stop()
    print("  MLEngine demo complete!")


async def demo_full_system():
    """Demo the complete RealTimeOrchestrator"""
    print("\n" + "=" * 60)
    print("DEMO: Complete Real-Time Trading System")
    print("=" * 60)
    
    from trading_bot.realtime import create_realtime_system
    
    # Create system
    system = create_realtime_system({
        'mode': 'simulation',
        'symbols': ['BTCUSDT'],
        'initial_capital': 100000,
        'enable_ml': True,
        'enable_signals': True,
        'enable_execution': True,
        'enable_risk': True
    })
    
    # Initialize
    print("\n  Initializing system...")
    await system.initialize()
    
    # Subscribe to status updates
    def on_status(status):
        print(f"  Status: ticks={status.ticks_processed} signals={status.signals_generated} "
              f"orders={status.orders_executed} pnl=${status.current_pnl:.2f}")
    
    system.subscribe_status(on_status)
    
    # Run for 10 seconds
    print("\n  Running for 10 seconds...")
    
    task = asyncio.create_task(system.start())
    await asyncio.sleep(10)
    await system.stop()
    
    # Final status
    status = system.get_status()
    print("\n  Final Status:")
    print(f"    State: {status.state.value}")
    print(f"    Uptime: {status.uptime_seconds:.1f}s")
    print(f"    Ticks Processed: {status.ticks_processed}")
    print(f"    Signals Generated: {status.signals_generated}")
    print(f"    Orders Executed: {status.orders_executed}")
    print(f"    Current P&L: ${status.current_pnl:.2f}")
    print(f"    Risk Level: {status.risk_level}")
    
    print("\n  Full system demo complete!")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("    ALPHAALGO REAL-TIME TRADING SYSTEM DEMO")
    print("    Version 3.0.0")
    print("=" * 60)
    
    try:
        # Individual component demos
        await demo_data_hub()
        await demo_signal_engine()
        await demo_execution()
        await demo_risk_monitor()
        await demo_ml_engine()
        
        # Full system demo
        await demo_full_system()
        
        print("\n" + "=" * 60)
        print("    ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
