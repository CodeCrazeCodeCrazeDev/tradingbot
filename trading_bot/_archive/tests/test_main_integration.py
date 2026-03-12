"""Integration test for main execution flow with all new components."""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import datetime as dt
import argparse
import sys
import os

# Add parent directory to path to allow importing main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from main import main, parse_args
from trading_bot.strategy.ml_strategy import MLStrategyEngine
from trading_bot.strategy.strategy_engine import StrategyEngine
from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.analytics.enhanced_performance import EnhancedPerformanceAnalytics
from trading_bot.analytics.emotional_tracker import EmotionalStateTracker
from typing import Set
import datetime
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class TestMainIntegration(unittest.TestCase):
    """Test cases for main execution flow with all new components."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock command line arguments
        self.args = argparse.Namespace(
            symbol="EURUSD",
            timeframe="M15",
            bars=100,
            mode="paper",
            log_level="INFO",
            profile=False,
            use_ml=True,
            execution_algo="smart",
            track_emotions=True,
            use_sentiment=True
        )
        
        # Create sample OHLC data
        self.df = pd.DataFrame({
            'time': pd.date_range(start='2023-01-01', periods=100),
            'open': np.random.normal(1.1, 0.01, 100),
            'high': np.random.normal(1.11, 0.01, 100),
            'low': np.random.normal(1.09, 0.01, 100),
            'close': np.random.normal(1.1, 0.01, 100),
            'volume': np.random.randint(100, 1000, 100)
        })
        
        # Convert time to POSIX timestamp
        self.df['time'] = self.df['time'].astype('int64') // 10**9

    @patch('main.MT5Interface')
    @patch('main.StrategyEngine')
    @patch('main.MLStrategyEngine')
    @patch('main.PaperExecutor')
    @patch('main.TWAPExecutor')
    @patch('main.VWAPExecutor')
    @patch('main.SmartOrderRouter')
    @patch('main.EmotionalStateTracker')
    @patch('main.EnhancedPerformanceAnalytics')
    @patch('main.parse_args')
    def test_main_with_ml_and_emotional_tracking(
        self, mock_parse_args, mock_enhanced_perf, mock_emotional_tracker,
        mock_smart_router, mock_vwap, mock_twap, mock_paper_executor,
        mock_ml_strategy, mock_strategy, mock_mt5
    ):
        """Test main execution flow with ML and emotional tracking enabled."""
        # Configure mocks
        mock_parse_args.return_value = self.args
        
        # MT5 mock
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = True
        mt5_instance.get_ohlc.return_value = self.df
        mt5_instance.get_current_price.return_value = 1.1000
        
        # Strategy mock
        ml_strategy_instance = mock_ml_strategy.return_value
        ml_strategy_instance.analyse.return_value = [
            MagicMock(
                symbol="EURUSD",
                direction="buy",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=80.0
            )
        ]
        
        # Executor mock
        paper_executor_instance = mock_paper_executor.return_value
        smart_router_instance = mock_smart_router.return_value
        
        # Emotional tracker mock
        emotional_tracker_instance = mock_emotional_tracker.return_value
        
        # Enhanced performance mock
        enhanced_perf_instance = mock_enhanced_perf.return_value
        enhanced_perf_instance.summary.return_value = {
            'trades': 3,
            'win_rate': 0.67,
            'net_profit': 100.0,
            'emotional_impact': {
                'confidence': {'correlation': 0.8},
                'fear': {'correlation': -0.7}
            },
            'recommendations': ['Trade with higher confidence']
        }
        
        # Run main
        main()
        
        # Verify MT5 connection
        mt5_instance.connect.assert_called_once()
        mt5_instance.get_ohlc.assert_called_once()
        
        # Verify ML strategy was used
        mock_ml_strategy.assert_called_once()
        ml_strategy_instance.analyse.assert_called_once()
        
        # Verify Smart Order Router was used
        mock_smart_router.assert_called_once()
        smart_router_instance.process.assert_called_once()
        
        # Verify emotional tracking was used
        mock_emotional_tracker.assert_called_once()
        
        # Verify enhanced performance analytics was used
        mock_enhanced_perf.assert_called_once()
        enhanced_perf_instance.summary.assert_called_once()

    @patch('main.MT5Interface')
    @patch('main.StrategyEngine')
    @patch('main.MLStrategyEngine')
    @patch('main.PaperExecutor')
    @patch('main.TWAPExecutor')
    @patch('main.VWAPExecutor')
    @patch('main.SmartOrderRouter')
    @patch('main.parse_args')
    def test_main_with_twap_execution(
        self, mock_parse_args, mock_smart_router, mock_vwap, mock_twap,
        mock_paper_executor, mock_ml_strategy, mock_strategy, mock_mt5
    ):
        """Test main execution flow with TWAP execution algorithm."""
        # Configure args for TWAP
        args_twap = self.args
        args_twap.execution_algo = "twap"
        args_twap.use_ml = False
        args_twap.track_emotions = False
        
        mock_parse_args.return_value = args_twap
        
        # MT5 mock
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = True
        mt5_instance.get_ohlc.return_value = self.df
        mt5_instance.get_current_price.return_value = 1.1000
        
        # Strategy mock
        strategy_instance = mock_strategy.return_value
        strategy_instance.analyse.return_value = [
            MagicMock(
                symbol="EURUSD",
                direction="buy",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=80.0
            )
        ]
        
        # Executor mock
        paper_executor_instance = mock_paper_executor.return_value
        twap_instance = mock_twap.return_value
        
        # Run main
        main()
        
        # Verify traditional strategy was used
        mock_strategy.assert_called_once()
        strategy_instance.analyse.assert_called_once()
        
        # Verify TWAP executor was used
        mock_twap.assert_called_once()
        twap_instance.process.assert_called_once()

    @patch('main.MT5Interface')
    @patch('main.StrategyEngine')
    @patch('main.MLStrategyEngine')
    @patch('main.PaperExecutor')
    @patch('main.TWAPExecutor')
    @patch('main.VWAPExecutor')
    @patch('main.SmartOrderRouter')
    @patch('main.parse_args')
    def test_main_with_vwap_execution(
        self, mock_parse_args, mock_smart_router, mock_vwap, mock_twap,
        mock_paper_executor, mock_ml_strategy, mock_strategy, mock_mt5
    ):
        """Test main execution flow with VWAP execution algorithm."""
        # Configure args for VWAP
        args_vwap = self.args
        args_vwap.execution_algo = "vwap"
        args_vwap.use_ml = False
        args_vwap.track_emotions = False
        
        mock_parse_args.return_value = args_vwap
        
        # MT5 mock
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = True
        mt5_instance.get_ohlc.return_value = self.df
        mt5_instance.get_current_price.return_value = 1.1000
        
        # Strategy mock
        strategy_instance = mock_strategy.return_value
        strategy_instance.analyse.return_value = [
            MagicMock(
                symbol="EURUSD",
                direction="buy",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=80.0
            )
        ]
        
        # Executor mock
        paper_executor_instance = mock_paper_executor.return_value
        vwap_instance = mock_vwap.return_value
        
        # Run main
        main()
        
        # Verify traditional strategy was used
        mock_strategy.assert_called_once()
        strategy_instance.analyse.assert_called_once()
        
        # Verify VWAP executor was used
        mock_vwap.assert_called_once()
        vwap_instance.process.assert_called_once()


if __name__ == '__main__':
    unittest.main()
