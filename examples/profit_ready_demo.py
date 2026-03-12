"""
Profit-Ready Trading System Demo
Demonstrates the complete optimized trading system with all enhancements
"""

import asyncio
import logging
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Import trading engine
from trading_bot.trading_engine import TradingEngine

# Import data models and validation
from trading_bot.models.data_models import MarketTick, OHLCBar, TradingSignal
from trading_bot.models.schema_integration import SchemaValidator

# Import performance tracking
from trading_bot.analytics.signal_performance_tracker import SignalPerformanceTracker

# Import backtest parity
from trading_bot.analytics.backtest_parity import BacktestParityAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"profit_ready_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ProfitReadyDemo:
    pass
    """
    Comprehensive demo of the profit-ready trading system
    """
    
    def __init__(self, config_path: str):
    pass
        self.config_path = config_path
        
        # Load configuration
        with open(config_path, 'r') as f:
    pass
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.engine = None
        self.performance_tracker = SignalPerformanceTracker(self.config)
        self.parity_analyzer = BacktestParityAnalyzer(self.config)
        
        # Test symbols
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        # Create directories
        Path("reports").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        
        logger.info("Profit-ready demo initialized")
    
    async def run_complete_demo(self):
    pass
        """Run complete demonstration of the profit-ready system"""
        logger.info("Starting profit-ready trading system demo")
        
        # Step 1: Run smoke test
        await self._run_smoke_test()
        
        # Step 2: Run backtest
        await self._run_backtest()
        
        # Step 3: Run live trading simulation
        await self._run_live_simulation()
        
        # Step 4: Compare backtest and live results
        await self._analyze_parity()
        
        # Step 5: Generate performance report
        self._generate_performance_report()
        
        logger.info("Profit-ready demo completed")
    
    async def _run_smoke_test(self):
    pass
        """Run smoke test to validate system functionality"""
        logger.info("Running smoke test...")
        
        # Import smoke test
        from examples.smoke_test import SmokeTest
