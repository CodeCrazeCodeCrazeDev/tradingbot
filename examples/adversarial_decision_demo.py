"""
Adversarial Decision Framework Demo

Demonstrates the complete 9-step adversarial decision-making process.
"""

import asyncio
from datetime import datetime, timedelta
import random
from typing import Dict, Any

from trading_bot.adversarial_decision import (
    AdversarialDecisionEngine,
    quick_start,
    DecisionOutcome,
)


def generate_market_data(regime: str = 'TRENDING') -> Dict[str, Any]:
    """Generate sample market data"""
    return {
        'regime': regime,
        'regime_stability': random.uniform(0.5, 0.9),
        'regime_duration': random.randint(10, 100),
        'volatility': random.uniform(0.01, 0.03),
        'historical_volatility': 0.02,
        'volatility_percentile': random.uniform(30, 70),
        'volatility_regime': 'NORMAL',
        'vol_of_vol': random.uniform(0.1, 0.3),
        'bid_ask_spread': 0.0001,
        'volume': random.uniform(80000, 120000),
        'avg_volume': 100000,
        'market_depth': random.uniform(5000, 15000),
        'latency': random.uniform(10, 30),
        'order_book_depth': random.uniform(5000, 15000),
        'execution_quality': random.uniform(0.7, 0.9),
        'venue_status': 'ONLINE',
        'market_hours': True,
        'irreversibility_score': random.uniform(0.3, 0.6),
        'trend_strength': random.uniform(0.5, 0.8),
    }


def generate_signal_data(quality: str = 'good') -> Dict[str, Any]:
    """Generate sample signal data"""
    if quality == 'good':
        return {
            'edge_density': random.uniform(0.4, 0.7),
            'active_strategies': random.randint(3, 5),
            'profitable_regimes': ['TRENDING', 'RANGING'],
            'expectancy': random.uniform(0.01, 0.03),
            'win_rate': random.uniform(0.55, 0.65),
            'avg_win': random.uniform(0.015, 0.025),
            'avg_loss': random.uniform(0.008, 0.012),
            'sample_size': random.randint(100, 500),
            'profit_factor': random.uniform(1.5, 2.5),
            'sharpe_ratio': random.uniform(1.0, 2.0),
            'in_sample_sharpe': 1.8,
            'out_sample_sharpe': 1.5,
            'signal_age_seconds': random.randint(1, 30),
            'model_last_updated': datetime.utcnow() - timedelta(days=random.randint(10, 60)),
        }
    else:  # poor quality
        return {
            'edge_density': random.uniform(0.1, 0.25),
            'active_strategies': 1,
            'profitable_regimes': ['RANGING'],
            'expectancy': random.uniform(-0.01, 0.005),
            'win_rate': random.uniform(0.4, 0.5),
            'avg_win': 0.01,
            'avg_loss': 0.015,
            'sample_size': 25,
            'profit_factor': 0.8,
            'sharpe_ratio': 0.3,
            'in_sample_sharpe': 2.0,
            'out_sample_sharpe': 0.5,
            'signal_age_seconds': 120,
            'model_last_updated': datetime.utcnow() - timedelta(days=150),
        }


def generate_portfolio_state(drawdown: float = 0.0) -> Dict[str, Any]:
    """Generate sample portfolio state"""
    return {
        'account_value': 100000.0,
        'positions': {
            'GBPUSD': {'value': 5000, 'pnl': 200},
        },
        'correlations': {
            'EURUSD_GBPUSD': 0.75,
            'max': 0.75,
        },
        'concentration': 0.05,
        'current_drawdown': drawdown,
        'expected_drawdown': random.uniform(0.01, 0.03),
        'var_95': random.uniform(0.02, 0.04),
        'cvar_95': random.uniform(0.03, 0.05),
        'max_drawdown': random.uniform(0.05, 0.10),
        'leverage': 1.5,
        'margin_usage': 0.3,
    }


