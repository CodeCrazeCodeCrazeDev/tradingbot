#!/usr/bin/env python
"""
Advanced Trading Bot Launcher

This script provides an easy way to launch the trading bot with different configurations.
"""
import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional

def load_config(config_name: str) -> Dict:
    """Load a configuration file by name."""
    config_path = Path(__file__).parent / "config" / f"{config_name}.yaml"
    if not config_path.exists():
        raise ValueError(f"Configuration '{config_name}' not found")
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_available_configs() -> List[str]:
    """Get list of available configurations."""
    config_dir = Path(__file__).parent / "config"
    return [f.stem for f in config_dir.glob("*.yaml")]

def build_command_args(config: Dict, supported_args: List[str]) -> List[str]:
    """Build command line arguments from configuration."""
    cmd_args = []
    
    # Handle special case for multi-symbol configuration
    if "symbols" in config and isinstance(config["symbols"], list) and len(config["symbols"]) > 0:
        # Use the first symbol as the primary symbol
        cmd_args.append("--symbol")
        cmd_args.append(config["symbols"][0])
        
        # Add additional symbols if the bot supports it
        if "additional_symbols" in supported_args:
            cmd_args.append("--additional-symbols")
            additional_symbols = ",".join(config["symbols"][1:]) if len(config["symbols"]) > 1 else ""
            cmd_args.append(additional_symbols)
    elif "symbol" in config:
        # Single symbol configuration
        cmd_args.append("--symbol")
        cmd_args.append(config["symbol"])
    
    # Process other arguments
    for key, value in config.items():
        # Skip already processed keys
        if key in ["symbol", "symbols", "watchlist", "risk_allocation"]:
            continue
            
        if key not in supported_args:
            continue
            
        if isinstance(value, bool):
            if value:
                cmd_args.append(f"--{key.replace('_', '-')}")
        elif isinstance(value, (str, int, float)):
            cmd_args.append(f"--{key.replace('_', '-')}")
            cmd_args.append(str(value))
            
    return cmd_args

def main():
    """Run the trading bot with the specified configuration."""
    # Define supported arguments
    supported_args = [
        "symbol", "timeframe", "bars", "mode", "log_level", "profile",
        "use_ml", "use_transformer", "use_rl", "market_regime", "execution_algo",
        "track_emotions", "sentiment_analysis", "news_api_key", "news_data_dir",
        "strategy_research", "fundamental_analysis", "fred_api_key", "research_data_dir",
        "order_flow", "quantum_blockchain", "adaptive_mode", "self_improve",
        "internet_access", "api_source", "websocket_feed", "news_scraping",
        "cache_dir", "api_keys_file", "additional_symbols", "manage_correlations",
        "max_correlated_exposure"
    ]
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Advanced Trading Bot Launcher")
    parser.add_argument(
        "config",
        choices=get_available_configs(),
        help="Configuration to use"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode instead of paper mode"
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable performance profiling"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override mode if --live is specified
        if args.live:
            config["mode"] = "live"
            
        # Add profiling if requested
        if args.profile:
            config["profile"] = True
            
        # Add debug logging if requested
        if args.debug:
            config["log_level"] = "DEBUG"
        
        # Build command line arguments
        cmd_args = build_command_args(config, supported_args)
        
        # Run the bot
        cmd = [sys.executable, "main.py"] + cmd_args
        print(f"Running trading bot with {args.config} configuration...")
        print(f"Command: {' '.join(cmd)}")
        os.execv(sys.executable, cmd)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
