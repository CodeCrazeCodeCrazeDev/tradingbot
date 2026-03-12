"""Portfolio-level risk management system."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio."""
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    portfolio_delta: float
    portfolio_gamma: float
    portfolio_vega: float
    max_drawdown: float
    current_drawdown: float
    correlation_risk: float
    sector_exposure: Dict[str, float]
    total_exposure: float
    risk_score: float


class PortfolioRiskManager:
    """Manage portfolio-level risk."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize portfolio risk manager."""
        try:
            self.config = config or {}
            self.max_var = self.config.get('max_var', 0.05)
            self.max_cvar = self.config.get('max_cvar', 0.08)
            self.max_drawdown = self.config.get('max_drawdown', 0.15)
            self.max_correlation_risk = self.config.get('max_correlation_risk', 0.10)
            self.max_sector_exposure = self.config.get('max_sector_exposure', 0.25)
        
            self.positions = {}
            self.peak_equity = None
            self.current_equity = 0
            self.returns_history = []
            self.max_history = 252  # 1 year of daily returns
        
            logger.info("PortfolioRiskManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_position(self, position_id: str, symbol: str, size: float, 
                    entry_price: float, sector: str = "other"):
        """Add position to portfolio."""
        try:
            self.positions[position_id] = {
                'symbol': symbol,
                'size': size,
                'entry_price': entry_price,
                'sector': sector,
                'current_price': entry_price,
                'pnl': 0
            }
            logger.info(f"Added position: {symbol} ({size} @ {entry_price})")
        except Exception as e:
            logger.error(f"Error in add_position: {e}")
            raise
    
    def remove_position(self, position_id: str):
        """Remove position from portfolio."""
        try:
            if position_id in self.positions:
                pos = self.positions.pop(position_id)
                logger.info(f"Removed position: {pos['symbol']}")
        except Exception as e:
            logger.error(f"Error in remove_position: {e}")
            raise
    
    def update_position_price(self, position_id: str, current_price: float):
        """Update position current price."""
        try:
            if position_id in self.positions:
                pos = self.positions[position_id]
                pos['current_price'] = current_price
                pos['pnl'] = (current_price - pos['entry_price']) * pos['size']
        except Exception as e:
            logger.error(f"Error in update_position_price: {e}")
            raise
    
    def update_equity(self, current_equity: float):
        """Update current portfolio equity."""
        try:
            self.current_equity = current_equity
        
            if self.peak_equity is None:
                self.peak_equity = current_equity
            else:
                self.peak_equity = max(self.peak_equity, current_equity)
        
            # Track returns
            if self.returns_history:
                last_equity = self.returns_history[-1]['equity']
                daily_return = (current_equity - last_equity) / last_equity if last_equity > 0 else 0
            else:
                daily_return = 0
        
            self.returns_history.append({
                'timestamp': datetime.now(),
                'equity': current_equity,
                'return': daily_return
            })
        
            # Keep history size limited
            if len(self.returns_history) > self.max_history:
                self.returns_history.pop(0)
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise
    
    def calculate_var_cvar(self, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional VaR."""
        try:
            if len(self.returns_history) < 10:
                return 0.0, 0.0
        
            returns = np.array([r['return'] for r in self.returns_history])
        
            # VaR: percentile of returns
            var = np.percentile(returns, (1 - confidence) * 100)
        
            # CVaR: mean of returns worse than VaR
            cvar = returns[returns <= var].mean() if len(returns[returns <= var]) > 0 else var
        
            return abs(var), abs(cvar)
        except Exception as e:
            logger.error(f"Error in calculate_var_cvar: {e}")
            raise
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        try:
            if len(self.returns_history) < 2:
                return 0.0
        
            equities = np.array([r['equity'] for r in self.returns_history])
            running_max = np.maximum.accumulate(equities)
            drawdown = (equities - running_max) / running_max
        
            return float(np.min(drawdown))
        except Exception as e:
            logger.error(f"Error in calculate_max_drawdown: {e}")
            raise
    
    def get_current_drawdown(self) -> float:
        """Get current drawdown from peak."""
        try:
            if self.peak_equity is None or self.peak_equity == 0:
                return 0.0
        
            return (self.current_equity - self.peak_equity) / self.peak_equity
        except Exception as e:
            logger.error(f"Error in get_current_drawdown: {e}")
            raise
    
    def calculate_correlation_risk(self, correlation_matrix: np.ndarray) -> float:
        """Calculate portfolio correlation risk."""
        try:
            if len(self.positions) < 2:
                return 0.0
        
            # Simple correlation risk: average absolute correlation
            correlations = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
            return float(np.mean(np.abs(correlations)))
        except Exception as e:
            logger.error(f"Error in calculate_correlation_risk: {e}")
            raise
    
    def calculate_sector_exposure(self) -> Dict[str, float]:
        """Calculate exposure by sector."""
        try:
            sector_exposure = {}
            total_value = 0
        
            for pos in self.positions.values():
                sector = pos['sector']
                value = pos['size'] * pos['current_price']
                sector_exposure[sector] = sector_exposure.get(sector, 0) + value
                total_value += value
        
            # Normalize to percentages
            if total_value > 0:
                sector_exposure = {s: v / total_value for s, v in sector_exposure.items()}
        
            return sector_exposure
        except Exception as e:
            logger.error(f"Error in calculate_sector_exposure: {e}")
            raise
    
    def calculate_total_exposure(self) -> float:
        """Calculate total portfolio exposure."""
        try:
            total = 0
            for pos in self.positions.values():
                total += pos['size'] * pos['current_price']
            return total
        except Exception as e:
            logger.error(f"Error in calculate_total_exposure: {e}")
            raise
    
    def calculate_risk_metrics(self, correlation_matrix: Optional[np.ndarray] = None) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        try:
            var_95, cvar_95 = self.calculate_var_cvar(0.95)
            max_dd = self.calculate_max_drawdown()
            current_dd = self.get_current_drawdown()
            sector_exp = self.calculate_sector_exposure()
            total_exp = self.calculate_total_exposure()
        
            corr_risk = 0.0
            if correlation_matrix is not None:
                corr_risk = self.calculate_correlation_risk(correlation_matrix)
        
            # Calculate Greeks (simplified)
            portfolio_delta = sum(pos['size'] for pos in self.positions.values())
            portfolio_gamma = 0.0  # Simplified
            portfolio_vega = 0.0   # Simplified
        
            # Calculate risk score (0-100)
            risk_score = min(100, 
                (var_95 * 100) * 0.3 +
                (cvar_95 * 100) * 0.3 +
                (abs(max_dd) * 100) * 0.2 +
                (corr_risk * 100) * 0.2
            )
        
            return RiskMetrics(
                var_95=var_95,
                cvar_95=cvar_95,
                portfolio_delta=portfolio_delta,
                portfolio_gamma=portfolio_gamma,
                portfolio_vega=portfolio_vega,
                max_drawdown=max_dd,
                current_drawdown=current_dd,
                correlation_risk=corr_risk,
                sector_exposure=sector_exp,
                total_exposure=total_exp,
                risk_score=risk_score
            )
        except Exception as e:
            logger.error(f"Error in calculate_risk_metrics: {e}")
            raise
    
    def check_risk_limits(self, metrics: RiskMetrics) -> Tuple[bool, List[str]]:
        """Check if portfolio exceeds risk limits."""
        try:
            violations = []
        
            if metrics.var_95 > self.max_var:
                violations.append(f"VaR exceeds limit: {metrics.var_95:.2%} > {self.max_var:.2%}")
        
            if metrics.cvar_95 > self.max_cvar:
                violations.append(f"CVaR exceeds limit: {metrics.cvar_95:.2%} > {self.max_cvar:.2%}")
        
            if metrics.current_drawdown < -self.max_drawdown:
                violations.append(f"Drawdown exceeds limit: {metrics.current_drawdown:.2%} < -{self.max_drawdown:.2%}")
        
            if metrics.correlation_risk > self.max_correlation_risk:
                violations.append(f"Correlation risk exceeds limit: {metrics.correlation_risk:.2%} > {self.max_correlation_risk:.2%}")
        
            for sector, exposure in metrics.sector_exposure.items():
                if exposure > self.max_sector_exposure:
                    violations.append(f"Sector {sector} exposure exceeds limit: {exposure:.2%} > {self.max_sector_exposure:.2%}")
        
            return len(violations) == 0, violations
        except Exception as e:
            logger.error(f"Error in check_risk_limits: {e}")
            raise
    
    def get_risk_report(self) -> Dict:
        """Get comprehensive risk report."""
        try:
            metrics = self.calculate_risk_metrics()
            is_safe, violations = self.check_risk_limits(metrics)
        
            return {
                'timestamp': datetime.now().isoformat(),
                'is_safe': is_safe,
                'risk_score': metrics.risk_score,
                'var_95': metrics.var_95,
                'cvar_95': metrics.cvar_95,
                'max_drawdown': metrics.max_drawdown,
                'current_drawdown': metrics.current_drawdown,
                'correlation_risk': metrics.correlation_risk,
                'sector_exposure': metrics.sector_exposure,
                'total_exposure': metrics.total_exposure,
                'violations': violations,
                'num_positions': len(self.positions)
            }
        except Exception as e:
            logger.error(f"Error in get_risk_report: {e}")
            raise
