"""
Regime-Aware Backtester
Implements backtesting with market regime detection and regime-specific metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .backtesting_engine import LeakageFreeBacktester, BacktestResult
from .fitness_evaluator import FitnessScore

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"


@dataclass
class RegimeMetrics:
    """Performance metrics for a specific market regime"""
    regime: MarketRegime
    start_date: datetime
    end_date: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    win_rate: float
    avg_trade_pnl: float
    volatility: float


@dataclass
class RegimeDetectionConfig:
    """Configuration for regime detection"""
    lookback_period: int = 20
    trend_threshold: float = 0.05
    volatility_threshold: float = 0.02
    crisis_volatility_threshold: float = 0.05
    ranging_threshold: float = 0.01


class RegimeClassifier:
    """
    Classifies market data into different regimes based on:
    - Trend strength
    - Volatility levels
    - Price action patterns
    """
    
    def __init__(self, config: Optional[RegimeDetectionConfig] = None):
        self.config = config or RegimeDetectionConfig()
    
    def classify_regime(self, data: pd.DataFrame) -> MarketRegime:
        """
        Classify current market regime based on recent data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            MarketRegime classification
        """
        if len(data) < self.config.lookback_period:
            return MarketRegime.RANGING
        
        recent_data = data.tail(self.config.lookback_period)
        
        # Calculate metrics
        returns = recent_data['close'].pct_change().dropna()
        volatility = returns.std()
        total_return = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1)
        
        # Crisis detection (very high volatility)
        if volatility > self.config.crisis_volatility_threshold:
            return MarketRegime.CRISIS
        
        # Low volatility
        if volatility < self.config.volatility_threshold / 2:
            return MarketRegime.LOW_VOLATILITY
        
        # High volatility (but not crisis)
        if volatility > self.config.volatility_threshold:
            return MarketRegime.VOLATILE
        
        # Trend detection
        if abs(total_return) > self.config.trend_threshold:
            if total_return > 0:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.TRENDING_DOWN
        
        # Ranging market
        return MarketRegime.RANGING
    
    def detect_regime_changes(self, data: pd.DataFrame) -> List[Tuple[datetime, MarketRegime]]:
        """
        Detect all regime changes in the data.
        
        Returns:
            List of (timestamp, regime) tuples
        """
        regimes = []
        current_regime = None
        
        for i in range(self.config.lookback_period, len(data)):
            window = data.iloc[i-self.config.lookback_period:i]
            regime = self.classify_regime(window)
            
            if regime != current_regime:
                regimes.append((data.index[i], regime))
                current_regime = regime
        
        return regimes


class RegimeAwareBacktester(LeakageFreeBacktester):
    """
    Backtester that tracks performance across different market regimes.
    
    Provides regime-specific metrics to ensure strategies work
    across various market conditions.
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 initial_capital: float = 100000.0,
                 risk_free_rate: float = 0.02,
                 regime_config: Optional[Dict] = None):
        super().__init__(data, initial_capital, risk_free_rate)
        
        self.regime_classifier = RegimeClassifier(
            RegimeDetectionConfig(**(regime_config or {}))
        )
        
        # Track regime-specific performance
        self.regime_performance: Dict[MarketRegime, Dict] = {
            regime: {
                'returns': [],
                'trades': [],
                'periods': []
            }
            for regime in MarketRegime
        }
        
        logger.info("RegimeAwareBacktester initialized")
    
    def run_regime_aware_backtest(self, strategy) -> Tuple[BacktestResult, Dict[MarketRegime, RegimeMetrics]]:
        """
        Run backtest with regime tracking.
        
        Returns:
            Tuple of (BacktestResult, Dict of regime-specific metrics)
        """
        # Run standard backtest
        result = self.run_backtest(strategy)
        
        # Calculate regime-specific metrics
        regime_metrics = self._calculate_regime_metrics(result)
        
        return result, regime_metrics
    
    def _calculate_regime_metrics(self, backtest_result: BacktestResult) -> Dict[MarketRegime, RegimeMetrics]:
        """Calculate performance metrics for each market regime"""
        regime_metrics = {}
        
        # Detect regimes during backtest period
        regime_changes = self.regime_classifier.detect_regime_changes(self.data)
        
        if not regime_changes:
            # Single regime for entire period
            regime = self.regime_classifier.classify_regime(self.data)
            metrics = self._calculate_single_regime_metrics(
                regime, self.data.index[0], self.data.index[-1], backtest_result
            )
            regime_metrics[regime] = metrics
        else:
            # Multiple regimes
            for i, (timestamp, regime) in enumerate(regime_changes):
                if i < len(regime_changes) - 1:
                    end_time = regime_changes[i + 1][0]
                else:
                    end_time = self.data.index[-1]
                
                # Get data for this regime period
                mask = (self.data.index >= timestamp) & (self.data.index <= end_time)
                period_data = self.data[mask]
                
                # Calculate metrics for this period
                metrics = self._calculate_single_regime_metrics(
                    regime, timestamp, end_time, backtest_result, period_data
                )
                regime_metrics[regime] = metrics
        
        return regime_metrics
    
    def _calculate_single_regime_metrics(self,
                                       regime: MarketRegime,
                                       start_date: datetime,
                                       end_date: datetime,
                                       backtest_result: BacktestResult,
                                       period_data: Optional[pd.DataFrame] = None) -> RegimeMetrics:
        """Calculate metrics for a single regime period"""
        if period_data is None:
            period_data = self.data
        
        # Filter trades to this period
        period_trades = [
            t for t in backtest_result.trades
            if start_date <= t.timestamp <= end_date
        ]
        
        # Calculate metrics
        if period_trades:
            wins = sum(1 for t in period_trades if t.pnl > 0)
            win_rate = wins / len(period_trades)
            avg_pnl = np.mean([t.pnl for t in period_trades])
        else:
            win_rate = 0.0
            avg_pnl = 0.0
        
        # Calculate returns for this period
        mask = (self.data.index >= start_date) & (self.data.index <= end_date)
        period_returns = backtest_result.returns[mask]
        
        if len(period_returns) > 0:
            total_return = (1 + period_returns).prod() - 1
            volatility = period_returns.std() * np.sqrt(252)  # Annualized
            
            # Sharpe ratio
            if volatility > 0:
                sharpe = (period_returns.mean() * 252 - self.risk_free_rate) / volatility
            else:
                sharpe = 0.0
            
            # Max drawdown
            cumulative = (1 + period_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = drawdown.min()
        else:
            total_return = 0.0
            sharpe = 0.0
            max_dd = 0.0
            volatility = 0.0
        
        return RegimeMetrics(
            regime=regime,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            num_trades=len(period_trades),
            win_rate=win_rate,
            avg_trade_pnl=avg_pnl,
            volatility=volatility
        )
    
    def get_regime_stability_score(self, regime_metrics: Dict[MarketRegime, RegimeMetrics]) -> float:
        """
        Calculate how stable strategy performance is across regimes.
        
        Higher score means more consistent performance across all regimes.
        """
        if not regime_metrics:
            return 0.0
        
        # Get Sharpe ratios for all regimes
        sharpe_ratios = [
            m.sharpe_ratio for m in regime_metrics.values()
        ]
        
        if not sharpe_ratios:
            return 0.0
        
        # Calculate coefficient of variation (lower is more stable)
        mean_sharpe = np.mean(sharpe_ratios)
        std_sharpe = np.std(sharpe_ratios)
        
        if mean_sharpe == 0:
            return 0.0
        
        cv = std_sharpe / abs(mean_sharpe)
        
        # Convert to stability score (0-1, higher is better)
        stability = 1 / (1 + cv)
        
        return stability


class MonteCarloValidator:
    """
    Monte Carlo simulation for robust strategy validation.
    
    Tests strategy robustness through:
    - Trade reshuffling
    - Return permutation
    - Stress testing
    """
    
    def __init__(self, num_simulations: int = 1000, confidence_level: float = 0.95):
        self.num_simulations = num_simulations
        self.confidence_level = confidence_level
    
    def validate(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """
        Run Monte Carlo validation on backtest results.
        
        Returns:
            Dictionary with validation statistics
        """
        returns = backtest_result.returns.dropna()
        
        if len(returns) < 10:
            return {'error': 'Insufficient data for Monte Carlo validation'}
        
        simulations = []
        
        for _ in range(self.num_simulations):
            # Resample returns with replacement
            sampled_returns = np.random.choice(returns, size=len(returns), replace=True)
            
            # Calculate metrics
            total_return = (1 + sampled_returns).prod() - 1
            sharpe = self._calculate_sharpe(sampled_returns)
            max_dd = self._calculate_max_drawdown(sampled_returns)
            
            simulations.append({
                'total_return': total_return,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_dd
            })
        
        # Calculate statistics
        sim_returns = [s['total_return'] for s in simulations]
        sim_sharpes = [s['sharpe_ratio'] for s in simulations]
        sim_drawdowns = [s['max_drawdown'] for s in simulations]
        
        alpha = 1 - self.confidence_level
        
        return {
            'total_return_mean': np.mean(sim_returns),
            'total_return_std': np.std(sim_returns),
            'total_return_ci': (
                np.percentile(sim_returns, alpha/2 * 100),
                np.percentile(sim_returns, (1 - alpha/2) * 100)
            ),
            'sharpe_mean': np.mean(sim_sharpes),
            'sharpe_std': np.std(sim_sharpes),
            'sharpe_ci': (
                np.percentile(sim_sharpes, alpha/2 * 100),
                np.percentile(sim_sharpes, (1 - alpha/2) * 100)
            ),
            'max_dd_mean': np.mean(sim_drawdowns),
            'max_dd_worst': np.min(sim_drawdowns),
            'prob_profit': np.mean([r > 0 for r in sim_returns]),
            'prob_sharpe_gt_1': np.mean([s > 1.0 for s in sim_sharpes]),
            'num_simulations': self.num_simulations
        }
    
    def _calculate_sharpe(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sharpe ratio"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        # Assuming daily returns, annualize
        excess_return = returns.mean() * 252 - risk_free_rate
        volatility = returns.std() * np.sqrt(252)
        
        return excess_return / volatility
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
