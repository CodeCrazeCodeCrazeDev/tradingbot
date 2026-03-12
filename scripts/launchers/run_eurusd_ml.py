#!/usr/bin/env python
"""
Run the trading bot with EURUSD H1 ML-enhanced configuration.
"""
import os
import sys
import yaml
import argparse
from pathlib import Path

def main():
    """Run the trading bot with the EURUSD H1 ML configuration."""
    parser = argparse.ArgumentParser(description="Run the trading bot with EURUSD H1 ML configuration")
    parser.add_argument("--live", action="store_true", help="Run in live mode instead of paper mode")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = Path(__file__).parent / "config" / "eurusd_h1_ml.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Override mode if --live is specified
    if args.live:
        config["mode"] = "live"
    
    # Define supported arguments
    supported_args = [
        "symbol", "timeframe", "bars", "mode", "log_level", "profile",
        "use_ml", "use_transformer", "use_rl", "market_regime", "execution_algo",
        "track_emotions", "sentiment_analysis", "news_api_key", "news_data_dir",
        "strategy_research", "fundamental_analysis", "fred_api_key", "research_data_dir",
        "order_flow", "quantum_blockchain", "adaptive_mode", "self_improve",
        "internet_access", "api_source", "websocket_feed", "news_scraping",
        "cache_dir", "api_keys_file"
    ]
    
    # Build the command line arguments
    cmd_args = []
    for key, value in config.items():
        if key not in supported_args:
            continue
            
        if isinstance(value, bool):
            if value:
                cmd_args.append(f"--{key.replace('_', '-')}")
        elif isinstance(value, (str, int, float)):
            cmd_args.append(f"--{key.replace('_', '-')}")
            cmd_args.append(str(value))
        elif isinstance(value, list) and key == "watchlist":
            # Skip watchlist as it's handled by the main.py directly
            pass
    
    # Run the bot
    cmd = [sys.executable, "main.py"] + cmd_args
    print(f"Running command: {' '.join(cmd)}")
    os.execv(sys.executable, cmd)

if __name__ == "__main__":
    main()