def generate_historical_data(losses: int = 0) -> Dict[str, Any]:
    """Generate sample historical data"""
    recent_losses = []
    for i in range(losses):
        recent_losses.append({
            'timestamp': datetime.utcnow() - timedelta(hours=i*2),
            'pnl': random.uniform(-500, -100),
        })
    
    return {
        'recent_losses': recent_losses,
        'recent_sharpe': random.uniform(0.5, 1.5) if losses == 0 else random.uniform(-0.5, 0.3),
        'regime_performance': {
            'TRENDING': random.uniform(0.01, 0.03),
            'RANGING': random.uniform(0.005, 0.015),
        },
        'regime_losses': {
            'TRENDING': [],
            'RANGING': [random.uniform(-0.01, -0.005) for _ in range(2)],
        },
        'regime_first_seen': {
            'TRENDING': datetime.utcnow() - timedelta(days=60),
            'RANGING': datetime.utcnow() - timedelta(days=90),
        },
        'similar_conditions': [
            {'outcome': random.uniform(-0.01, 0.02)} for _ in range(20)
        ],
    }


async def demo_good_trade():
    """Demo: High-quality trade that should be approved"""
    print("\n" + "="*80)
    print("DEMO 1: HIGH-QUALITY TRADE (Should be APPROVED)")
    print("="*80)
    
    engine = quick_start()
    
    decision = engine.evaluate_trade(
        symbol='EURUSD',
        direction='buy',
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        market_data=generate_market_data('TRENDING'),
        signal_data=generate_signal_data('good'),
        portfolio_state=generate_portfolio_state(0.0),
        historical_data=generate_historical_data(0)
    )
    
    print(f"\n✓ Decision: {decision.outcome.value.upper()}")
    print(f"✓ Approved: {decision.approved}")
    if decision.approved:
        print(f"✓ Position Size: {decision.position_size:.4f}")
        print(f"✓ Min Confidence: {decision.confidence_vector.get_minimum():.2f}")
        print(f"✓ Weakest Dimension: {decision.confidence_vector.get_weakest_dimension()}")
        if decision.sizing_factors:
            print(f"✓ Risk Per Trade: {decision.sizing_factors.final_risk_per_trade:.2%}")
            print(f"✓ Confidence Multiplier: {decision.sizing_factors.confidence_multiplier:.2f}")
    else:
        print(f"✗ Rejection Category: {decision.rejection_category.value if decision.rejection_category else 'N/A'}")
        print(f"✗ Reasons: {'; '.join(decision.rejection_reasons[:3])}")
    
    print(f"\n⏱ Processing Time: {decision.processing_time_ms:.2f}ms")
    print(f"📊 Summary: {decision.get_summary()}")


async def demo_poor_trade():
    """Demo: Poor-quality trade that should be rejected"""
    print("\n" + "="*80)
    print("DEMO 2: POOR-QUALITY TRADE (Should be REJECTED)")
    print("="*80)
    
    engine = quick_start()
    
    decision = engine.evaluate_trade(
        symbol='EURUSD',
        direction='buy',
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        market_data=generate_market_data('TRANSITIONING'),
        signal_data=generate_signal_data('poor'),
        portfolio_state=generate_portfolio_state(0.0),
        historical_data=generate_historical_data(0)
    )
    
    print(f"\n✗ Decision: {decision.outcome.value.upper()}")
    print(f"✗ Approved: {decision.approved}")
    print(f"✗ Rejection Category: {decision.rejection_category.value if decision.rejection_category else 'N/A'}")
    print(f"✗ Rejection Reasons:")
    for i, reason in enumerate(decision.rejection_reasons[:5], 1):
        print(f"   {i}. {reason}")
    
    print(f"\n⏱ Processing Time: {decision.processing_time_ms:.2f}ms")
    print(f"📊 Summary: {decision.get_summary()}")


