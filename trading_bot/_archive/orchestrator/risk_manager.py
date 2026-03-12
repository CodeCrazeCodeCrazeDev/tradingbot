"""
Portfolio Risk Management System with Dynamic Hedging
Ensures capital preservation while maximizing returns
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk levels for positions"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    portfolio_var: float  # Value at Risk
    portfolio_cvar: float  # Conditional VaR
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    beta: float
    correlation_risk: float
    concentration_risk: float
    liquidity_risk: float
    tail_risk: float
    stress_test_results: Dict[str, float]

class PortfolioRiskManager:
    """
    Comprehensive portfolio risk management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Risk limits
        self.max_portfolio_var = self.config.get('max_portfolio_var', 0.05)
        self.max_position_risk = self.config.get('max_position_risk', 0.02)
        self.max_correlation = self.config.get('max_correlation', 0.7)
        self.max_concentration = self.config.get('max_concentration', 0.2)
        self.max_leverage = self.config.get('max_leverage', 2.0)
        
        # Risk models
        self.var_confidence = self.config.get('var_confidence', 0.95)
        self.lookback_period = self.config.get('lookback_period', 252)
        
        # Portfolio state
        self.positions = {}
        self.portfolio_value = 0
        self.cash_balance = 0
        
        # Risk calculations
        self.correlation_matrix = None
        self.covariance_matrix = None
        self.risk_metrics = None
        
        # Hedging
        self.hedge_calculator = HedgeCalculator()
        self.active_hedges = {}
        
        # Position sizing
        self.position_sizer = PositionSizer()
        
        # Drawdown control
        self.drawdown_controller = DrawdownController()
        
        logger.info("Portfolio Risk Manager initialized")
    
    def assess_portfolio_risk(self, positions: Dict, market_data: Dict) -> RiskMetrics:
        """
        Comprehensive portfolio risk assessment
        """
        self.positions = positions
        
        # Calculate correlation and covariance
        self._update_correlation_matrix(market_data)
        
        # Calculate VaR and CVaR
        portfolio_var = self._calculate_portfolio_var()
        portfolio_cvar = self._calculate_portfolio_cvar()
        
        # Calculate risk ratios
        sharpe = self._calculate_sharpe_ratio()
        sortino = self._calculate_sortino_ratio()
        
        # Calculate drawdowns
        max_dd, current_dd = self._calculate_drawdowns()
        
        # Calculate beta
        beta = self._calculate_portfolio_beta(market_data)
        
        # Assess various risks
        correlation_risk = self._assess_correlation_risk()
        concentration_risk = self._assess_concentration_risk()
        liquidity_risk = self._assess_liquidity_risk(market_data)
        tail_risk = self._assess_tail_risk()
        
        # Stress testing
        stress_results = self._run_stress_tests(market_data)
        
        self.risk_metrics = RiskMetrics(
            portfolio_var=portfolio_var,
            portfolio_cvar=portfolio_cvar,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            beta=beta,
            correlation_risk=correlation_risk,
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk,
            tail_risk=tail_risk,
            stress_test_results=stress_results
        )
        
        return self.risk_metrics
    
    def _update_correlation_matrix(self, market_data: Dict):
        """Update correlation matrix for portfolio assets"""
        symbols = list(self.positions.keys())
        n = len(symbols)
        
        if n < 2:
            self.correlation_matrix = np.array([[1.0]])
            return
        
        # Calculate returns for each symbol
        returns_data = []
        for symbol in symbols:
            if symbol in market_data and 'price_history' in market_data[symbol]:
                prices = market_data[symbol]['price_history']
                returns = np.diff(np.log(prices))
                returns_data.append(returns)
        
        if returns_data:
            # Calculate correlation matrix
            min_length = min(len(r) for r in returns_data)
            aligned_returns = np.array([r[-min_length:] for r in returns_data])
            self.correlation_matrix = np.corrcoef(aligned_returns)
            
            # Calculate covariance matrix
            std_devs = np.std(aligned_returns, axis=1)
            self.covariance_matrix = np.outer(std_devs, std_devs) * self.correlation_matrix
    
    def _calculate_portfolio_var(self) -> float:
        """
        Calculate Portfolio Value at Risk
        """
        if not self.positions:
            return 0
        
        # Get position weights
        weights = self._get_position_weights()
        
        if self.covariance_matrix is None:
            # Use simple VaR if no covariance data
            return self._calculate_simple_var(weights)
        
        # Calculate portfolio variance
        portfolio_variance = np.dot(weights, np.dot(self.covariance_matrix, weights))
        portfolio_std = np.sqrt(portfolio_variance)
        
        # Calculate VaR at confidence level
        z_score = stats.norm.ppf(self.var_confidence)
        portfolio_var = portfolio_std * z_score * np.sqrt(1/252)  # Daily VaR
        
        return portfolio_var
    
    def _calculate_portfolio_cvar(self) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall)
        """
        var = self._calculate_portfolio_var()
        
        # CVaR is typically 1.2-1.5x VaR for normal distributions
        # More sophisticated calculation would use historical simulation
        cvar = var * 1.3
        
        return cvar
    
    def _calculate_simple_var(self, weights: np.ndarray) -> float:
        """Simple VaR calculation without correlation"""
        # Assume 20% annual volatility as default
        portfolio_vol = 0.2 * np.sqrt(np.sum(weights**2))
        z_score = stats.norm.ppf(self.var_confidence)
        return portfolio_vol * z_score * np.sqrt(1/252)
    
    def _get_position_weights(self) -> np.ndarray:
        """Get position weights in portfolio"""
        total_value = sum(pos['value'] for pos in self.positions.values())
        
        if total_value == 0:
            return np.array([])
        
        weights = []
        for symbol, position in self.positions.items():
            weight = position['value'] / total_value
            weights.append(weight)
        
        return np.array(weights)
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate portfolio Sharpe ratio"""
        # Simplified calculation
        # In production, use actual returns history
        
        expected_return = 0.1  # 10% annual
        portfolio_std = 0.15  # 15% volatility
        risk_free_rate = 0.02  # 2% risk-free rate
        
        if portfolio_std == 0:
            return 0
        
        sharpe = (expected_return - risk_free_rate) / portfolio_std
        
        return sharpe
    
    def _calculate_sortino_ratio(self) -> float:
        """Calculate portfolio Sortino ratio (downside risk)"""
        expected_return = 0.1
        downside_std = 0.1  # Downside volatility
        risk_free_rate = 0.02
        
        if downside_std == 0:
            return 0
        
        sortino = (expected_return - risk_free_rate) / downside_std
        
        return sortino
    
    def _calculate_drawdowns(self) -> Tuple[float, float]:
        """Calculate maximum and current drawdown"""
        # Simplified - would use actual equity curve
        max_drawdown = 0.15  # 15% max drawdown
        current_drawdown = 0.05  # 5% current drawdown
        
        return max_drawdown, current_drawdown
    
    def _calculate_portfolio_beta(self, market_data: Dict) -> float:
        """Calculate portfolio beta relative to market"""
        # Simplified - would calculate vs actual market index
        return 1.2
    
    def _assess_correlation_risk(self) -> float:
        """Assess risk from asset correlations"""
        if self.correlation_matrix is None:
            return 0.5
        
        # Average absolute correlation
        n = len(self.correlation_matrix)
        if n <= 1:
            return 0
        
        # Extract upper triangle (excluding diagonal)
        upper_triangle = np.triu(self.correlation_matrix, k=1)
        avg_correlation = np.sum(np.abs(upper_triangle)) / (n * (n-1) / 2)
        
        return avg_correlation
    
    def _assess_concentration_risk(self) -> float:
        """Assess portfolio concentration risk"""
        if not self.positions:
            return 0
        
        weights = self._get_position_weights()
        
        # Herfindahl-Hirschman Index
        hhi = np.sum(weights**2)
        
        # Convert to risk score (0-1)
        # HHI of 1 means fully concentrated, 1/n means equally weighted
        n = len(weights)
        min_hhi = 1/n if n > 0 else 1
        
        concentration_risk = (hhi - min_hhi) / (1 - min_hhi) if min_hhi < 1 else 0
        
        return concentration_risk
    
    def _assess_liquidity_risk(self, market_data: Dict) -> float:
        """Assess liquidity risk of portfolio"""
        liquidity_scores = []
        
        for symbol, position in self.positions.items():
            if symbol in market_data:
                volume = market_data[symbol].get('volume', 0)
                position_size = position['value']
                
                # Days to liquidate at 10% of daily volume
                if volume > 0:
                    days_to_liquidate = position_size / (volume * 0.1)
                    liquidity_score = min(1.0, days_to_liquidate / 10)  # Normalize to 10 days
                else:
                    liquidity_score = 1.0
                
                liquidity_scores.append(liquidity_score)
        
        return np.mean(liquidity_scores) if liquidity_scores else 0.5
    
    def _assess_tail_risk(self) -> float:
        """Assess tail risk (black swan events)"""
        # Simplified - would use actual returns distribution
        # Check for fat tails using kurtosis
        
        kurtosis = 3.5  # Placeholder - would calculate from returns
        
        # Normal distribution has kurtosis of 3
        # Higher kurtosis indicates fatter tails
        tail_risk = max(0, min(1, (kurtosis - 3) / 5))
        
        return tail_risk
    
    def _run_stress_tests(self, market_data: Dict) -> Dict[str, float]:
        """Run portfolio stress tests"""
        stress_results = {}
        
        # Market crash scenario (-20%)
        stress_results['market_crash'] = self._stress_test_scenario(
            market_shock=-0.20,
            vol_shock=2.0
        )
        
        # Flash crash scenario (-10% rapid)
        stress_results['flash_crash'] = self._stress_test_scenario(
            market_shock=-0.10,
            vol_shock=3.0
        )
        
        # Interest rate shock (+200bps)
        stress_results['rate_shock'] = self._stress_test_scenario(
            rate_shock=0.02
        )
        
        # Liquidity crisis
        stress_results['liquidity_crisis'] = self._stress_test_scenario(
            liquidity_shock=0.5
        )
        
        # Correlation breakdown
        stress_results['correlation_breakdown'] = self._stress_test_scenario(
            correlation_shock=0.8
        )
        
        return stress_results
    
    def _stress_test_scenario(self, market_shock: float = 0, vol_shock: float = 1,
                             rate_shock: float = 0, liquidity_shock: float = 0,
                             correlation_shock: float = 0) -> float:
        """Run a specific stress test scenario"""
        portfolio_value = sum(pos['value'] for pos in self.positions.values())
        
        # Apply shocks
        shocked_value = portfolio_value
        
        # Market shock
        if market_shock != 0:
            shocked_value *= (1 + market_shock)
        
        # Volatility shock increases potential losses
        if vol_shock != 1:
            var = self._calculate_portfolio_var()
            additional_loss = var * (vol_shock - 1)
            shocked_value *= (1 - additional_loss)
        
        # Rate shock affects fixed income and growth stocks differently
        if rate_shock != 0:
            # Simplified - would need asset class breakdown
            shocked_value *= (1 - rate_shock * 2)  # Assume 2x duration
        
        # Liquidity shock increases transaction costs
        if liquidity_shock != 0:
            transaction_cost = portfolio_value * liquidity_shock * 0.01
            shocked_value -= transaction_cost
        
        # Correlation shock (all correlations go to correlation_shock)
        if correlation_shock != 0:
            # Increases portfolio risk
            shocked_value *= (1 - correlation_shock * 0.1)
        
        # Return percentage loss
        return (portfolio_value - shocked_value) / portfolio_value if portfolio_value > 0 else 0
    
    def calculate_optimal_hedge(self, positions: Dict, market_data: Dict) -> Dict:
        """
        Calculate optimal hedge for portfolio
        """
        return self.hedge_calculator.calculate_hedge(positions, market_data, self.risk_metrics)
    
    def validate_trade(self, trade: Dict) -> Tuple[bool, str]:
        """
        Validate if trade fits within risk limits
        """
        # Check position risk
        position_risk = trade.get('risk', 0.5) * trade.get('size', 0)
        if position_risk > self.max_position_risk:
            return False, f"Position risk {position_risk} exceeds limit {self.max_position_risk}"
        
        # Check portfolio VaR
        if self.risk_metrics:
            new_var = self._estimate_new_var_with_trade(trade)
            if new_var > self.max_portfolio_var:
                return False, f"New VaR {new_var} would exceed limit {self.max_portfolio_var}"
        
        # Check concentration
        symbol = trade.get('symbol')
        if symbol:
            new_concentration = self._calculate_new_concentration(symbol, trade)
            if new_concentration > self.max_concentration:
                return False, f"Concentration {new_concentration} would exceed limit {self.max_concentration}"
        
        # Check correlation
        correlation_with_portfolio = self._calculate_trade_correlation(trade)
        if correlation_with_portfolio > self.max_correlation:
            return False, f"Correlation {correlation_with_portfolio} exceeds limit {self.max_correlation}"
        
        return True, "Trade validated"
    
    def _estimate_new_var_with_trade(self, trade: Dict) -> float:
        """Estimate new VaR if trade is added"""
        # Simplified - would recalculate with new position
        current_var = self.risk_metrics.portfolio_var if self.risk_metrics else 0
        trade_var = trade.get('risk', 0.5) * trade.get('size', 0) * 0.01
        
        # Assume some diversification benefit
        new_var = np.sqrt(current_var**2 + trade_var**2)
        
        return new_var
    
    def _calculate_new_concentration(self, symbol: str, trade: Dict) -> float:
        """Calculate new concentration if trade is added"""
        total_value = sum(pos['value'] for pos in self.positions.values())
        trade_value = trade.get('size', 0)
        
        existing_position = self.positions.get(symbol, {}).get('value', 0)
        new_position = existing_position + trade_value
        new_total = total_value + trade_value
        
        if new_total == 0:
            return 0
        
        return new_position / new_total
    
    def _calculate_trade_correlation(self, trade: Dict) -> float:
        """Calculate correlation of trade with portfolio"""
        # Simplified - would use actual correlation data
        return 0.5


