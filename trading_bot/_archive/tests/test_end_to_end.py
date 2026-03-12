"""End-to-end integration test for the complete trading bot system."""
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
from trading_bot.strategy.strategy_engine import StrategyEngine, Signal
from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.analytics.enhanced_performance import EnhancedPerformanceAnalytics
from trading_bot.analytics.emotional_tracker import EmotionalStateTracker
from trading_bot.analytics.performance import Trade
from typing import Set
import datetime
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class TestEndToEnd(unittest.TestCase):
    """End-to-end test for the complete trading bot system."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock command line arguments for full-featured execution
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
        
        # Create sample OHLC data with realistic patterns
        self.df = self._create_realistic_price_data()
        
        # Sample trades for performance analytics
        self.trades = [
            Trade(
                ticket=1,
                symbol="EURUSD",
                direction="buy",
                lot=0.1,
                entry_price=1.1000,
                exit_price=1.1050,
                entry_time=dt.datetime.now().timestamp() - 3600,
                exit_time=dt.datetime.now().timestamp() - 1800,
                profit=50.0
            ),
            Trade(
                ticket=2,
                symbol="GBPUSD",
                direction="sell",
                lot=0.2,
                entry_price=1.2500,
                exit_price=1.2450,
                entry_time=dt.datetime.now().timestamp() - 7200,
                exit_time=dt.datetime.now().timestamp() - 5400,
                profit=100.0
            ),
            Trade(
                ticket=3,
                symbol="USDJPY",
                direction="buy",
                lot=0.1,
                entry_price=110.00,
                exit_price=109.50,
                entry_time=dt.datetime.now().timestamp() - 10800,
                exit_time=dt.datetime.now().timestamp() - 9000,
                profit=-50.0
            )
        ]

    def _create_realistic_price_data(self):
        """Create realistic price data with trends and patterns."""
        # Start with a base price and add a trend
        n_periods = 100
        base_price = 1.1000
        trend = np.linspace(0, 0.02, n_periods)  # Upward trend
        
        # Add some cyclical patterns
        cycles = 0.005 * np.sin(np.linspace(0, 4*np.pi, n_periods))
        
        # Add random noise
        noise = np.random.normal(0, 0.001, n_periods)
        
        # Combine components
        close_prices = base_price + trend + cycles + noise
        
        # Create realistic OHLC data
        df = pd.DataFrame({
            'time': pd.date_range(start='2023-01-01', periods=n_periods),
            'close': close_prices
        })
        
        # Generate open, high, low based on close
        df['open'] = df['close'].shift(1)
        df.loc[0, 'open'] = df.loc[0, 'close'] - 0.0005
        
        # High is max of open/close plus a random amount
        df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0.0001, 0.0020, n_periods)
        
        # Low is min of open/close minus a random amount
        df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0.0001, 0.0020, n_periods)
        
        # Add volume with some correlation to price movement
        price_changes = np.abs(df['close'] - df['open'])
        df['volume'] = 100 + 5000 * price_changes + np.random.randint(50, 500, n_periods)
        
        # Convert time to POSIX timestamp
        df['time'] = df['time'].astype('int64') // 10**9
        
        return df

    @patch('main.MT5Interface')
    @patch('main.StrategyEngine')
    @patch('main.MLStrategyEngine')
    @patch('main.PaperExecutor')
    @patch('main.TWAPExecutor')
    @patch('main.VWAPExecutor')
    @patch('main.SmartOrderRouter')
    @patch('main.EmotionalStateTracker')
    @patch('main.EnhancedPerformanceAnalytics')
    @patch('main.PerformanceAnalytics')
    @patch('main.parse_args')
    def test_full_trading_session(
        self, mock_parse_args, mock_perf, mock_enhanced_perf, mock_emotional_tracker,
        mock_smart_router, mock_vwap, mock_twap, mock_paper_executor,
        mock_ml_strategy, mock_strategy, mock_mt5
    ):
        """Test a complete trading session with all features enabled."""
        # Configure mocks
        mock_parse_args.return_value = self.args
        
        # MT5 mock
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = True
        mt5_instance.get_ohlc.return_value = self.df
        mt5_instance.get_current_price.return_value = 1.1020
        mt5_instance.account_info.return_value = MagicMock(balance=10000.0)
        
        # Strategy mocks
        ml_strategy_instance = mock_ml_strategy.return_value
        
        # Create realistic signals with different confidence levels
        signals = [
            Signal(
                time=dt.datetime.now(),
                symbol="EURUSD",
                direction="buy",
                rationale="Breakout pattern detected with ML confirmation",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=85.0
            ),
            Signal(
                time=dt.datetime.now(),
                symbol="EURUSD",
                direction="buy",
                rationale="Support level with high volume",
                stop_loss_pips=15,
                take_profit_rr=1.5,
                confidence=70.0
            )
        ]
        ml_strategy_instance.analyse.return_value = signals
        
        # Executor mocks
        paper_executor_instance = mock_paper_executor.return_value
        smart_router_instance = mock_smart_router.return_value
        
        # Emotional tracker mock
        emotional_tracker_instance = mock_emotional_tracker.return_value
        emotional_tracker_instance.detect_state_from_actions.return_value = {
            'confidence': 0.7,
            'excitement': 0.6,
            'fear': 0.3
        }
        
        # Enhanced performance mock
        enhanced_perf_instance = mock_enhanced_perf.return_value
        enhanced_perf_instance.summary.return_value = {
            'trades': 3,
            'win_rate': 0.67,
            'net_profit': 100.0,
            'profit_factor': 1.5,
            'max_drawdown': 50.0,
            'emotional_impact': {
                'confidence': {'correlation': 0.8, 'win_rate': 0.75},
                'fear': {'correlation': -0.7, 'win_rate': 0.25}
            },
            'recommendations': [
                'Trade with higher confidence levels',
                'Reduce trading during periods of high fear'
            ]
        }
        enhanced_perf_instance.trades = self.trades
        
        # Run main
        main()
        
        # Verify MT5 connection and data retrieval
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
    @patch('main.EmotionalStateTracker')
    @patch('main.EnhancedPerformanceAnalytics')
    @patch('main.parse_args')
    def test_error_handling(
        self, mock_parse_args, mock_enhanced_perf, mock_emotional_tracker,
        mock_smart_router, mock_vwap, mock_twap, mock_paper_executor,
        mock_ml_strategy, mock_strategy, mock_mt5
    ):
        """Test error handling in the main execution flow."""
        # Configure args
        mock_parse_args.return_value = self.args
        
        # MT5 mock - simulate connection failure
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = False
        
        # Run main and expect graceful handling of connection failure
        with self.assertRaises(SystemExit):
            main()
        
        # Verify connection was attempted
        mt5_instance.connect.assert_called_once()
        
        # Reset mocks
        mock_mt5.reset_mock()
        
        # Now simulate successful connection but data retrieval failure
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = True
        mt5_instance.get_ohlc.side_effect = Exception("Failed to retrieve data")
        
        # Run main and expect graceful handling of data retrieval failure
        with self.assertRaises(SystemExit):
            main()
        
        # Verify connection was successful but get_ohlc failed
        mt5_instance.connect.assert_called_once()
        mt5_instance.get_ohlc.assert_called_once()

    @patch('main.MT5Interface')
    @patch('main.StrategyEngine')
    @patch('main.MLStrategyEngine')
    @patch('main.PaperExecutor')
    @patch('main.parse_args')
    def test_fallback_to_traditional_strategy(
        self, mock_parse_args, mock_paper_executor, 
        mock_ml_strategy, mock_strategy, mock_mt5
    ):
        """Test fallback to traditional strategy when ML fails."""
        # Configure args with ML enabled
        args = self.args
        args.use_ml = True
        mock_parse_args.return_value = args
        
        # MT5 mock
        mt5_instance = mock_mt5.return_value
        mt5_instance.connect.return_value = True
        mt5_instance.get_ohlc.return_value = self.df
        mt5_instance.get_current_price.return_value = 1.1020
        
        # ML Strategy mock - simulate failure
        mock_ml_strategy.side_effect = Exception("ML model initialization failed")
        
        # Traditional Strategy mock
        strategy_instance = mock_strategy.return_value
        strategy_instance.analyse.return_value = [
            Signal(
                time=dt.datetime.now(),
                symbol="EURUSD",
                direction="buy",
                rationale="Traditional signal",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=65.0
            )
        ]
        
        # Executor mock
        paper_executor_instance = mock_paper_executor.return_value
        
        # Run main with error handling to catch the ML failure
        try:
            main()
        except Exception:
            pass
        
        # Verify traditional strategy was used as fallback
        mock_strategy.assert_called_once()
        strategy_instance.analyse.assert_called_once()


if __name__ == '__main__':
    unittest.main()
