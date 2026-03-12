"""
Risk Validation Gate - Centralized Pre-Trade Validation
========================================================

This module provides comprehensive validation before any trade execution.
All trades must pass through this gate to ensure risk limits are enforced.

Author: AI Assistant
Date: October 19, 2025
Version: 1.0.0
"""

import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum, auto

from loguru import logger

class ValidationResult(Enum):
    """Validation result status."""
    APPROVED = auto()
    REJECTED = auto()
    WARNING = auto()

@dataclass
class ValidationResponse:
    """Response from validation gate."""
    result: ValidationResult
    approved: bool
    reasons: List[str]
    warnings: List[str]
    risk_score: float  # 0-100, higher is riskier
    timestamp: datetime
    
    def __post_init__(self):
        self.approved = (self.result == ValidationResult.APPROVED)

class RiskValidationGate:
    """
    Centralized Risk Validation Gate
    
    All trades must pass through this gate before execution.
    Enforces:
    - Position size limits
    - Daily/weekly/monthly loss limits
    - Portfolio risk limits
    - Correlation limits
    - Drawdown limits
    - Emergency shutdown checks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validation gate.
        
        Args:
            config: Configuration dictionary with risk limits
        """
        self.config = config or {}
        
        # Risk limits (from config or defaults)
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)  # 2%
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.05)  # 5%
        self.max_correlated_risk = self.config.get('max_correlated_risk', 0.08)  # 8%
        self.max_daily_loss = self.config.get('max_daily_loss', 0.05)  # 5%
        self.max_weekly_loss = self.config.get('max_weekly_loss', 0.10)  # 10%
        self.max_monthly_loss = self.config.get('max_monthly_loss', 0.20)  # 20%
        self.max_drawdown = self.config.get('max_drawdown', 0.25)  # 25%
        self.emergency_drawdown = self.config.get('emergency_drawdown', 0.30)  # 30%
        self.max_open_positions = self.config.get('max_open_positions', 10)
        self.max_correlated_positions = self.config.get('max_correlated_positions', 3)
        
        # State tracking
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.monthly_loss = 0.0
        self.current_drawdown = 0.0
        self.open_positions = {}
        self.emergency_shutdown = False
        
        # Time tracking for loss resets
        self.last_daily_reset = datetime.now()
        self.last_weekly_reset = datetime.now()
        self.last_monthly_reset = datetime.now()
        
        logger.info("Risk Validation Gate initialized")
    
    def validate_trade(
        self,
        symbol: str,
        position_size: float,
        risk_amount: float,
        risk_percent: float,
        direction: str,
        **kwargs
    ) -> ValidationResponse:
        """
        Validate a trade before execution.
        
        Args:
            symbol: Trading symbol
            position_size: Position size (lots)
            risk_amount: Risk amount in currency
            risk_percent: Risk as percentage of equity
            direction: Trade direction (LONG/SHORT)
            **kwargs: Additional parameters
            
        Returns:
            ValidationResponse with approval status and reasons
        """
        reasons = []
        warnings = []
        risk_score = 0.0
        
        try:
            # Reset time-based limits if needed
            self._reset_time_based_limits()
            
            # 1. Emergency shutdown check (CRITICAL)
            if self.emergency_shutdown:
                reasons.append("EMERGENCY SHUTDOWN ACTIVE - No new trades allowed")
                return ValidationResponse(
                    result=ValidationResult.REJECTED,
                    approved=False,
                    reasons=reasons,
                    warnings=warnings,
                    risk_score=100.0,
                    timestamp=datetime.now()
                )
            
            # 2. Drawdown check (CRITICAL)
            if self.current_drawdown >= self.emergency_drawdown:
                self.emergency_shutdown = True
                reasons.append(f"EMERGENCY: Drawdown {self.current_drawdown:.1%} >= {self.emergency_drawdown:.1%}")
                return ValidationResponse(
                    result=ValidationResult.REJECTED,
                    approved=False,
                    reasons=reasons,
                    warnings=warnings,
                    risk_score=100.0,
                    timestamp=datetime.now()
                )
            
            if self.current_drawdown >= self.max_drawdown:
                reasons.append(f"Drawdown limit exceeded: {self.current_drawdown:.1%} >= {self.max_drawdown:.1%}")
                risk_score += 30
            
            # 3. Position size validation
            if position_size <= 0:
                reasons.append(f"Invalid position size: {position_size}")
                return ValidationResponse(
                    result=ValidationResult.REJECTED,
                    approved=False,
                    reasons=reasons,
                    warnings=warnings,
                    risk_score=100.0,
                    timestamp=datetime.now()
                )
            
            # 4. Risk per trade check
            if risk_percent > self.max_risk_per_trade:
                reasons.append(f"Risk per trade too high: {risk_percent:.2%} > {self.max_risk_per_trade:.2%}")
                risk_score += 25
            
            # 5. Daily loss limit check
            if self.daily_loss >= self.max_daily_loss:
                reasons.append(f"Daily loss limit reached: {self.daily_loss:.2%} >= {self.max_daily_loss:.2%}")
                risk_score += 20
            
            # 6. Weekly loss limit check
            if self.weekly_loss >= self.max_weekly_loss:
                reasons.append(f"Weekly loss limit reached: {self.weekly_loss:.2%} >= {self.max_weekly_loss:.2%}")
                risk_score += 20
            
            # 7. Monthly loss limit check
            if self.monthly_loss >= self.max_monthly_loss:
                reasons.append(f"Monthly loss limit reached: {self.monthly_loss:.2%} >= {self.max_monthly_loss:.2%}")
                risk_score += 20
            
            # 8. Portfolio risk check
            total_portfolio_risk = sum(pos.get('risk_pct', 0) for pos in self.open_positions.values())
            if total_portfolio_risk + risk_percent > self.max_portfolio_risk:
                reasons.append(f"Portfolio risk limit exceeded: {total_portfolio_risk + risk_percent:.2%} > {self.max_portfolio_risk:.2%}")
                risk_score += 20
            
            # 9. Max open positions check
            if len(self.open_positions) >= self.max_open_positions:
                reasons.append(f"Max open positions reached: {len(self.open_positions)} >= {self.max_open_positions}")
                risk_score += 15
            
            # 10. Correlation check (simplified - would need actual correlation data)
            correlated_positions = self._count_correlated_positions(symbol)
            if correlated_positions >= self.max_correlated_positions:
                warnings.append(f"High correlated positions: {correlated_positions} for {symbol}")
                risk_score += 10
            
            # 11. Symbol already has position check
            if symbol in self.open_positions:
                warnings.append(f"Symbol {symbol} already has an open position")
                risk_score += 5
            
            # Determine result
            if reasons:
                result = ValidationResult.REJECTED
                approved = False
            elif warnings:
                result = ValidationResult.WARNING
                approved = True  # Approve with warnings
            else:
                result = ValidationResult.APPROVED
                approved = True
            
            return ValidationResponse(
                result=result,
                approved=approved,
                reasons=reasons,
                warnings=warnings,
                risk_score=min(risk_score, 100.0),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Validation error: {e}")

        try:
            import traceback
            logger.error(traceback.format_exc())
            
            return ValidationResponse(
                result=ValidationResult.REJECTED,
                approved=False,
                reasons=[f"Validation error: {str(e)}"],
                warnings=[],
                risk_score=100.0,
                timestamp=datetime.now()
            )
    
        except Exception:
            pass
    def _reset_time_based_limits(self):
        """Reset daily/weekly/monthly limits if time period has passed."""
        now = datetime.now()
        
        # Reset daily
        if (now - self.last_daily_reset).days >= 1:
            logger.info(f"Resetting daily loss: {self.daily_loss:.2%} → 0%")
            self.daily_loss = 0.0
            self.last_daily_reset = now
        
        # Reset weekly
        if (now - self.last_weekly_reset).days >= 7:
            logger.info(f"Resetting weekly loss: {self.weekly_loss:.2%} → 0%")
            self.weekly_loss = 0.0
            self.last_weekly_reset = now
        
        # Reset monthly
        if (now - self.last_monthly_reset).days >= 30:
            logger.info(f"Resetting monthly loss: {self.monthly_loss:.2%} → 0%")
            self.monthly_loss = 0.0
            self.last_monthly_reset = now
    
    def _count_correlated_positions(self, symbol: str) -> int:
        """Count positions correlated with given symbol (simplified)."""
        # Simplified correlation check - would need actual correlation matrix
        # For now, check for same currency pairs
        base_currency = symbol[:3] if len(symbol) >= 6 else symbol
        
        count = 0
        for pos_symbol in self.open_positions.keys():
            if base_currency in pos_symbol:
                count += 1
        
        return count
    
    def add_position(self, symbol: str, position_data: Dict[str, Any]):
        """Add position to tracking."""
        self.open_positions[symbol] = position_data
        logger.info(f"Position added: {symbol}, Total positions: {len(self.open_positions)}")
    
    def remove_position(self, symbol: str):
        """Remove position from tracking."""
        if symbol in self.open_positions:
            del self.open_positions[symbol]
            logger.info(f"Position removed: {symbol}, Total positions: {len(self.open_positions)}")
    
    def update_loss(self, loss_amount: float, loss_percent: float):
        """Update loss tracking."""
        self.daily_loss += loss_percent
        self.weekly_loss += loss_percent
        self.monthly_loss += loss_percent
        logger.info(f"Loss updated: Daily: {self.daily_loss:.2%}, Weekly: {self.weekly_loss:.2%}, Monthly: {self.monthly_loss:.2%}")
    
    def update_drawdown(self, drawdown: float):
        """Update current drawdown."""
        self.current_drawdown = drawdown
        logger.info(f"Drawdown updated: {drawdown:.2%}")
    
    def reset_emergency_shutdown(self):
        """Reset emergency shutdown (use with caution)."""
        logger.warning("Resetting emergency shutdown - ensure conditions have improved!")
        self.emergency_shutdown = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current validation gate status."""
        return {
            'emergency_shutdown': self.emergency_shutdown,
            'current_drawdown': self.current_drawdown,
            'daily_loss': self.daily_loss,
            'weekly_loss': self.weekly_loss,
            'monthly_loss': self.monthly_loss,
            'open_positions': len(self.open_positions),
            'limits': {
                'max_risk_per_trade': self.max_risk_per_trade,
                'max_portfolio_risk': self.max_portfolio_risk,
                'max_daily_loss': self.max_daily_loss,
                'max_weekly_loss': self.max_weekly_loss,
                'max_monthly_loss': self.max_monthly_loss,
                'max_drawdown': self.max_drawdown,
                'emergency_drawdown': self.emergency_drawdown,
                'max_open_positions': self.max_open_positions
            }
        }

# Global validation gate instance
_validation_gate = None

def get_validation_gate(config: Optional[Dict[str, Any]] = None) -> RiskValidationGate:
    """Get or create global validation gate instance."""
    global _validation_gate
    if _validation_gate is None:
        _validation_gate = RiskValidationGate(config)
    return _validation_gate

logger.info("Risk Validation Gate module loaded")
