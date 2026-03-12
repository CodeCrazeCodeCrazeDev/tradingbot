"""
Market Student System Runner
============================

AI becomes the student, Market becomes the teacher.

This is the main entry point for running the Market Student system.

Usage:
    python run_market_student.py [--mode paper|live] [--symbol EURUSD]
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'market_student_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print the Market Student banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         MARKET STUDENT SYSTEM                                ║
║                                                                              ║
║              AI becomes the student, Market becomes the teacher              ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  🎓 YOUR ROLE (AI = The Student)                                    │    ║
║  │     - Learn from every market movement                              │    ║
║  │     - Extract lessons from wins, losses, missed trades              │    ║
║  │     - Propose improvements (NEVER implement without approval)       │    ║
║  │     - Seek clarity, simplicity, and accuracy                        │    ║
║  │                                                                     │    ║
║  │  📘 MARKET ROLE (Market = The Teacher)                              │    ║
║  │     - Every candle is a lesson                                      │    ║
║  │     - Every trend is a lecture                                      │    ║
║  │     - Every loss is a correction                                    │    ║
║  │     - Every win is a confirmation                                   │    ║
║  │                                                                     │    ║
║  │  🔒 CONSTRAINTS                                                     │    ║
║  │     - AI NEVER pushes code changes directly                         │    ║
║  │     - All modifications are PROPOSALS only                          │    ║
║  │     - Human MUST approve all changes                                │    ║
║  │     - Reward system is IMMUTABLE                                    │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def run_interactive_mode(orchestrator):
    """Run in interactive mode"""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    print("\nCommands:")
    print("  status    - Show system status")
    print("  lessons   - Show recent lessons")
    print("  proposals - Show pending proposals")
    print("  approve   - Approve a proposal")
    print("  reject    - Reject a proposal")
    print("  insights  - Show actionable insights")
    print("  limits    - Show risk limits")
    print("  export    - Export knowledge")
    print("  quit      - Exit")
    print()
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'quit' or cmd == 'exit':
                break
            
            elif cmd == 'status':
                status = orchestrator.get_system_status()
                print("\n📊 SYSTEM STATUS")
                print(f"   Running: {status['is_running']}")
                print(f"   Total cycles: {status['statistics']['total_cycles']}")
                print(f"   Total lessons: {status['statistics']['total_lessons']}")
                print(f"   Total proposals: {status['statistics']['total_proposals']}")
                print(f"   Reward score: {status['reward_status']['cumulative_score']:.2f}")
            
            elif cmd == 'lessons':
                lessons = orchestrator.get_recent_lessons(limit=10)
                print(f"\n📚 RECENT LESSONS ({len(lessons)})")
                for l in lessons:
                    print(f"\n   [{l['severity']}] {l['lesson_type']}")
                    print(f"   Lesson: {l['lesson_learned'][:80]}...")
                    print(f"   Insight: {l['actionable_insight'][:80]}...")
            
            elif cmd == 'proposals':
                proposals = orchestrator.get_pending_proposals()
                print(f"\n📝 PENDING PROPOSALS ({len(proposals)})")
                for p in proposals:
                    print(f"\n   ID: {p['proposal_id']}")
                    print(f"   Title: {p['title']}")
                    print(f"   Priority: {p['priority']}")
                    print(f"   Type: {p['proposal_type']}")
            
            elif cmd == 'approve':
                proposal_id = input("   Proposal ID: ").strip()
                approver = input("   Your name: ").strip()
                if orchestrator.approve_proposal(proposal_id, approver):
                    print("   ✅ Proposal approved!")
                else:
                    print("   ❌ Failed to approve proposal")
            
            elif cmd == 'reject':
                proposal_id = input("   Proposal ID: ").strip()
                reason = input("   Reason: ").strip()
                if orchestrator.reject_proposal(proposal_id, reason):
                    print("   ✅ Proposal rejected!")
                else:
                    print("   ❌ Failed to reject proposal")
            
            elif cmd == 'insights':
                insights = orchestrator.get_actionable_insights(limit=10)
                print("\n💡 ACTIONABLE INSIGHTS")
                for i, insight in enumerate(insights, 1):
                    print(f"   {i}. {insight}")
            
            elif cmd == 'limits':
                limits = orchestrator.get_risk_limits()
                print("\n🔒 RISK LIMITS (IMMUTABLE)")
                for key, value in limits.items():
                    print(f"   {key}: {value}")
            
            elif cmd == 'export':
                filepath = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                orchestrator.export_knowledge(filepath)
                print(f"   ✅ Knowledge exported to {filepath}")
            
            elif cmd == 'help':
                print("\nCommands: status, lessons, proposals, approve, reject, insights, limits, export, quit")
            
            else:
                print("   Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"   Error: {e}")


async def run_demo_mode(orchestrator):
    """Run a demonstration of the system"""
    print("\n" + "=" * 60)
    print("DEMO MODE - Simulating market learning")
    print("=" * 60)
    
    # Simulate market data
    print("\n1️⃣ Simulating market data...")
    market_data = {
        'open': [1.1000, 1.1010, 1.1020, 1.1030, 1.1040],
        'high': [1.1015, 1.1025, 1.1035, 1.1045, 1.1055],
        'low': [1.0995, 1.1005, 1.1015, 1.1025, 1.1035],
        'close': [1.1010, 1.1020, 1.1030, 1.1040, 1.1050],
        'volume': [10000, 12000, 11000, 13000, 15000],
        'indicators': {
            'atr': [0.0010, 0.0011, 0.0012, 0.0013, 0.0014],
            'rsi': [50, 55, 60, 65, 70],
        },
        'regime': 'trending',
        'volatility': 'normal',
        'timeframe': '1H',
    }
    
    signal = {
        'direction': 'long',
        'confidence': 0.72,
        'entry_price': 1.1050,
        'stop_loss': 1.1020,
        'take_profit': 1.1100,
    }
    
    result = await orchestrator.process_market_data(
        symbol='EURUSD',
        market_data=market_data,
        signal=signal
    )
    print(f"   ✅ Processed market data")
    print(f"   📚 Lessons extracted: {len(result['lessons'])}")
    
    # Simulate a winning trade
    print("\n2️⃣ Simulating winning trade...")
    winning_trade = {
        'id': 'trade_win_001',
        'pnl': 75.50,
        'risk': 0.015,
        'slippage': 0.0002,
        'execution_time_ms': 45,
        'signal_confidence': 0.72,
    }
    
    win_result = await orchestrator.process_trade_outcome(
        symbol='EURUSD',
        trade=winning_trade,
        market_data=market_data,
        signal=signal
    )
    print(f"   ✅ Winning trade processed")
    print(f"   💰 PnL: +${winning_trade['pnl']:.2f}")
    print(f"   🎯 Reward score: {win_result.get('reward_score', 0):.2f}")
    
    # Simulate a losing trade
    print("\n3️⃣ Simulating losing trade...")
    losing_trade = {
        'id': 'trade_loss_001',
        'pnl': -45.00,
        'risk': 0.02,
        'slippage': 0.0005,
        'execution_time_ms': 120,
        'signal_confidence': 0.55,
        'stop_hit': True,
    }
    
    loss_result = await orchestrator.process_trade_outcome(
        symbol='EURUSD',
        trade=losing_trade,
        market_data=market_data,
        signal={'direction': 'long', 'confidence': 0.55}
    )
    print(f"   ✅ Losing trade processed")
    print(f"   💸 PnL: -${abs(losing_trade['pnl']):.2f}")
    print(f"   📝 Insights: {loss_result['insights'][:2]}")
    
    # Show proposals
    print("\n4️⃣ Checking improvement proposals...")
    proposals = orchestrator.get_pending_proposals()
    print(f"   📋 Pending proposals: {len(proposals)}")
    for p in proposals[:3]:
        print(f"\n   📌 {p['title']}")
        print(f"      Priority: {p['priority']}")
        print(f"      Rationale: {p['rationale'][:60]}...")
    
    # Show system status
    print("\n5️⃣ System status...")
    status = orchestrator.get_system_status()
    print(f"   📊 Total cycles: {status['statistics']['total_cycles']}")
    print(f"   📚 Total lessons: {status['statistics']['total_lessons']}")
    print(f"   📝 Total proposals: {status['statistics']['total_proposals']}")
    print(f"   🎯 Cumulative reward: {status['reward_status']['cumulative_score']:.2f}")
    
    # Show risk limits
    print("\n6️⃣ Risk limits (IMMUTABLE)...")
    limits = orchestrator.get_risk_limits()
    print(f"   🔒 Max risk per trade: {limits['max_risk_per_trade']:.1%}")
    print(f"   🔒 Max daily loss: {limits['max_daily_loss']:.1%}")
    print(f"   🔒 Max drawdown: {limits['max_drawdown']:.1%}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nThe AI has learned from the market and proposed improvements.")
    print("All proposals require HUMAN APPROVAL before implementation.")
    print("The reward system and risk limits are IMMUTABLE.")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Market Student System')
    parser.add_argument('--mode', choices=['demo', 'interactive', 'background'], 
                       default='demo', help='Running mode')
    parser.add_argument('--symbol', default='EURUSD', help='Trading symbol')
    parser.add_argument('--auto-learn', action='store_true', help='Enable auto-learning')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Import orchestrator
    from trading_bot.market_student import MarketStudentOrchestrator, quick_start
    
    # Initialize
    print("\n🚀 Initializing Market Student system...")
    orchestrator = await quick_start({
        'auto_learn': args.auto_learn,
        'require_approval': True,
        'storage_path': 'market_student_data',
    })
    print("   ✅ System initialized")
    
    try:
        if args.mode == 'demo':
            await run_demo_mode(orchestrator)
        elif args.mode == 'interactive':
            await run_interactive_mode(orchestrator)
        elif args.mode == 'background':
            print("\n🔄 Running in background mode...")
            print("   Press Ctrl+C to stop")
            while True:
                await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    
    finally:
        print("\n🛑 Stopping Market Student system...")
        await orchestrator.stop()
        print("   ✅ System stopped")


if __name__ == '__main__':
    asyncio.run(main())
