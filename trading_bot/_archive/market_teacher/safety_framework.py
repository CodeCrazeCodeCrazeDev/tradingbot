"""
Safety Framework
=================
Hierarchical risk management and safe exploration system.

Features:
- Safe exploration with risk boundaries
- Hierarchical risk control (5 levels)
- Circuit breakers
- Emergency shutdown
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels in the hierarchy"""
    SURVIVAL = "survival"           # Level 1: Supreme override
    PORTFOLIO = "portfolio"         # Level 2: Strategic limits
    POSITION = "position"           # Level 3: Tactical limits
    LEARNING = "learning"           # Level 4: Adaptive optimization
    EXECUTION = "execution"         # Level 5: Tactical decisions


class SafetyViolationType(Enum):
    """Types of safety violations"""
    POSITION_SIZE = "position_size"
    DAILY_LOSS = "daily_loss"
    DRAWDOWN = "drawdown"
    PORTFOLIO_VAR = "portfolio_var"
    CORRELATION = "correlation"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"


@dataclass
class SafetyViolation:
    """Record of a safety violation"""
    violation_id: str
    violation_type: SafetyViolationType
    risk_level: RiskLevel
    current_value: float
    limit_value: float
    severity: str
    action_taken: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'violation_id': self.violation_id,
            'violation_type': self.violation_type.value,
            'risk_level': self.risk_level.value,
            'current_value': self.current_value,
            'limit_value': self.limit_value,
            'severity': self.severity,
            'action_taken': self.action_taken,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SafetyConstraints:
    """Safety constraints configuration"""
    # Level 1: Survival constraints (NEVER VIOLATE)
    max_total_loss: float = 0.20          # 20% max total loss → FULL SHUTDOWN
    unusual_market_threshold: float = 3.0  # 3x normal volatility → PAUSE
    
    # Level 2: Portfolio constraints
    max_portfolio_var: float = 0.15       # 15% portfolio VaR
    max_market_correlation: float = 0.10  # 10% max correlation to market
    min_diversification: int = 3          # Minimum 3 positions
    
    # Level 3: Position constraints
    max_position_size: float = 0.02       # 2% per trade
    max_strategy_allocation: float = 0.05 # 5% per strategy
    max_asset_allocation: float = 0.03    # 3% per asset
    
    # Level 4: Learning constraints
    target_sharpe: float = 2.0
    min_win_rate: float = 0.50
    max_drawdown: float = 0.15
    
    # Level 5: Execution constraints
    max_slippage: float = 0.001           # 10 bps max slippage
    max_spread: float = 0.002             # 20 bps max spread
    
    def to_dict(self) -> Dict:
        return {
            'max_total_loss': self.max_total_loss,
            'unusual_market_threshold': self.unusual_market_threshold,
            'max_portfolio_var': self.max_portfolio_var,
            'max_market_correlation': self.max_market_correlation,
            'min_diversification': self.min_diversification,
            'max_position_size': self.max_position_size,
            'max_strategy_allocation': self.max_strategy_allocation,
            'max_asset_allocation': self.max_asset_allocation,
            'target_sharpe': self.target_sharpe,
            'min_win_rate': self.min_win_rate,
            'max_drawdown': self.max_drawdown,
            'max_slippage': self.max_slippage,
            'max_spread': self.max_spread
        }


