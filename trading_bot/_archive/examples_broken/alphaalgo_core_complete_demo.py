"""
AlphaAlgo Core - Complete Integration Demo

Demonstrates all integration patterns:
1. Basic usage
2. MSOS integration
3. SurvivalCore integration
4. Signal generator wrapping
5. Risk manager integration
6. Main loop integration
7. Multi-layer defense
8. Monitoring and statistics

Author: AlphaAlgo Core
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DEMO 1: Basic Usage
# ============================================================================

async def demo_basic_usage():
    """Demonstrate basic AlphaAlgo Core usage"""
    print("\n" + "="*80)
    print("DEMO 1: Basic Usage")
    print("="*80)
    
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
        request_id="demo_001",
        symbol="BTCUSDT",
        direction="long",
        quantity=1.0,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        signal_strength=0.75,
        signal_source="demo",
        strategy_id="trend_follower",
        regime="trending",
        volatility=0.15,
        liquidity_score=0.8,
        current_equity=100000.0,
        current_drawdown=0.05,
        correlation_exposure=0.3
    )
    
    # Evaluate
    decision = await core.evaluate_trade_request(request)
    
    # Display results
    print(f"\n📊 Trade Request: {request.symbol} {request.direction}")
    print(f"   Entry: ${request.entry_price:,.2f}")
    print(f"   Stop Loss: ${request.stop_loss:,.2f}")
    print(f"   Quantity: {request.quantity}")
    print(f"   Signal Strength: {request.signal_strength:.2%}")
    
    print(f"\n🎯 Decision: {decision.outcome.value}")
    print(f"   Approved: {'✅ YES' if decision.approved else '❌ NO'}")
    
    if decision.approved:
        print(f"   Approved Quantity: {decision.approved_quantity:.4f}")
        print(f"   Min Confidence: {decision.min_confidence:.2%}")
        print(f"\n   Confidence Breakdown:")
        for component, value in decision.confidence_breakdown.items():
            print(f"      {component}: {value:.2%}")
    else:
        print(f"   Rejection Reason: {decision.rejection_reason}")
        print(f"   Market Hostility: {decision.market_hostility}")
    
    print(f"\n⏱️  Evaluation Time: {decision.evaluation_time_ms:.1f}ms")
    print(f"   Risk Score: {decision.risk_score:.2%}")


# ============================================================================
# DEMO 2: MSOS Integration
# ============================================================================

async def demo_msos_integration():
    """Demonstrate MSOS integration"""
    print("\n" + "="*80)
    print("DEMO 2: MSOS Integration")
    print("="*80)
    
    from trading_bot.core.alphaalgo_core_integration import create_msos_adapter
    
    # Initialize adapter
    msos_adapter = create_msos_adapter()
    
    # MSOS signal data
    signal_data = {
        'direction': 'long',
        'quantity': 1.0,
        'price': 1.0850,
        'stop_loss': 1.0800,
        'take_profit': 1.0950,
        'confidence': 0.75,
        'regime': 'trending',
        'volatility': 0.12,
        'liquidity_score': 0.85,
        'drawdown': 0.03,
        'correlation': 0.25
    }
    
    strategy_config = {
        'strategy_id': 'msos_trend_v1',
        'max_risk': 0.02,
        'max_leverage': 3.0
    }
    
    # Evaluate
    approved, position_size, reason = await msos_adapter.evaluate_msos_signal(
        symbol="EURUSD",
        signal_data=signal_data,
        strategy_config=strategy_config,
        equity=100000.0
    )
    
    # Display results
    print(f"\n📊 MSOS Signal: EURUSD {signal_data['direction']}")
    print(f"   Price: {signal_data['price']:.4f}")
    print(f"   Stop Loss: {signal_data['stop_loss']:.4f}")
    print(f"   MSOS Confidence: {signal_data['confidence']:.2%}")
    
    print(f"\n🎯 AlphaAlgo Core Decision:")
    print(f"   Approved: {'✅ YES' if approved else '❌ NO'}")
    
    if approved:
        print(f"   Position Size: {position_size:.4f}")
        print(f"   Reason: {reason}")
    else:
        print(f"   Rejection Reason: {reason}")


# ============================================================================
# DEMO 3: SurvivalCore Integration
# ============================================================================

async def demo_survival_core_integration():
    """Demonstrate SurvivalCore integration"""
    print("\n" + "="*80)
    print("DEMO 3: SurvivalCore Integration")
    print("="*80)
    
    from trading_bot.core.alphaalgo_core_integration import create_survival_core_adapter
    
    # Initialize adapter
    survival_adapter = create_survival_core_adapter()
    
    # Signal from SurvivalCore
    signal = {
        'signal_id': 'survival_001',
        'symbol': 'BTCUSDT',
        'direction': 'long',
        'quantity': 0.5,
        'price': 50000.0,
        'stop_loss': 49000.0,
        'confidence': 0.70,
        'strategy': 'survival_momentum'
    }
    
    portfolio_state = {
        'equity': 100000.0,
        'drawdown': 0.08
    }
    
    # Validate
    approved, reason = await survival_adapter.validate_survival_signal(
        signal=signal,
        portfolio_state=portfolio_state
    )
    
    # Display results
    print(f"\n📊 SurvivalCore Signal: {signal['symbol']} {signal['direction']}")
    print(f"   Strategy: {signal['strategy']}")
    print(f"   Confidence: {signal['confidence']:.2%}")
    print(f"   Current Drawdown: {portfolio_state['drawdown']:.2%}")
    
    print(f"\n🎯 AlphaAlgo Core Validation:")
    print(f"   Approved: {'✅ YES' if approved else '❌ NO'}")
    print(f"   Reason: {reason}")


# ============================================================================
# DEMO 4: Signal Generator Wrapping
# ============================================================================

class MockSignalGenerator:
    """Mock signal generator for demo"""
    
    def __init__(self, name: str):
        self.name = name
    
    def generate(self, symbol: str, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate mock signal"""
        return {
            'symbol': symbol,
            'direction': 'long',
            'quantity': 1.0,
            'price': market_data['close'].iloc[-1],
            'stop_loss': market_data['close'].iloc[-1] * 0.98,
            'take_profit': market_data['close'].iloc[-1] * 1.04,
            'confidence': 0.72
        }


