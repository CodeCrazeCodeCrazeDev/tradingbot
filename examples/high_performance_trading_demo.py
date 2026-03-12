"""
High-Performance Trading Demo
Demonstrates the optimized data pipeline with best flow for profitable trading
"""

import asyncio
import logging
import yaml
import json
import argparse
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from trading_bot.trading_engine import TradingEngine
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_demo.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingDemo:
    """
    Demo application for high-performance trading
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.engine = None
        self.performance_data = []
    
    async def run(self, symbols: list, duration: int = 3600):
        """Run trading demo for specified duration (seconds)"""
        logger.info(f"Starting trading demo with symbols: {symbols}")
        
        # Initialize trading engine
        self.engine = TradingEngine(self.config_path)
        await self.engine.initialize()
        
        # Start trading
        await self.engine.start_trading(symbols)
        
        # Monitor performance
        start_time = datetime.now()
        try:
            while (datetime.now() - start_time).total_seconds() < duration:
                # Get system metrics
                metrics = self.engine._get_system_metrics()
                
                # Store for analysis
                self.performance_data.append({
                    'timestamp': datetime.now(),
                    **metrics
                })
                
                # Display key metrics
                self._display_metrics(metrics)
                
                # Wait for next update
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Trading demo interrupted by user")
        
        # Cleanup
        await self.engine.cleanup()
        
        # Generate performance report
        self._generate_performance_report()
    
    def _display_metrics(self, metrics: dict):
        """Display key performance metrics"""
        trading = metrics.get('trading', {})
        pipeline = metrics.get('pipeline', {})
        
        print("\n" + "="*50)
        print("TRADING PERFORMANCE")
        print(f"Trades: {trading.get('trades', 0)}")
        print(f"Win Rate: {trading.get('win_rate', 0):.2%}")
        print(f"Total P&L: {trading.get('total_pnl', 0):.2f}")
        print(f"Sharpe Ratio: {trading.get('sharpe_ratio', 0):.2f}")
        
        print("\nDATA PIPELINE PERFORMANCE")
        print(f"Avg Latency: {pipeline.get('avg_latency', 0)*1000:.2f} ms")
        print(f"Throughput: {pipeline.get('throughput', 0):.2f} ops/sec")
        
        opportunities = metrics.get('opportunities', {})
        print("\nOPPORTUNITY DETECTION")
        print(f"Momentum: {opportunities.get('opportunity_types', {}).get('momentum', 0)}")
        print(f"Volatility: {opportunities.get('opportunity_types', {}).get('volatility', 0)}")
        print(f"Flow: {opportunities.get('opportunity_types', {}).get('flow', 0)}")
        
        print("="*50)
    
    def _generate_performance_report(self):
        """Generate performance report from collected data"""
        if not self.performance_data:
            logger.warning("No performance data collected")
            return
        
        # Create output directory
        Path("reports").mkdir(exist_ok=True)
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': d['timestamp'],
                'trades': d.get('trading', {}).get('trades', 0),
                'win_rate': d.get('trading', {}).get('win_rate', 0),
                'pnl': d.get('trading', {}).get('total_pnl', 0),
                'latency_ms': d.get('pipeline', {}).get('avg_latency', 0) * 1000,
                'throughput': d.get('pipeline', {}).get('throughput', 0),
                'opportunities': sum(d.get('opportunities', {}).get('opportunity_types', {}).values())
            }
            for d in self.performance_data
        ])
        
        # Save raw data
        df.to_csv("reports/performance_data.csv", index=False)
        
        # Generate plots
        self._plot_performance(df)
        
        logger.info("Performance report generated in 'reports' directory")
    
    def _plot_performance(self, df: pd.DataFrame):
        """Generate performance plots"""
        # Create figure with subplots
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
        
        # Plot 1: Trading Performance
        ax1 = axs[0]
        ax1.plot(df['timestamp'], df['pnl'], 'b-', label='Total P&L')
        ax1.set_title('Trading Performance')
        ax1.set_ylabel('P&L')
        ax1.grid(True)
        
        # Add win rate on secondary axis
        ax1b = ax1.twinx()
        ax1b.plot(df['timestamp'], df['win_rate'], 'r--', label='Win Rate')
        ax1b.set_ylabel('Win Rate')
        ax1b.set_ylim(0, 1)
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1b.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Plot 2: Pipeline Performance
        ax2 = axs[1]
        ax2.plot(df['timestamp'], df['latency_ms'], 'g-', label='Latency (ms)')
        ax2.set_title('Data Pipeline Performance')
        ax2.set_ylabel('Latency (ms)')
        ax2.grid(True)
        
        # Add throughput on secondary axis
        ax2b = ax2.twinx()
        ax2b.plot(df['timestamp'], df['throughput'], 'm--', label='Throughput (ops/sec)')
        ax2b.set_ylabel('Throughput (ops/sec)')
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2b.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Plot 3: Opportunities and Trades
        ax3 = axs[2]
        ax3.plot(df['timestamp'], df['opportunities'], 'c-', label='Opportunities')
        ax3.set_title('Opportunities and Trades')
        ax3.set_ylabel('Count')
        ax3.set_xlabel('Time')
        ax3.grid(True)
        
        # Add trades on same axis
        ax3.plot(df['timestamp'], df['trades'], 'y-', label='Trades')
        ax3.legend(loc='upper left')
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig("reports/performance_charts.png")
        
        # Generate additional analytics
        if len(df) > 1:
            # Calculate key metrics
            latency_stats = {
                'min': df['latency_ms'].min(),
                'max': df['latency_ms'].max(),
                'avg': df['latency_ms'].mean(),
                'p95': df['latency_ms'].quantile(0.95)
            }
            
            # Calculate opportunity to trade conversion
            if df['opportunities'].max() > 0:
                conversion_rate = df['trades'].iloc[-1] / df['opportunities'].iloc[-1]
            else:
                conversion_rate = 0
            
            # Save analytics
            analytics = {
                'latency_stats': latency_stats,
                'final_win_rate': df['win_rate'].iloc[-1],
                'final_pnl': df['pnl'].iloc[-1],
                'opportunity_to_trade_conversion': conversion_rate,
                'avg_throughput': df['throughput'].mean()
            }
            
            with open("reports/performance_analytics.json", 'w') as f:
                json.dump(analytics, f, indent=2)

async def main():
    parser = argparse.ArgumentParser(description='High-Performance Trading Demo')
    parser.add_argument('--config', type=str, default='examples/trading_config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--symbols', type=str, default='EURUSD,GBPUSD,USDJPY',
                        help='Comma-separated list of symbols to trade')
    parser.add_argument('--duration', type=int, default=3600,
                        help='Duration of demo in seconds')
    
    args = parser.parse_args()
    
    # Run demo
    demo = TradingDemo(args.config)
    await demo.run(args.symbols.split(','), args.duration)

if __name__ == "__main__":
    asyncio.run(main())
