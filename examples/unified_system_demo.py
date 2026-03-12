#!/usr/bin/env python3
"""
Unified System Demo - Comprehensive demonstration of the 11-layer architecture

This demo showcases:
1. System initialization
2. Layer registration and lifecycle
3. Market data processing
4. Signal generation and verification
5. Risk management
6. Execution simulation
7. Governance and audit
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def demo_basic_usage():
    """Demonstrate basic system usage"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic System Usage")
    print("=" * 70)
    
    from trading_bot.unified_system import UnifiedMasterSystem
    from trading_bot.unified_system.unified_types import MarketData, Timeframe
    
    # Create system
    config = {
        'system_name': 'Demo System',
        'trading_mode': 'simulation',
        'symbols': ['BTCUSDT'],
        'initial_capital': 10000.0,
    }
    
    system = UnifiedMasterSystem(config)
    
    # Initialize
    print("\n[Step 1] Initializing system...")
    await system.initialize()
    print(f"Status: {system.get_status().value}")
    
    # Start
    print("\n[Step 2] Starting system...")
    await system.start()
    print(f"Status: {system.get_status().value}")
    
    # Get health
    print("\n[Step 3] Checking health...")
    health = await system.get_health()
    print(f"  Uptime: {health.uptime_seconds:.1f}s")
    print(f"  Layers active: {len(health.layer_status)}")
    
    # Process sample data
    print("\n[Step 4] Processing market data...")
    sample_data = MarketData(
        symbol='BTCUSDT',
        timestamp=datetime.utcnow(),
        open=50000.0,
        high=50500.0,
        low=49800.0,
        close=50200.0,
        volume=1000.0,
        timeframe=Timeframe.M1
    )
    
    decision = await system.process_tick(sample_data)
    print(f"  Decision generated: {decision is not None}")
    
    # Get metrics
    print("\n[Step 5] System metrics...")
    metrics = system.get_metrics()
    print(f"  Signals: {metrics.total_signals}")
    print(f"  Trades: {metrics.total_trades}")
    print(f"  Errors: {metrics.total_errors}")
    
    # Shutdown
    print("\n[Step 6] Shutting down...")
    await system.shutdown()
    print(f"Status: {system.get_status().value}")
    
    print("\n✓ Basic usage demo complete")


async def demo_layer_registry():
    """Demonstrate layer registry functionality"""
    print("\n" + "=" * 70)
    print("DEMO 2: Layer Registry")
    print("=" * 70)
    
    from trading_bot.unified_system.layer_registry import LayerRegistry
    
    registry = LayerRegistry()
    
    print("\n11-Layer Architecture:")
    print("-" * 40)
    for layer_id, name in registry.LAYER_NAMES.items():
        print(f"  Layer {layer_id:2d}: {name}")
    
    print("\n✓ Layer registry demo complete")