async def demo_signal_generator_wrapping():
    """Demonstrate signal generator wrapping"""
    print("\n" + "="*80)
    print("DEMO 4: Signal Generator Wrapping")
    print("="*80)
    
    from trading_bot.core.alphaalgo_core_integration import create_core_integration
    
    # Create mock market data
    market_data = pd.DataFrame({
        'close': [50000, 50100, 50200, 50150, 50300],
        'volume': [100, 110, 105, 115, 120]
    })
    
    # Mock portfolio
    class MockPortfolio:
        equity = 100000.0
        drawdown = 0.03
    
    portfolio = MockPortfolio()
    
    # Original generator
    base_generator = MockSignalGenerator("trend_follower")
    
    # Wrap with AlphaAlgo Core
    from trading_bot.core.alphaalgo_core_integration import IntegratedTradeRequest
    
    core = create_core_integration()
    
    # Generate base signal
    base_signal = base_generator.generate('BTCUSDT', market_data)
    
    print(f"\n📊 Base Signal Generated:")
    print(f"   Symbol: {base_signal['symbol']}")
    print(f"   Direction: {base_signal['direction']}")
    print(f"   Price: ${base_signal['price']:,.2f}")
    print(f"   Confidence: {base_signal['confidence']:.2%}")
    
    # Validate through AlphaAlgo Core
    request = IntegratedTradeRequest(
        request_id=f"{base_signal['symbol']}_{datetime.utcnow().timestamp()}",
        symbol=base_signal['symbol'],
        direction=base_signal['direction'],
        quantity=base_signal['quantity'],
        entry_price=base_signal['price'],
        stop_loss=base_signal['stop_loss'],
        take_profit=base_signal['take_profit'],
        signal_strength=base_signal['confidence'],
        signal_source='signal_generator',
        strategy_id=base_generator.name,
        current_equity=portfolio.equity,
        current_drawdown=portfolio.drawdown
    )
    
    decision = await core.evaluate_trade_request(request)
    
    print(f"\n🎯 AlphaAlgo Core Validation:")
    print(f"   Approved: {'✅ YES' if decision.approved else '❌ NO'}")
    
    if decision.approved:
        print(f"   Approved Quantity: {decision.approved_quantity:.4f}")
        print(f"   Original Quantity: {base_signal['quantity']:.4f}")
        print(f"   Adjustment: {(decision.approved_quantity / base_signal['quantity'] - 1) * 100:+.1f}%")
    else:
        print(f"   Rejection Reason: {decision.rejection_reason}")