class PositionSizer:
    """
    Optimal position sizing using various methods
    """
    
    def __init__(self):
        self.methods = {
            'kelly': self._kelly_criterion,
            'fixed_fractional': self._fixed_fractional,
            'optimal_f': self._optimal_f,
            'risk_parity': self._risk_parity,
            'max_diversification': self._max_diversification
        }
    
    def calculate_position_size(self, opportunity: Dict, portfolio: Dict, 
                               method: str = 'kelly') -> float:
        """
        Calculate optimal position size
        """
        if method in self.methods:
            return self.methods[method](opportunity, portfolio)
        
        return self._kelly_criterion(opportunity, portfolio)
    
    def _kelly_criterion(self, opportunity: Dict, portfolio: Dict) -> float:
        """Kelly criterion position sizing"""
        win_prob = opportunity.get('success_probability', 0.5)
        win_loss_ratio = opportunity.get('expected_return', 0.01) / opportunity.get('risk', 0.01)
        
        if win_loss_ratio == 0:
            return 0
        
        # Kelly formula
        kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        
        # Apply Kelly fraction cap
        kelly_fraction = max(0, min(0.25, kelly_fraction))
        
        # Calculate position size
        available_capital = portfolio.get('available_capital', 100000)
        position_size = available_capital * kelly_fraction
        
        return position_size
    
    def _fixed_fractional(self, opportunity: Dict, portfolio: Dict) -> float:
        """Fixed fractional position sizing"""
        risk_per_trade = 0.02  # Risk 2% per trade
        
        available_capital = portfolio.get('available_capital', 100000)
        stop_loss = opportunity.get('stop_loss_percent', 0.05)
        
        if stop_loss == 0:
            return 0
        
        position_size = (available_capital * risk_per_trade) / stop_loss
        
        return position_size
    
    def _optimal_f(self, opportunity: Dict, portfolio: Dict) -> float:
        """Ralph Vince's Optimal f position sizing"""
        # Simplified - would use historical trade results
        
        # Use conservative estimate
        optimal_f = 0.15
        
        available_capital = portfolio.get('available_capital', 100000)
        position_size = available_capital * optimal_f
        
        return position_size
    
    def _risk_parity(self, opportunity: Dict, portfolio: Dict) -> float:
        """Risk parity position sizing"""
        target_risk = 0.01  # 1% risk contribution
        
        opportunity_vol = opportunity.get('volatility', 0.2)
        
        if opportunity_vol == 0:
            return 0
        
        # Size inversely proportional to volatility
        available_capital = portfolio.get('available_capital', 100000)
        position_size = (available_capital * target_risk) / opportunity_vol
        
        return position_size
    
    def _max_diversification(self, opportunity: Dict, portfolio: Dict) -> float:
        """Maximum diversification position sizing"""
        # Simplified - would optimize for maximum diversification ratio
        
        num_positions = len(portfolio.get('positions', {}))
        target_positions = 20
        
        # Equal weight if below target, reduced if above
        if num_positions < target_positions:
            weight = 1 / target_positions
        else:
            weight = 1 / (num_positions + 1)
        
        available_capital = portfolio.get('available_capital', 100000)
        position_size = available_capital * weight
        
        return position_size


