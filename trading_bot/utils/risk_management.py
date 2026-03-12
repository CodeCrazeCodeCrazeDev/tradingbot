"""
Risk Management Module - Compatibility Layer

This module provides compatibility imports from the main risk management system.
It acts as a bridge between different naming conventions used across the codebase.
"""
import numpy as np
from typing import Optional

try:
    from trading_bot.risk import (
        RiskManager,
        UnifiedRiskManager,
        AdvancedRiskManager,
        KellyCriterion,
        PositionSizeCalculator
    )
    from trading_bot.risk.ml_risk_manager import MlRiskManager as MLRiskManager
    from trading_bot.risk.monte_carlo import MonteCarloSimulator
    from trading_bot.risk.correlation_manager import CorrelationManager
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Optional risk imports failed: {e}")
    RiskManager = None
    UnifiedRiskManager = None
    AdvancedRiskManager = None
    MLRiskManager = None
    KellyCriterion = None
    PositionSizeCalculator = None
    MonteCarloSimulator = None
    CorrelationManager = None

# Additional risk management components
    from backtesting.backtest_engine import AdvancedBacktester
except ImportError:
    AdvancedBacktester = None


class RiskEngine:
    """
    Unified Risk Engine that combines multiple risk management components
    """
    
    def __init__(self, config=None):
        """
        Initialize Risk Engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.risk_manager = UnifiedRiskManager(config=self.config)
        self.kelly = KellyCriterion()
        self.position_calculator = PositionSizeCalculator()
        
        try:
            # Optional components
            self.monte_carlo = MonteCarloSimulator()
        except Exception:
            self.monte_carlo = None
            self.correlation_manager = CorrelationManager()
        except Exception:
            self.correlation_manager = None
    
    def calculate_position_size(self, symbol, risk_pct, stop_loss_pips, **kwargs):
        """Calculate position size based on risk parameters"""
        return self.risk_manager.calculate_position_size(
            symbol=symbol,
            risk_pct=risk_pct,
            sl_pips=stop_loss_pips
        )
    
    def check_risk_limits(self, symbol, position_size, **kwargs):
        """Check if trade passes risk limits"""
        return self.risk_manager.check_risk_limits(symbol, position_size)
    
    def get_portfolio_risk(self):
        """Get current portfolio risk metrics"""
        return self.risk_manager.get_portfolio_risk()


class VaRCalculator:
    """
    Value at Risk Calculator
    """
    
    def __init__(self, confidence_level=0.95):
        """
        Initialize VaR Calculator
        
        Args:
            confidence_level: Confidence level for VaR calculation (default 95%)
        """
        self.confidence_level = confidence_level
    
    def calculate_var(self, returns, method='historical'):
        """
        Calculate Value at Risk
        
        Args:
            returns: Array of returns
            method: Calculation method ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            VaR value
        """
        
        if method == 'historical':
            return np.percentile(returns, (1 - self.confidence_level) * 100)
        elif method == 'parametric':
            mean = np.mean(returns)
            std = np.std(returns)
            from scipy import stats
            z_score = stats.norm.ppf(1 - self.confidence_level)
            return mean + z_score * std
        else:
            # Monte Carlo method
            return np.percentile(returns, (1 - self.confidence_level) * 100)
    
    def calculate_cvar(self, returns):
        """
        Calculate Conditional Value at Risk (Expected Shortfall)
        
        Args:
            returns: Array of returns
            
        Returns:
            CVaR value
        """
        var = self.calculate_var(returns)
        return np.mean(returns[returns <= var])


class DrawdownMonitor:
    """
    Drawdown Monitoring System
    """
    
    def __init__(self, config=None):
        """
        Initialize Drawdown Monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.max_drawdown = self.config.get('max_drawdown', 0.15)  # 15%
        self.current_drawdown = 0.0
        self.peak_equity = 0.0
        self.current_equity = 0.0
    
    def update(self, equity):
        """
        Update drawdown calculation
        
        Args:
            equity: Current equity value
        """
        self.current_equity = equity
        
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - equity) / self.peak_equity
    
    def check_drawdown(self):
        """
        Check if drawdown is within limits
        
        Returns:
            True if within limits, False otherwise
        """
        return self.current_drawdown < self.max_drawdown
    
    def get_drawdown_level(self):
        """
        Get current drawdown level
        
        Returns:
            Drawdown level as percentage
        """
        return self.current_drawdown
    
    def get_status(self):
        """
        Get drawdown status
        
        Returns:
            Dictionary with drawdown information
        """
        return {
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'peak_equity': self.peak_equity,
            'current_equity': self.current_equity,
            'within_limits': self.check_drawdown()
        }


class PortfolioManager:
    """
    Portfolio Management System
    """
    
    def __init__(self, config=None):
        """
        Initialize Portfolio Manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.positions = {}
        self.max_positions = self.config.get('max_positions', 5)
        self.correlation_limit = self.config.get('correlation_limit', 0.7)
    
    def add_position(self, symbol, position_data):
        """Add a position to the portfolio"""
        if len(self.positions) >= self.max_positions:
            return False
        
        self.positions[symbol] = position_data
        return True
    
    def remove_position(self, symbol):
        """Remove a position from the portfolio"""
        if symbol in self.positions:
            del self.positions[symbol]
            return True
        return False
    
    def get_position(self, symbol):
        """Get position data for a symbol"""
        return self.positions.get(symbol)
    
    def get_all_positions(self):
        """Get all positions"""
        return self.positions
    
    def get_portfolio_value(self):
        """Calculate total portfolio value"""
        return sum(pos.get('value', 0) for pos in self.positions.values())
    
    def get_portfolio_risk(self):
        """Calculate portfolio risk metrics"""
        return {
            'num_positions': len(self.positions),
            'max_positions': self.max_positions,
            'utilization': len(self.positions) / self.max_positions if self.max_positions > 0 else 0
        }


# Export all components
__all__ = [
    'RiskEngine',
    'VaRCalculator',
    'DrawdownMonitor',
    'PortfolioManager',
    'RiskManager',
    'UnifiedRiskManager',
    'AdvancedRiskManager',
    'MLRiskManager',
    'KellyCriterion',
    'PositionSizeCalculator'
]
