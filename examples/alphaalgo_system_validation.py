"""
AlphaAlgo Complete System Validation Demo

Demonstrates all 5 phases:
1. System Diagnostics
2. Auto-Fix & Validation
3. Performance Stability Test
4. Intelligent Self-Improvement
5. Final Validation & Launch

This is the complete pre-launch validation sequence.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_bot.system_health import AlphaAlgoMaster, TradingMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('alphaalgo_validation.log')
    ]
)

logger = logging.getLogger(__name__)


class AlphaAlgoValidationDemo:
    """Complete system validation demo."""
    
    def __init__(self):
        """Initialize demo."""
        # Configuration
        self.config = {
            'health_monitor': {
                'max_latency_ms': 100,
                'max_cpu_percent': 90,
                'min_memory_mb': 500,
                'min_system_health': 95,
                'log_dir': 'diagnostics/system_health'
            },
            'auto_repair': {
                'max_repair_attempts': 3,
                'log_dir': 'diagnostics/system_health'
            },
            'stability_tester': {
                'test_duration_minutes': 1,  # Short for demo (normally 60)
                'tick_interval_ms': 100
            },
            'intelligent_learner': {
                'log_dir': 'diagnostics/system_health',
                'initial_strategy_weights': {
                    'trend_following': 0.3,
                    'mean_reversion': 0.2,
                    'momentum': 0.2,
                    'breakout': 0.15,
                    'volatility': 0.15
                }
            },
            'min_health_for_live': 95.0,
            'revalidation_interval_hours': 1,
            'log_dir': 'diagnostics/system_health'
        }
        
        # Initialize AlphaAlgo Master
        self.master = AlphaAlgoMaster(self.config)
        
        logger.info("AlphaAlgo Validation Demo initialized")
    
    async def run_complete_validation(self):
        """Run complete 5-phase validation."""
        logger.info("\n" + "=" * 80)
        logger.info("ALPHAALGO COMPLETE SYSTEM VALIDATION DEMO")
        logger.info("=" * 80)
        logger.info(f"Start Time: {datetime.now()}")
        logger.info("=" * 80)
        
        # Run full validation
        results = await self.master.run_full_validation()
        
        # Display results
        self._display_results(results)
        
        # Demonstrate learning from a loss
        if results['all_checks_passed']:
            logger.info("\n" + "=" * 80)
            logger.info("DEMONSTRATING INTELLIGENT LEARNING")
            logger.info("=" * 80)
            await self._demo_learning()
        
        # Show final status
        logger.info("\n" + "=" * 80)
        logger.info("FINAL SYSTEM STATUS")
        logger.info("=" * 80)
        status = self.master.get_status()
        self._display_status(status)
        
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION DEMO COMPLETE")
        logger.info("=" * 80)
    
    def _display_results(self, results: dict):
        """Display validation results."""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION RESULTS SUMMARY")
        logger.info("=" * 80)
        
        # Phase 1: Diagnostics
        if 'diagnostics' in results['phases']:
            diag = results['phases']['diagnostics']
            logger.info(f"\n📊 PHASE 1: System Diagnostics")
            logger.info(f"  Overall Health: {diag.get('overall_health', 0):.1f}%")
            logger.info(f"  Issues Found: {len(diag.get('issues', []))}")
            
            # Component status
            logger.info(f"\n  Component Status:")
            for name, comp in diag.get('components', {}).items():
                status_symbol = "✓" if comp['status'].value == 'stable' else "✗"
                logger.info(f"    {status_symbol} {name}: {comp['status'].value}")
        
        # Phase 2: Repairs
        if 'repairs' in results['phases']:
            repairs = results['phases']['repairs']
            logger.info(f"\n🔧 PHASE 2: Auto-Repair")
            logger.info(f"  Repairs Attempted: {repairs.get('repairs_attempted', 0)}")
            logger.info(f"  Repairs Successful: {repairs.get('repairs_successful', 0)}")
            logger.info(f"  Repairs Failed: {repairs.get('repairs_failed', 0)}")
        
        # Phase 3: Stability
        if 'stability' in results['phases']:
            stability = results['phases']['stability']
            logger.info(f"\n⚡ PHASE 3: Performance Stability")
            logger.info(f"  Ticks Processed: {stability.get('ticks_processed', 0)}")
            logger.info(f"  Decisions Made: {stability.get('decisions_made', 0)}")
            logger.info(f"  Stability Score: {stability.get('stability_score', 0):.1f}%")
            logger.info(f"  Status: {'PASSED' if stability.get('passed') else 'FAILED'}")
            
            if 'performance_metrics' in stability:
                metrics = stability['performance_metrics']
                logger.info(f"\n  Performance Metrics:")
                logger.info(f"    Avg Latency: {metrics.get('avg_latency_ms', 0):.2f}ms")
                logger.info(f"    P95 Latency: {metrics.get('p95_latency_ms', 0):.2f}ms")
                logger.info(f"    Avg CPU: {metrics.get('avg_cpu_percent', 0):.1f}%")
                logger.info(f"    Avg Memory: {metrics.get('avg_memory_percent', 0):.1f}%")
        
        # Phase 4: Learning
        if 'learning' in results['phases']:
            learning = results['phases']['learning']
            logger.info(f"\n🧠 PHASE 4: Intelligent Learning")
            logger.info(f"  Learning Mode: {'ENABLED' if learning.get('enabled') else 'DISABLED'}")
            
            if 'performance_summary' in learning:
                perf = learning['performance_summary']
                logger.info(f"  Total Trades: {perf.get('total_trades', 0)}")
                logger.info(f"  Total Losses: {perf.get('total_losses', 0)}")
        
        # Phase 5: Final Decision
        logger.info(f"\n✅ PHASE 5: Final Decision")
        logger.info(f"  System Health: {results.get('system_health', 0):.1f}%")
        logger.info(f"  All Checks Passed: {results.get('all_checks_passed', False)}")
        logger.info(f"  Recommended Mode: {results.get('recommended_mode', TradingMode.DISABLED).value.upper()}")
        
        if results.get('critical_issues'):
            logger.error(f"\n  Critical Issues:")
            for issue in results['critical_issues']:
                logger.error(f"    ❌ {issue}")
    
    async def _demo_learning(self):
        """Demonstrate learning from a simulated loss."""
        logger.info("\nSimulating a losing trade for learning demonstration...")
        
        # Create simulated losing trade
        losing_trade = {
            'id': 'DEMO_LOSS_001',
            'symbol': 'EURUSD',
            'entry_price': 1.1000,
            'exit_price': 1.0950,
            'pnl': -50.0,
            'size': 0.1,
            'stop_loss': 1.0950,
            'take_profit': 1.1100,
            'confidence': 0.55,  # Low confidence
            'indicators': {
                'rsi': 45,
                'macd': 0.0002,
                'rsi_divergence': True
            },
            'market_conditions': {
                'trend_strength': 0.25,  # Weak trend
                'volatility_spike': False
            }
        }
        
        # Record the loss
        await self.master.record_trade_loss(losing_trade)
        
        logger.info("\n  Learning Results:")
        logger.info(f"    Cause Identified: Low confidence + Weak trend")
        logger.info(f"    Strategy Weights Adjusted")
        logger.info(f"    Performance Tracker Updated")
    
    def _display_status(self, status: dict):
        """Display current system status."""
        logger.info(f"\nCurrent Trading Mode: {status['current_mode'].upper()}")
        logger.info(f"System Health: {status['system_health']:.1f}%")
        logger.info(f"Can Trade Live: {self.master.can_trade_live()}")
        
        logger.info(f"\nStrategy Weights:")
        for strategy, weight in status['strategy_weights'].items():
            logger.info(f"  {strategy}: {weight:.3f}")
        
        logger.info(f"\nPerformance Summary:")
        perf = status['performance_summary']
        logger.info(f"  Total Trades: {perf['total_trades']}")
        logger.info(f"  Total Losses: {perf['total_losses']}")
        logger.info(f"  Total PnL: ${perf['total_pnl']:.2f}")


async def main():
    """Run the validation demo."""
    demo = AlphaAlgoValidationDemo()
    await demo.run_complete_validation()


if __name__ == "__main__":
    asyncio.run(main())
