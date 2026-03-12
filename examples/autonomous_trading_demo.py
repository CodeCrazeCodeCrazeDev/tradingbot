"""
Autonomous Trading Bot Demo

Demonstrates the complete autonomous system:
1. Pre-trading safety checks with auto-fix
2. Learning from losses via internet search
3. Testing improvements in mirror market
4. Deploying best strategies to live

This is the FULL autonomous loop you requested.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_bot.self_improvement import AutonomousOrchestrator
from enum import auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('autonomous_trading_demo.log')
    ]
)

logger = logging.getLogger(__name__)


class AutonomousTradingDemo:
    """Demo of fully autonomous trading bot."""
    
    def __init__(self):
        """Initialize demo."""
        # Configuration
        self.config = {
            'autonomous_fixer': {
                'auto_fix_enabled': True,
                'max_fix_attempts': 3,
                'safety_check_interval': 60
            },
            'internet_improver': {
                'internet_learning_enabled': True,
                'api_keys': {
                    'openai': ''  # Add your API key if available
                }
            },
            'mirror_tester': {
                'mirror_test_duration_hours': 24,
                'min_trades_required': 30,
                'performance_threshold': 0.05  # 5% improvement required
            },
            'self_improvement': {
                'AUTO_LEARN': True,
                'CONF_THRESHOLD': 0.6,
                'AUTO_PROMOTE': False
            }
        }
        
        # Initialize autonomous orchestrator
        self.orchestrator = AutonomousOrchestrator(self.config)
        
        logger.info("Autonomous Trading Demo initialized")
    
    async def run_complete_demo(self):
        """Run complete autonomous trading demo."""
        logger.info("=" * 80)
        logger.info("AUTONOMOUS TRADING BOT - COMPLETE DEMO")
        logger.info("=" * 80)
        
        # Scenario 1: Pre-trading safety check
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 1: Pre-Trading Safety Check")
        logger.info("=" * 80)
        await self._demo_safety_check()
        
        # Scenario 2: Handle losing trade with full autonomous improvement
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 2: Autonomous Improvement After Loss")
        logger.info("=" * 80)
        await self._demo_loss_improvement()
        
        # Scenario 3: Show system status
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 3: System Status")
        logger.info("=" * 80)
        self._demo_system_status()
        
        logger.info("\n" + "=" * 80)
        logger.info("DEMO COMPLETED")
        logger.info("=" * 80)
    
    async def _demo_safety_check(self):
        """Demo pre-trading safety check."""
        logger.info("Running pre-trading safety check...")
        
        result = await self.orchestrator.pre_trading_check()
        
        logger.info(f"\nSafety Check Result:")
        logger.info(f"  Safe to Trade: {result['safe_to_trade']}")
        logger.info(f"  Status: {result['status']}")
        logger.info(f"  Issues Found: {len(result['issues'])}")
        logger.info(f"  Fixes Applied: {len(result['fixes_applied'])}")
        
        if result['safe_to_trade']:
            logger.info("\n✓ SYSTEM READY FOR TRADING")
        else:
            logger.warning("\n✗ TRADING PAUSED - Issues detected")
            for issue in result['issues']:
                logger.warning(f"  - {issue}")
    
    async def _demo_loss_improvement(self):
        """Demo autonomous improvement after losing trade."""
        logger.info("Simulating losing trade...")
        
        # Create simulated losing trade
        trade = {
            'ticket_id': 'DEMO_001',
            'entry_time': datetime.now(),
            'exit_time': datetime.now(),
            'symbol': 'EURUSD',
            'side': 'buy',
            'entry_price': 1.1000,
            'exit_price': 1.0950,  # Loss
            'size': 0.1,
            'sl': 1.0950,
            'tp': 1.1100,
            'pnl': -50.0,
            'fees': 2.0
        }
        
        signal_data = {
            'indicators_used': ['RSI', 'MACD'],
            'indicator_values': {'RSI': 45, 'MACD': 0.0002},
            'model_confidence': 0.55,
            'timeframe': 'H1',
            'market_regime': 'trending'
        }
        
        market_data = {
            'candles_before': [],
            'candles_after': [],
            'atr': 0.0015,
            'spread': 0.0001,
            'volume_avg': 1000
        }
        
        system_data = {
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'latency_ms': 150,
            'order_fill_type': 'full',
            'errors_in_logs': []
        }
        
        equity = 10000.0
        
        logger.info("\nProcessing losing trade through autonomous system...")
        logger.info("This will:")
        logger.info("  1. Analyze root cause")
        logger.info("  2. Search internet for improvements")
        logger.info("  3. Test improvements in mirror market")
        logger.info("  4. Deploy best strategy if found")
        
        result = await self.orchestrator.on_trade_loss(
            trade, signal_data, market_data, system_data, equity
        )
        
        logger.info(f"\nAutonomous Improvement Result:")
        logger.info(f"  Status: {result['status']}")
        logger.info(f"  Trade ID: {result['trade_id']}")
        
        if 'improvements_tested' in result:
            logger.info(f"  Improvements Tested: {result['improvements_tested']}")
        
        if result['status'] == 'deployed':
            logger.info(f"  Best Improvement: {result['best_improvement']:.1%}")
            logger.info(f"\n✓ IMPROVED STRATEGY DEPLOYED TO LIVE")
            logger.info(f"  Deployment: {result['deployment']}")
        elif result['status'] == 'no_deployment':
            logger.warning(f"\n⚠ No improvements passed validation")
            logger.warning(f"  Reason: {result['reason']}")
        else:
            logger.info(f"\n  Result: {result}")
    
    def _demo_system_status(self):
        """Demo system status display."""
        status = self.orchestrator.get_status()
        
        logger.info("\nCurrent System Status:")
        logger.info(f"  Safe to Trade: {status['safe_to_trade']}")
        logger.info(f"  Pending Improvements: {status['pending_improvements']}")
        logger.info(f"  Active Tests: {status['active_tests']}")
        logger.info(f"  Timestamp: {status['timestamp']}")


async def main():
    """Run the autonomous trading demo."""
    demo = AutonomousTradingDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