# ============================================================================
# DEMO 5: Multi-Layer Defense
# ============================================================================

async def demo_multi_layer_defense():
    """Demonstrate multi-layer defense pattern"""
    print("\n" + "="*80)
    print("DEMO 5: Multi-Layer Defense")
    print("="*80)
    
    create_core_integration,
    IntegratedTradeRequest
    )
    
    # Initialize
    core = create_core_integration()
    
    # Mock signal
    signal = {
        'id': 'multi_001',
        'symbol': 'EURUSD',
        'direction': 'long',
        'quantity': 1.0,
        'price': 1.0850,
        'stop_loss': 1.0800,
        'confidence': 0.68
    }
    
    print(f"\n📊 Signal: {signal['symbol']} {signal['direction']}")
    print(f"   Confidence: {signal['confidence']:.2%}")
    
    # Layer 1: Basic validation
    print(f"\n🛡️  Layer 1: Basic Validation")
    if signal['confidence'] < 0.5:
        print("   ❌ REJECTED: Confidence too low")
        return
    print("   ✅ PASSED")
    
    # Layer 2: Mock MSOS check
    print(f"\n🛡️  Layer 2: MSOS Check")
    msos_can_trade = True  # Mock
    if not msos_can_trade:
        print("   ❌ REJECTED: MSOS blocked")
        return
    print("   ✅ PASSED")
    
    # Layer 3: AlphaAlgo Core (Adversarial)
    print(f"\n🛡️  Layer 3: AlphaAlgo Core (Adversarial)")
    request = IntegratedTradeRequest(
        request_id=signal['id'],
        symbol=signal['symbol'],
        direction=signal['direction'],
        quantity=signal['quantity'],
        entry_price=signal['price'],
        stop_loss=signal['stop_loss'],
        signal_strength=signal['confidence'],
        current_equity=100000.0,
        current_drawdown=0.04
    )
    
    decision = await core.evaluate_trade_request(request)
    
    if not decision.approved:
        print(f"   ❌ REJECTED: {decision.rejection_reason}")
        return
    print(f"   ✅ PASSED (approved qty: {decision.approved_quantity:.4f})")
    
    # Layer 4: Mock Risk Manager
    print(f"\n🛡️  Layer 4: Risk Manager")
    risk_approved = True  # Mock
    if not risk_approved:
        print("   ❌ REJECTED: Risk limits exceeded")
        return
    print("   ✅ PASSED")
    
    # All layers passed
    print(f"\n✅ ALL LAYERS PASSED - TRADE APPROVED")
    print(f"   Final Quantity: {decision.approved_quantity:.4f}")


# ============================================================================
# DEMO 6: Market Hostility Detection
# ============================================================================