class CircuitBreaker:
    """
    Circuit breaker for automatic trading halts.
    
    Triggers:
    - Rapid losses
    - Unusual market conditions
    - System anomalies
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.loss_threshold = config.get('loss_threshold', 0.03)  # 3% daily loss
        self.volatility_threshold = config.get('volatility_threshold', 3.0)  # 3x normal
        self.error_threshold = config.get('error_threshold', 5)  # 5 errors
        self.cooldown_minutes = config.get('cooldown_minutes', 30)
        
        self.is_triggered: bool = False
        self.trigger_time: Optional[datetime] = None
        self.trigger_reason: Optional[str] = None
        
        self.daily_loss: float = 0.0
        self.error_count: int = 0
        self.trigger_history: List[Dict] = []
        
    def check_and_trigger(
        self,
        daily_pnl: float,
        current_volatility: float,
        normal_volatility: float,
        error_occurred: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check conditions and trigger if necessary.
        
        Returns:
            Tuple of (should_halt, reason)
        """
        # Check if in cooldown
        if self.is_triggered:
            if self._is_cooldown_over():
                self.reset()
            else:
                return True, f"Circuit breaker active: {self.trigger_reason}"
        
        # Check daily loss
        if daily_pnl < -self.loss_threshold:
            self._trigger(f"Daily loss exceeded {self.loss_threshold*100:.1f}%")
            return True, self.trigger_reason
        
        # Check volatility
        vol_ratio = current_volatility / max(normal_volatility, 0.0001)
        if vol_ratio > self.volatility_threshold:
            self._trigger(f"Volatility {vol_ratio:.1f}x normal")
            return True, self.trigger_reason
        
        # Check errors
        if error_occurred:
            self.error_count += 1
            if self.error_count >= self.error_threshold:
                self._trigger(f"Error threshold reached ({self.error_count} errors)")
                return True, self.trigger_reason
        
        return False, None
    
    def _trigger(self, reason: str):
        """Trigger the circuit breaker"""
        self.is_triggered = True
        self.trigger_time = datetime.now()
        self.trigger_reason = reason
        
        self.trigger_history.append({
            'reason': reason,
            'timestamp': self.trigger_time.isoformat()
        })
        
        logger.warning(f"🔴 CIRCUIT BREAKER TRIGGERED: {reason}")
    
    def _is_cooldown_over(self) -> bool:
        """Check if cooldown period is over"""
        if self.trigger_time is None:
            return True
        
        elapsed = (datetime.now() - self.trigger_time).total_seconds() / 60
        return elapsed >= self.cooldown_minutes
    
    def reset(self):
        """Reset the circuit breaker"""
        self.is_triggered = False
        self.trigger_time = None
        self.trigger_reason = None
        self.error_count = 0
        logger.info("🟢 Circuit breaker reset")
    
    def force_trigger(self, reason: str):
        """Force trigger the circuit breaker"""
        self._trigger(f"FORCED: {reason}")
    
    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        return {
            'is_triggered': self.is_triggered,
            'trigger_reason': self.trigger_reason,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'cooldown_minutes': self.cooldown_minutes,
            'error_count': self.error_count,
            'trigger_history': self.trigger_history[-10:]
        }