from typing import Set
import numpy
        
        # Run smoke test
        test = SmokeTest(self.config_path)
        await test.run(duration=15)  # Short duration for demo
        
        logger.info("Smoke test completed")
    
    async def _run_backtest(self):
    pass
        """Run backtest on historical data"""
        logger.info("Running backtest...")
        
        # Initialize trading engine
        self.engine = TradingEngine(self.config_path)
        await self.engine.initialize()
        
        # Set up backtest period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # 1 week of data
        
        # Run backtest for each symbol
        for symbol in self.symbols:
    pass
            # Run backtest using parity analyzer
            await self.parity_analyzer.run_backtest(
                symbol, 
                start_date, 
                end_date, 
                self.engine.analytics
            )
            
            # Track performance of backtest trades
            for trade in self.parity_analyzer.backtest_trades.get(symbol, []):
    pass
                self.performance_tracker.track_signal(
                    trade.get('signal_type', 'unknown'),
                    trade
                )
        
        # Save backtest performance data
        self.performance_tracker.save_performance_data()
        
        logger.info("Backtest completed")
    
    async def _run_live_simulation(self):
    pass
        """Run live trading simulation"""
        logger.info("Running live trading simulation...")
        
        # Initialize trading engine if needed
        if not self.engine:
    pass
            self.engine = TradingEngine(self.config_path)
            await self.engine.initialize()
        
        # Start trading
        await self.engine.start_trading(self.symbols)
        
        # Generate synthetic market data
        await self._generate_synthetic_data(duration=30)  # 30 seconds of data
        
        # Cleanup
        await self.engine.cleanup()
        
        logger.info("Live simulation completed")
    
    async def _generate_synthetic_data(self, duration: int):
    pass
        """Generate synthetic market data for live simulation"""
        logger.info(f"Generating synthetic market data for {duration} seconds")
        
        start_time = datetime.now()
        tick_interval = 0.1  # 100ms between ticks
        
        # Base prices for test symbols
        base_prices = {
            'EURUSD': 1.2000,
            'GBPUSD': 1.3800,
            'USDJPY': 110.50
        }
        
        # Generate data until duration is reached
        while (datetime.now() - start_time).total_seconds() < duration:
    pass
            for symbol in self.symbols:
    pass
                # Generate random price movement
                price_change = np.random.normal(0, 0.0001)
                base_prices[symbol] += price_change
                
                # Create synthetic tick
                tick_data = {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'bid': base_prices[symbol] - 0.0001,
                    'ask': base_prices[symbol] + 0.0001,
                    'volume': np.random.randint(1, 100)
                }
                
                # Validate tick data
                tick = SchemaValidator.validate_market_tick(tick_data)
                
                # Push to market stream
                await self.engine.market_stream.push_data(f"{symbol}_market", tick)
                
                # Check for signals and trades
                self._check_for_signals_and_trades(symbol)
            
            # Wait for next tick
            await asyncio.sleep(tick_interval)
    
    def _check_for_signals_and_trades(self, symbol: str):
    pass
        """Check for signals and trades for a symbol"""
        # Check for signals
        if symbol in self.engine.signal_processor.active_signals:
    pass
            for signal_id, signal in self.engine.signal_processor.active_signals[symbol].items():
    pass
                # Record signal for parity analysis
                self.parity_analyzer.record_live_signal(signal)
        
        # Check for trades
        if symbol in self.engine.active_trades:
    pass
            for trade_id, trade in self.engine.active_trades.items():
    pass
                if trade['order']['symbol'] == symbol and trade['status'] == 'closed':
    pass
                    # Record trade for parity analysis
                    self.parity_analyzer.record_live_trade(trade)
                    
                    # Track performance
                    self.performance_tracker.track_signal(
                        trade['signal'].signal_type,
                        {
                            'profit': trade['pnl'],
                            'success': trade['pnl'] > 0
                        }
                    )
    
    async def _analyze_parity(self):
    pass
        """Analyze parity between backtest and live results"""
        logger.info("Analyzing backtest-live parity...")
        
        # Generate parity report
        self.parity_analyzer.generate_parity_report(self.symbols)
        
        logger.info("Parity analysis completed")
    
    def _generate_performance_report(self):
    pass
        """Generate comprehensive performance report"""
        logger.info("Generating performance report...")
        
        # Generate performance report
        self.performance_tracker.generate_performance_report()
        
        # Create comprehensive report
        self._create_comprehensive_report()
        
        logger.info("Performance report generated")
    
    def _create_comprehensive_report(self):
    pass
        """Create comprehensive report combining all metrics"""
        # Create report directory
        Path("reports/comprehensive").mkdir(parents=True, exist_ok=True)
        
        # Load performance data
        try:
    pass
            with open('reports/performance_summary.json', 'r') as f:
    pass
                performance_data = json.load(f)
    pass
            performance_data = {"overall_stats": {}}
        
        # Load parity data
        try:
    pass
            with open('reports/parity/parity_summary.json', 'r') as f:
    pass
                parity_data = json.load(f)
    pass
            parity_data = {"average_metrics": {}}
        
        # Load smoke test data
        try:
    pass
            with open('test_reports/smoke_test_summary.json', 'r') as f:
    pass
                smoke_test_data = json.load(f)
    pass
            smoke_test_data = {}
        
        # Create comprehensive report
        report = {
            "timestamp": datetime.now(),
            "system_status": {
                "smoke_test": smoke_test_data.get('overall_result', 'N/A'),
                "data_flow": smoke_test_data.get('data_flow_validation', 'N/A'),
                "signal_generation": smoke_test_data.get('signal_generation_validation', 'N/A'),
                "execution": smoke_test_data.get('execution_validation', 'N/A'),
                "latency": smoke_test_data.get('latency_validation', 'N/A')
            },
            "performance_metrics": {
                "win_rate": performance_data.get('overall_stats', {}).get('win_rate', 0),
                "profit_factor": performance_data.get('overall_stats', {}).get('profit_factor', 0),
                "net_profit": performance_data.get('overall_stats', {}).get('net_profit', 0),
                "total_trades": performance_data.get('overall_stats', {}).get('total_trades', 0)
            },
            "parity_metrics": {
                "recall": parity_data.get('average_metrics', {}).get('recall', 0),
                "precision": parity_data.get('average_metrics', {}).get('precision', 0),
                "win_rate_delta": parity_data.get('average_metrics', {}).get('win_rate_delta', 0),
                "return_delta": parity_data.get('average_metrics', {}).get('return_delta', 0),
                "slippage_delta": parity_data.get('average_metrics', {}).get('slippage_delta', 0)
            },
            "symbols_analyzed": self.symbols,
            "top_signals": performance_data.get('top_signals', [])
        }
        
        # Save comprehensive report
        with open('reports/comprehensive/system_report.json', 'w') as f:
    pass
            json.dump(report, f, indent=2, default=str)
        
        # Generate markdown report
        md_report = f"""# Profit-Ready Trading System Report
Generated: {datetime.now()}

## System Status
- Smoke Test: {report['system_status']['smoke_test']}
- Data Flow: {report['system_status']['data_flow']}
- Signal Generation: {report['system_status']['signal_generation']}
- Execution: {report['system_status']['execution']}
- Latency: {report['system_status']['latency']}

## Performance Metrics
- Win Rate: {report['performance_metrics']['win_rate']:.2%}
- Profit Factor: {report['performance_metrics']['profit_factor']:.2f}
- Net Profit: {report['performance_metrics']['net_profit']:.2f}
- Total Trades: {report['performance_metrics']['total_trades']}

## Backtest-Live Parity
- Signal Recall: {report['parity_metrics']['recall']:.2%}
- Signal Precision: {report['parity_metrics']['precision']:.2%}
- Win Rate Delta: {report['parity_metrics']['win_rate_delta']:.2%}
- Return Delta: {report['parity_metrics']['return_delta']:.4f}
- Slippage Delta: {report['parity_metrics']['slippage_delta']:.6f}

## Symbols Analyzed
{', '.join(report['symbols_analyzed'])}

## Next Steps
1. Review signal performance and promote top performers
2. Optimize parameters for signals with high recall but low precision
3. Address any slippage issues identified in parity analysis
4. Scale up with additional symbols after validation
5. Monitor system performance with regular parity checks
"""
        
        # Save markdown report
        with open('reports/comprehensive/system_report.md', 'w') as f:
    pass
            f.write(md_report)

async def main():
    pass
    # Run profit-ready demo
    demo = ProfitReadyDemo('examples/trading_config.yaml')
    await demo.run_complete_demo()

if __name__ == "__main__":
    pass
    asyncio.run(main())
