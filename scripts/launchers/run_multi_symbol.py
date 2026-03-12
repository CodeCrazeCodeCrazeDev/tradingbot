#!/usr/bin/env python
"""
Multi-Symbol Trading Bot Launcher

This script demonstrates how to run the trading bot with multi-symbol configurations.
"""
import os
import sys
import argparse
from pathlib import Path

def main():
    """Run the trading bot with multi-symbol configurations."""
    parser = argparse.ArgumentParser(description="Multi-Symbol Trading Bot Launcher")
    parser.add_argument(
        "config_type",
        choices=["majors", "crosses", "commodities", "exotics", "diversified"],
        help="Type of multi-symbol configuration to use"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode instead of paper mode"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()
    
    # Map config type to file name
    config_map = {
        "majors": "multi_symbol_majors.yaml",
        "crosses": "multi_symbol_crosses.yaml",
        "commodities": "multi_symbol_commodities.yaml",
        "exotics": "multi_symbol_exotics.yaml",
        "diversified": "multi_symbol_diversified.yaml"
    }
    
    # Build command
    cmd = [sys.executable, "run_bot.py", config_map[args.config_type].split('.')[0]]
    
    # Add optional flags
    if args.live:
        cmd.append("--live")
    if args.debug:
        cmd.append("--debug")
    
    # Run the bot
    print(f"Running multi-symbol trading bot with {args.config_type} configuration...")
    print(f"Command: {' '.join(cmd)}")
    os.execv(sys.executable, cmd)

if __name__ == "__main__":
    main()
