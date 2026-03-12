#!/usr/bin/env python
"""
Run script for Elite Trading System - Survival Edition

This script provides a command-line interface for starting and controlling
the Elite Trading System with enhanced survival capabilities.
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
import yaml
from datetime import datetime
from pathlib import Path

# Import trading system
from trading_bot.core.survival_core import SurvivalCore

# Configure logging
def setup_logging(log_level="INFO", log_file=None):
    """Set up logging configuration"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

# Parse command line arguments
def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Elite Trading System")
    
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="config/survival_config.yaml"
    )
    
    parser.add_argument(
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO"
    )
    
    parser.add_argument(
        "--log-file",
        help="Path to log file",
        default="logs/trading_system.log"
    )
    
    parser.add_argument(
        "--symbols",
        help="Comma-separated list of symbols to trade",
        default=None
    )
    
    parser.add_argument(
        "--timeframes",
        help="Comma-separated list of timeframes to analyze",
        default=None
    )
    
    parser.add_argument(
        "--no-trading",
        help="Disable trading (analysis only)",
        action="store_true"
    )
    
    parser.add_argument(
        "--risk-level",
        help="Risk level (conservative, moderate, aggressive)",
        default="moderate"
    )
    
    parser.add_argument(
        "--emergency-mode",
        help="Start in emergency mode with reduced risk",
        action="store_true"
    )
    
    return parser.parse_args()

# Load configuration
def load_config(config_path):
    """Load configuration from file"""
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

# Main function
async def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger("trading_system")
    
    # Load configuration
    config = load_config(args.config)
    
    # Override configuration with command line arguments
    if args.symbols:
        config["symbols"] = args.symbols.split(",")
    
    if args.timeframes:
        config["timeframes"] = args.timeframes.split(",")
    
    if args.no_trading:
        config["trading_enabled"] = False
        
    # Set risk level
    if args.risk_level:
        if "risk_limits" not in config:
            config["risk_limits"] = {}
            
        if args.risk_level == "conservative":
            config["risk_limits"]["max_position_size"] = 0.01  # 1% max risk per trade
            config["risk_limits"]["max_daily_loss"] = 0.03  # 3% max daily loss
        elif args.risk_level == "aggressive":
            config["risk_limits"]["max_position_size"] = 0.03  # 3% max risk per trade
            config["risk_limits"]["max_daily_loss"] = 0.07  # 7% max daily loss
        else:  # moderate
            config["risk_limits"]["max_position_size"] = 0.02  # 2% max risk per trade
            config["risk_limits"]["max_daily_loss"] = 0.05  # 5% max daily loss
            
    # Emergency mode settings
    if args.emergency_mode:
        logger.warning("Starting in EMERGENCY MODE with reduced risk")
        config["emergency_mode"] = True
        config["risk_limits"]["max_position_size"] = 0.005  # 0.5% max risk per trade
        config["risk_limits"]["max_daily_loss"] = 0.01  # 1% max daily loss
        config["risk_limits"]["max_open_positions"] = 2  # Max 2 open positions
    
    # Create trading system with survival capabilities
    trading_system = SurvivalCore(config)
    
    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    
    def shutdown_handler():
        logger.info("Shutdown signal received")
        asyncio.create_task(trading_system.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_handler)
    
    try:
        # Start trading system
        logger.info("Starting Elite Trading System - Survival Edition")
        await trading_system.start()
        
        # Keep running until stopped
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Trading system cancelled")
    except Exception as e:
        logger.exception(f"Error in trading system: {e}")
    finally:
        # Stop trading system
        logger.info("Stopping Elite Trading System - Survival Edition")
        await trading_system.stop()

# Entry point
if __name__ == "__main__":
    asyncio.run(main())
