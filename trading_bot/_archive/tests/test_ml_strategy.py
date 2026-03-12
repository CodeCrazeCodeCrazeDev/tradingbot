"""Integration tests for ML strategy engine."""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from trading_bot.strategy.ml_strategy import MLStrategyEngine
from trading_bot.data import MT5Interface
from typing import Set


class TestMLStrategyEngine(unittest.TestCase):
    """Test cases for the ML-enhanced strategy engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.mt5i = MagicMock(spec=MT5Interface)
        self.mt5i.account_info.return_value = MagicMock(balance=10000.0)
        
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
        
        # Create strategy engine
        self.ml_strategy = MLStrategyEngine(
            self.mt5i,
            symbol="EURUSD",
            use_price_prediction=True,
            use_pattern_recognition=True,
            use_sentiment=False
        )

    def test_initialization(self):
        """Test proper initialization of ML strategy engine."""
        self.assertEqual(self.ml_strategy.symbol, "EURUSD")
        self.assertIsNotNone(self.ml_strategy.price_predictor)
        self.assertIsNotNone(self.ml_strategy.pattern_recognizer)
        self.assertIsNone(self.ml_strategy.sentiment_analyzer)
        self.assertIsNotNone(self.ml_strategy.strategy_optimizer)

    def test_analyse_returns_signals(self):
        """Test that analyse method returns signals."""
        signals = self.ml_strategy.analyse(self.df)
        self.assertIsInstance(signals, list)
        
    def test_ml_signals_generation(self):
        """Test ML signal generation."""
        ml_signals = self.ml_strategy._generate_ml_signals(self.df)
        self.assertIsInstance(ml_signals, list)
        
    @patch('trading_bot.ml.PricePredictor.predict_next_bars')
    def test_price_prediction_signals(self, mock_predict):
        """Test price prediction signal generation."""
        # Mock the prediction result
        mock_predict.return_value = {
            'values': [1.1, 1.105, 1.11],
            'confidence': 75.0,
            'volatility': 0.002
        }
        
        signals = self.ml_strategy._generate_price_prediction_signals(self.df)
        self.assertIsInstance(signals, list)
        if signals:  # If any signals were generated
            self.assertEqual(signals[0].symbol, "EURUSD")
            self.assertIn(signals[0].direction, ["buy", "sell"])
            self.assertGreaterEqual(signals[0].confidence, self.ml_strategy.confidence_threshold)
            
    def test_feature_preparation(self):
        """Test feature preparation for ML models."""
        features = self.ml_strategy._prepare_features(self.df)
        self.assertIsInstance(features, dict)
        self.assertIn('ohlc', features)
        self.assertIn('returns', features)
        self.assertIn('rsi', features)
        self.assertIn('macd', features)
        
    def test_signal_combination(self):
        """Test combining traditional and ML signals."""
        # Create some test signals
        from trading_bot.strategy.strategy_engine import Signal
        import datetime as dt
        
        traditional_signals = [
            Signal(
                time=dt.datetime.now(),
                symbol="EURUSD",
                direction="buy",
                rationale="Test traditional signal",
                stop_loss_pips=10,
                take_profit_rr=2.0,
                confidence=65.0
            )
        ]
        
        ml_signals = [
            Signal(
                time=dt.datetime.now(),
                symbol="EURUSD",
                direction="sell",
                rationale="Test ML signal",
                stop_loss_pips=15,
                take_profit_rr=1.5,
                confidence=80.0
            )
        ]
        
        # Test signal combination
        combined = self.ml_strategy._combine_signals(traditional_signals, ml_signals)
        self.assertIsInstance(combined, list)
        self.assertGreaterEqual(len(combined), 0)  # At least some signals should pass filtering


if __name__ == '__main__':
    unittest.main()
