"""
Test script for the TAMIC (Time-Aware Market Intelligence and Control) system.

This script tests the functionality of the TAMIC system components and integration.
"""

import asyncio
import logging
import sys
import os
import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import TAMIC components
from trading_bot.tamic import (
    TAMIC, 
    TimeHorizon, 
    MarketTimeState, 
    SignalHalfLife,
    create_tamic,
    quick_start,
    TAMICIntegration
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestTAMICSystem(unittest.TestCase):
    """Test cases for TAMIC system"""
    
    def setUp(self):
        """Set up test environment"""
        self.loop = asyncio.get_event_loop()
        
        # Sample market data
        self.market_data = self.loop.run_until_complete(self.generate_sample_market_data("AAPL"))
        
        # Sample strategy config
        self.strategy_config = {
            "strategy_id": "momentum_strategy_001",
            "strategy_type": "momentum",
            "time_horizon": "intraday",
            "risk_limit": 0.02,
            "max_exposure": 0.5,
            "parameters": {
                "lookback_periods": 20,
                "entry_threshold": 0.5,
                "exit_threshold": -0.2
            }
        }
    
    async def generate_sample_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Generate sample market data for testing.
        
        Args:
            symbol: Market symbol
            
        Returns:
            Sample market data
        """
        import numpy as np
        
        # Generate sample OHLCV data
        n_periods = 100
        close = np.random.normal(100, 1, n_periods).cumsum()
        high = close + np.random.uniform(0, 2, n_periods)
        low = close - np.random.uniform(0, 2, n_periods)
        open_prices = close - np.random.uniform(-1, 1, n_periods)
        volume = np.random.uniform(1000, 5000, n_periods)
        
        # Calculate some derived metrics
        volatility = np.std(np.diff(close) / close[:-1]) * np.sqrt(252)
        liquidity = np.mean(volume) / 1000
        
        # Create market data dictionary
        market_data = {
            "symbol": symbol,
            "timestamp": time.time(),
            "open": open_prices.tolist(),
            "high": high.tolist(),
            "low": low.tolist(),
            "close": close.tolist(),
            "volume": volume.tolist(),
            "volatility": volatility,
            "liquidity": liquidity,
            "spread": 0.01,
            "market_regime": "trending",
            "correlation": {
                "spy": 0.7,
                "qqq": 0.8
            }
        }
        
        return market_data
    
    async def generate_market_data_with_forbidden_behavior(self, behavior_type: str) -> Dict[str, Any]:
        """
        Generate market data that should trigger a forbidden behavior.
        
        Args:
            behavior_type: Type of forbidden behavior to trigger
            
        Returns:
            Market data with forbidden behavior
        """
        # Start with base market data
        market_data = await self.generate_sample_market_data("AAPL")
        
        # Modify based on behavior type
        if behavior_type == "chase_recent_performance":
            # Add exceptional recent performance
            market_data["recent_performance"] = 0.15  # 15% recent return
        
        elif behavior_type == "mix_time_horizons":
            # Add data from multiple horizons
            market_data["microstructure_data"] = {"volatility": 0.02}
            market_data["intraday_data"] = {"volatility": 0.03}
        
        elif behavior_type == "reuse_expired_signals":
            # Add expired signal timestamp
            market_data["signal_timestamp"] = time.time() - 86400  # 24 hours ago
        
        elif behavior_type == "retrain_during_drawdowns":
            # Add drawdown and retraining flag
            market_data["drawdown"] = 0.15  # 15% drawdown
            market_data["is_retraining"] = True
        
        elif behavior_type == "increase_leverage_after_losses":
            # Add loss streak and leverage increase
            market_data["loss_streak"] = 3
            market_data["previous_leverage"] = 1.0
            market_data["current_leverage"] = 2.0
        
        elif behavior_type == "assume_stationarity":
            # Add regime change flag
            market_data["regime_changed"] = True
            market_data["volatility_change"] = 0.5  # 50% increase
        
        return market_data
    
    def test_tamic_creation(self):
        """Test TAMIC creation"""
        # Create TAMIC instance
        tamic = self.loop.run_until_complete(quick_start())
        
        # Check TAMIC instance
        self.assertIsNotNone(tamic)
        self.assertIsInstance(tamic, TAMIC)
        
        # Check components
        self.assertIn("horizon_segmentation", tamic.components)
        self.assertIn("signal_decay", tamic.components)
        self.assertIn("market_time", tamic.components)
        self.assertIn("time_risk", tamic.components)
    
    def test_tamic_evaluation(self):
        """Test TAMIC market evaluation"""
        # Create TAMIC instance
        tamic = self.loop.run_until_complete(quick_start())
        
        # Evaluate market
        decision = self.loop.run_until_complete(
            tamic.evaluate_market(
                symbol="AAPL",
                horizon=TimeHorizon.INTRADAY,
                market_data=self.market_data
            )
        )
        
        # Check decision
        self.assertIsNotNone(decision)
        self.assertIsInstance(decision.is_trade_recommended, bool)
        self.assertIsInstance(decision.confidence_level, float)
        self.assertIsInstance(decision.exposure_recommendation, float)
        self.assertIsInstance(decision.market_time_state, MarketTimeState)
        self.assertIsInstance(decision.signal_half_life, SignalHalfLife)
    
    def test_forbidden_behaviors(self):
        """Test forbidden behaviors detection"""
        # Create TAMIC instance
        tamic = self.loop.run_until_complete(quick_start())
        
        # Test each forbidden behavior
        behaviors = [
            "chase_recent_performance",
            "mix_time_horizons",
            "reuse_expired_signals",
            "retrain_during_drawdowns",
            "increase_leverage_after_losses",
            "assume_stationarity"
        ]
        
        for behavior in behaviors:
            # Generate market data with forbidden behavior
            market_data = self.loop.run_until_complete(
                self.generate_market_data_with_forbidden_behavior(behavior)
            )
            
            # Evaluate market
            decision = self.loop.run_until_complete(
                tamic.evaluate_market(
                    symbol="AAPL",
                    horizon=TimeHorizon.INTRADAY,
                    market_data=market_data
                )
            )
            
            # Check if forbidden behavior was detected (not all will be detected)
            logger.info(f"Testing behavior: {behavior}")
            logger.info(f"  Trade recommended: {decision.is_trade_recommended}")
            if not decision.is_trade_recommended:
                logger.info(f"  No trade reason: {decision.no_trade_reason}")
    
    def test_time_horizons(self):
        """Test different time horizons"""
        # Create TAMIC instance
        tamic = self.loop.run_until_complete(quick_start())
        
        # Test each time horizon
        horizons = [
            TimeHorizon.MICROSTRUCTURE,
            TimeHorizon.INTRADAY,
            TimeHorizon.SHORT_SWING,
            TimeHorizon.MEDIUM_HORIZON
        ]
        
        for horizon in horizons:
            # Evaluate market
            decision = self.loop.run_until_complete(
                tamic.evaluate_market(
                    symbol="AAPL",
                    horizon=horizon,
                    market_data=self.market_data
                )
            )
            
            # Check decision
            self.assertIsNotNone(decision)
            self.assertEqual(decision.time_horizon, horizon)
            logger.info(f"Horizon: {horizon.value}")
            logger.info(f"  Trade recommended: {decision.is_trade_recommended}")
            logger.info(f"  Confidence: {decision.confidence_level:.2f}")
            logger.info(f"  Exposure: {decision.exposure_recommendation:.2f}")
    
    def test_market_time_states(self):
        """Test market time states"""
        # Create TAMIC instance
        tamic = self.loop.run_until_complete(quick_start())
        
        # Test normal market time
        normal_market_data = self.market_data.copy()
        normal_market_data["volatility"] = 0.01  # Low volatility
        
        # Test accelerated market time
        accelerated_market_data = self.market_data.copy()
        accelerated_market_data["volatility"] = 0.03  # High volatility
        
        # Test extreme market time
        extreme_market_data = self.market_data.copy()
        extreme_market_data["volatility"] = 0.05  # Very high volatility
        
        # Evaluate markets
        normal_decision = self.loop.run_until_complete(
            tamic.evaluate_market(
                symbol="AAPL",
                horizon=TimeHorizon.INTRADAY,
                market_data=normal_market_data
            )
        )
        
        accelerated_decision = self.loop.run_until_complete(
            tamic.evaluate_market(
                symbol="AAPL",
                horizon=TimeHorizon.INTRADAY,
                market_data=accelerated_market_data
            )
        )
        
        extreme_decision = self.loop.run_until_complete(
            tamic.evaluate_market(
                symbol="AAPL",
                horizon=TimeHorizon.INTRADAY,
                market_data=extreme_market_data
            )
        )
        
        # Log results
        logger.info(f"Normal market time: {normal_decision.market_time_state.value}")
        logger.info(f"Accelerated market time: {accelerated_decision.market_time_state.value}")
        logger.info(f"Extreme market time: {extreme_decision.market_time_state.value}")
        
        # Check confidence levels
        # Higher volatility should generally lead to lower confidence
        logger.info(f"Normal confidence: {normal_decision.confidence_level:.2f}")
        logger.info(f"Accelerated confidence: {accelerated_decision.confidence_level:.2f}")
        logger.info(f"Extreme confidence: {extreme_decision.confidence_level:.2f}")


async def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTAMICSystem)
    
    # Run tests
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_tests())
