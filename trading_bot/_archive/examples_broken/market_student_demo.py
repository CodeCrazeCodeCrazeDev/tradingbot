"""
Market Student System - Comprehensive Demo
==========================================

AI becomes the student, Market becomes the teacher.

This demo shows:
    pass
1. How the AI learns from market data
2. How lessons are extracted from trades
3. How improvement proposals are generated
4. How the human approval flow works
5. How the immutable reward system guides learning

Run: python examples/market_student_demo.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    pass
    """Run the Market Student demo"""
    
    print("\n" + "=" * 70)
    print("                    MARKET STUDENT SYSTEM DEMO")
    print("           AI becomes the student, Market becomes the teacher")
    print("=" * 70)
    
    # Import components
    from trading_bot.market_student import (
import json
        MarketStudentOrchestrator,
        MarketTeacher,
        StudentAI,
        AlphaLearningCycle,
        LessonDatabase,
        SafeEvolutionEngine,
        ImmutableRewardSystem,
        quick_start,
    )
    
    # =========================================================================
    # PART 1: Initialize the System
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 1: SYSTEM INITIALIZATION")
    print("-" * 70)
    
    orchestrator = await quick_start({
        'auto_learn': False,  # Manual control for demo
        'require_approval': True,
        'storage_path': 'demo_market_student_data',
    })
    
    print("✅ Market Student system initialized")
    print(f"   Storage: demo_market_student_data/")
    print(f"   Approval required: True")
    
    # =========================================================================
    # PART 2: Show Immutable Risk Limits
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 2: IMMUTABLE RISK LIMITS (Cannot be changed by AI)")
    print("-" * 70)
    
    limits = orchestrator.get_risk_limits()
    print("\n🔒 FROZEN RISK LIMITS:")
    for key, value in limits.items():
    pass
        if isinstance(value, float) and value < 1:
    pass
            print(f"   {key}: {value:.1%}")
        else:
    pass
            print(f"   {key}: {value}")
    
    print("\n⚠️  These limits are IMMUTABLE. The AI cannot modify them.")
    
    # =========================================================================
    # PART 3: Simulate Market Data and Learning
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 3: LEARNING FROM MARKET DATA")
    print("-" * 70)
    
    # Simulate trending market data
    market_data_trending = {
        'open': [1.1000, 1.1020, 1.1040, 1.1060, 1.1080],
        'high': [1.1025, 1.1045, 1.1065, 1.1085, 1.1105],
        'low': [1.0995, 1.1015, 1.1035, 1.1055, 1.1075],
        'close': [1.1020, 1.1040, 1.1060, 1.1080, 1.1100],
        'volume': [10000, 12000, 14000, 16000, 18000],  # Increasing volume
        'indicators': {
            'atr': [0.0015, 0.0016, 0.0017, 0.0018, 0.0019],
            'rsi': [55, 60, 65, 70, 72],
        },
        'regime': 'trending',
        'volatility': 'normal',
        'timeframe': '1H',
    }
    
    signal_long = {
        'direction': 'long',
        'confidence': 0.78,
        'entry_price': 1.1100,
        'stop_loss': 1.1050,
        'take_profit': 1.1200,
    }
    
    print("\n📊 Processing trending market data...")
    result1 = await orchestrator.process_market_data(
        symbol='EURUSD',
        market_data=market_data_trending,
        signal=signal_long
    )
    
    print(f"   ✅ Market data processed")
    print(f"   📚 Lessons extracted: {len(result1['lessons'])}")
    print(f"   💡 Insights: {result1['insights'][:2] if result1['insights'] else ['None']}")
    
    # =========================================================================
    # PART 4: Learning from Winning Trade
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 4: LEARNING FROM WINNING TRADE")
    print("-" * 70)
    
    winning_trade = {
        'id': 'demo_win_001',
        'direction': 'long',
        'entry_price': 1.1100,
        'exit_price': 1.1180,
        'pnl': 80.00,
        'risk': 0.015,
        'slippage': 0.0001,
        'execution_time_ms': 35,
        'signal_confidence': 0.78,
        'timeframe': '1H',
    }
    
    print("\n🎯 Processing winning trade...")
    print(f"   Entry: {winning_trade['entry_price']}")
    print(f"   Exit: {winning_trade['exit_price']}")
    print(f"   PnL: +${winning_trade['pnl']:.2f}")
    
    win_result = await orchestrator.process_trade_outcome(
        symbol='EURUSD',
        trade=winning_trade,
        market_data=market_data_trending,
        signal=signal_long
    )
    
    print(f"\n   ✅ Trade processed")
    print(f"   🎯 Reward score: {win_result.get('reward_score', 0):.2f}")
    print(f"   📝 Lessons: {win_result['lessons']}")
    
    # =========================================================================
    # PART 5: Learning from Losing Trade
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 5: LEARNING FROM LOSING TRADE (The Market Corrects)")
    print("-" * 70)
    
    # Simulate volatile market data
    market_data_volatile = {
        'open': [1.1100, 1.1080, 1.1050, 1.1020, 1.0990],
        'high': [1.1110, 1.1090, 1.1060, 1.1030, 1.1000],
        'low': [1.1070, 1.1040, 1.1010, 1.0980, 1.0950],
        'close': [1.1080, 1.1050, 1.1020, 1.0990, 1.0960],
        'volume': [20000, 25000, 30000, 35000, 40000],  # High volume
        'indicators': {
            'atr': [0.0030, 0.0035, 0.0040, 0.0045, 0.0050],  # High volatility
            'rsi': [45, 40, 35, 30, 28],
        },
        'regime': 'volatile',
        'volatility': 'high',
        'timeframe': '1H',
    }
    
    signal_wrong = {
        'direction': 'long',
        'confidence': 0.52,  # Low confidence
        'entry_price': 1.1100,
        'stop_loss': 1.1050,
        'take_profit': 1.1200,
    }
    
    losing_trade = {
        'id': 'demo_loss_001',
        'direction': 'long',
        'entry_price': 1.1100,
        'exit_price': 1.1050,
        'pnl': -50.00,
        'risk': 0.02,
        'slippage': 0.0008,  # High slippage
        'execution_time_ms': 150,  # Slow execution
        'signal_confidence': 0.52,
        'stop_hit': True,
        'timeframe': '1H',
    }
    
    print("\n📉 Processing losing trade...")
    print(f"   Entry: {losing_trade['entry_price']}")
    print(f"   Exit: {losing_trade['exit_price']} (Stop hit)")
    print(f"   PnL: -${abs(losing_trade['pnl']):.2f}")
    
    loss_result = await orchestrator.process_trade_outcome(
        symbol='EURUSD',
        trade=losing_trade,
        market_data=market_data_volatile,
        signal=signal_wrong
    )
    
    print(f"\n   ✅ Trade processed")
    print(f"   ⚠️ Penalty score: {loss_result.get('penalty_score', 0):.2f}")
    print(f"   📝 Lessons: {loss_result['lessons']}")
    print(f"   💡 Insights:")
    for insight in loss_result['insights'][:3]:
    pass
        print(f"      - {insight}")
    
    # =========================================================================
    # PART 6: Check Improvement Proposals
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 6: IMPROVEMENT PROPOSALS (AI Proposes, Human Approves)")
    print("-" * 70)
    
    proposals = orchestrator.get_pending_proposals()
    
    print(f"\n📋 Pending proposals: {len(proposals)}")
    
    for i, p in enumerate(proposals[:5], 1):
    pass
        print(f"\n   Proposal {i}:")
        print(f"   ID: {p['proposal_id']}")
        print(f"   Title: {p['title']}")
        print(f"   Priority: {p['priority']}")
        print(f"   Type: {p['proposal_type']}")
        print(f"   Rationale: {p['rationale'][:80]}...")
    
    print("\n⚠️  These proposals require HUMAN APPROVAL before implementation.")
    
    # =========================================================================
    # PART 7: Human Approval Flow
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 7: HUMAN APPROVAL FLOW")
    print("-" * 70)
    
    if proposals:
    pass
        # Approve first proposal
        first_proposal = proposals[0]
        print(f"\n👤 Human reviewing proposal: {first_proposal['proposal_id']}")
        print(f"   Title: {first_proposal['title']}")
        
        # Simulate approval
        approved = orchestrator.approve_proposal(
            first_proposal['proposal_id'],
            approver='Demo Human',
            notes='Approved after review'
        )
        
        if approved:
    pass
            print(f"   ✅ Proposal APPROVED by 'Demo Human'")
        else:
    pass
            print(f"   ❌ Approval failed")
        
        # Reject second proposal if exists
        if len(proposals) > 1:
    pass
            second_proposal = proposals[1]
            print(f"\n👤 Human reviewing proposal: {second_proposal['proposal_id']}")
            print(f"   Title: {second_proposal['title']}")
            
            rejected = orchestrator.reject_proposal(
                second_proposal['proposal_id'],
                reason='Not suitable for current market conditions'
            )
            
            if rejected:
    pass
                print(f"   ❌ Proposal REJECTED: 'Not suitable for current market conditions'")
    
    # =========================================================================
    # PART 8: System Status
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 8: SYSTEM STATUS")
    print("-" * 70)
    
    status = orchestrator.get_system_status()
    
    print("\n📊 LEARNING STATISTICS:")
    print(f"   Total cycles: {status['statistics']['total_cycles']}")
    print(f"   Total lessons: {status['statistics']['total_lessons']}")
    print(f"   Total proposals: {status['statistics']['total_proposals']}")
    
    print("\n🎯 REWARD STATUS:")
    print(f"   Cumulative score: {status['reward_status']['cumulative_score']:.2f}")
    print(f"   Total rewards: {status['reward_status']['total_rewards']}")
    print(f"   Total penalties: {status['reward_status']['total_penalties']}")
    
    learning_state = status['learning_state']
    print("\n📚 LEARNING STATE:")
    print(f"   Phase: {learning_state['phase']}")
    print(f"   Patterns recognized: {learning_state['patterns_recognized']}")
    print(f"   Weaknesses identified: {learning_state['weaknesses_identified']}")
    print(f"   Improvements proposed: {learning_state['improvements_proposed']}")
    print(f"   Improvements approved: {learning_state['improvements_approved']}")
    print(f"   Improvements rejected: {learning_state['improvements_rejected']}")
    
    # =========================================================================
    # PART 9: Actionable Insights
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 9: ACTIONABLE INSIGHTS")
    print("-" * 70)
    
    insights = orchestrator.get_actionable_insights(limit=5)
    
    print("\n💡 TOP INSIGHTS FROM MARKET LESSONS:")
    for i, insight in enumerate(insights, 1):
    pass
        print(f"   {i}. {insight}")
    
    # =========================================================================
    # PART 10: Cleanup
    # =========================================================================
    print("\n" + "-" * 70)
    print("PART 10: CLEANUP")
    print("-" * 70)
    
    # Export knowledge
    export_file = f"demo_knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    orchestrator.export_knowledge(export_file)
    print(f"\n📁 Knowledge exported to: {export_file}")
    
    # Stop system
    await orchestrator.stop()
    print("✅ System stopped")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("                         DEMO SUMMARY")
    print("=" * 70)
    
    print("""
    The Market Student System demonstrates:
    pass
    1. ✅ IMMUTABLE REWARD SYSTEM
       - Risk limits cannot be changed by AI
       - Reward/penalty weights are frozen
       
    2. ✅ MARKET AS TEACHER
       - Lessons extracted from price action
       - Lessons extracted from trade outcomes
       - Volatility, volume, and trend analysis
       
    3. ✅ AI AS STUDENT
       - Learns from every market movement
       - Proposes improvements based on lessons
       - Never implements without approval
       
    4. ✅ HUMAN APPROVAL FLOW
       - All proposals require human review
       - Humans can approve or reject
       - AI learns from rejections too
       
    5. ✅ CONTINUOUS LEARNING
       - Alpha Learning Cycle (8 phases)
       - Persistent lesson database
       - Safe evolution engine
    
    The AI evolves WITHOUT losing its FOUNDATION.
    """)
    
    print("=" * 70)
    print("                      DEMO COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    pass
    asyncio.run(main())
