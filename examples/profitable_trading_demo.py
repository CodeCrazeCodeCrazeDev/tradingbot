"""
Profitable Trading Demo using Optimized Data Pipeline
"""

import asyncio
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Any
from trading_bot.examples.optimized_trading_example import OptimizedTradingSystem

async def run_trading_demo():
    # Load optimized configuration
    with open('examples/trading_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize trading system
    system = OptimizedTradingSystem(config)
    await system.initialize()
    
    # Define trading symbols
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    try:
        # Start trading
        await system.start_trading(symbols)
        
        # Monitor performance
        while True:
            # Get system metrics
            metrics = system.get_performance_metrics()
            
            # Log performance
            print("\n=== System Performance ===")
            print(f"Pipeline Latency: {metrics['data_pipeline']['stream']['average_processing_time']}ms")
            print(f"Signal Quality: {metrics['analysis']['signals']['performance']}")
            print(f"Active Trades: {metrics['trading']['active_trades']}")
            
            # Monitor profitability
            if 'trading' in metrics and 'total_pnl' in metrics['trading']:
                print(f"Total P&L: {metrics['trading']['total_pnl']}")
                print(f"Win Rate: {metrics['trading']['win_rate']:.2%}")
                print(f"Sharpe Ratio: {metrics['trading']['sharpe_ratio']:.2f}")
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\nShutting down trading system...")
        await system.cleanup()

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run trading system
    asyncio.run(run_trading_demo())

if __name__ == "__main__":
    main()
