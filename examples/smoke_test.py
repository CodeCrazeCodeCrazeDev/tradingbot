"""
Smoke Test for Trading System
Validates end-to-end flow with synthetic data
"""

import asyncio
import logging
import yaml
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Any

from trading_bot.trading_engine import TradingEngine
from trading_bot.database.data_normalizer import DataNormalizer
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("smoke_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SmokeTest:
    """
    Smoke test for trading system with synthetic data
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.engine = None
        self.test_symbols = ['TEST1', 'TEST2']
        self.test_results = {
            'data_flow': [],
            'signals': [],
            'executions': [],
            'latency': []
        }
    
    async def run(self, duration: int = 60):
        """Run smoke test for specified duration (seconds)"""
        logger.info(f"Starting smoke test with symbols: {self.test_symbols}")
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update config for testing
        config['data_pipeline']['market_stream']['use_zmq'] = False  # Use in-process queues
        config['data_pipeline']['database']['use_redis'] = False  # Use in-memory cache
        
        # Initialize trading engine
        self.engine = TradingEngine(self.config_path)
        await self.engine.initialize()
        
        # Start trading
        await self.engine.start_trading(self.test_symbols)
        
        # Generate synthetic data
        data_task = asyncio.create_task(self._generate_synthetic_data(duration))
        
        # Monitor system
        monitor_task = asyncio.create_task(self._monitor_system(duration))
        
        # Wait for tasks to complete
        await asyncio.gather(data_task, monitor_task)
        
        # Generate report
        self._generate_report()
        
        # Cleanup
        await self.engine.cleanup()
        logger.info("Smoke test completed")
    
    async def _generate_synthetic_data(self, duration: int):
        """Generate synthetic market data"""
        logger.info("Generating synthetic market data")
        
        start_time = datetime.now()
        tick_interval = 0.1  # 100ms between ticks
        
        # Base prices for test symbols
        base_prices = {
            'TEST1': 1.2000,
            'TEST2': 100.50
        }
        
        # Generate data until duration is reached
        while (datetime.now() - start_time).total_seconds() < duration:
            for symbol in self.test_symbols:
                # Generate random price movement
                price_change = random.uniform(-0.0010, 0.0010)
                base_prices[symbol] += price_change
                
                # Create synthetic tick
                tick = {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'bid': base_prices[symbol] - 0.0001,
                    'ask': base_prices[symbol] + 0.0001,
                    'volume': random.randint(1, 100)
                }
                
                # Normalize data
                tick = DataNormalizer.normalize_tick_data(tick)
                
                # Push to market stream
                await self.engine.market_stream.push_data(f"{symbol}_market", tick)
                
                # Record for validation
                self.test_results['data_flow'].append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'price': tick['price'],
                    'volume': tick['volume']
                })
            
            # Wait for next tick
            await asyncio.sleep(tick_interval)
    
    async def _monitor_system(self, duration: int):
        """Monitor system metrics and performance"""
        logger.info("Monitoring system performance")
        
        start_time = datetime.now()
        check_interval = 1.0  # Check every second
        
        while (datetime.now() - start_time).total_seconds() < duration:
            # Get system metrics
            metrics = self.engine._get_system_metrics()
            
            # Record latency
            if 'pipeline' in metrics and 'avg_latency' in metrics['pipeline']:
                self.test_results['latency'].append({
                    'timestamp': datetime.now(),
                    'latency_ms': metrics['pipeline']['avg_latency'] * 1000
                })
            
            # Record signals
            if 'signals' in metrics:
                signal_metrics = metrics.get('signals', {})
                self.test_results['signals'].append({
                    'timestamp': datetime.now(),
                    'count': signal_metrics.get('total_signals', 0)
                })
            
            # Record executions
            if 'trading' in metrics:
                trading_metrics = metrics.get('trading', {})
                self.test_results['executions'].append({
                    'timestamp': datetime.now(),
                    'trades': trading_metrics.get('trades', 0),
                    'active_trades': trading_metrics.get('active_trades', 0)
                })
            
            # Log progress
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Test progress: {elapsed:.1f}/{duration}s - " +
                      f"Data points: {len(self.test_results['data_flow'])}, " +
                      f"Signals: {self.test_results['signals'][-1]['count'] if self.test_results['signals'] else 0}, " +
                      f"Trades: {self.test_results['executions'][-1]['trades'] if self.test_results['executions'] else 0}")
            
            # Wait for next check
            await asyncio.sleep(check_interval)
    
    def _generate_report(self):
        """Generate test report"""
        logger.info("Generating test report")
        
        # Create output directory
        Path("test_reports").mkdir(exist_ok=True)
        
        # Save raw data
        with open("test_reports/smoke_test_results.json", 'w') as f:
            json.dump(self.test_results, f, default=str, indent=2)
        
        # Convert to DataFrames
        df_data = pd.DataFrame(self.test_results['data_flow'])
        df_signals = pd.DataFrame(self.test_results['signals'])
        df_executions = pd.DataFrame(self.test_results['executions'])
        df_latency = pd.DataFrame(self.test_results['latency'])
        
        # Generate plots
        self._generate_plots(df_data, df_signals, df_executions, df_latency)
        
        # Generate summary
        self._generate_summary(df_data, df_signals, df_executions, df_latency)
    
    def _generate_plots(self, df_data, df_signals, df_executions, df_latency):
        """Generate performance plots"""
        # Create figure with subplots
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
        
        # Plot 1: Price and Volume
        if not df_data.empty:
            ax1 = axs[0]
            for symbol in self.test_symbols:
                symbol_data = df_data[df_data['symbol'] == symbol]
                if not symbol_data.empty:
                    ax1.plot(symbol_data['timestamp'], symbol_data['price'], label=f"{symbol} Price")
            
            ax1.set_title('Synthetic Price Data')
            ax1.set_ylabel('Price')
            ax1.grid(True)
            ax1.legend()
        
        # Plot 2: Signals and Executions
        ax2 = axs[1]
        
        if not df_signals.empty:
            ax2.plot(df_signals['timestamp'], df_signals['count'], 'g-', label='Signals')
        
        if not df_executions.empty:
            ax2.plot(df_executions['timestamp'], df_executions['trades'], 'r-', label='Trades')
            ax2.plot(df_executions['timestamp'], df_executions['active_trades'], 'b--', label='Active Trades')
        
        ax2.set_title('Signals and Executions')
        ax2.set_ylabel('Count')
        ax2.grid(True)
        ax2.legend()
        
        # Plot 3: Latency
        if not df_latency.empty:
            ax3 = axs[2]
            ax3.plot(df_latency['timestamp'], df_latency['latency_ms'], 'm-', label='Pipeline Latency')
            ax3.set_title('Processing Latency')
            ax3.set_ylabel('Latency (ms)')
            ax3.set_xlabel('Time')
            ax3.grid(True)
            ax3.legend()
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig("test_reports/smoke_test_plots.png")
    
    def _generate_summary(self, df_data, df_signals, df_executions, df_latency):
        """Generate summary report"""
        summary = {
            'test_duration': f"{(df_data['timestamp'].max() - df_data['timestamp'].min()).total_seconds():.1f}s" if not df_data.empty else "N/A",
            'data_points': len(df_data),
            'data_rate': f"{len(df_data) / (df_data['timestamp'].max() - df_data['timestamp'].min()).total_seconds():.1f} points/sec" if not df_data.empty else "N/A",
            'signals_generated': df_signals['count'].max() if not df_signals.empty else 0,
            'trades_executed': df_executions['trades'].max() if not df_executions.empty else 0,
            'signal_to_trade_ratio': f"{df_executions['trades'].max() / df_signals['count'].max():.2f}" if not df_signals.empty and not df_executions.empty and df_signals['count'].max() > 0 else "N/A",
            'avg_latency': f"{df_latency['latency_ms'].mean():.2f} ms" if not df_latency.empty else "N/A",
            'max_latency': f"{df_latency['latency_ms'].max():.2f} ms" if not df_latency.empty else "N/A",
            'data_flow_validation': "PASS" if len(df_data) > 0 else "FAIL",
            'signal_generation_validation': "PASS" if not df_signals.empty and df_signals['count'].max() > 0 else "FAIL",
            'execution_validation': "PASS" if not df_executions.empty and df_executions['trades'].max() > 0 else "FAIL",
            'latency_validation': "PASS" if not df_latency.empty and df_latency['latency_ms'].mean() < 10 else "FAIL"  # Fail if avg latency > 10ms
        }
        
        # Overall test result
        summary['overall_result'] = "PASS" if all(v == "PASS" for k, v in summary.items() if k.endswith('_validation')) else "FAIL"
        
        # Save summary
        with open("test_reports/smoke_test_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("SMOKE TEST SUMMARY")
        logger.info("="*50)
        for key, value in summary.items():
            logger.info(f"{key.replace('_', ' ').title()}: {value}")
        logger.info("="*50)

async def main():
    # Run smoke test
    test = SmokeTest('examples/trading_config.yaml')
    await test.run(duration=30)  # Run for 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
