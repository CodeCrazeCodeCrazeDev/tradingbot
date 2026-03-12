#!/usr/bin/env python3
"""
Ultimate Production Trading System - Main Runner
=================================================

This is the ONE-CLICK entry point for the absolute best trading system.

Usage:
    python run_ultimate_production.py                    # Paper trading (default)
    python run_ultimate_production.py --mode live        # Live trading
    python run_ultimate_production.py --mode backtest    # Backtesting
    python run_ultimate_production.py --symbols EURUSD GBPUSD  # Custom symbols
    python run_ultimate_production.py --capital 50000    # Custom capital

Features:
- 10 proven profitable strategies
- Real-time ML predictions with transformer + ensemble
- Bulletproof risk management
- Smart order execution
- Comprehensive monitoring
- Self-learning system

Author: Elite Trading Bot Team
"""

import asyncio
import argparse
import logging
import sys
import os
import signal
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'ultimate_production_{datetime.now().strftime("%Y%m%d")}.log'),
    ]
)

logger = logging.getLogger('UltimateProduction')


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██╗   ██╗██╗  ████████╗██╗███╗   ███╗ █████╗ ████████╗███████╗           ║
║     ██║   ██║██║  ╚══██╔══╝██║████╗ ████║██╔══██╗╚══██╔══╝██╔════╝           ║
║     ██║   ██║██║     ██║   ██║██╔████╔██║███████║   ██║   █████╗             ║
║     ██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝             ║
║     ╚██████╔╝███████╗██║   ██║██║ ╚═╝ ██║██║  ██║   ██║   ███████╗           ║
║      ╚═════╝ ╚══════╝╚═╝   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝           ║
║                                                                              ║
║     ██████╗ ██████╗  ██████╗ ██████╗ ██╗   ██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗ ║
║     ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██║   ██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║ ║
║     ██████╔╝██████╔╝██║   ██║██║  ██║██║   ██║██║        ██║   ██║██║   ██║██╔██╗ ██║ ║
║     ██╔═══╝ ██╔══██╗██║   ██║██║  ██║██║   ██║██║        ██║   ██║██║   ██║██║╚██╗██║ ║
║     ██║     ██║  ██║╚██████╔╝██████╔╝╚██████╔╝╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║ ║
║     ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ║
║                                                                              ║
║                    The Absolute Best Trading System                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config(config: dict):
    """Print configuration summary"""
    print("\n" + "="*60)
    print("CONFIGURATION")
    print("="*60)
    print(f"  Mode:           {config['mode'].upper()}")
    print(f"  Capital:        ${config['initial_capital']:,.2f}")
    print(f"  Symbols:        {', '.join(config['symbols'])}")
    print(f"  Max Positions:  {config['max_positions']}")
    print(f"  Max Daily Loss: {config['max_daily_loss']:.1%}")
    print(f"  Max Drawdown:   {config['max_drawdown']:.1%}")
    print("="*60 + "\n")


