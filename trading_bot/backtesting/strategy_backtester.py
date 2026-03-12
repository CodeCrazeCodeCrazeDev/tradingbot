import logging
logger = logging.getLogger(__name__)
"""Strategy backtesting module for testing trading strategies."""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio
from loguru import logger

from .backtester import Backtester
try:
    from trading_bot.analysis import MarketContextAnalyzer
except ImportError:
    MarketContextAnalyzer = None

try:
    from trading_bot.analysis.liquidity import LiquidityAnalyzer
except ImportError:
    LiquidityAnalyzer = None

try:
    from trading_bot.analysis.order_flow import OrderFlowAnalyzer
except ImportError:
    OrderFlowAnalyzer = None

try:
    from trading_bot.ml.predictive_models import PricePredictor
except ImportError:
    PricePredictor = None

try:
    from trading_bot.ml import StrategyOptimizer
except ImportError:
    StrategyOptimizer = None

try:
    from trading_bot.risk import RiskManager
except ImportError:
    RiskManager = None
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator




@dataclass
class StrategyBacktestResult:
    """Results from strategy backtesting."""
    strategy_name: str
    performance_metrics: Dict[str, float]
    trades: List[Dict[str, Any]]
    predictions: List[Dict[str, Any]]
    market_conditions: List[Dict[str, Any]]
    risk_metrics: Dict[str, float]


class StrategyBacktester:
    """Advanced strategy backtester with ML and market analysis capabilities."""
    
    def __init__(self):
        """Initialize strategy backtester."""
        self.market_analyzer = MarketContextAnalyzer()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.order_flow_analyzer = OrderFlowAnalyzer()
        self.price_predictor = PricePredictor()
        self.strategy_optimizer = StrategyOptimizer()
        self.risk_manager = RiskManager()
        
    async def backtest_strategy(
        self,
        strategy_name: str,
        market_data: pd.DataFrame,
        strategy_params: Dict[str, Any],
        initial_capital: float = 100000.0,
        risk_per_trade: float = 0.02
    ) -> StrategyBacktestResult:
        """
        Backtest a trading strategy with advanced analytics.
        
        Args:
            strategy_name: Name of the strategy
            market_data: OHLCV DataFrame
            strategy_params: Strategy-specific parameters
            initial_capital: Initial capital for backtesting
            risk_per_trade: Risk per trade as fraction of capital
            
        Returns:
            StrategyBacktestResult with comprehensive metrics
        """
        try:
            # Market analysis
            market_context = await self.market_analyzer.analyze(market_data)
            liquidity_zones = self.liquidity_analyzer.analyze(market_data)
            order_flow = self.order_flow_analyzer.analyze_order_flow(market_data)
            
            # Price predictions
            predictions = self.price_predictor.predict(market_data)
            
            # Optimize strategy parameters
            optimized_params = await self.strategy_optimizer.optimize(
                strategy_name,
                market_data,
                strategy_params,
                market_context
            )
            
            # Run backtesting with optimized parameters
            backtester = Backtester(initial_capital=initial_capital)
            trades = []
            
            for i in range(len(market_data) - 1):
                current_data = market_data.iloc[:i+1]
                
                # Get trading signals
                signal = self._generate_signal(
                    current_data,
                    optimized_params,
                    predictions[i] if i < len(predictions) else None,
                    market_context,
                    liquidity_zones,
                    order_flow
                )
                
                if signal:
                    # Apply risk management
                    position_size = self.risk_manager.calculate_position_size(
                        signal['direction'],
                        current_data.iloc[-1],
                        risk_per_trade,
                        backtester.capital
                    )
                    
                    # Execute trade
                    trade = backtester.execute_trade(
                        signal['direction'],
                        position_size,
                        current_data.iloc[-1]
                    )
                    
                    if trade:
                        trades.append(trade)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(trades, market_data)
            risk_metrics = self._calculate_risk_metrics(trades, market_data)
            
            return StrategyBacktestResult(
                strategy_name=strategy_name,
                performance_metrics=performance_metrics,
                trades=trades,
                predictions=predictions,
                market_conditions={
                    'market_context': market_context,
                    'liquidity_zones': liquidity_zones,
                    'order_flow': order_flow
                },
                risk_metrics=risk_metrics
            )
            
        except Exception as e:
            logger.error(f"Error in strategy backtesting: {e}")
            raise
    
    def _generate_signal(
        self,
        data: pd.DataFrame,
        params: Dict[str, Any],
        prediction: Optional[Dict[str, Any]],
        market_context: Dict[str, Any],
        liquidity_zones: Dict[str, Any],
        order_flow: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on all available information."""
        try:
            # Implement strategy-specific logic here
            # This is a placeholder for actual signal generation
            signal = None
            
            # Example signal generation logic
            if prediction and prediction.get('confidence', 0) > params.get('confidence_threshold', 0.7):
                signal = {
                    'direction': 'buy' if prediction['direction'] > 0 else 'sell',
                    'confidence': prediction['confidence'],
                    'reason': 'ml_prediction'
                }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
    
    def _calculate_performance_metrics(
        self,
        trades: List[Dict[str, Any]],
        market_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        try:
            if not trades:
                return {
                    'total_return': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'sharpe_ratio': 0.0
                }
            
            profits = [t['profit'] for t in trades]
            wins = [p for p in profits if p > 0]
            
            metrics = {
                'total_return': sum(profits),
                'win_rate': len(wins) / len(trades) if trades else 0,
                'profit_factor': (
                    sum(p for p in profits if p > 0) /
                    abs(sum(p for p in profits if p < 0))
                    if sum(p for p in profits if p < 0) != 0 else float('inf')
                ),
                'sharpe_ratio': (
                    np.mean(profits) / np.std(profits)
                    if len(profits) > 1 else 0
                )
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _calculate_risk_metrics(
        self,
        trades: List[Dict[str, Any]],
        market_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate risk metrics."""
        try:
            if not trades:
                return {
                    'max_drawdown': 0.0,
                    'var_95': 0.0,
                    'expected_shortfall': 0.0
                }
            
            # Calculate running equity curve
            profits = [t['profit'] for t in trades]
            equity_curve = np.cumsum([0] + profits)
            
            # Calculate maximum drawdown
            rolling_max = np.maximum.accumulate(equity_curve)
            drawdowns = (rolling_max - equity_curve) / rolling_max
            max_drawdown = np.max(drawdowns)
            
            # Calculate Value at Risk (VaR)
            returns = pd.Series(profits)
            var_95 = np.percentile(returns, 5)  # 95% VaR
            
            # Calculate Expected Shortfall (ES)
            es_threshold = np.percentile(returns, 5)
            expected_shortfall = returns[returns <= es_threshold].mean()
            
            metrics = {
                'max_drawdown': max_drawdown,
                'var_95': var_95,
                'expected_shortfall': expected_shortfall
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}
