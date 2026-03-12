#!/usr/bin/env python3
"""
Unified Architecture Demo
=========================

Demonstrates the complete 6-layer unified trading architecture.

This demo shows:
    pass
1. System initialization
2. Data fetching and validation
3. Intelligence analysis (MoE, Cognitive, RL)
4. Signal generation and verification
5. Risk checking
6. Execution simulation
7. Orchestration and reporting
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    pass
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    pass
    """Print a subsection header"""
    print(f"\n--- {title} ---")


async def demo_layer1_data():
    pass
    """Demo Layer 1: Data Foundation"""
    print_header("LAYER 1: DATA FOUNDATION")
    
    from trading_bot.unified_architecture.layer1_data_foundation import (
        DataFoundation, DataQuality
    )
    
    # Initialize
    print_subheader("Initializing Data Foundation")
    data_layer = DataFoundation()
    
    # Show sources
    print("\nData Sources:")
    for name, source in data_layer.sources.items():
    pass
        print(f"  - {name}: {source.source_type.value}")
    
    # Connect (will fail without real connections, but shows the flow)
    print_subheader("Connecting to Data Sources")
    results = await data_layer.connect_all()
    for name, connected in results.items():
    pass
        status = "✓" if connected else "✗"
        print(f"  {status} {name}")
    
    print("\nData Foundation Status:")
    status = data_layer.get_status()
    print(f"  Packets received: {status['stats']['packets_received']}")
    print(f"  Packets validated: {status['stats']['packets_validated']}")
    
    return data_layer


async def demo_layer2_intelligence():
    pass
    """Demo Layer 2: Intelligence Core"""
    print_header("LAYER 2: INTELLIGENCE CORE")
    
    from trading_bot.unified_architecture.layer2_intelligence_core import (
        IntelligenceCore, ExpertCategory
    )
    
    # Initialize
    print_subheader("Initializing Intelligence Core")
    intel_layer = IntelligenceCore()
    
    # Show experts
    print("\nExperts Loaded:")
    for expert_id, expert in intel_layer.expert_router.routed_experts.items():
    pass
        print(f"  - {expert_id} ({expert.category.value})")
    
    print(f"\nShared Expert: {intel_layer.expert_router.shared_expert.expert_id}")
    print(f"Top-K Routing: {intel_layer.expert_router.top_k}")
    
    # Show status
    print("\nIntelligence Core Status:")
    status = intel_layer.get_status()
    print(f"  Expert count: {status['expert_count']}")
    print(f"  Cognitive available: {status['cognitive_available']}")
    print(f"  RL available: {status['rl_available']}")
    
    return intel_layer


async def demo_layer3_strategy():
    pass
    """Demo Layer 3: Strategy Engine"""
    print_header("LAYER 3: STRATEGY ENGINE")
    
    from trading_bot.unified_architecture.layer3_strategy_engine import (
        StrategyEngine, SignalDirection, MarketRegime
    )
    import pandas as pd
    import numpy as np
    
    # Initialize
    print_subheader("Initializing Strategy Engine")
    strategy_layer = StrategyEngine()
    
    # Create sample market data
    print_subheader("Creating Sample Market Data")
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', periods=100, freq='1H')
    prices = 50000 + np.cumsum(np.random.normal(0, 100, 100))
    
    market_data = pd.DataFrame({
        'open': prices + np.random.normal(0, 10, 100),
        'high': prices + np.abs(np.random.normal(50, 20, 100)),
        'low': prices - np.abs(np.random.normal(50, 20, 100)),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    print(f"  Data points: {len(market_data)}")
    print(f"  Price range: ${market_data['close'].min():,.2f} - ${market_data['close'].max():,.2f}")
    
    # Detect regime
    print_subheader("Detecting Market Regime")
    regime, confidence = strategy_layer.regime_detector.detect(market_data)
    print(f"  Regime: {regime.value}")
    print(f"  Confidence: {confidence:.2%}")
    
    # Generate signal
    print_subheader("Generating Trading Signal")
    signal = await strategy_layer.generate_signal(
        symbol='BTCUSDT',
        market_data=market_data,
        indicators={'rsi': 45},
        sentiment={'average': 0.2}
    )
    
    if signal:
    pass
        print(f"  Direction: {signal.direction.value}")
        print(f"  Strength: {signal.strength.value}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Verification Score: {signal.verification_score:.2%}")
        print(f"  Entry: ${signal.entry_price:,.2f}")
        print(f"  Stop Loss: ${signal.stop_loss:,.2f}")
        print(f"  Take Profit: ${signal.take_profit:,.2f}")
        print(f"\n  Reasoning: {signal.reasoning[:100]}...")
    else:
    pass
        print("  No signal generated (verification failed)")
    
    return strategy_layer


async def demo_layer4_execution():
    pass
    """Demo Layer 4: Execution Layer"""
    print_header("LAYER 4: EXECUTION LAYER")
    
    from trading_bot.unified_architecture.layer4_execution import (
        ExecutionLayer, OrderSide, OrderType
    )
    
    # Initialize
    print_subheader("Initializing Execution Layer")
    exec_layer = ExecutionLayer()
    
    # Create order
    print_subheader("Creating Order")
    order = exec_layer.order_manager.create_order(
        symbol='BTCUSDT',
        side=OrderSide.BUY,
        quantity=0.1,
        order_type=OrderType.MARKET,
        price=50000
    )
    
    print(f"  Order ID: {order.order_id}")
    print(f"  Symbol: {order.symbol}")
    print(f"  Side: {order.side.value}")
    print(f"  Quantity: {order.quantity}")
    print(f"  Status: {order.status.value}")
    
    # Show routing
    print_subheader("Smart Routing")
    venue = exec_layer.router.route(order)
    print(f"  Selected venue: {venue}")
    
    # Show slippage protection
    print_subheader("Slippage Protection")
    print(f"  Max slippage: {exec_layer.slippage_protector.max_slippage_bps} bps")
    print(f"  Warning threshold: {exec_layer.slippage_protector.warning_slippage_bps} bps")
    
    return exec_layer


async def demo_layer5_risk():
    pass
    """Demo Layer 5: Risk & Safety"""
    print_header("LAYER 5: RISK & SAFETY")
    
    from trading_bot.unified_architecture.layer5_risk_safety import (
        RiskSafetyLayer, RiskLevel, FailSafeMode
    )
    
    # Initialize
    print_subheader("Initializing Risk & Safety Layer")
    risk_layer = RiskSafetyLayer({
        'risk': {
            'initial_equity': 100000,
            'limits': {
                'max_risk_per_trade_pct': 2.0,
                'max_daily_loss_pct': 5.0,
                'max_drawdown_pct': 20.0
            }
        }
    })
    
    # Show limits
    print("\nRisk Limits:")
    print(f"  Max risk/trade: {risk_layer.risk_manager.limits.max_risk_per_trade_pct}%")
    print(f"  Max daily loss: {risk_layer.risk_manager.limits.max_daily_loss_pct}%")
    print(f"  Max drawdown: {risk_layer.risk_manager.limits.max_drawdown_pct}%")
    print(f"  Max positions: {risk_layer.risk_manager.limits.max_positions}")
    
    # Check trade
    print_subheader("Pre-Trade Risk Check")
    result = risk_layer.pre_trade_check(
        symbol='BTCUSDT',
        side='buy',
        size=0.1,
        entry_price=50000,
        stop_loss=49000
    )
    
    print(f"  Approved: {result.approved}")
    print(f"  Risk Level: {result.risk_level.value}")
    print(f"  Adjusted Size: {result.adjusted_size}")
    if result.warnings:
    pass
        print(f"  Warnings: {result.warnings}")
    if result.rejections:
    pass
        print(f"  Rejections: {result.rejections}")
    
    # Show fail-safe
    print_subheader("Fail-Safe System")
    print(f"  Current Mode: {risk_layer.fail_safe.mode.value}")
    print(f"  Position Multiplier: {risk_layer.fail_safe.get_position_multiplier()}")
    
    # Show circuit breaker
    print_subheader("Circuit Breaker")
    print(f"  State: {risk_layer.circuit_breaker.state.value}")
    print(f"  Error threshold: {risk_layer.circuit_breaker.error_threshold}")
    
    return risk_layer


async def demo_layer6_orchestration():
    pass
    """Demo Layer 6: Orchestration"""
    print_header("LAYER 6: ORCHESTRATION")
    
    from trading_bot.unified_architecture.layer6_orchestration import (
        MasterOrchestrator, OperationMode, MessageType, MessagePriority
    )
    
    # Initialize
    print_subheader("Initializing Master Orchestrator")
    orchestrator = MasterOrchestrator({
        'autonomous': {
            'mode': 'semi_autonomous',
            'max_autonomous_trades': 10
        }
    })
    
    # Show operation mode
    print(f"\nOperation Mode: {orchestrator.autonomous.mode.value}")
    print(f"Max Autonomous Trades: {orchestrator.autonomous.max_autonomous_trades}")
    
    # Send message
    print_subheader("Human Protocol - Sending Message")
    msg_id = orchestrator.human_protocol.send_message(
        message_type=MessageType.STATUS,
        priority=MessagePriority.LOW,
        subject="Demo Status Update",
        content="This is a demo message from the unified architecture."
    )
    print(f"  Message sent: {msg_id}")
    
    # Show evolution
    print_subheader("Evolution Engine")
    issues = orchestrator.evolution_engine.analyze_performance({
        'win_rate': 0.40,
        'drawdown': 0.12,
        'sharpe_ratio': 0.8
    })
    print(f"  Issues detected: {len(issues)}")
    for issue in issues:
    pass
        print(f"    - {issue}")
    
    return orchestrator


async def demo_unified_system():
    pass
    """Demo the complete unified system"""
    print_header("UNIFIED TRADING SYSTEM")
    
    from trading_bot.unified_architecture import (
import numpy
import pandas
        UnifiedTradingSystem, SystemConfig, TradingMode
    )
    
    # Create configuration
    print_subheader("Creating System Configuration")
    config = SystemConfig(
        mode=TradingMode.SIMULATION,
        symbols=['BTCUSDT', 'ETHUSDT'],
        initial_capital=100000,
        max_risk_per_trade=2.0,
        max_drawdown=20.0,
        cycle_interval_seconds=60,
        operation_mode='semi_autonomous'
    )
    
    print(f"  Mode: {config.mode.value}")
    print(f"  Symbols: {config.symbols}")
    print(f"  Capital: ${config.initial_capital:,.2f}")
    
    # Create system
    print_subheader("Creating Unified System")
    system = UnifiedTradingSystem(config)
    
    # Initialize
    print_subheader("Initializing System")
    await system.initialize()
    
    # Get status
    print_subheader("System Status")
    status = system.get_status()
    print(f"  Status: {status['system']['status']}")
    print(f"  Mode: {status['system']['mode']}")
    
    # Get statistics
    print_subheader("System Statistics")
    stats = system.get_statistics()
    print(f"  Equity: ${stats['risk']['equity']:,.2f}")
    print(f"  Drawdown: {stats['risk']['drawdown']:.2%}")
    
    # Cleanup
    await system.stop()
    
    return system


async def main():
    pass
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  UNIFIED TRADING ARCHITECTURE - COMPLETE DEMO")
    print("=" * 70)
    print("\nThis demo showcases all 6 layers of the unified architecture.")
    print("Each layer integrates the best components from the existing codebase")
    print("with DeepSeek-inspired innovations.")
    
    try:
    pass
        # Demo each layer
        await demo_layer1_data()
        await demo_layer2_intelligence()
        await demo_layer3_strategy()
        await demo_layer4_execution()
        await demo_layer5_risk()
        await demo_layer6_orchestration()
        
        # Demo unified system
        await demo_unified_system()
        
        # Summary
        print_header("DEMO COMPLETE")
        print("""