async def run_trading_system(config: dict):
    """Run the trading system"""
    from trading_bot.ultimate_production import UltimateProductionEngine
    
    # Create engine
    engine = UltimateProductionEngine(config)
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize
        logger.info("Initializing Ultimate Production Engine...")
        success = await engine.initialize()
        
        if not success:
            logger.error("Failed to initialize engine")
            return 1
        
        # Start trading
        logger.info("Starting trading system...")
        await engine.start()
        
        # Print initial status
        status = engine.get_status()
        print("\n" + "="*60)
        print("SYSTEM STATUS")
        print("="*60)
        for key, value in status.items():
            print(f"  {key}: {value}")
        print("="*60 + "\n")
        
        logger.info("Trading system is now running. Press Ctrl+C to stop.")
        
        # Run until shutdown
        while not shutdown_event.is_set():
            await asyncio.sleep(1)
            
            # Periodic status update
            if datetime.now().second == 0:  # Every minute
                status = engine.get_status()
                logger.info(
                    f"Status: {status['state']} | "
                    f"Capital: {status['capital']:.2f} | "
                    f"Positions: {status['open_positions']} | "
                    f"P&L: {status['total_pnl']}"
                )
        
    except Exception as e:
        logger.error(f"Error running trading system: {e}", exc_info=True)
        return 1
    
    finally:
        # Graceful shutdown
        logger.info("Shutting down trading system...")
        await engine.stop()
        
        # Print final status
        status = engine.get_status()
        print("\n" + "="*60)
        print("FINAL STATUS")
        print("="*60)
        for key, value in status.items():
            print(f"  {key}: {value}")
        print("="*60 + "\n")
        
        logger.info("Trading system stopped successfully")
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Ultimate Production Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ultimate_production.py                         # Paper trading
  python run_ultimate_production.py --mode live             # Live trading
  python run_ultimate_production.py --symbols EURUSD GBPUSD # Custom symbols
  python run_ultimate_production.py --capital 50000         # Custom capital
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['paper', 'live', 'backtest', 'shadow'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    
    parser.add_argument(
        '--symbols', '-s',
        nargs='+',
        default=['EURUSD', 'GBPUSD', 'USDJPY'],
        help='Symbols to trade (default: EURUSD GBPUSD USDJPY)'
    )
    
    parser.add_argument(
        '--capital', '-c',
        type=float,
        default=10000.0,
        help='Initial capital (default: 10000)'
    )
    
    parser.add_argument(
        '--max-positions', '-p',
        type=int,
        default=5,
        help='Maximum concurrent positions (default: 5)'
    )
    
    parser.add_argument(
        '--max-daily-loss',
        type=float,
        default=0.02,
        help='Maximum daily loss as fraction (default: 0.02 = 2%%)'
    )
    
    parser.add_argument(
        '--max-drawdown',
        type=float,
        default=0.10,
        help='Maximum drawdown as fraction (default: 0.10 = 10%%)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Skip startup banner'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print banner
    if not args.no_banner:
        print_banner()
    
    # Build configuration
    config = {
        'mode': args.mode,
        'symbols': args.symbols,
        'initial_capital': args.capital,
        'max_positions': args.max_positions,
        'max_daily_loss': args.max_daily_loss,
        'max_drawdown': args.max_drawdown,
        'data_dir': 'ultimate_production_data',
        
        # Strategy configuration
        'strategy_config': {
            'trend_following': {'enabled': True, 'weight': 1.2},
            'mean_reversion': {'enabled': True, 'weight': 1.0},
            'momentum_breakout': {'enabled': True, 'weight': 1.1},
            'support_resistance': {'enabled': True, 'weight': 0.9},
            'vwap_reversion': {'enabled': True, 'weight': 0.8},
            'order_flow': {'enabled': True, 'weight': 1.0},
            'multi_timeframe': {'enabled': True, 'weight': 1.3},
            'volatility_breakout': {'enabled': True, 'weight': 0.9},
            'range_trading': {'enabled': True, 'weight': 0.7},
            'sentiment_fade': {'enabled': True, 'weight': 0.8},
        },
        
        # ML configuration
        'ml_config': {
            'sequence_length': 20,
            'hidden_dim': 64,
            'horizons': ['1h', '4h', '1d'],
        },
        
        # Risk configuration
        'risk_config': {
            'limits': {
                'max_position_size': 0.02,
                'max_portfolio_risk': 0.06,
                'max_daily_loss': args.max_daily_loss,
                'max_drawdown': args.max_drawdown,
                'max_positions': args.max_positions,
                'min_risk_reward': 1.5,
            },
            'position_sizing': {
                'method': 'volatility_adjusted',
                'base_risk': 0.02,
            },
        },
        
        # Execution configuration
        'execution_config': {
            'mode': args.mode,
            'default_slices': 10,
            'show_ratio': 0.1,
        },
        
        # Monitor configuration
        'monitor_config': {
            'health_check_interval': 30,
            'max_drawdown_warning': 0.05,
            'max_drawdown_critical': 0.10,
        },
        
        # Learning configuration
        'learning_config': {
            'data_dir': 'learning_data',
        },
    }
    
    # Print configuration
    print_config(config)
    
    # Confirm live trading
    if args.mode == 'live':
        print("\n" + "!"*60)
        print("WARNING: LIVE TRADING MODE")
        print("This will execute REAL trades with REAL money!")
        print("!"*60)
        
        confirm = input("\nType 'YES' to confirm live trading: ")
        if confirm != 'YES':
            print("Live trading cancelled.")
            return 1
    
    # Run the system
    try:
        return asyncio.run(run_trading_system(config))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
