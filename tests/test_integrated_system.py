#!/usr/bin/env python
"""
Integration Test for Elite Trading System

This script tests the integration of all three pillars:
Analysis, Execution, and Monitoring.
"""

import asyncio
import logging
import unittest
import os
import sys
import yaml
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core components
from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator
from trading_bot.core.execution_manager import ExecutionManager, OrderType
from trading_bot.core.monitoring_system import MonitoringSystem
from trading_bot.core.trading_system import TradingSystem

# Import data components
from trading_bot.data.market_data_stream import MarketDataStream
from trading_bot.data.time_series_db import TimeSeriesDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_integrated_system")


class TestIntegratedSystem(unittest.IsolatedAsyncioTestCase):
    """Test case for the integrated trading system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Test configuration
        cls.config = {
            "symbols": ["EURUSD"],
            "timeframes": ["M15"],
            "data_update_interval": 1.0,
            "analysis_interval": 1.0,
            "trading_enabled": False,  # Disable trading for tests
            "data_stream": {
                "simulate_data": True,
                "use_redis": False
            },
            "time_series_db": {
                "data_dir": "tests/data/time_series",
                "partition_by": "day",
                "compression": "snappy",
                "cache_enabled": True
            },
            "analysis": {
                "min_confidence": 60.0
            },
            "execution": {
                "max_retries": 1
            },
            "monitoring": {
                "health": {
                    "monitor_interval": 1.0
                },
                "alerts": {
                    "channels": ["console"]
                }
            }
        }
        
        # Create test directories
        Path("tests/data/time_series").mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        cls.analysis = AnalysisOrchestrator(cls.config.get("analysis", {}))
        cls.execution = ExecutionManager(cls.config.get("execution", {}))
        cls.monitoring = MonitoringSystem(cls.config.get("monitoring", {}))
        cls.data_stream = MarketDataStream(cls.config.get("data_stream", {}))
        cls.time_series_db = TimeSeriesDB(cls.config.get("time_series_db", {}))
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        import shutil
        if Path("tests/data").exists():
            shutil.rmtree("tests/data")

    async def test_data_stream(self):
        """Test market data stream"""
        # Start data stream
        await self.data_stream.start()
        
        # Verify it's running
        self.assertTrue(self.data_stream.is_running)
        
        # Stop data stream
        await self.data_stream.stop()
        
        # Verify it's stopped
        self.assertFalse(self.data_stream.is_running)

    async def test_time_series_db(self):
        """Test time series database"""
        symbol = self.config["symbols"][0]
        timeframe = self.config["timeframes"][0]
        
        # Create sample data
        ohlcv_data = pd.DataFrame({
            'open': [1.1000],
            'high': [1.1050],
            'low': [1.0950],
            'close': [1.1020],
            'volume': [1000]
        }, index=[datetime.now()])
        
        # Store data
        result = await self.time_series_db.store(symbol, timeframe, ohlcv_data)
        self.assertTrue(result)
        
        # Load data
        loaded_data = await self.time_series_db.load(symbol, timeframe)
        
        # Verify loaded data
        self.assertIsNotNone(loaded_data)
        self.assertIsInstance(loaded_data, pd.DataFrame)
        self.assertGreater(len(loaded_data), 0)

    async def test_analysis_orchestrator(self):
        """Test analysis orchestrator"""
        # Get OHLCV data
        symbol = self.config["symbols"][0]
        timeframe = self.config["timeframes"][0]
        ohlcv_data = await self.data_stream.get_ohlcv(symbol, timeframe, 100)
        
        # Analyze market
        context = await self.analysis.analyze_market(symbol, timeframe, ohlcv_data)
        
        # Verify context
        self.assertIsNotNone(context)
        
        # Generate signals
        signals = await self.analysis.generate_signals(symbol, timeframe, ohlcv_data)
        
        # Verify signals
        self.assertIsInstance(signals, list)

    async def test_execution_manager(self):
        """Test execution manager"""
        # Place order
        symbol = self.config["symbols"][0]
        order = await self.execution.place_order(
            symbol=symbol,
            order_type=OrderType.MARKET,
            side="buy",
            quantity=1.0,
            urgency=0.5,
            market_volatility=0.3
        )

        # Verify order
        self.assertIsNotNone(order)
        self.assertEqual(order.symbol, symbol)
        self.assertEqual(order.side, "buy")

        # Process fill
        trade = await self.execution.process_fill(
            order_id=order.id,
            fill_quantity=1.0,
            fill_price=1.1050
        )

        # Verify trade
        self.assertIsNotNone(trade)

        # Get position
        position = self.execution.get_position(symbol)

        # Verify position
        self.assertIsNotNone(position)

        # Close position
        close_order = await self.execution.close_position(symbol)

        # Verify close order
        self.assertIsNotNone(close_order)

    async def test_monitoring_system(self):
        """Test monitoring system"""
        # Add trade
        trade = {
            'symbol': 'EURUSD',
            'entry_price': 1.1000,
            'exit_price': 1.1050,
            'quantity': 1.0,
            'entry_time': datetime.now() - timedelta(hours=1),
            'exit_time': datetime.now(),
            'side': 'buy',
            'pnl': 50.0,
            'commission': 1.0,
            'strategy': 'test'
        }

        self.monitoring.add_trade(trade)

        # Update component status
        self.monitoring.update_component_status('data_feed', 'ok', {'latency_ms': 15})

        # Add alert
        alert = self.monitoring.add_alert('info', 'test', 'Test alert')

        # Verify alert
        self.assertIsNotNone(alert)

        # Get dashboard data
        dashboard_data = self.monitoring.get_dashboard_data()

        # Verify dashboard data
        self.assertIsNotNone(dashboard_data)

    async def test_trading_system(self):
        """Test trading system"""
        # Create trading system
        trading_system = TradingSystem(self.config)

        try:
            # Start trading system
            await trading_system.start()

            # Verify system is running
            self.assertTrue(trading_system.running)

            # Wait for a few cycles
            await asyncio.sleep(1)

            # Get dashboard data
            dashboard_data = await trading_system.get_dashboard_data()

            # Verify dashboard data
            self.assertIsNotNone(dashboard_data)

        finally:
            # Stop trading system
            await trading_system.stop()

            # Verify system is stopped
            self.assertFalse(trading_system.running)


if __name__ == '__main__':
    unittest.main()