The unified architecture successfully integrates:
    pass
✓ Layer 1: Data Foundation
  - Multi-source data acquisition
  - Quality validation and quarantine
  - Feature preprocessing
  - Data fusion

✓ Layer 2: Intelligence Core
  - 257 Expert Mixture of Experts
  - 10-Layer Cognitive Architecture
  - Offline RL (CQL, BCQ, IQL)
  - Meta-learning

✓ Layer 3: Strategy Engine
  - Generator-Verifier architecture
  - Full reasoning chains
  - Market regime detection
  - Multi-timeframe analysis

✓ Layer 4: Execution Layer
  - Smart order routing
  - Order lifecycle management
  - Fill tracking
  - Slippage protection

✓ Layer 5: Risk & Safety
  - Multi-layer risk management
  - Fail-safe system (5 modes)
  - Circuit breaker
  - Emergency shutdown

✓ Layer 6: Orchestration
  - Human-in-loop protocol
  - Self-evolution engine
  - Autonomous operation
  - Daily reporting

To run the full system:
    pass
  python main_unified.py --mode paper --symbols BTCUSDT

To run with the launcher:
    pass
  RUN_UNIFIED_SYSTEM.bat
""")
        
    pass
        logger.exception(f"Demo error: {e}")
        raise


if __name__ == "__main__":
    pass
    asyncio.run(main())
