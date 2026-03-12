"""
AlphaAlgo - Complete Autonomous Trading System Launcher

This is the main entry point that integrates:
1. System Health Validation (5-phase validation)
2. Autonomous Trading (auto-fix, internet learning, mirror testing)
3. Self-Improvement Engine (loss learning)
4. Continuous Monitoring

Run this to start the complete autonomous trading system.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Add to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trading_bot.system_health import AlphaAlgoMaster, TradingMode
from trading_bot.self_improvement import AutonomousOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'alphaalgo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


class AlphaAlgoLauncher:
    """
    Complete AlphaAlgo Launcher
    
    Integrates all autonomous systems:
    - System validation and health monitoring
    - Autonomous trading with internet learning
    - Self-improvement from losses
    - Continuous monitoring and adaptation
    """
    
    def __init__(self, config_file: str = 'config/alphaalgo_config.yaml'):
        """Initialize AlphaAlgo launcher."""
        self.config = self._load_config(config_file)
        
        # Initialize system validation
        self.validator = AlphaAlgoMaster(self.config.get('system_health', {}))
        
        # Initialize autonomous trading
        self.autonomous = AutonomousOrchestrator(self.config.get('autonomous', {}))
        
        logger.info("=" * 80)
        logger.info("ALPHAALGO - COMPLETE AUTONOMOUS TRADING SYSTEM")
        logger.info("=" * 80)
        logger.info(f"Initialized at: {datetime.now()}")
        logger.info("=" * 80)
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from file."""
        config_path = Path(config_file)
        
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
        
        # Default configuration
        return {
            'system_health': {
                'min_health_for_live': 95.0,
                'revalidation_interval_hours': 1,
                'health_monitor': {
                    'max_latency_ms': 100,
                    'max_cpu_percent': 90,
                    'min_memory_mb': 500
                },
                'stability_tester': {
                    'test_duration_minutes': 60,
                    'tick_interval_ms': 100
                }
            },
            'autonomous': {
                'autonomous_fixer': {
                    'auto_fix_enabled': True,
                    'max_fix_attempts': 3
                },
                'internet_improver': {
                    'internet_learning_enabled': True,
                    'api_keys': {}
                },
                'mirror_tester': {
                    'mirror_test_duration_hours': 24,
                    'min_trades_required': 30,
                    'performance_threshold': 0.05
                },
                'self_improvement': {
                    'AUTO_LEARN': True,
                    'CONF_THRESHOLD': 0.6,
                    'AUTO_PROMOTE': False
                }
            }
        }
    
    async def launch(self):
        """
        Launch AlphaAlgo with complete validation and monitoring.
        
        Steps:
        1. Run 5-phase system validation
        2. Check if safe to trade
        3. Start autonomous trading if approved
        4. Enable continuous monitoring
        5. Handle trading loop with self-improvement
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: SYSTEM VALIDATION (5 Phases)")
        logger.info("=" * 80)
        
        # Run complete validation
        validation_results = await self.validator.run_full_validation()
        
        # Check if can proceed
        if not self.validator.can_trade_live():
            logger.error("\n" + "=" * 80)
            logger.error("❌ VALIDATION FAILED - CANNOT START TRADING")
            logger.error("=" * 80)
            logger.error(f"System Health: {validation_results['system_health']:.1f}%")
            logger.error(f"Mode: {validation_results['recommended_mode'].value}")
            logger.error("\nReasons:")
            for reason in validation_results['reasons']:
                logger.error(f"  • {reason}")
            
            if validation_results['critical_issues']:
                logger.error("\nCritical Issues:")
                for issue in validation_results['critical_issues']:
                    logger.error(f"  ❌ {issue}")
            
            logger.error("\nRecommendation: Fix issues and re-run validation")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ VALIDATION PASSED - STARTING ALPHAALGO")
        logger.info("=" * 80)
        logger.info(f"System Health: {validation_results['system_health']:.1f}%")
        logger.info(f"Trading Mode: {validation_results['recommended_mode'].value}")
        
        # Start continuous monitoring in background
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: STARTING CONTINUOUS MONITORING")
        logger.info("=" * 80)
        
        monitoring_task = asyncio.create_task(self.validator.continuous_monitoring())
        logger.info("✓ Continuous monitoring started (re-validates every hour)")
        
        # Start autonomous trading
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: STARTING AUTONOMOUS TRADING SYSTEM")
        logger.info("=" * 80)
        
        # Run trading loop
        await self.trading_loop()
    
    async def trading_loop(self):
        """
        Main trading loop with autonomous features.
        
        Features:
        - Pre-trading safety checks
        - Autonomous issue fixing
        - Internet-based strategy improvement
        - Mirror market testing
        - Self-improvement from losses
        """
        logger.info("Trading loop started...")
        logger.info("Features enabled:")
        logger.info("  ✓ Pre-trading safety checks")
        logger.info("  ✓ Autonomous issue fixing")
        logger.info("  ✓ Internet-based learning")
        logger.info("  ✓ Mirror market testing")
        logger.info("  ✓ Self-improvement from losses")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Trading Loop Iteration {iteration}")
                logger.info(f"{'='*60}")
                
                # Pre-trading safety check
                safety = await self.autonomous.pre_trading_check()
                
                if not safety['safe_to_trade']:
                    logger.warning("⚠️ Pre-trading check failed - pausing")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                logger.info("✓ Pre-trading check passed")
                
                # Simulate trading activity
                # In production: Replace with actual trading logic
                logger.info("Trading active...")
                
                # Simulate a losing trade for demonstration
                if iteration % 10 == 0:  # Every 10th iteration
                    logger.info("\n📉 Simulated losing trade detected")
                    
                    # Create simulated trade
                    trade = {
                        'ticket_id': f'TRADE_{iteration}',
                        'symbol': 'EURUSD',
                        'entry_price': 1.1000,
                        'exit_price': 1.0950,
                        'pnl': -50.0,
                        'size': 0.1,
                        'sl': 1.0950,
                        'tp': 1.1100,
                        'confidence': 0.55
                    }
                    
                    signal_data = {
                        'indicators_used': ['RSI', 'MACD'],
                        'model_confidence': 0.55,
                        'timeframe': 'H1',
                        'market_regime': 'trending'
                    }
                    
                    market_data = {
                        'candles_before': [],
                        'atr': 0.0015,
                        'spread': 0.0001,
                        'volatility_spike': False
                    }
                    
                    system_data = {
                        'cpu_usage': 45.0,
                        'memory_usage': 60.0,
                        'latency_ms': 150,
                        'errors_in_logs': []
                    }
                    
                    equity = 10000.0
                    
                    # Process through autonomous system
                    result = await self.autonomous.on_trade_loss(
                        trade, signal_data, market_data, system_data, equity
                    )
                    
                    logger.info(f"Autonomous improvement result: {result['status']}")
                    
                    # Also record in validator for learning
                    await self.validator.record_trade_loss(trade)
                
                # Sleep before next iteration
                await asyncio.sleep(60)  # 1 minute
            
            except KeyboardInterrupt:
                logger.info("\n" + "=" * 80)
                logger.info("SHUTDOWN REQUESTED")
                logger.info("=" * 80)
                break
            
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        logger.info("Trading loop stopped")
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("\n" + "=" * 80)
        logger.info("ALPHAALGO SHUTDOWN")
        logger.info("=" * 80)
        
        # Get final status
        status = self.validator.get_status()
        
        logger.info(f"\nFinal Status:")
        logger.info(f"  Mode: {status['current_mode']}")
        logger.info(f"  System Health: {status['system_health']:.1f}%")
        logger.info(f"  Total Trades: {status['performance_summary']['total_trades']}")
        logger.info(f"  Total PnL: ${status['performance_summary']['total_pnl']:.2f}")
        
        logger.info("\n" + "=" * 80)
        logger.info("ALPHAALGO STOPPED")
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    launcher = AlphaAlgoLauncher()
    
    try:
        await launcher.launch()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    finally:
        await launcher.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
