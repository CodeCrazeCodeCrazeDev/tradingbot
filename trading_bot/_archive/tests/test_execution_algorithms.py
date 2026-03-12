"""Integration tests for execution optimization algorithms."""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import datetime as dt

from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.execution import PaperExecutor
from trading_bot.data import MT5Interface
from trading_bot.risk import RiskManager
from trading_bot.strategy.strategy_engine import Signal
from typing import Set
import datetime
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class TestExecutionAlgorithms(unittest.TestCase):
    """Test cases for execution optimization algorithms."""

    def setUp(self):
        """Set up test fixtures."""
        self.mt5i = MagicMock(spec=MT5Interface)
        self.mt5i.account_info.return_value = MagicMock(balance=10000.0)
        
        self.risk_manager = MagicMock(spec=RiskManager)
        self.risk_manager.calculate_position_size.return_value = 0.1
        
        self.base_executor = MagicMock(spec=PaperExecutor)
        self.base_executor.mt5 = self.mt5i
        self.base_executor.risk = self.risk_manager
        
        # Create sample signals
        self.signals = [
            Signal(
                time=dt.datetime.now(),
                symbol="EURUSD",
                direction="buy",
                rationale="Test signal 1",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=75.0
            ),
            Signal(
                time=dt.datetime.now(),
                symbol="GBPUSD",
                direction="sell",
                rationale="Test signal 2",
                stop_loss_pips=15,
                take_profit_rr=1.5,
                confidence=80.0
            )
        ]
        
        # Create sample historical volume profile
        self.volume_profile = pd.DataFrame({
            'hour': range(24),
            'volume_percent': [
                2, 1, 1, 1, 2, 3, 5, 7, 8, 9, 8, 7,
                6, 7, 8, 9, 7, 5, 4, 3, 2, 2, 2, 1
            ]
        })

    def test_twap_executor_initialization(self):
        """Test proper initialization of TWAP executor."""
        twap = TWAPExecutor(self.base_executor)
        self.assertEqual(twap.base_executor, self.base_executor)
        self.assertEqual(twap.mt5, self.mt5i)
        self.assertEqual(twap.risk, self.risk_manager)
        
    def test_twap_executor_order_chunking(self):
        """Test TWAP order chunking logic."""
        twap = TWAPExecutor(self.base_executor)
        
        # Mock the _should_use_algo method to always return True
        twap._should_use_algo = MagicMock(return_value=True)
        
        # Mock the base executor's process method
        twap.base_executor.process = MagicMock()
        
        # Process signals
        twap.process(self.signals, 1.1000)
        
        # Check that the base executor was called multiple times (once per chunk)
        self.assertGreater(twap.base_executor.process.call_count, 1)
        
    def test_vwap_executor_initialization(self):
        """Test proper initialization of VWAP executor."""
        vwap = VWAPExecutor(self.base_executor)
        self.assertEqual(vwap.base_executor, self.base_executor)
        self.assertEqual(vwap.mt5, self.mt5i)
        self.assertEqual(vwap.risk, self.risk_manager)
        
    @patch('trading_bot.execution.algorithms.VWAPExecutor._get_volume_profile')
    def test_vwap_executor_volume_based_execution(self, mock_get_volume):
        """Test VWAP volume-based execution logic."""
        # Mock the volume profile
        mock_get_volume.return_value = self.volume_profile
        
        vwap = VWAPExecutor(self.base_executor)
        
        # Mock the _should_use_algo method to always return True
        vwap._should_use_algo = MagicMock(return_value=True)
        
        # Mock the base executor's process method
        vwap.base_executor.process = MagicMock()
        
        # Process signals
        vwap.process(self.signals, 1.1000)
        
        # Check that the base executor was called
        self.assertGreater(vwap.base_executor.process.call_count, 0)
        
    def test_smart_order_router_initialization(self):
        """Test proper initialization of Smart Order Router."""
        router = SmartOrderRouter(self.base_executor)
        self.assertEqual(router.base_executor, self.base_executor)
        self.assertEqual(router.mt5, self.mt5i)
        self.assertEqual(router.risk, self.risk_manager)
        
    def test_smart_order_router_algorithm_selection(self):
        """Test Smart Order Router algorithm selection logic."""
        router = SmartOrderRouter(self.base_executor)
        
        # Test with a large order (should select VWAP or TWAP)
        large_signal = Signal(
            time=dt.datetime.now(),
            symbol="EURUSD",
            direction="buy",
            rationale="Large order test",
            stop_loss_pips=10,
            take_profit_rr=2.0,
            confidence=75.0
        )
        
        # Mock lot size calculation to return a large value
        router.risk.calculate_position_size = MagicMock(return_value=5.0)
        
        # Mock the execution methods
        router._execute_with_twap = MagicMock()
        router._execute_with_vwap = MagicMock()
        router._execute_with_market = MagicMock()
        
        # Process the large signal
        router.process([large_signal], 1.1000)
        
        # Either TWAP or VWAP should have been called, but not market
        self.assertTrue(
            router._execute_with_twap.called or router._execute_with_vwap.called
        )
        self.assertFalse(router._execute_with_market.called)
        
        # Reset mocks
        router._execute_with_twap.reset_mock()
        router._execute_with_vwap.reset_mock()
        router._execute_with_market.reset_mock()
        
        # Test with a small order (should select market)
        small_signal = Signal(
            time=dt.datetime.now(),
            symbol="EURUSD",
            direction="buy",
            rationale="Small order test",
            stop_loss_pips=10,
            take_profit_rr=2.0,
            confidence=75.0
        )
        
        # Mock lot size calculation to return a small value
        router.risk.calculate_position_size = MagicMock(return_value=0.01)
        
        # Process the small signal
        router.process([small_signal], 1.1000)
        
        # Market execution should have been called
        self.assertTrue(router._execute_with_market.called)
        self.assertFalse(router._execute_with_twap.called)
        self.assertFalse(router._execute_with_vwap.called)


if __name__ == '__main__':
    unittest.main()
