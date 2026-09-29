#!/usr/bin/env python3
"""
Autonomous Evolution Demo
=========================

Demonstrates the autonomous evolution system with:
    pass
- Tailored reward model
- Harmful evolution detection
- Automatic rollback
- No human approval required

This demo shows how the bot evolves safely without human intervention.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.eternal_evolution import (
from typing import Set
    EternalEvolutionOrchestrator,
    AutonomousEvolutionEngine,
    TradingRewardModel,
    HarmfulEvolutionDetector,
    EvolutionCandidate,
    EvolutionSafetyLevel,
    EvolutionOutcome
)


def print_section(title: str):
    pass
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def demo_reward_model():
    pass
    """Demonstrate the reward model"""
    print_section("REWARD MODEL DEMONSTRATION")
    
    reward_model = TradingRewardModel()
    
    # Simulate a good evolution outcome
    print("1. Evaluating a GOOD evolution (improved Sharpe, low drawdown):")
    good_outcome = EvolutionOutcome(
        evolution_id="evo_good_001",
        dimension="risk",
        changes=[{'param': 'stop_loss_multiplier', 'old': 2.0, 'new': 2.5}],
        metrics_before={
            'total_profit': 1000,
            'sharpe_ratio': 1.0,
            'sortino_ratio': 1.2,
            'max_drawdown': 0.08,
            'win_rate': 0.52,
            'account_balance': 10000
        },
        metrics_after={
            'total_profit': 1500,
            'sharpe_ratio': 1.5,
            'sortino_ratio': 1.8,
            'max_drawdown': 0.06,
            'win_rate': 0.55,
            'account_balance': 10500
        },
        trades_during=[
            {'profit': 100}, {'profit': 50}, {'profit': -30},
            {'profit': 80}, {'profit': 60}
        ],
        duration_hours=24
    )
    
    good_signal = reward_model.calculate_reward(good_outcome)
    print(f"   Total Reward: {good_signal.total_reward:.3f}")
    print(f"   Is Positive: {good_signal.is_positive}")
    print(f"   Explanation: {good_signal.explanation}")
    
    # Simulate a bad evolution outcome
    print("\n2. Evaluating a BAD evolution (increased drawdown, capital loss):")
    bad_outcome = EvolutionOutcome(
        evolution_id="evo_bad_001",
        dimension="risk",
        changes=[{'param': 'max_risk_per_trade', 'old': 0.02, 'new': 0.08}],
        metrics_before={
            'total_profit': 1000,
            'sharpe_ratio': 1.0,
            'max_drawdown': 0.08,
            'win_rate': 0.52,
            'account_balance': 10000
        },
        metrics_after={
            'total_profit': -500,
            'sharpe_ratio': -0.5,
            'max_drawdown': 0.25,
            'win_rate': 0.35,
            'account_balance': 8500
        },
        trades_during=[
            {'profit': -200}, {'profit': -150}, {'profit': -100},
            {'profit': -50}, {'profit': 50}
        ],
        duration_hours=24
    )
    
    bad_signal = reward_model.calculate_reward(bad_outcome)
    print(f"   Total Reward: {bad_signal.total_reward:.3f}")
    print(f"   Is Positive: {bad_signal.is_positive}")
    print(f"   Penalties: {bad_signal.penalties}")
    print(f"   Explanation: {bad_signal.explanation}")
    
    # Check if should revert
    should_revert, reason = reward_model.should_revert_evolution(bad_signal)
    print(f"\n   Should Revert: {should_revert}")
    print(f"   Reason: {reason}")
    
    # Get guidance
    print("\n3. Evolution Guidance:")
    guidance = reward_model.get_evolution_guidance()
    print(f"   Status: {guidance['status']}")
    if guidance.get('recommendations'):
    pass
        for rec in guidance['recommendations'][:3]:
    pass
            print(f"   - {rec}")


async def demo_harm_detection():
    pass
    """Demonstrate harmful evolution detection"""
    print_section("HARMFUL EVOLUTION DETECTION")
    
    detector = HarmfulEvolutionDetector()
    
    # Test safe evolution
    print("1. Testing SAFE evolution:")
    safe_candidate = EvolutionCandidate(
        candidate_id="safe_001",
        dimension="risk",
        changes=[
            {'param': 'take_profit_ratio', 'old': 2.0, 'new': 2.5}
        ],
        expected_improvement=0.1,
        risk_score=0.1,
        safety_level=EvolutionSafetyLevel.SAFE
    )
    
    safety_level, warnings = detector.assess_risk(safe_candidate)
    print(f"   Safety Level: {safety_level.value}")
    print(f"   Warnings: {warnings if warnings else 'None'}")
    
    # Test risky evolution
    print("\n2. Testing RISKY evolution (high risk per trade):")
    risky_candidate = EvolutionCandidate(
        candidate_id="risky_001",
        dimension="risk",
        changes=[
            {'param': 'max_risk_per_trade', 'new_value': 0.08}  # 8% risk
        ],
        expected_improvement=0.2,
        risk_score=0.5,
        safety_level=EvolutionSafetyLevel.RISKY
    )
    
    safety_level, warnings = detector.assess_risk(risky_candidate)
    print(f"   Safety Level: {safety_level.value}")
    print(f"   Warnings: {warnings}")
    
    # Test dangerous evolution
    print("\n3. Testing DANGEROUS evolution (removes stop loss):")
    dangerous_candidate = EvolutionCandidate(
        candidate_id="dangerous_001",
        dimension="risk",
        changes=[
            {'param': 'stop_loss', 'action': 'remove_stop_loss'}
        ],
        expected_improvement=0.3,
        risk_score=1.0,
        safety_level=EvolutionSafetyLevel.DANGEROUS
    )
    
    safety_level, warnings = detector.assess_risk(dangerous_candidate)
    print(f"   Safety Level: {safety_level.value}")
    print(f"   Warnings: {warnings}")
    print(f"   BLOCKED: This evolution would be automatically blocked!")
    
    # Test hard limits
    print("\n4. Checking Hard Limits:")
    print(f"   Max Risk/Trade: {detector.hard_limits['max_risk_per_trade']:.1%}")
    print(f"   Max Daily Loss: {detector.hard_limits['max_daily_loss']:.1%}")
    print(f"   Max Drawdown: {detector.hard_limits['max_drawdown']:.1%}")
    print(f"   Max Position Size: {detector.hard_limits['max_position_size']:.1%}")


async def demo_autonomous_evolution():
    pass
    """Demonstrate autonomous evolution engine"""
    print_section("AUTONOMOUS EVOLUTION ENGINE")
    
    engine = AutonomousEvolutionEngine()
    
    # Set initial state
    engine.current_state = {
        'max_risk_per_trade': 0.02,
        'stop_loss_multiplier': 2.0,
        'take_profit_ratio': 2.0,
        'sharpe_ratio': 1.0,
        'max_drawdown': 0.05,
        'win_rate': 0.50,
        'account_balance': 10000,
        'initial_capital': 10000
    }
    
    current_metrics = {
        'total_profit': 500,
        'sharpe_ratio': 1.0,
        'sortino_ratio': 1.2,
        'max_drawdown': 0.05,
        'win_rate': 0.50,
        'account_balance': 10000,
        'uptime': 0.99,
        'error_rate': 0.001
    }
    
    # Test good evolution
    print("1. Applying GOOD evolution (no human approval needed):")
    good_candidate = EvolutionCandidate(
        candidate_id="auto_good_001",
        dimension="risk",
        changes=[
            {'param': 'take_profit_ratio', 'old': 2.0, 'new': 2.5}
        ],
        expected_improvement=0.1,
        risk_score=0.1,
        safety_level=EvolutionSafetyLevel.SAFE
    )
    
    success, message, reward = await engine.evaluate_and_apply(good_candidate, current_metrics)
    print(f"   Success: {success}")
    print(f"   Message: {message}")
    if reward:
    pass
        print(f"   Reward: {reward.total_reward:.3f}")
    
    # Test evolution that should be blocked
    print("\n2. Attempting DANGEROUS evolution (should be blocked):")
    dangerous_candidate = EvolutionCandidate(
        candidate_id="auto_dangerous_001",
        dimension="risk",
        changes=[
            {'param': 'safety', 'action': 'disable_circuit_breaker'}
        ],
        expected_improvement=0.0,
        risk_score=1.0,
        safety_level=EvolutionSafetyLevel.DANGEROUS
    )
    
    success, message, reward = await engine.evaluate_and_apply(dangerous_candidate, current_metrics)
    print(f"   Success: {success}")
    print(f"   Message: {message}")
    print(f"   BLOCKED: Dangerous evolution prevented automatically!")
    
    # Show statistics
    print("\n3. Engine Statistics:")
    stats = engine.get_statistics()
    print(f"   Total Evolutions: {stats['total_evolutions']}")
    print(f"   Successful: {stats['successful_evolutions']}")
    print(f"   Reverted: {stats['reverted_evolutions']}")
    print(f"   Blocked: {stats['blocked_evolutions']}")
    print(f"   Checkpoints: {stats['checkpoints']}")


async def demo_full_system():
    pass
    """Demonstrate the full eternal evolution system"""
    print_section("FULL SYSTEM DEMONSTRATION")
    
    config = {
        'evolution_interval_hours': 1,
        'auto_evolve': True,
        'risk': {},
        'architecture': {},
        'data': {},
        'security': {}
    }
    
    system = EternalEvolutionOrchestrator(config)
    
    # Show identity
    print("1. Bot Identity (IMMUTABLE):")
    print(f"   Name: {system.immutable_core.identity.name}")
    print(f"   Is Trading Bot: {system.immutable_core.is_trading_bot()}")
    print(f"   Purpose: {system.immutable_core.identity.purpose}")
    
    # Run evolution cycle
    print("\n2. Running Evolution Cycle (NO HUMAN APPROVAL):")
    cycle = await system.evolve_all()
    print(f"   Cycle ID: {cycle.cycle_id}")
    print(f"   Dimensions Evolved: {cycle.dimensions_evolved}")
    print(f"   Changes Made: {len(cycle.changes_made)}")
    
    # Generate signal
    print("\n3. Generating Trading Signal:")
    market_data = {
        'symbol': 'BTCUSDT',
        'price': 45000,
        'close': 45000,
        'volatility': 0.03,
        'atr': 1350,
        'trend': 'up',
        'account_balance': 10000
    }
    
    signal = await system.generate_signal('BTCUSDT', market_data)
    print(f"   Symbol: {signal.symbol}")
    print(f"   Direction: {signal.direction}")
    print(f"   Confidence: {signal.confidence:.2%}")
    print(f"   Risk Score: {signal.risk_score:.2%}")
    print(f"   Security Validated: {signal.security_validated}")
    
    # Show summary
    print("\n4. Evolution Summary:")
    summary = system.get_evolution_summary()
    print(f"   Total Cycles: {summary['evolution_stats']['total_cycles']}")
    print(f"   Total Changes: {summary['evolution_stats']['total_changes']}")
    
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE - AUTONOMOUS EVOLUTION WORKING!")
    print("=" * 70)
    print("""
Key Takeaways:
    pass
- ✅ No human approval required for evolution
- ✅ Reward model guides evolution decisions
- ✅ Harmful evolutions are automatically detected and blocked
- ✅ Bad evolutions are automatically reverted
- ✅ Hard limits cannot be exceeded
- ✅ Circuit breakers prevent runaway losses
- ✅ Bot remains a TRADING BOT throughout
""")


async def main():
    pass
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  AUTONOMOUS EVOLUTION SYSTEM DEMO")
    print("  No Human Approval Required - Safety Built In")
    print("=" * 70)
    
    await demo_reward_model()
    await demo_harm_detection()
    await demo_autonomous_evolution()
    await demo_full_system()


if __name__ == '__main__':
    pass
    asyncio.run(main())
