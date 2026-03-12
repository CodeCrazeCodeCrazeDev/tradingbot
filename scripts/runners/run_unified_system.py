#!/usr/bin/env python3
"""
AlphaAlgo Trading Bot - Unified System Runner
Integrates ALL 175+ modules into a single production-ready trading system

Usage:
    python run_unified_system.py [--mode paper|live|simulation] [--symbols BTCUSDT,EURUSD]
    
Options:
    --mode      Trading mode: simulation, paper, live (default: paper)
    --symbols   Comma-separated list of symbols to trade
    --capital   Initial capital (default: 100000)
    --config    Path to config file
    --verbose   Enable verbose logging
    --dry-run   Load modules but don't start trading
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.unified_master_integrator import (
    UnifiedMasterIntegrator,
    create_unified_system,
    quick_start
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class UnifiedSystemRunner:
    """Runner for the unified trading system"""
    
    def __init__(self, config: dict):
        self.config = config
        self.integrator: UnifiedMasterIntegrator = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> bool:
        """Initialize the unified system"""
        logger.info("=" * 80)
        logger.info("ALPHAALGO UNIFIED TRADING SYSTEM")
        logger.info("=" * 80)
        logger.info(f"Mode: {self.config.get('trading_mode', 'paper')}")
        logger.info(f"Symbols: {self.config.get('symbols', [])}")
        logger.info(f"Capital: ${self.config.get('initial_capital', 100000):,.2f}")
        logger.info("=" * 80)
        
        try:
            # Create unified system
            self.integrator = await create_unified_system(self.config)
            
            # Print status
            self.integrator.print_status_report()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}", exc_info=True)
            return False
    
    async def start(self) -> bool:
        """Start the unified system"""
        if not self.integrator:
            logger.error("System not initialized")
            return False
        
        try:
            # Start all modules
            await self.integrator.start_all_modules()
            
            self._running = True
            logger.info("=" * 80)
            logger.info("SYSTEM STARTED SUCCESSFULLY")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}", exc_info=True)
            return False
    
    async def run_trading_loop(self):
        """Main trading loop"""
        logger.info("Starting trading loop...")
        
        iteration = 0
        while self._running and not self._shutdown_event.is_set():
            try:
                iteration += 1
                
                # Log heartbeat every 60 iterations
                if iteration % 60 == 0:
                    logger.info(f"Trading loop iteration {iteration} - System healthy")
                    self.integrator.print_status_report()
                
                # Wait for next iteration (1 second)
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=1.0
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    pass  # Continue loop
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("Trading loop stopped")
    
    async def stop(self):
        """Stop the unified system"""
        logger.info("Stopping unified system...")
        
        self._running = False
        self._shutdown_event.set()
        
        if self.integrator:
            await self.integrator.stop_all_modules()
        
        logger.info("System stopped")
    
    def request_shutdown(self):
        """Request graceful shutdown"""
        logger.info("Shutdown requested...")
        self._shutdown_event.set()


async def main():
    """Main entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Unified Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_unified_system.py --mode paper
    python run_unified_system.py --mode simulation --symbols BTCUSDT,ETHUSD
    python run_unified_system.py --mode paper --capital 50000 --verbose
        """
    )
    
    parser.add_argument('--mode', choices=['simulation', 'paper', 'live'],
                       default='paper', help='Trading mode')
    parser.add_argument('--symbols', type=str, default='BTCUSDT,EURUSD',
                       help='Comma-separated list of symbols')
    parser.add_argument('--capital', type=float, default=100000.0,
                       help='Initial capital')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Load modules but do not start trading')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build configuration
    config = {
        'trading_mode': args.mode,
        'symbols': args.symbols.split(','),
        'initial_capital': args.capital,
        'risk': {
            'max_position_size_pct': 10.0,
            'max_risk_per_trade_pct': 2.0,
            'max_daily_loss_pct': 5.0,
            'max_drawdown_pct': 20.0,
            'max_leverage': 3.0,
        },
        'features': {
            'enable_alpha_engine': True,
            'enable_msos': True,
            'enable_cognitive_architecture': True,
            'enable_elite_ai': True,
            'enable_event_pipeline': True,
            'enable_self_evolution': True,
        }
    }
    
    # Create runner
    runner = UnifiedSystemRunner(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        runner.request_shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize
        if not await runner.initialize():
            logger.error("Failed to initialize system")
            return 1
        
        # Dry run - just show status and exit
        if args.dry_run:
            logger.info("Dry run complete - exiting")
            return 0
        
        # Start
        if not await runner.start():
            logger.error("Failed to start system")
            return 1
        
        # Run trading loop
        await runner.run_trading_loop()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        await runner.stop()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