class HedgeCalculator:
    """
    Calculates optimal hedges for portfolio protection
    """
    
    def __init__(self):
        self.hedge_instruments = ['VIX', 'PUT_OPTIONS', 'GOLD', 'BONDS', 'INVERSE_ETF']
    
    def calculate_hedge(self, positions: Dict, market_data: Dict, 
                       risk_metrics: RiskMetrics) -> Dict:
        """
        Calculate optimal hedge for portfolio
        """
        hedge_recommendations = {}
        
        # Tail risk hedge
        if risk_metrics and risk_metrics.tail_risk > 0.5:
            hedge_recommendations['tail_hedge'] = self._calculate_tail_hedge(positions)
        
        # Correlation hedge
        if risk_metrics and risk_metrics.correlation_risk > 0.7:
            hedge_recommendations['correlation_hedge'] = self._calculate_correlation_hedge(positions)
        
        # Drawdown protection
        if risk_metrics and risk_metrics.current_drawdown > 0.1:
            hedge_recommendations['drawdown_hedge'] = self._calculate_drawdown_hedge(positions)
        
        # Calculate hedge ratios
        hedge_ratios = self._optimize_hedge_ratios(hedge_recommendations, positions)
        
        return {
            'recommendations': hedge_recommendations,
            'ratios': hedge_ratios,
            'estimated_cost': self._calculate_hedge_cost(hedge_ratios),
            'protection_level': self._calculate_protection_level(hedge_ratios)
        }
    
    def _calculate_tail_hedge(self, positions: Dict) -> Dict:
        """Calculate tail risk hedge"""
        portfolio_value = sum(pos['value'] for pos in positions.values())
        
        return {
            'instrument': 'PUT_OPTIONS',
            'strike': 'ATM-10%',  # 10% out of the money
            'size': portfolio_value * 0.05,  # Hedge 5% of portfolio
            'expiry': '30_days'
        }
    
    def _calculate_correlation_hedge(self, positions: Dict) -> Dict:
        """Calculate correlation hedge"""
        return {
            'instrument': 'VIX',
            'size': sum(pos['value'] for pos in positions.values()) * 0.02,
            'type': 'CALL_OPTIONS'
        }
    
    def _calculate_drawdown_hedge(self, positions: Dict) -> Dict:
        """Calculate drawdown protection hedge"""
        return {
            'instrument': 'INVERSE_ETF',
            'size': sum(pos['value'] for pos in positions.values()) * 0.1,
            'rebalance_frequency': 'daily'
        }
    
    def _optimize_hedge_ratios(self, recommendations: Dict, positions: Dict) -> Dict:
        """Optimize hedge ratios"""
        # Simplified - would use portfolio optimization
        
        ratios = {}
        for hedge_type, hedge in recommendations.items():
            ratios[hedge_type] = {
                'ratio': 0.1,  # 10% hedge ratio
                'delta': -0.5,  # Delta of hedge
                'gamma': 0.02,
                'cost_ratio': 0.005  # 0.5% of portfolio
            }
        
        return ratios
    
    def _calculate_hedge_cost(self, hedge_ratios: Dict) -> float:
        """Calculate total hedge cost"""
        total_cost = sum(h.get('cost_ratio', 0) for h in hedge_ratios.values())
        return total_cost
    
    def _calculate_protection_level(self, hedge_ratios: Dict) -> float:
        """Calculate protection level provided by hedges"""
        # Simplified - would calculate actual portfolio protection
        protection = sum(h.get('ratio', 0) * abs(h.get('delta', 0)) 
                        for h in hedge_ratios.values())
        return min(1.0, protection)


