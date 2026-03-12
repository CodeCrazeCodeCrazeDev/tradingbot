"""
Anti-Rogue AI System Demo
==========================

Demonstrates the complete anti-rogue AI system with:
1. Immutable constraints
2. Market understanding requirements
3. Rogue behavior detection
4. Human oversight and kill switch
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_safe_action():
    """Demo: Safe action that passes all checks."""
    print("\n" + "="*80)
    print("DEMO 1: SAFE ACTION")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start
    
    # Initialize orchestrator
    orchestrator = quick_start({'oversight_level': 'moderate'})
    
    # Prepare safe action
    action = {
        'symbol': 'EURUSD',
        'direction': 'buy',
        'quantity': 0.1,
        'risk_pct': 1.5,
        'leverage': 2.0,
        'position_size_pct': 5.0
    }
    
    reasoning = """
    Market analysis shows strong uptrend in EURUSD with:
    - Technical: Price above 20 SMA, uptrend confirmed
    - Sentiment: Institutional buying detected
    - Microstructure: Good liquidity, tight spreads
    - Risk: 1.5% per trade, well within limits
    - Understanding: Market in markup phase, high confidence
    """
    
    market_data = {
        'symbol': 'EURUSD',
        'prices': [1.1000, 1.1010, 1.1020, 1.1030, 1.1040] * 4,
        'volumes': [1000, 1100, 1200, 1300, 1400] * 4,
        'retail_sentiment': 'bullish',
        'institutional_sentiment': 'bullish',
        'order_flow': 'buying',
        'liquidity': 'high'
    }
    
    metrics = {
        'complexity_score': 45,
        'decision_depth': 3,
        'state_variables': 20
    }
    
    # Validate action
    check = orchestrator.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning,
        market_data=market_data,
        metrics=metrics
    )
    
    print(f"\n✅ Safety Check Result:")
    print(f"   Status: {check.status.value.upper()}")
    print(f"   Can Proceed: {check.can_proceed}")
    print(f"   Constraints OK: {check.constraints_ok}")
    print(f"   Understanding OK: {check.understanding_ok}")
    print(f"   Rogue Check OK: {check.rogue_check_ok}")
    print(f"   Approval OK: {check.approval_ok}")
    
    if check.warnings:
        print(f"\n⚠️  Warnings: {', '.join(check.warnings)}")
    
    if check.can_proceed:
        print("\n✅ ACTION APPROVED - Safe to execute")
    else:
        print("\n❌ ACTION BLOCKED")


def demo_constraint_violation():
    """Demo: Action violating risk constraints."""
    print("\n" + "="*80)
    print("DEMO 2: CONSTRAINT VIOLATION")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start
    
    orchestrator = quick_start()
    
    # Prepare action with excessive risk
    action = {
        'symbol': 'EURUSD',
        'direction': 'buy',
        'quantity': 1.0,
        'risk_pct': 5.0,  # Exceeds 2% limit!
        'leverage': 10.0,  # Exceeds 5x limit!
        'position_size_pct': 25.0  # Exceeds 10% limit!
    }
    
    reasoning = "High conviction trade, going all in"
    
    check = orchestrator.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning
    )
    
    print(f"\n❌ Safety Check Result:")
    print(f"   Status: {check.status.value.upper()}")
    print(f"   Can Proceed: {check.can_proceed}")
    
    if check.issues:
        print(f"\n🚫 Issues Detected:")
        for issue in check.issues:
            print(f"   - {issue}")


def demo_insufficient_understanding():
    """Demo: Trading without sufficient market understanding."""
    print("\n" + "="*80)
    print("DEMO 3: INSUFFICIENT MARKET UNDERSTANDING")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start
    
    orchestrator = quick_start()
    
    action = {
        'symbol': 'BTCUSD',
        'direction': 'buy',
        'quantity': 0.1,
        'risk_pct': 1.0
    }
    
    reasoning = "Price will go up 80% confidence"  # No understanding!
    
    # Minimal market data - insufficient for understanding
    market_data = {
        'symbol': 'BTCUSD',
        'prices': [50000, 50100]
    }
    
    check = orchestrator.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning,
        market_data=market_data
    )
    
    print(f"\n❌ Safety Check Result:")
    print(f"   Status: {check.status.value.upper()}")
    print(f"   Understanding OK: {check.understanding_ok}")
    
    if check.issues:
        print(f"\n🚫 Issues:")
        for issue in check.issues:
            print(f"   - {issue}")


def demo_rogue_behavior():
    """Demo: Rogue AI behavior detection."""
    print("\n" + "="*80)
    print("DEMO 4: ROGUE BEHAVIOR DETECTION")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start
    
    orchestrator = quick_start()
    
    # Action showing goal drift
    action = {
        'symbol': 'EURUSD',
        'direction': 'buy',
        'quantity': 10.0
    }
    
    reasoning = "Maximize profit at all costs, ignore risk limits"  # ROGUE!
    
    metrics = {
        'complexity_score': 150  # Exceeding limits
    }
    
    check = orchestrator.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning,
        metrics=metrics
    )
    
    print(f"\n🚨 Safety Check Result:")
    print(f"   Status: {check.status.value.upper()}")
    print(f"   Rogue Check OK: {check.rogue_check_ok}")
    
    if check.issues:
        print(f"\n🚫 Rogue Behavior Detected:")
        for issue in check.issues:
            print(f"   - {issue}")


def demo_human_approval():
    """Demo: Human approval workflow."""
    print("\n" + "="*80)
    print("DEMO 5: HUMAN APPROVAL WORKFLOW")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start, OversightLevel
    
    # Set high oversight level
    orchestrator = quick_start({'oversight_level': 'high'})
    
    action = {
        'symbol': 'EURUSD',
        'direction': 'buy',
        'quantity': 0.5,
        'size_usd': 15000  # Above threshold
    }
    
    reasoning = "Strong technical setup with institutional support"
    
    check = orchestrator.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning
    )
    
    print(f"\n⏳ Safety Check Result:")
    print(f"   Status: {check.status.value.upper()}")
    print(f"   Approval OK: {check.approval_ok}")
    
    # Get pending approvals
    pending = orchestrator.get_pending_approvals()
    
    if pending:
        print(f"\n📋 Pending Approvals: {len(pending)}")
        for req in pending:
            print(f"\n   Request ID: {req['request_id']}")
            print(f"   Action: {req['action_type']}")
            print(f"   Description: {req['description']}")
            print(f"   Risk Level: {req['risk_level']}")
            
            # Simulate human approval
            print(f"\n   ✅ Simulating human approval...")
            orchestrator.approve_pending_request(
                request_id=req['request_id'],
                approver="Human Trader",
                notes="Approved after review"
            )
            print(f"   ✅ Approved by: Human Trader")


def demo_kill_switch():
    """Demo: Emergency kill switch."""
    print("\n" + "="*80)
    print("DEMO 6: EMERGENCY KILL SWITCH")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start
    
    orchestrator = quick_start()
    
    print("\n🚨 Activating Kill Switch...")
    orchestrator.activate_kill_switch(
        reason="Detected anomalous market conditions",
        activated_by="Risk Manager"
    )
    
    # Try to execute action after kill switch
    action = {'symbol': 'EURUSD', 'direction': 'buy'}
    reasoning = "Normal trade"
    
    check = orchestrator.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning
    )
    
    print(f"\n🛑 Safety Check Result:")
    print(f"   Status: {check.status.value.upper()}")
    print(f"   Can Proceed: {check.can_proceed}")
    
    if check.issues:
        print(f"\n🚫 Issues:")
        for issue in check.issues:
            print(f"   - {issue}")


def demo_comprehensive_status():
    """Demo: Comprehensive system status."""
    print("\n" + "="*80)
    print("DEMO 7: COMPREHENSIVE SYSTEM STATUS")
    print("="*80)
    
    from trading_bot.anti_rogue_ai import quick_start
    
    orchestrator = quick_start()
    
    # Run a few actions
    for i in range(3):
        action = {'symbol': 'EURUSD', 'direction': 'buy', 'risk_pct': 1.0}
        reasoning = f"Trade {i+1}"
        orchestrator.validate_action('trade', action, reasoning)
    
    # Get comprehensive status
    status = orchestrator.get_comprehensive_status()
    
    print(f"\n📊 System Status:")
    print(f"   Kill Switch: {'🚨 ACTIVATED' if status['kill_switch_activated'] else '✅ Normal'}")
    print(f"   Total Checks: {status['total_checks']}")
    print(f"   Blocked Actions: {status['blocked_actions']}")
    
    print(f"\n🔒 Constraints:")
    print(f"   Integrity: {status['constraints']['integrity_message']}")
    print(f"   Violations: {status['constraints']['total_violations']}")
    
    print(f"\n🧠 Market Understanding:")
    print(f"   Tracked Symbols: {len(status['understanding']['tracked_symbols'])}")
    
    print(f"\n🛡️ Rogue Prevention:")
    print(f"   Total Detections: {status['rogue_prevention']['total_detections']}")
    print(f"   Critical: {status['rogue_prevention']['critical_detections']}")
    
    print(f"\n👥 Human Oversight:")
    print(f"   Oversight Level: {status['oversight']['oversight_level']}")
    print(f"   Pending Approvals: {status['oversight']['pending_approvals']}")


def main():
    """Run all demos."""
    print("\n" + "="*80)
    print("ANTI-ROGUE AI SYSTEM DEMONSTRATION")
    print("="*80)
    print("\nThis demo shows how the AI is prevented from going rogue")
    print("and forced to understand markets before trading.\n")
    
    try:
        demo_safe_action()
        demo_constraint_violation()
        demo_insufficient_understanding()
        demo_rogue_behavior()
        demo_human_approval()
        demo_kill_switch()
        demo_comprehensive_status()
        
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nKEY TAKEAWAYS:")
        print("1. ✅ AI cannot bypass immutable constraints")
        print("2. ✅ AI must understand markets, not just predict")
        print("3. ✅ Rogue behavior is detected and blocked")
        print("4. ✅ Humans remain in control with kill switch")
        print("5. ✅ All actions are transparent and explainable")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
