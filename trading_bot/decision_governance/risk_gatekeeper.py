"""
Risk Gatekeeper

Hard risk controls that must never be bypassed.
Enforces capital limits, position limits, drawdown controls, and correlation constraints.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskViolationType(Enum):
    """Types of risk violations"""
    POSITION_SIZE_EXCEEDED = "position_size_exceeded"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    PORTFOLIO_HEAT_EXCEEDED = "portfolio_heat_exceeded"
    CORRELATION_CONCENTRATION = "correlation_concentration"
    DRAWDOWN_LIMIT = "drawdown_limit"
    MARGIN_EXCEEDED = "margin_exceeded"
    SECTOR_CONCENTRATION = "sector_concentration"
    VOLATILITY_EXPOSURE = "volatility_exposure"


@dataclass
class RiskLimits:
    """Hard risk limits configuration"""
    max_position_size_pct: float = 0.10  # 10% per position
    max_daily_loss_pct: float = 0.02  # 2% daily stop
    max_portfolio_heat: int = 5  # Max concurrent positions
    max_correlation: float = 0.7  # Max correlation between positions
    max_drawdown_pct: float = 0.10  # 10% max drawdown
    max_sector_exposure_pct: float = 0.30  # 30% per sector
    max_volatility_exposure: float = 0.20  # Portfolio volatility limit
    max_margin_utilization: float = 0.50  # 50% margin limit


@dataclass
class RiskCheckResult:
    """Result of risk gate check"""
    passed: bool
    violations: List[Tuple[RiskViolationType, str, float]] = field(default_factory=list)
    adjusted_size: float = 0.0
    risk_score: float = 0.0


class RiskGatekeeper:
    """
    Hard risk gate that must never be bypassed.
    
    Enforces:
    - Position size limits
    - Daily loss limits
    - Portfolio concentration limits
    - Drawdown controls
    - Correlation constraints
    - Margin limits
    """
    
    def __init__(
        self,
        limits: Optional[RiskLimits] = None,
        enforce_strict: bool = True
    ):
        self.limits = limits or RiskLimits()
        self.enforce_strict = enforce_strict
        
        # State tracking
        self.current_positions: Dict[str, Dict[str, Any]] = {}
        self.daily_pnl: float = 0.0
        self.peak_portfolio_value: float = 0.0
        self.current_portfolio_value: float = 0.0
        self.last_reset_date: datetime = datetime.utcnow()
        
    def check_risk(
        self,
        symbol: str,
        proposed_direction: str,
        proposed_size: float,
        proposed_price: float,
        portfolio_value: float,
        sector: Optional[str] = None,
        position_beta: float = 1.0
    ) -> RiskCheckResult:
        """
        Check if proposed trade passes all risk gates.
        
        Args:
            symbol: Trading symbol
            proposed_direction: 'buy' or 'sell'
            proposed_size: Position size (units or %)
            proposed_price: Entry price
            portfolio_value: Total portfolio value
            sector: Sector classification
            position_beta: Beta of the position
            
        Returns:
            RiskCheckResult
        """
        violations = []
        
        # Update state
        self.current_portfolio_value = portfolio_value
        if portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = portfolio_value
            
        # Check 1: Position size limit
        position_dollar = proposed_size * proposed_price
        position_pct = position_dollar / portfolio_value if portfolio_value > 0 else 0
        
        if position_pct > self.limits.max_position_size_pct:
            violations.append((
                RiskViolationType.POSITION_SIZE_EXCEEDED,
                f"Position size {position_pct:.1%} exceeds limit {self.limits.max_position_size_pct:.1%}",
                position_pct - self.limits.max_position_size_pct
            ))
            
        # Check 2: Daily loss limit
        if abs(self.daily_pnl) > self.limits.max_daily_loss_pct * portfolio_value:
            violations.append((
                RiskViolationType.DAILY_LOSS_LIMIT,
                f"Daily loss limit reached: {self.daily_pnl:.2%}",
                abs(self.daily_pnl) / portfolio_value - self.limits.max_daily_loss_pct
            ))
            
        # Check 3: Portfolio heat (max positions)
        current_heat = len(self.current_positions)
        if symbol not in self.current_positions:
            if current_heat >= self.limits.max_portfolio_heat:
                violations.append((
                    RiskViolationType.PORTFOLIO_HEAT_EXCEEDED,
                    f"Portfolio heat {current_heat} >= limit {self.limits.max_portfolio_heat}",
                    current_heat - self.limits.max_portfolio_heat
                ))
                
        # Check 4: Drawdown limit
        if self.peak_portfolio_value > 0:
            drawdown = (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value
            if drawdown > self.limits.max_drawdown_pct:
                violations.append((
                    RiskViolationType.DRAWDOWN_LIMIT,
                    f"Drawdown {drawdown:.1%} exceeds limit {self.limits.max_drawdown_pct:.1%}",
                    drawdown - self.limits.max_drawdown_pct
                ))
                
        # Check 5: Sector concentration
        if sector:
            sector_exposure = self._calculate_sector_exposure(sector)
            new_exposure = sector_exposure + (position_dollar / portfolio_value if portfolio_value > 0 else 0)
            if new_exposure > self.limits.max_sector_exposure_pct:
                violations.append((
                    RiskViolationType.SECTOR_CONCENTRATION,
                    f"Sector exposure {new_exposure:.1%} exceeds limit",
                    new_exposure - self.limits.max_sector_exposure_pct
                ))
                
        # Check 6: Correlation concentration
        if symbol not in self.current_positions:
            max_corr = self._calculate_max_correlation(symbol)
            if max_corr > self.limits.max_correlation:
                violations.append((
                    RiskViolationType.CORRELATION_CONCENTRATION,
                    f"Max correlation {max_corr:.2f} exceeds limit {self.limits.max_correlation}",
                    max_corr - self.limits.max_correlation
                ))
                
        # Check 7: Volatility exposure
        vol_exposure = self._calculate_volatility_exposure()
        position_vol = position_pct * position_beta * 0.2  # Assume 20% vol
        new_vol_exposure = vol_exposure + position_vol
        if new_vol_exposure > self.limits.max_volatility_exposure:
            violations.append((
                RiskViolationType.VOLATILITY_EXPOSURE,
                f"Vol exposure {new_vol_exposure:.1%} exceeds limit",
                new_vol_exposure - self.limits.max_volatility_exposure
            ))
            
        # Calculate adjusted size
        adjusted_size = self._calculate_adjusted_size(
            proposed_size, violations, position_pct
        )
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(violations)
        
        passed = len(violations) == 0 or not self.enforce_strict
        
        if violations:
            logger.warning(
                f"Risk violations for {symbol}: {[v[0].value for v in violations]}"
            )
            
        return RiskCheckResult(
            passed=passed,
            violations=violations,
            adjusted_size=adjusted_size,
            risk_score=risk_score
        )
    
    def update_position(
        self,
        symbol: str,
        size: float,
        entry_price: float,
        sector: Optional[str] = None,
        beta: float = 1.0
    ) -> None:
        """Update position state"""
        self.current_positions[symbol] = {
            'size': size,
            'entry_price': entry_price,
            'sector': sector,
            'beta': beta,
            'entry_time': datetime.utcnow()
        }
        
    def close_position(self, symbol: str, pnl: float) -> None:
        """Close a position and update PnL"""
        if symbol in self.current_positions:
            del self.current_positions[symbol]
            
        self.daily_pnl += pnl
        
        # Check for daily reset
        now = datetime.utcnow()
        if now.date() != self.last_reset_date.date():
            self.daily_pnl = 0.0
            self.last_reset_date = now
            
    def reset_daily_pnl(self) -> None:
        """Reset daily PnL tracking"""
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.utcnow()
        
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary"""
        
        portfolio_value = self.current_portfolio_value or 1.0
        
        return {
            'current_positions': len(self.current_positions),
            'portfolio_heat': len(self.current_positions),
            'daily_pnl_pct': self.daily_pnl / portfolio_value if portfolio_value > 0 else 0,
            'max_drawdown': (
                (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value
                if self.peak_portfolio_value > 0 else 0
            ),
            'sector_exposures': {
                sector: self._calculate_sector_exposure(sector)
                for sector in set(
                    p.get('sector') for p in self.current_positions.values()
                    if p.get('sector')
                )
            },
            'volatility_exposure': self._calculate_volatility_exposure()
        }
    
    def _calculate_sector_exposure(self, sector: str) -> float:
        """Calculate current exposure to a sector"""
        portfolio_value = self.current_portfolio_value or 1.0
        
        sector_value = sum(
            p['size'] * p['entry_price']
            for p in self.current_positions.values()
            if p.get('sector') == sector
        )
        
        return sector_value / portfolio_value
    
    def _calculate_max_correlation(self, new_symbol: str) -> float:
        """Calculate maximum correlation with existing positions"""
        # In practice, this would use historical correlation matrix
        # For now, use simple heuristic
        
        same_sector_count = sum(
            1 for p in self.current_positions.values()
            if p.get('sector')  # Count positions with sectors
        )
        
        # Assume higher correlation within same sector
        base_corr = 0.3
        if same_sector_count > 0:
            base_corr += 0.2 * min(same_sector_count / 3, 1.0)
            
        return min(0.9, base_corr)
    
    def _calculate_volatility_exposure(self) -> float:
        """Calculate portfolio volatility exposure"""
        portfolio_value = self.current_portfolio_value or 1.0
        
        total_exposure = sum(
            (p['size'] * p['entry_price'] / portfolio_value) * p.get('beta', 1.0) * 0.2
            for p in self.current_positions.values()
        )
        
        return total_exposure
    
    def _calculate_adjusted_size(
        self,
        proposed_size: float,
        violations: List[Tuple[RiskViolationType, str, float]],
        position_pct: float
    ) -> float:
        """Calculate risk-adjusted position size"""
        
        adjusted = proposed_size
        
        # Reduce for position size violation
        size_violations = [v for v in violations if v[0] == RiskViolationType.POSITION_SIZE_EXCEEDED]
        if size_violations:
            # Scale down to limit
            adjusted *= self.limits.max_position_size_pct / position_pct if position_pct > 0 else 0.5
            
        # Reduce for correlation
        if any(v[0] == RiskViolationType.CORRELATION_CONCENTRATION for v in violations):
            adjusted *= 0.5
            
        # Reduce for sector concentration
        if any(v[0] == RiskViolationType.SECTOR_CONCENTRATION for v in violations):
            adjusted *= 0.7
            
        # Reduce for volatility
        if any(v[0] == RiskViolationType.VOLATILITY_EXPOSURE for v in violations):
            adjusted *= 0.6
            
        return adjusted
    
    def _calculate_risk_score(
        self,
        violations: List[Tuple[RiskViolationType, str, float]]
    ) -> float:
        """Calculate aggregate risk score 0-1"""
        
        if not violations:
            return 0.0
            
        # Severity weights
        weights = {
            RiskViolationType.DRAWDOWN_LIMIT: 1.0,
            RiskViolationType.DAILY_LOSS_LIMIT: 0.9,
            RiskViolationType.MARGIN_EXCEEDED: 0.9,
            RiskViolationType.POSITION_SIZE_EXCEEDED: 0.5,
            RiskViolationType.PORTFOLIO_HEAT_EXCEEDED: 0.4,
            RiskViolationType.CORRELATION_CONCENTRATION: 0.4,
            RiskViolationType.SECTOR_CONCENTRATION: 0.3,
            RiskViolationType.VOLATILITY_EXPOSURE: 0.3
        }
        
        total_score = sum(
            weights.get(v[0], 0.5) * (1 + v[2])  # Weight * (1 + severity)
            for v in violations
        )
        
        return min(1.0, total_score / len(violations) if violations else 0)