async def demo_market_hostility():
    """Demonstrate market hostility detection"""
    print("\n" + "="*80)
    print("DEMO 6: Market Hostility Detection")
    print("="*80)
    
        create_core_integration,
        IntegratedTradeRequest
    )
    
    core = create_core_integration()
    
    # Test different market conditions
    scenarios = [
        {
            'name': 'Normal Market',
            'context': {
                'recent_performance': [0.01, 0.02, -0.005, 0.015, 0.01],
                'regime_stability': 0.8,
                'liquidity_stress': 0.2,
                'cross_strategy_dispersion': 0.3
            }
        },
        {
            'name': 'Hostile Market',
            'context': {
                'recent_performance': [-0.02, -0.03, -0.01, -0.025, -0.015],
                'regime_stability': 0.3,
                'liquidity_stress': 0.8,
                'cross_strategy_dispersion': 0.9
            }
        },
        {
            'name': 'Low Edge Density',
            'context': {
                'recent_performance': [-0.005, 0.003, -0.002, 0.001, -0.004],
                'regime_stability': 0.6,
                'liquidity_stress': 0.3,
                'cross_strategy_dispersion': 0.5
            }
        }
    ]
    
    request = IntegratedTradeRequest(
        request_id="hostility_test",
        symbol="BTCUSDT",
        direction="long",
        quantity=1.0,
        entry_price=50000.0,
        stop_loss=49000.0,
        signal_strength=0.75,
        current_equity=100000.0,
        current_drawdown=0.03
    )
    
    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"   Regime Stability: {scenario['context']['regime_stability']:.2%}")
        print(f"   Liquidity Stress: {scenario['context']['liquidity_stress']:.2%}")
        print(f"   Strategy Dispersion: {scenario['context']['cross_strategy_dispersion']:.2%}")
        
        decision = await core.evaluate_trade_request(request, scenario['context'])
        
        print(f"\n   Decision: {decision.outcome.value}")
        print(f"   Market Hostility: {decision.market_hostility}")
        
        if decision.approved:
            print(f"   ✅ Trade Approved")
        else:
            print(f"   ❌ Trade Rejected: {decision.rejection_reason}")


# ============================================================================
# DEMO 7: Statistics and Monitoring
# ============================================================================

async def demo_statistics_monitoring():
    """Demonstrate statistics and monitoring"""
    print("\n" + "="*80)
    print("DEMO 7: Statistics and Monitoring")
    print("="*80)
    
        create_core_integration,
        IntegratedTradeRequest
    )
    
    core = create_core_integration()
    
    # Generate multiple trade requests
    print(f"\n📊 Evaluating 10 trade requests...")
    
    for i in range(10):
        request = IntegratedTradeRequest(
            request_id=f"stats_test_{i}",
            symbol="BTCUSDT",
            direction="long" if i % 2 == 0 else "short",
            quantity=1.0,
            entry_price=50000.0 + (i * 100),
            stop_loss=49000.0 + (i * 100),
            signal_strength=0.5 + (i * 0.05),  # Varying confidence
            current_equity=100000.0,
            current_drawdown=0.02 + (i * 0.01)  # Increasing drawdown
        )
        
        decision = await core.evaluate_trade_request(request)
        status = "✅" if decision.approved else "❌"
        print(f"   {status} Request {i+1}: conf={request.signal_strength:.2%}, dd={request.current_drawdown:.2%}")
    
    # Get statistics
    stats = core.get_statistics()
    
    print(f"\n📈 AlphaAlgo Core Statistics:")
    print(f"\n   Core Engine:")
    print(f"      Total Evaluations: {stats['core_engine']['total_evaluations']}")
    print(f"      Approved: {stats['core_engine']['approved']}")
    print(f"      Rejected: {stats['core_engine']['rejected']}")
    print(f"      Market Hostile: {stats['core_engine']['market_hostile']}")
    print(f"      Approval Rate: {stats['core_engine']['approval_rate']:.2%}")
    
    print(f"\n   Top Rejection Reasons:")
    for reason, count in list(stats['core_engine']['top_rejection_reasons'].items())[:3]:
        print(f"      {count}x: {reason}")
    
    print(f"\n   Integration:")
    print(f"      MSOS Enabled: {stats['integration']['msos_enabled']}")
    print(f"      SurvivalCore Enabled: {stats['integration']['survival_core_enabled']}")
    print(f"      Confidence Threshold: {stats['integration']['confidence_threshold']:.2%}")
    print(f"      Strict Mode: {stats['integration']['strict_mode']}")