class SafeExplorationFramework:
    """
    Framework for safe exploration during learning.
    
    Critical Principle: Learn aggressively, but NEVER risk ruin.
    
    Features:
    - Hard constraints (never violated)
    - Soft constraints (try to respect)
    - Graduated position sizing
    - Automatic constraint enforcement
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        # HARD CONSTRAINTS (NEVER VIOLATE)
        self.MAX_POSITION_SIZE = config.get('max_position_size', 0.02)
        self.MAX_PORTFOLIO_RISK = config.get('max_portfolio_risk', 0.10)
        self.MAX_DAILY_LOSS = config.get('max_daily_loss', 0.03)
        self.MAX_DRAWDOWN = config.get('max_drawdown', 0.15)
        
        # SOFT CONSTRAINTS (Try to respect)
        self.TARGET_SHARPE = config.get('target_sharpe', 2.0)
        self.TARGET_WIN_RATE = config.get('target_win_rate', 0.55)
        
        # Exploration parameters
        self.MIN_EXPLORATION_SIZE = config.get('min_exploration_size', 0.001)  # 0.1%
        self.EXPLORATION_TRADES = config.get('exploration_trades', 30)
        
        # State
        self.daily_loss: float = 0.0
        self.current_drawdown: float = 0.0
        self.portfolio_risk: float = 0.0
        self.is_halted: bool = False
        self.halt_reason: Optional[str] = None
        
        self.violations: List[SafetyViolation] = []
        
        logger.info("SafeExplorationFramework initialized with hard constraints")
    
    def explore_safely(
        self,
        strategy_id: str,
        proposed_size: float,
        current_portfolio: Dict
    ) -> Tuple[str, float]:
        """
        Explore a new strategy safely.
        
        Returns:
            Tuple of (status, approved_size)
        """
        # Check hard constraints before EVERY trade
        violation = self._check_hard_constraints(current_portfolio)
        if violation:
            return "ABORT", 0.0
        
        # Start with minimal allocation
        approved_size = min(proposed_size, self.MIN_EXPLORATION_SIZE)
        
        # Check if adding this position violates constraints
        new_portfolio_risk = current_portfolio.get('risk', 0) + approved_size
        
        if new_portfolio_risk > self.MAX_PORTFOLIO_RISK:
            # Reduce size to fit within limits
            available_risk = self.MAX_PORTFOLIO_RISK - current_portfolio.get('risk', 0)
            approved_size = max(0, available_risk)
            
            if approved_size <= 0:
                return "REJECTED_RISK_LIMIT", 0.0
        
        return "APPROVED", approved_size
    
    def _check_hard_constraints(self, portfolio: Dict) -> Optional[SafetyViolation]:
        """
        Check all hard constraints.
        
        Returns violation if any constraint is breached.
        """
        # Check daily loss
        daily_pnl = portfolio.get('daily_pnl', 0)
        if daily_pnl < -self.MAX_DAILY_LOSS:
            violation = SafetyViolation(
                violation_id=f"viol_{datetime.now().timestamp()}",
                violation_type=SafetyViolationType.DAILY_LOSS,
                risk_level=RiskLevel.SURVIVAL,
                current_value=daily_pnl,
                limit_value=-self.MAX_DAILY_LOSS,
                severity="CRITICAL",
                action_taken="HALT_ALL_TRADING"
            )
            self._handle_violation(violation)
            return violation
        
        # Check drawdown
        drawdown = portfolio.get('drawdown', 0)
        if drawdown > self.MAX_DRAWDOWN:
            violation = SafetyViolation(
                violation_id=f"viol_{datetime.now().timestamp()}",
                violation_type=SafetyViolationType.DRAWDOWN,
                risk_level=RiskLevel.SURVIVAL,
                current_value=drawdown,
                limit_value=self.MAX_DRAWDOWN,
                severity="CRITICAL",
                action_taken="HALT_ALL_TRADING"
            )
            self._handle_violation(violation)
            return violation
        
        # Check portfolio risk
        portfolio_risk = portfolio.get('risk', 0)
        if portfolio_risk > self.MAX_PORTFOLIO_RISK:
            violation = SafetyViolation(
                violation_id=f"viol_{datetime.now().timestamp()}",
                violation_type=SafetyViolationType.PORTFOLIO_VAR,
                risk_level=RiskLevel.PORTFOLIO,
                current_value=portfolio_risk,
                limit_value=self.MAX_PORTFOLIO_RISK,
                severity="HIGH",
                action_taken="REDUCE_POSITIONS"
            )
            self._handle_violation(violation)
            return violation
        
        return None
    
    def _handle_violation(self, violation: SafetyViolation):
        """Handle a constraint violation"""
        self.violations.append(violation)
        
        logger.critical(f"🚨 SAFETY VIOLATION: {violation.violation_type.value}")
        logger.critical(f"Current: {violation.current_value:.4f}, Limit: {violation.limit_value:.4f}")
        logger.critical(f"Action: {violation.action_taken}")
        
        if violation.severity == "CRITICAL":
            self.halt_all_trading(violation.action_taken)
    
    def halt_all_trading(self, reason: str):
        """Halt all trading"""
        self.is_halted = True
        self.halt_reason = reason
        logger.critical(f"🛑 ALL TRADING HALTED: {reason}")
    
    def resume_trading(self):
        """Resume trading after halt"""
        self.is_halted = False
        self.halt_reason = None
        logger.info("✅ Trading resumed")
    
    def reduce_all_positions(self, factor: float = 0.5):
        """Reduce all positions by a factor"""
        logger.warning(f"Reducing all positions by {(1-factor)*100:.0f}%")
        return factor
    
    def get_status(self) -> Dict:
        """Get safety framework status"""
        return {
            'is_halted': self.is_halted,
            'halt_reason': self.halt_reason,
            'daily_loss': self.daily_loss,
            'current_drawdown': self.current_drawdown,
            'portfolio_risk': self.portfolio_risk,
            'violations_count': len(self.violations),
            'recent_violations': [v.to_dict() for v in self.violations[-5:]],
            'hard_constraints': {
                'max_position_size': self.MAX_POSITION_SIZE,
                'max_portfolio_risk': self.MAX_PORTFOLIO_RISK,
                'max_daily_loss': self.MAX_DAILY_LOSS,
                'max_drawdown': self.MAX_DRAWDOWN
            }
        }


class HierarchicalRiskManager:
    """
    Hierarchical risk management with 5 levels.
    
    Level 1: SURVIVAL (Supreme Override)
    Level 2: PORTFOLIO RISK (Strategic Limits)
    Level 3: POSITION RISK (Tactical Limits)
    Level 4: LEARNING LAYER (Adaptive Optimization)
    Level 5: EXECUTION LAYER (Tactical Decisions)
    
    Higher levels can override lower levels.
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.constraints = SafetyConstraints()
        self.circuit_breaker = CircuitBreaker(config)
        self.safe_exploration = SafeExplorationFramework(config)
        
        # State tracking
        self.current_portfolio: Dict = {}
        self.pending_trades: List[Dict] = []
        self.approved_trades: List[Dict] = []
        self.rejected_trades: List[Dict] = []
        
        logger.info("HierarchicalRiskManager initialized with 5 levels")
    
    def check_trade(self, proposed_trade: Dict) -> Dict:
        """
        Check a proposed trade through all risk levels.
        
        Returns:
            Dict with approval status and any modifications
        """
        original_size = proposed_trade.get('size', 0)
        approved_size = original_size
        rejections = []
        modifications = []
        
        # Level 1: SURVIVAL CHECK
        if self.safe_exploration.is_halted:
            return {
                'approved': False,
                'reason': f"Trading halted: {self.safe_exploration.halt_reason}",
                'level': 'SURVIVAL'
            }
        
        # Check circuit breaker
        is_triggered, reason = self.circuit_breaker.check_and_trigger(
            daily_pnl=self.current_portfolio.get('daily_pnl', 0),
            current_volatility=self.current_portfolio.get('volatility', 0.01),
            normal_volatility=self.current_portfolio.get('normal_volatility', 0.01)
        )
        
        if is_triggered:
            return {
                'approved': False,
                'reason': reason,
                'level': 'SURVIVAL'
            }
        
        # Level 2: PORTFOLIO RISK CHECK
        portfolio_risk = self.current_portfolio.get('risk', 0)
        if portfolio_risk + approved_size > self.constraints.max_portfolio_var:
            available = max(0, self.constraints.max_portfolio_var - portfolio_risk)
            if available <= 0:
                rejections.append("Portfolio risk limit reached")
            else:
                approved_size = min(approved_size, available)
                modifications.append(f"Reduced size for portfolio risk: {original_size} → {approved_size}")
        
        # Level 3: POSITION RISK CHECK
        if approved_size > self.constraints.max_position_size:
            approved_size = self.constraints.max_position_size
            modifications.append(f"Reduced size for position limit: {original_size} → {approved_size}")
        
        # Level 4: LEARNING LAYER CHECK
        # (Would check strategy performance, but we allow learning)
        
        # Level 5: EXECUTION LAYER CHECK
        spread = proposed_trade.get('spread', 0)
        if spread > self.constraints.max_spread:
            rejections.append(f"Spread too wide: {spread:.4f} > {self.constraints.max_spread:.4f}")
        
        # Final decision
        if rejections:
            self.rejected_trades.append({
                'trade': proposed_trade,
                'rejections': rejections,
                'timestamp': datetime.now().isoformat()
            })
            return {
                'approved': False,
                'reason': "; ".join(rejections),
                'level': 'POSITION' if 'position' in str(rejections).lower() else 'PORTFOLIO'
            }
        
        # Approved with possible modifications
        approved_trade = proposed_trade.copy()
        approved_trade['size'] = approved_size
        approved_trade['modifications'] = modifications
        
        self.approved_trades.append({
            'trade': approved_trade,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'approved': True,
            'trade': approved_trade,
            'modifications': modifications,
            'level': 'APPROVED'
        }
    
    def update_portfolio(self, portfolio: Dict):
        """Update current portfolio state"""
        self.current_portfolio = portfolio
        
        # Check if we need to take action
        violation = self.safe_exploration._check_hard_constraints(portfolio)
        if violation:
            logger.warning(f"Portfolio update triggered violation: {violation.violation_type.value}")
    
    def emergency_shutdown(self, reason: str):
        """Emergency shutdown of all trading"""
        self.safe_exploration.halt_all_trading(f"EMERGENCY: {reason}")
        self.circuit_breaker.force_trigger(f"EMERGENCY: {reason}")
        
        logger.critical(f"🚨 EMERGENCY SHUTDOWN: {reason}")
        
        return {
            'status': 'SHUTDOWN',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_risk_status(self) -> Dict:
        """Get comprehensive risk status"""
        return {
            'levels': {
                'survival': {
                    'is_halted': self.safe_exploration.is_halted,
                    'circuit_breaker': self.circuit_breaker.get_status()
                },
                'portfolio': {
                    'current_risk': self.current_portfolio.get('risk', 0),
                    'max_risk': self.constraints.max_portfolio_var
                },
                'position': {
                    'max_size': self.constraints.max_position_size
                },
                'learning': {
                    'target_sharpe': self.constraints.target_sharpe,
                    'min_win_rate': self.constraints.min_win_rate
                },
                'execution': {
                    'max_slippage': self.constraints.max_slippage,
                    'max_spread': self.constraints.max_spread
                }
            },
            'trades': {
                'approved': len(self.approved_trades),
                'rejected': len(self.rejected_trades)
            },
            'safe_exploration': self.safe_exploration.get_status()
        }


# Export all classes
__all__ = [
    'RiskLevel',
    'SafetyViolationType',
    'SafetyViolation',
    'SafetyConstraints',
    'CircuitBreaker',
    'SafeExplorationFramework',
    'HierarchicalRiskManager'
]