class DrawdownController:
    """
    Controls and limits portfolio drawdowns
    """
    
    def __init__(self):
        self.max_drawdown = 0.20  # 20% maximum
        self.drawdown_levels = {
            0.05: 'warning',
            0.10: 'reduce',
            0.15: 'defensive',
            0.20: 'stop'
        }
        self.equity_peak = 100000
        self.current_equity = 100000
    
    def check_drawdown(self, current_equity: float) -> Tuple[str, Dict]:
        """
        Check current drawdown and return action
        """
        self.current_equity = current_equity
        
        # Update peak
        if current_equity > self.equity_peak:
            self.equity_peak = current_equity
        
        # Calculate drawdown
        drawdown = (self.equity_peak - current_equity) / self.equity_peak if self.equity_peak > 0 else 0
        
        # Determine action
        action = 'normal'
        for level, level_action in self.drawdown_levels.items():
            if drawdown >= level:
                action = level_action
        
        # Generate recommendations
        recommendations = self._generate_drawdown_recommendations(drawdown, action)
        
        return action, recommendations
    
    def _generate_drawdown_recommendations(self, drawdown: float, action: str) -> Dict:
        """Generate recommendations based on drawdown level"""
        recommendations = {
            'current_drawdown': drawdown,
            'action': action,
            'position_adjustment': 1.0,
            'new_trades_allowed': True,
            'hedge_required': False
        }
        
        if action == 'warning':
            recommendations['position_adjustment'] = 0.9  # Reduce by 10%
            
        elif action == 'reduce':
            recommendations['position_adjustment'] = 0.7  # Reduce by 30%
            recommendations['hedge_required'] = True
            
        elif action == 'defensive':
            recommendations['position_adjustment'] = 0.5  # Reduce by 50%
            recommendations['new_trades_allowed'] = False
            recommendations['hedge_required'] = True
            
        elif action == 'stop':
            recommendations['position_adjustment'] = 0.2  # Keep only 20%
            recommendations['new_trades_allowed'] = False
            recommendations['hedge_required'] = True
            recommendations['emergency_exit'] = True
        
        return recommendations