# ============================================================================
# DEMO 8: Confidence Vector Analysis
# ============================================================================

async def demo_confidence_vector():
    """Demonstrate confidence vector analysis"""
    print("\n" + "="*80)
    print("DEMO 8: Confidence Vector Analysis")
    print("="*80)
    
        create_core_integration,
        IntegratedTradeRequest
    )
    
    core = create_core_integration()
    
    # High quality signal
    print(f"\n📊 High Quality Signal:")
    request_high = IntegratedTradeRequest(
        request_id="conf_high",
        symbol="BTCUSDT",
        direction="long",
        quantity=1.0,
        entry_price=50000.0,
        stop_loss=49500.0,
        signal_strength=0.85,
        regime="trending",
        volatility=0.15,
        liquidity_score=0.9,
        current_equity=100000.0,
        current_drawdown=0.02,
        correlation_exposure=0.2
    )
    
    decision_high = await core.evaluate_trade_request(request_high)
    
    print(f"   Signal Strength: {request_high.signal_strength:.2%}")
    print(f"   Decision: {'✅ APPROVED' if decision_high.approved else '❌ REJECTED'}")
    
    if decision_high.confidence_breakdown:
        print(f"\n   Confidence Vector:")
        for component, value in decision_high.confidence_breakdown.items():
            bar = "█" * int(value * 20)
            print(f"      {component:20s}: {bar} {value:.2%}")
        print(f"\n      {'MINIMUM (dominates)':20s}: {'█' * int(decision_high.min_confidence * 20)} {decision_high.min_confidence:.2%}")
    
    # Low quality signal
    print(f"\n📊 Low Quality Signal:")
    request_low = IntegratedTradeRequest(
        request_id="conf_low",
        symbol="BTCUSDT",
        direction="long",
        quantity=1.0,
        entry_price=50000.0,
        stop_loss=49500.0,
        signal_strength=0.55,
        regime="uncertain",
        volatility=0.35,
        liquidity_score=0.4,
        current_equity=100000.0,
        current_drawdown=0.12,
        correlation_exposure=0.7
    )
    
    decision_low = await core.evaluate_trade_request(request_low)
    
    print(f"   Signal Strength: {request_low.signal_strength:.2%}")
    print(f"   Decision: {'✅ APPROVED' if decision_low.approved else '❌ REJECTED'}")
    
    if decision_low.confidence_breakdown:
        print(f"\n   Confidence Vector:")
        for component, value in decision_low.confidence_breakdown.items():
            bar = "█" * int(value * 20)
            print(f"      {component:20s}: {bar} {value:.2%}")
        print(f"\n      {'MINIMUM (dominates)':20s}: {'█' * int(decision_low.min_confidence * 20)} {decision_low.min_confidence:.2%}")
    
    if not decision_low.approved:
        print(f"\n   ❌ Rejection Reason: {decision_low.rejection_reason}")


# ============================================================================
# Main Demo Runner
# ============================================================================

async def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("AlphaAlgo Core - Complete Integration Demo")
    print("="*80)
    print("\nDemonstrating hostile capital-preserving decision engine")
    print("with 7-stage adversarial evaluation pipeline\n")
    
    try:
        # Run all demos
        await demo_basic_usage()
        await demo_msos_integration()
        await demo_survival_core_integration()
        await demo_signal_generator_wrapping()
        await demo_multi_layer_defense()
        await demo_market_hostility()
        await demo_statistics_monitoring()
        await demo_confidence_vector()
        
        print("\n" + "="*80)
        print("✅ All Demos Completed Successfully")
        print("="*80)
        
        print("\n📚 Next Steps:")
        print("   1. Review ALPHAALGO_CORE_INTEGRATION_GUIDE.md")
        print("   2. Review ALPHAALGO_CORE_CODEBASE_AUDIT.md")
        print("   3. Integrate with your main trading loop")
        print("   4. Monitor approval rates and rejection reasons")
        print("   5. Tune confidence threshold based on results")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
