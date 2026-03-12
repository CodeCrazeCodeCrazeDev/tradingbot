"""
Advanced risk management system for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Risk metrics container."""
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional VaR
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    beta: float
    correlation: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RiskManager:
    """
    Advanced risk management system.
    Implements sophisticated risk monitoring and control.
    """
    
    def __init__(
        self,
        max_position_size: float = 1.0,
        max_portfolio_var: float = 0.02,  # 2% VaR limit
        max_drawdown: float = 0.1,        # 10% max drawdown
        max_correlation: float = 0.7,
        risk_free_rate: float = 0.02      # 2% risk-free rate
    ):
        self.max_position_size = max_position_size
        self.max_portfolio_var = max_portfolio_var
        self.max_drawdown = max_drawdown
        self.max_correlation = max_correlation
        self.risk_free_rate = risk_free_rate
        
        # Risk thresholds
        self.thresholds = {
            'var_95': 0.02,      # 2% daily VaR
            'volatility': 0.02,  # 2% daily volatility
            'drawdown': 0.1,     # 10% drawdown
            'correlation': 0.7,   # 70% correlation
            'leverage': 5.0       # 5x leverage
        }
        
        # Risk history
        self.risk_history: List[RiskMetrics] = []
        
        # Current state
        self.current_risk_level = RiskLevel.LOW
        self.position_limits = {}
        self.trading_restrictions = set()
        
        logger.info("✅ Risk Manager initialized")
    
    def calculate_risk_metrics(
        self,
        returns: np.ndarray,
        positions: Dict[str, float],
        market_data: Dict
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics.
        
        Args:
            returns: Historical returns
            positions: Current positions
            market_data: Current market data
        
        Returns:
            RiskMetrics object
        """
        try:
            # Calculate VaR
            var_95 = self._calculate_var(returns, 0.95)
            cvar_95 = self._calculate_cvar(returns, 0.95)
            
            # Calculate ratios
            sharpe = self._calculate_sharpe_ratio(returns)
            sortino = self._calculate_sortino_ratio(returns)
            
            # Calculate other metrics
            max_dd = self._calculate_max_drawdown(returns)
            vol = self._calculate_volatility(returns)
            beta = self._calculate_beta(returns, market_data.get('market_returns', []))
            corr = self._calculate_correlation(positions, market_data)
            
            metrics = RiskMetrics(
                var_95=var_95,
                cvar_95=cvar_95,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                max_drawdown=max_dd,
                volatility=vol,
                beta=beta,
                correlation=corr
            )
            
            # Update history
            self.risk_history.append(metrics)
            
            # Update risk level
            self._update_risk_level(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error calculating risk metrics: {str(e)}")
            raise
    
    def _calculate_var(
        self,
        returns: np.ndarray,
        confidence: float
    ) -> float:
        """Calculate Value at Risk."""
        if len(returns) == 0:
            return 0.0
        return float(np.percentile(returns, (1 - confidence) * 100))
    
    def _calculate_cvar(
        self,
        returns: np.ndarray,
        confidence: float
    ) -> float:
        """Calculate Conditional Value at Risk."""
        if len(returns) == 0:
            return 0.0
        var = self._calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]
        if len(tail_returns) == 0:
            return var
        return float(np.mean(tail_returns))
    
    def _calculate_sharpe_ratio(
        self,
        returns: np.ndarray
    ) -> float:
        """Calculate Sharpe Ratio."""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - self.risk_free_rate / 252  # Daily
        std = np.std(excess_returns)
        if std == 0:
            return 0.0
        return float(np.mean(excess_returns) / std * np.sqrt(252))
    
    def _calculate_sortino_ratio(
        self,
        returns: np.ndarray
    ) -> float:
        """Calculate Sortino Ratio."""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return float('inf')
        return float(np.mean(excess_returns) / downside_std * np.sqrt(252))
    
    def _calculate_max_drawdown(
        self,
        returns: np.ndarray
    ) -> float:
        """Calculate Maximum Drawdown."""
        if len(returns) == 0:
            return 0.0
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = cumulative / running_max - 1
        return float(np.min(drawdowns))
    
    def _calculate_volatility(
        self,
        returns: np.ndarray
    ) -> float:
        """Calculate volatility."""
        if len(returns) == 0:
            return 0.0
        return float(np.std(returns) * np.sqrt(252))
    
    def _calculate_beta(
        self,
        returns: np.ndarray,
        market_returns: np.ndarray
    ) -> float:
        """Calculate portfolio beta."""
        if len(market_returns) == 0 or len(returns) == 0:
            return 1.0
        # Ensure same length
        min_len = min(len(returns), len(market_returns))
        if min_len < 2:
            return 1.0
        returns = returns[-min_len:]
        market_returns = np.array(market_returns)[-min_len:]
        covar = np.cov(returns, market_returns)[0, 1]
        market_var = np.var(market_returns)
        return float(covar / market_var if market_var > 0 else 1.0)
    
    def _calculate_correlation(
        self,
        positions: Dict[str, float],
        market_data: Dict
    ) -> float:
        """Calculate portfolio correlation."""
        if not positions or 'correlations' not in market_data:
            return 0.0
        
        correlations = []
        symbols = list(positions.keys())
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                if (symbols[i], symbols[j]) in market_data['correlations']:
                    correlations.append(
                        abs(market_data['correlations'][(symbols[i], symbols[j])])
                    )
        
        return float(np.mean(correlations) if correlations else 0.0)
    
    def _update_risk_level(self, metrics: RiskMetrics):
        """Update current risk level."""
        risk_scores = []
        
        # VaR score (handle division by zero)
        if self.thresholds['var_95'] != 0:
            risk_scores.append(abs(metrics.var_95) / self.thresholds['var_95'])
        
        # Volatility score
        if self.thresholds['volatility'] != 0:
            risk_scores.append(metrics.volatility / self.thresholds['volatility'])
        
        # Drawdown score
        if self.thresholds['drawdown'] != 0:
            risk_scores.append(abs(metrics.max_drawdown) / self.thresholds['drawdown'])
        
        # Correlation score
        if self.thresholds['correlation'] != 0:
            risk_scores.append(metrics.correlation / self.thresholds['correlation'])
        
        # Average risk score
        if not risk_scores:
            avg_score = 0
        else:
            avg_score = np.mean(risk_scores)
        
        # Determine risk level
        if avg_score > 1.5:
            self.current_risk_level = RiskLevel.CRITICAL
        elif avg_score > 1.0:
            self.current_risk_level = RiskLevel.HIGH
        elif avg_score > 0.7:
            self.current_risk_level = RiskLevel.MEDIUM
        else:
            self.current_risk_level = RiskLevel.LOW
    
    def check_position_risk(
        self,
        symbol: str,
        size: float,
        price: float
    ) -> Tuple[bool, str]:
        """
        Check if position meets risk requirements.
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check position size
        if size > self.max_position_size:
            return False, "Position size exceeds limit"
        
        # Check symbol restrictions
        if symbol in self.trading_restrictions:
            return False, "Trading restricted for symbol"
        
        # Check risk level limits
        if self.current_risk_level == RiskLevel.CRITICAL:
            return False, "Critical risk level - no new positions"
        
        if self.current_risk_level == RiskLevel.HIGH:
            if size > self.max_position_size * 0.5:
                return False, "Reduced position size limit under high risk"
        
        return True, "Position allowed"
    
    def update_position_limits(self, market_data: Dict):
        """Update position limits based on market conditions."""
        for symbol in market_data:
            volatility = market_data[symbol].get('volatility', 0.02)
            
            # Adjust limit based on volatility
            if volatility > 0.03:  # High volatility
                self.position_limits[symbol] = self.max_position_size * 0.5
            elif volatility > 0.02:  # Medium volatility
                self.position_limits[symbol] = self.max_position_size * 0.75
            else:  # Low volatility
                self.position_limits[symbol] = self.max_position_size
    
    def update_trading_restrictions(self, market_data: Dict):
        """Update trading restrictions based on market conditions."""
        self.trading_restrictions.clear()
        
        for symbol, data in market_data.items():
            # Check for extreme conditions
            if data.get('volatility', 0) > 0.05:  # 5% volatility
                self.trading_restrictions.add(symbol)
            
            if abs(data.get('returns', 0)) > 0.1:  # 10% move
                self.trading_restrictions.add(symbol)
    
    def get_risk_summary(self) -> Dict:
        """Get current risk summary."""
        if not self.risk_history:
            return {
                'risk_level': self.current_risk_level.value,
                'metrics': None,
                'limits': self.position_limits,
                'restrictions': list(self.trading_restrictions)
            }
        
        latest = self.risk_history[-1]
        
        return {
            'risk_level': self.current_risk_level.value,
            'metrics': {
                'var_95': latest.var_95,
                'cvar_95': latest.cvar_95,
                'sharpe_ratio': latest.sharpe_ratio,
                'sortino_ratio': latest.sortino_ratio,
                'max_drawdown': latest.max_drawdown,
                'volatility': latest.volatility,
                'beta': latest.beta,
                'correlation': latest.correlation
            },
            'limits': self.position_limits,
            'restrictions': list(self.trading_restrictions)
        }
    
    def get_risk_report(self) -> str:
        """Generate detailed risk report."""
        summary = self.get_risk_summary()
        
        if summary['metrics'] is None:
            return f"RISK MANAGEMENT REPORT\n{'=' * 50}\nRisk Level: {summary['risk_level'].upper()}\nNo metrics available yet."
        
        report = [
            "RISK MANAGEMENT REPORT",
            "=" * 50,
            f"\nRisk Level: {summary['risk_level'].upper()}",
            
            "\nRisk Metrics:",
            f"- VaR (95%): {summary['metrics']['var_95']:.2%}",
            f"- CVaR (95%): {summary['metrics']['cvar_95']:.2%}",
            f"- Sharpe Ratio: {summary['metrics']['sharpe_ratio']:.2f}",
            f"- Sortino Ratio: {summary['metrics']['sortino_ratio']:.2f}",
            f"- Max Drawdown: {summary['metrics']['max_drawdown']:.2%}",
            f"- Volatility: {summary['metrics']['volatility']:.2%}",
            f"- Beta: {summary['metrics']['beta']:.2f}",
            f"- Correlation: {summary['metrics']['correlation']:.2f}",
            
            "\nPosition Limits:",
            *[f"- {sym}: {limit:.2f}" for sym, limit in summary['limits'].items()] or ["- None"],
            
            "\nTrading Restrictions:",
            *[f"- {sym}" for sym in summary['restrictions']] or ["- None"],
        ]
        
        return "\n".join(report)