async def demo_configuration():
    """Demonstrate configuration management"""
    print("\n" + "=" * 70)
    print("DEMO 3: Configuration Management")
    print("=" * 70)
    
    from trading_bot.unified_system.unified_config import UnifiedConfig
    
    # Create config
    config = UnifiedConfig(
        system_name="Demo Config",
        trading_mode="paper",
        symbols=['BTCUSDT', 'ETHUSDT'],
        initial_capital=25000.0,
    )
    
    print("\nConfiguration:")
    print(f"  System: {config.system_name}")
    print(f"  Mode: {config.trading_mode.value}")
    print(f"  Symbols: {config.symbols}")
    print(f"  Capital: ${config.initial_capital:,.2f}")
    
    print("\nRisk Settings:")
    print(f"  Max risk/trade: {config.risk.max_risk_per_trade:.1%}")
    print(f"  Max daily loss: {config.risk.max_daily_loss:.1%}")
    print(f"  Max drawdown: {config.risk.max_drawdown:.1%}")
    
    print("\nSignal Settings:")
    print(f"  Min confidence: {config.signal.min_confidence:.1%}")
    print(f"  Verification: {config.signal.verification_enabled}")
    
    # Validate
    valid, errors = config.validate()
    print(f"\nValidation: {'✓ Passed' if valid else '✗ Failed'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    print("\n✓ Configuration demo complete")


async def demo_types():
    """Demonstrate unified types"""
    print("\n" + "=" * 70)
    print("DEMO 4: Unified Types")
    print("=" * 70)
    
    from trading_bot.unified_system.unified_types import (
        MarketData, TradingSignal, Order, Position, RiskMetrics,
        SignalDirection, SignalStrength, SignalSource, OrderType, OrderSide,
        MarketRegime, Timeframe
    )
    
    # Market Data
    print("\nMarketData:")
    data = MarketData(
        symbol='BTCUSDT',
        timestamp=datetime.utcnow(),
        open=50000.0,
        high=50500.0,
        low=49800.0,
        close=50200.0,
        volume=1000.0,
        timeframe=Timeframe.M5
    )
    print(f"  {data.symbol}: O={data.open} H={data.high} L={data.low} C={data.close}")
    
    # Trading Signal
    print("\nTradingSignal:")
    signal = TradingSignal(
        signal_id="SIG-001",
        symbol='BTCUSDT',
        direction=SignalDirection.BUY,
        confidence=0.85,
        strength=SignalStrength.STRONG,
        timestamp=datetime.utcnow(),
        source=SignalSource.ENSEMBLE,
        reasoning="Strong uptrend with momentum confirmation",
        stop_loss=49500.0,
        take_profit=51500.0,
        regime=MarketRegime.TRENDING_UP
    )
    print(f"  {signal.symbol}: {signal.direction.value} @ {signal.confidence:.1%} confidence")
    print(f"  Reasoning: {signal.reasoning}")
    
    # Order
    print("\nOrder:")
    order = Order(
        order_id="ORD-001",
        symbol='BTCUSDT',
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=0.1,
        price=50200.0
    )
    print(f"  {order.order_id}: {order.side.value} {order.quantity} {order.symbol} @ {order.price}")
    
    # Risk Metrics
    print("\nRiskMetrics:")
    risk = RiskMetrics(
        portfolio_var=0.02,
        max_drawdown=0.15,
        daily_loss=0.01,
        daily_loss_limit=0.05
    )
    print(f"  VaR: {risk.portfolio_var:.1%}")
    print(f"  Max DD: {risk.max_drawdown:.1%}")
    print(f"  Daily Loss: {risk.daily_loss:.1%} / {risk.daily_loss_limit:.1%}")
    
    print("\n✓ Types demo complete")


async def demo_emergency_stop():
    """Demonstrate emergency stop functionality"""
    print("\n" + "=" * 70)
    print("DEMO 5: Emergency Stop")
    print("=" * 70)
    
    from trading_bot.unified_system import UnifiedMasterSystem
    
    system = UnifiedMasterSystem({'trading_mode': 'simulation'})
    await system.initialize()
    await system.start()
    
    print("\nSystem running...")
    print(f"Status: {system.get_status().value}")
    
    print("\nTriggering emergency stop...")
    await system.emergency_stop()
    
    print(f"Status: {system.get_status().value}")
    
    print("\n✓ Emergency stop demo complete")


async def demo_summary():
    """Show system summary"""
    print("\n" + "=" * 70)
    print("SYSTEM SUMMARY")
    print("=" * 70)
    
    print("""
    UNIFIED TRADING SYSTEM v3.0
    ===========================
    
    Architecture:
    - 11 Layers (Infrastructure → Governance)
    - 177 Modules integrated
    - 3,121 Files
    - ~1,494,642 Lines of code
    
    Key Features:
    ✓ Multi-layer architecture
    ✓ Centralized configuration
    ✓ Layer registry and lifecycle management
    ✓ Unified type system
    ✓ Risk management and circuit breakers
    ✓ Multi-agent decision verification
    ✓ Smart order execution
    ✓ Governance and audit logging
    ✓ Emergency stop capability
    
    Entry Points:
    - main_unified_system.py (CLI)
    - RUN_UNIFIED_SYSTEM.bat (Windows launcher)
    - trading_bot.unified_system (Python package)
    
    Documentation:
    - docs/UNIFIED_SYSTEM_ARCHITECTURE.md
    - docs/DEPLOYMENT_GUIDE.md
    """)


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("UNIFIED TRADING SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 70)
    print("\nThis demo showcases the 11-layer unified architecture.")
    
    try:
        await demo_layer_registry()
        await demo_configuration()
        await demo_types()
        await demo_basic_usage()
        await demo_emergency_stop()
        await demo_summary()
        
        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 70 + "\n")
        
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())
