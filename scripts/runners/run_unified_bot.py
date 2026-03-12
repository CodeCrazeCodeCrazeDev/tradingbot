#!/usr/bin/env python
"""
AlphaAlgo Unified Bot Runner

This is the main entry point for running the trading bot.
It uses the new unified architecture with all safety layers.

Usage:
    python run_unified_bot.py --mode paper
    python run_unified_bot.py --mode live
    python run_unified_bot.py --mode backtest
"""

import argparse
import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the unified system
from trading_bot.unified_main import UnifiedTradingSystem, run
from trading_bot.evolution_layer.reward_model import verify_reward_model_integrity, get_reward_model
from trading_bot.human_layer.approval import get_approval_gate
from trading_bot.human_layer.alerts import get_alert_manager, AlertPriority
from trading_bot.human_layer.override import get_manual_override
from trading_bot.telemetry.logging_config import setup_logging, LogLevel
from trading_bot.telemetry.metrics import get_metrics_collector
from trading_bot.telemetry.health import get_health_checker


def print_banner():
    """Print startup banner"""
    banner = """
    ============================================================
    
         ALPHAALGO TRADING BOT
         UNIFIED TRADING SYSTEM v2.0
    
    ============================================================
    
       * Stable API Layer (FROZEN interfaces)
       * Evolution Layer (IMMUTABLE reward model)
       * Human Layer (Approval gates, Emergency stop)
       * Telemetry Layer (Metrics, Logging, Health)
    
    ============================================================
    """
    print(banner)


def print_constraints():
    """Print reward model constraints"""
    rm = get_reward_model()
    constraints = rm.get_constraints_dict()
    
    print("\n    IMMUTABLE CONSTRAINTS (Cannot be changed by bot):")
    print("    -------------------------------------------------")
    print(f"    * Max Risk/Trade:    {constraints['risk']['max_risk_per_trade']:.0%}")
    print(f"    * Max Daily Loss:    {constraints['risk']['max_daily_loss']:.0%}")
    print(f"    * Max Drawdown:      {constraints['risk']['max_drawdown']:.0%}")
    print(f"    * Max Position Size: {constraints['risk']['max_position_size']:.0%}")
    print(f"    * Max Leverage:      {constraints['risk']['max_leverage']:.1f}x")
    print(f"    * Min Sharpe Ratio:  {constraints['performance']['min_sharpe_ratio']:.1f}")
    print(f"    * Min Win Rate:      {constraints['performance']['min_win_rate']:.0%}")
    print(f"    * Human Override:    ALWAYS AVAILABLE")
    print()


def verify_system():
    """Verify system integrity before starting"""
    print("    Verifying system integrity...")
    
    # Check reward model
    if not verify_reward_model_integrity():
        print("    [X] CRITICAL: Reward model integrity check FAILED!")
        print("       The reward model may have been tampered with.")
        print("       Cannot start trading system.")
        return False
    print("    [OK] Reward model integrity verified")
    
    # Check approval gate
    try:
        gate = get_approval_gate()
        print("    [OK] Human approval gate initialized")
    except Exception as e:
        print(f"    [X] Approval gate error: {e}")
        return False
    
    # Check alert manager
    try:
        alerts = get_alert_manager()
        print("    [OK] Alert manager initialized")
    except Exception as e:
        print(f"    [X] Alert manager error: {e}")
        return False
    
    # Check override system
    try:
        override = get_manual_override()
        print("    [OK] Manual override system initialized")
    except Exception as e:
        print(f"    [X] Override system error: {e}")
        return False
    
    print("    [OK] All systems verified\n")
    return True


async def run_bot(config: dict):
    """Run the trading bot"""
    
    # Create and run the unified system
    system = UnifiedTradingSystem(config)
    
    try:
        # Start the system
        await system.start()
        
        # Print status
        status = system.get_status()
        print(f"\n    System Status: {status['status']}")
        print(f"    Trading Mode:  {status['trading_mode']}")
        print(f"    Trading Allowed: {status['trading_allowed']}")
        print(f"    Reward Model Valid: {status['reward_model']['valid']}")
        print()
        
        # Main loop
        print("    Bot is running. Press Ctrl+C to stop.\n")
        
        while True:
            # Check if trading is allowed
            if not status.get('trading_allowed', True):
                print("    [!] Trading paused by human override")
            
            # Update status periodically
            await asyncio.sleep(5)
            status = system.get_status()
            
            # Print periodic status
            metrics = status.get('metrics', {}).get('trading', {})
            print(f"    [{datetime.now().strftime('%H:%M:%S')}] "
                  f"Trades: {metrics.get('trades', {}).get('total', 0)} | "
                  f"P&L: ${metrics.get('pnl', {}).get('net', 0):.2f} | "
                  f"Positions: {metrics.get('positions', {}).get('open', 0)}")
            
    except KeyboardInterrupt:
        print("\n    Shutdown requested...")
    except Exception as e:
        print(f"\n    [X] Error: {e}")
        logging.exception("Bot error")
    finally:
        await system.stop()
        print("    Bot stopped.\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AlphaAlgo Unified Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_unified_bot.py --mode paper
    python run_unified_bot.py --mode live --config config/production.yaml
    python run_unified_bot.py --mode backtest --symbol EURUSD
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['paper', 'live', 'backtest', 'simulation'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='EURUSD',
        help='Trading symbol (default: EURUSD)'
    )
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Logging level (default: info)'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='logs',
        help='Log directory (default: logs)'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Setup logging
    log_level = getattr(LogLevel, args.log_level.upper())
    setup_logging(level=log_level, log_dir=args.log_dir, console=True, file=True)
    
    # Print mode
    print(f"    Mode: {args.mode.upper()}")
    print(f"    Symbol: {args.symbol}")
    print(f"    Log Level: {args.log_level}")
    print()
    
    # Print constraints
    print_constraints()
    
    # Verify system
    if not verify_system():
        print("    System verification failed. Exiting.")
        sys.exit(1)
    
    # Live mode warning
    if args.mode == 'live':
        print("    ============================================================")
        print("    |  WARNING: LIVE TRADING MODE                              |")
        print("    |  This will use REAL MONEY!                               |")
        print("    |  Make sure you understand the risks.                     |")
        print("    ============================================================")
        print()
        confirm = input("    Type 'I UNDERSTAND' to continue: ")
        if confirm != 'I UNDERSTAND':
            print("    Cancelled.")
            sys.exit(0)
        print()
    
    # Build config
    config = {
        'trading_mode': args.mode,
        'symbol': args.symbol,
        'log_dir': args.log_dir,
        'log_level': args.log_level,
    }
    
    # Load config file if provided
    if args.config:
        import yaml
        with open(args.config) as f:
            file_config = yaml.safe_load(f)
            config.update(file_config)
    
    # Run the bot
    try:
        asyncio.run(run_bot(config))
    except KeyboardInterrupt:
        print("\n    Interrupted.")
    
    print("    Goodbye!")


if __name__ == "__main__":
    main()
