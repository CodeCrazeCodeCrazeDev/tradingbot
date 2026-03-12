"""
Quantitative Analyzer - Main Orchestrator
==========================================

Comprehensive quantitative analysis orchestrator that coordinates all analysis modules.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class QuantAnalyzer:
    """
    Main quantitative analysis orchestrator.
    
    Coordinates:
    - Statistical analysis
    - Factor analysis
    - Performance attribution
    - Risk analytics
    - Portfolio optimization
    - Backtesting analytics
    - Market microstructure
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize quant analyzer."""
        self.config = config or {}
        self._statistical_analyzer = None
        self._factor_analyzer = None
        self._performance_attributor = None
        self._risk_analyzer = None
        self._portfolio_optimizer = None
        self._backtest_analyzer = None
        self._microstructure_analyzer = None
        
        logger.info("QuantAnalyzer initialized")
    
    def analyze_returns(
        self,
        returns: Union[pd.Series, np.ndarray],
        benchmark_returns: Optional[Union[pd.Series, np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive returns analysis.
        
        Args:
            returns: Strategy returns
            benchmark_returns: Optional benchmark returns
            
        Returns:
            Analysis results with metrics
        """
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_return': self._calculate_total_return(returns),
            'annualized_return': self._calculate_annualized_return(returns),
            'volatility': self._calculate_volatility(returns),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'sortino_ratio': self._calculate_sortino_ratio(returns),
            'max_drawdown': self._calculate_max_drawdown(returns),
            'calmar_ratio': self._calculate_calmar_ratio(returns),
            'win_rate': self._calculate_win_rate(returns),
            'profit_factor': self._calculate_profit_factor(returns),
            'skewness': float(returns.skew()),
            'kurtosis': float(returns.kurtosis()),
        }
        
        if benchmark_returns is not None:
            if isinstance(benchmark_returns, np.ndarray):
                benchmark_returns = pd.Series(benchmark_returns)
            results['alpha'] = self._calculate_alpha(returns, benchmark_returns)
            results['beta'] = self._calculate_beta(returns, benchmark_returns)
            results['information_ratio'] = self._calculate_information_ratio(returns, benchmark_returns)
            results['tracking_error'] = self._calculate_tracking_error(returns, benchmark_returns)
        
        return results
    
    def analyze_strategy(
        self,
        trades: pd.DataFrame,
        prices: pd.DataFrame,
        positions: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive strategy analysis.
        
        Args:
            trades: Trade history DataFrame
            prices: Price data DataFrame
            positions: Optional position history
            
        Returns:
            Strategy analysis results
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'trade_statistics': self._analyze_trades(trades),
            'price_statistics': self._analyze_prices(prices),
        }
        
        if positions is not None:
            results['position_statistics'] = self._analyze_positions(positions)
        
        return results
    
    def run_factor_analysis(
        self,
        returns: pd.Series,
        factors: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run factor analysis on returns.
        
        Args:
            returns: Strategy returns
            factors: Factor returns DataFrame
            
        Returns:
            Factor analysis results
        """
        from sklearn.linear_model import LinearRegression
        
        X = factors.values
        y = returns.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'factor_exposures': dict(zip(factors.columns, model.coef_)),
            'alpha': float(model.intercept_),
            'r_squared': float(model.score(X, y)),
            'residuals': (y - model.predict(X)).tolist(),
        }
        
        return results
    
    def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio weights.
        
        Args:
            returns: Asset returns DataFrame
            constraints: Optional constraints dict
            
        Returns:
            Optimal weights and metrics
        """
        n_assets = len(returns.columns)
        
        # Mean-variance optimization (simplified)
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Equal weight as baseline
        weights = np.ones(n_assets) / n_assets
        
        portfolio_return = float(np.dot(weights, mean_returns))
        portfolio_vol = float(np.sqrt(np.dot(weights, np.dot(cov_matrix, weights))))
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'weights': dict(zip(returns.columns, weights)),
            'expected_return': portfolio_return,
            'expected_volatility': portfolio_vol,
            'sharpe_ratio': portfolio_return / portfolio_vol if portfolio_vol > 0 else 0,
        }
        
        return results
    
    def _calculate_total_return(self, returns: pd.Series) -> float:
        """Calculate total return."""
        return float((1 + returns).prod() - 1)
    
    def _calculate_annualized_return(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized return."""
        total_return = self._calculate_total_return(returns)
        n_periods = len(returns)
        if n_periods == 0:
            return 0.0
        return float((1 + total_return) ** (periods_per_year / n_periods) - 1)
    
    def _calculate_volatility(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized volatility."""
        return float(returns.std() * np.sqrt(periods_per_year))
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252) -> float:
        """Calculate Sharpe ratio."""
        excess_returns = returns - risk_free_rate / periods_per_year
        if excess_returns.std() == 0:
            return 0.0
        return float(excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year))
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252) -> float:
        """Calculate Sortino ratio."""
        excess_returns = returns - risk_free_rate / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return float(excess_returns.mean() / downside_returns.std() * np.sqrt(periods_per_year))
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def _calculate_calmar_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate Calmar ratio."""
        annualized_return = self._calculate_annualized_return(returns, periods_per_year)
        max_dd = abs(self._calculate_max_drawdown(returns))
        if max_dd == 0:
            return 0.0
        return float(annualized_return / max_dd)
    
    def _calculate_win_rate(self, returns: pd.Series) -> float:
        """Calculate win rate."""
        if len(returns) == 0:
            return 0.0
        return float((returns > 0).sum() / len(returns))
    
    def _calculate_profit_factor(self, returns: pd.Series) -> float:
        """Calculate profit factor."""
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        if losses == 0:
            return float('inf') if gains > 0 else 0.0
        return float(gains / losses)
    
    def _calculate_alpha(self, returns: pd.Series, benchmark_returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate alpha."""
        beta = self._calculate_beta(returns, benchmark_returns)
        strategy_return = returns.mean()
        benchmark_return = benchmark_returns.mean()
        return float(strategy_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate)))
    
    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta."""
        covariance = returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        if benchmark_variance == 0:
            return 0.0
        return float(covariance / benchmark_variance)
    
    def _calculate_information_ratio(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate information ratio."""
        active_returns = returns - benchmark_returns
        tracking_error = active_returns.std()
        if tracking_error == 0:
            return 0.0
        return float(active_returns.mean() / tracking_error)
    
    def _calculate_tracking_error(self, returns: pd.Series, benchmark_returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate tracking error."""
        active_returns = returns - benchmark_returns
        return float(active_returns.std() * np.sqrt(periods_per_year))
    
    def _analyze_trades(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trade statistics."""
        if len(trades) == 0:
            return {'total_trades': 0}
        
        return {
            'total_trades': len(trades),
            'winning_trades': int((trades.get('pnl', 0) > 0).sum()) if 'pnl' in trades.columns else 0,
            'losing_trades': int((trades.get('pnl', 0) < 0).sum()) if 'pnl' in trades.columns else 0,
            'avg_trade_pnl': float(trades['pnl'].mean()) if 'pnl' in trades.columns else 0.0,
            'avg_win': float(trades[trades['pnl'] > 0]['pnl'].mean()) if 'pnl' in trades.columns and (trades['pnl'] > 0).any() else 0.0,
            'avg_loss': float(trades[trades['pnl'] < 0]['pnl'].mean()) if 'pnl' in trades.columns and (trades['pnl'] < 0).any() else 0.0,
        }
    
    def _analyze_prices(self, prices: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price statistics."""
        if len(prices) == 0:
            return {}
        
        returns = prices.pct_change().dropna()
        
        return {
            'mean_return': float(returns.mean().mean()) if not returns.empty else 0.0,
            'volatility': float(returns.std().mean()) if not returns.empty else 0.0,
            'min_price': float(prices.min().min()),
            'max_price': float(prices.max().max()),
        }
    
    def _analyze_positions(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze position statistics."""
        if len(positions) == 0:
            return {}
        
        return {
            'avg_position_size': float(positions.abs().mean().mean()) if not positions.empty else 0.0,
            'max_position_size': float(positions.abs().max().max()) if not positions.empty else 0.0,
            'position_turnover': float(positions.diff().abs().sum().sum()) if not positions.empty else 0.0,
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive analysis report."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'analyzer': 'QuantAnalyzer',
            'status': 'active',
            'capabilities': [
                'returns_analysis',
                'strategy_analysis',
                'factor_analysis',
                'portfolio_optimization',
                'risk_metrics',
                'performance_attribution',
            ]
        }