async def demo_drawdown_trade():
    """Demo: Trade during drawdown (should reduce size)"""
    print("\n" + "="*80)
    print("DEMO 3: TRADE DURING DRAWDOWN (Should REDUCE SIZE)")
    print("="*80)
    
    engine = quick_start()
    
    decision = engine.evaluate_trade(
        symbol='EURUSD',
        direction='buy',
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        market_data=generate_market_data('TRENDING'),
        signal_data=generate_signal_data('good'),
        portfolio_state=generate_portfolio_state(0.12),  # 12% drawdown
        historical_data=generate_historical_data(3)  # 3 recent losses
    )
    
    print(f"\n⚠ Decision: {decision.outcome.value.upper()}")
    print(f"⚠ Approved: {decision.approved}")
    if decision.approved and decision.sizing_factors:
        print(f"⚠ Position Size: {decision.position_size:.4f}")
        print(f"⚠ Loss Fatigue Adjustment: {decision.sizing_factors.loss_fatigue_adjustment:.2f}")
        print(f"⚠ Final Risk: {decision.sizing_factors.final_risk_per_trade:.2%}")
        print(f"⚠ Recent Losses: 3")
        print(f"⚠ Current Drawdown: 12%")
    
    print(f"\n⏱ Processing Time: {decision.processing_time_ms:.2f}ms")
    print(f"📊 Summary: {decision.get_summary()}")


async def demo_statistics():
    """Demo: Run multiple trades and show statistics"""
    print("\n" + "="*80)
    print("DEMO 4: BATCH EVALUATION & STATISTICS")
    print("="*80)
    
    engine = quick_start()
    
    # Run 20 trades with varying quality
    print("\nEvaluating 20 trades...")
    for i in range(20):
        quality = 'good' if random.random() > 0.4 else 'poor'
        regime = random.choice(['TRENDING', 'RANGING', 'TRANSITIONING'])
        drawdown = random.uniform(0.0, 0.15)
        
        decision = engine.evaluate_trade(
            symbol='EURUSD',
            direction='buy',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            market_data=generate_market_data(regime),
            signal_data=generate_signal_data(quality),
            portfolio_state=generate_portfolio_state(drawdown),
            historical_data=generate_historical_data(random.randint(0, 3))
        )
        
        status = "✓" if decision.approved else "✗"
        print(f"  {status} Trade {i+1}: {decision.outcome.value} ({quality}, {regime})")
    
    # Show statistics
    stats = engine.get_statistics()
    print(f"\n📊 STATISTICS:")
    print(f"   Total Evaluations: {stats['total_evaluations']}")
    print(f"   Total Approved: {stats['total_approved']}")
    print(f"   Total Rejected: {stats['total_rejected']}")
    print(f"   Approval Rate: {stats['approval_rate']:.1%}")
    print(f"\n   Rejection Breakdown:")
    for reason, count in stats['rejection_stats'].items():
        if count > 0:
            print(f"      {reason}: {count}")


async def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("ADVERSARIAL DECISION FRAMEWORK - COMPREHENSIVE DEMO")
    print("="*80)
    print("\nThis demo showcases the 9-step adversarial decision-making process:")
    print("  1. Hard Reality Pre-Check")
    print("  2. Claim Decomposition")
    print("  3. Orthogonal Verification")
    print("  4. Adversarial Kill Phase")
    print("  5. Confidence Vector Calculation")
    print("  6. Failure Mode Matching")
    print("  7. Decision Gate")
    print("  8. Position Sizing")
    print("  9. Post-Decision Rules")
    
    await demo_good_trade()
    await demo_poor_trade()
    await demo_drawdown_trade()
    await demo_statistics()
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nKey Principles:")
    print("  ✓ Reject by default, approve only when ALL conditions pass")
    print("  ✓ Minimum confidence dominates (averages are irrelevant)")
    print("  ✓ Never size aggressively after drawdowns")
    print("  ✓ Doing nothing is preferred over forced action")
    print("  ✓ Learn from failures, update failure database")
    print("\n")


if __name__ == '__main__':
    asyncio.run(main())
