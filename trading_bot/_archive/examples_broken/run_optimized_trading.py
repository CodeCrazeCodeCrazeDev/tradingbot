"""
Run Optimized Trading System
Launches the trading system with optimal data flow configuration
"""

import asyncio
import argparse
import logging
import yaml
import os
from datetime import datetime
from pathlib import Path

from trading_bot.trading_engine import TradingEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_trading_system(config_path: str, symbols: list, mode: str = 'paper'):
    pass
    """
    Run the trading system with optimized data flow
    
    Args:
    pass
        config_path: Path to configuration file
        symbols: List of symbols to trade
        mode: Trading mode (paper, live)
    """
    logger.info(f"Starting trading system in {mode} mode with symbols: {symbols}")
    
    # Load configuration
    with open(config_path, 'r') as f:
    pass
        config = yaml.safe_load(f)
    
    # Update configuration based on mode
    if mode == 'live':
    pass
        config['trading']['paper_trading'] = False
        logger.warning("LIVE TRADING MODE ENABLED - REAL MONEY WILL BE USED")
    else:
    pass
        config['trading']['paper_trading'] = True
        logger.info("Paper trading mode enabled - no real money will be used")
    
    # Initialize trading engine
    engine = TradingEngine(config_path)
    await engine.initialize()
    
    try:
    pass
        # Start trading
        await engine.start_trading(symbols)
        
        # Keep running until interrupted
        while True:
    pass
            # Display performance metrics every minute
            metrics = engine._get_system_metrics()
            
            # Log key metrics
            logger.info(f"Active Trades: {metrics['trading']['active_trades']}")
            logger.info(f"P&L: {metrics['trading']['total_pnl']}")
            logger.info(f"Win Rate: {metrics['trading']['win_rate']:.2%}")
            logger.info(f"Pipeline Latency: {metrics['pipeline']['avg_latency']*1000:.2f}ms")
            logger.info(f"Opportunities: {sum(metrics['opportunities']['opportunity_types'].values())}")
            
            # Save metrics to file
            save_metrics(metrics)
            
            # Wait for next update
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
    pass
        logger.info("Trading system interrupted by user")
    except Exception as e:
    pass
        logger.error(f"Error in trading system: {e}", exc_info=True)
    finally:
    pass
        # Cleanup
        await engine.cleanup()
        logger.info("Trading system shutdown complete")

def save_metrics(metrics: dict):
    pass
    """Save metrics to file"""
    # Create metrics directory if needed
    Path("metrics").mkdir(exist_ok=True)
    
    # Save to timestamped file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"metrics/metrics_{timestamp}.yaml"
    
    with open(filename, 'w') as f:
    pass
        yaml.dump(metrics, f)

def optimize_system_resources():
    pass
    """Optimize system resources for best performance"""
    try:
    pass
        import psutil
from typing import List
        
        # Set process priority
        process = psutil.Process(os.getpid())
        process.nice(psutil.HIGH_PRIORITY_CLASS)
        
        # Optimize CPU affinity (use all cores)
        process.cpu_affinity(list(range(psutil.cpu_count())))
        
        logger.info("System resources optimized for high performance")
    pass
        logger.warning(f"Could not optimize system resources: {e}")

def main():
    pass
    parser = argparse.ArgumentParser(description='Run Optimized Trading System')
    parser.add_argument('--config', type=str, default='examples/trading_config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--symbols', type=str, default='EURUSD,GBPUSD,USDJPY',
                        help='Comma-separated list of symbols to trade')
    parser.add_argument('--mode', type=str, choices=['paper', 'live'], default='paper',
                        help='Trading mode (paper or live)')
    
    args = parser.parse_args()
    
    # Optimize system resources
    optimize_system_resources()
    
    # Run trading system
    asyncio.run(run_trading_system(
        args.config,
        args.symbols.split(','),
        args.mode
    ))

if __name__ == "__main__":
    pass
    main()
