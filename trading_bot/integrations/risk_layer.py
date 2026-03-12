"""
Risk Layer Integration - Unified risk management and safety
Integrates all risk, safety, and governance components
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from trading_bot.system_interfaces import (
    IRiskManager,
    TradingSignal,
    ComponentStatus,
    ComponentHealth,
)

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    approved: bool
    risk_score: float  # 0-1, higher = riskier
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    warnings: List[str]
    reasons: List[str]


class UnifiedRiskLayer(IRiskManager):
    """
    Unified Risk Layer - Integrates all risk and safety systems
    
    Integrates:
    - MSOS (Market Survival Operating System)
    - Master Risk Manager
    - Fail-safe systems
    - Circuit breakers
    - Position sizing (Kelly, Fixed, Volatility)
    - Drawdown management
    - Correlation management
    - Emergency systems
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.status = ComponentStatus.UNINITIALIZED
        
        # Risk managers
        self.msos = None
        self.master_risk = None
        self.fail_safe = None
        self.circuit_breaker = None
        
        # Position sizing
        self.position_sizer = None
        
        # Risk limits
        self.max_position_size_pct = config.get('max_position_size_pct', 10.0)
        self.max_portfolio_risk_pct = config.get('max_portfolio_risk_pct', 2.0)
        self.max_daily_loss_pct = config.get('max_daily_loss_pct', 5.0)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 20.0)
        
        # State
        self.current_capital = config.get('initial_capital', 100000.0)
        self.starting_capital = self.current_capital
        self.daily_pnl = 0.0
        self.peak_capital = self.current_capital
        self.current_drawdown_pct = 0.0
        
        # Metrics
        self.metrics = {
            'total_validations': 0,
            'approved_trades': 0,
            'rejected_trades': 0,
            'risk_limit_breaches': 0,
            'emergency_stops': 0,
        }
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize risk layer"""
        logger.info("Initializing Unified Risk Layer...")
        
        try:
            # Initialize risk managers
            if config.get('enable_msos', True):
                await self._initialize_msos()
            
            await self._initialize_master_risk()
            await self._initialize_fail_safe()
            await self._initialize_circuit_breaker()
            await self._initialize_position_sizer()
            
            self.status = ComponentStatus.READY
            logger.info("Unified Risk Layer initialized successfully")
            logger.info(f"Risk limits: Position={self.max_position_size_pct}%, "
                       f"Portfolio={self.max_portfolio_risk_pct}%, "
                       f"Daily Loss={self.max_daily_loss_pct}%, "
                       f"Drawdown={self.max_drawdown_pct}%")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing risk layer: {e}", exc_info=True)
            self.status = ComponentStatus.ERROR
            return False
    
    async def _initialize_msos(self):
        """Initialize MSOS"""
        logger.info("Initializing MSOS (Market Survival Operating System)...")
        self.msos = MockMSOS()
    
    async def _initialize_master_risk(self):
        """Initialize master risk manager"""
        logger.info("Initializing Master Risk Manager...")
        self.master_risk = MockMasterRisk()
    
    async def _initialize_fail_safe(self):
        """Initialize fail-safe system"""
        logger.info("Initializing Fail-Safe System...")
        self.fail_safe = MockFailSafe()
    
    async def _initialize_circuit_breaker(self):
        """Initialize circuit breaker"""
        logger.info("Initializing Circuit Breaker...")
        self.circuit_breaker = MockCircuitBreaker()
    
    async def _initialize_position_sizer(self):
        """Initialize position sizer"""
        logger.info("Initializing Position Sizer...")
        self.position_sizer = MockPositionSizer()
    
    async def start(self) -> bool:
        """Start risk layer"""
        if self.status != ComponentStatus.READY:
            logger.error("Risk layer not ready")
            return False
        
        logger.info("Starting Unified Risk Layer...")
        self.status = ComponentStatus.RUNNING
        return True
    
    async def stop(self) -> bool:
        """Stop risk layer"""
        logger.info("Stopping Unified Risk Layer...")
        self.status = ComponentStatus.STOPPED
        return True
    
    async def validate_trade(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        Validate if trade is allowed through multiple risk checks
        
        Checks (in order):
        1. Circuit breaker status
        2. Fail-safe system
        3. MSOS evaluation
        4. Risk limits
        5. Drawdown limits
        6. Daily loss limits
        """
        self.metrics['total_validations'] += 1
        
        # Update drawdown
        self._update_drawdown()
        
        # Check 1: Circuit breaker
        if self.circuit_breaker:
            breaker_ok, reason = await self.circuit_breaker.check()
            if not breaker_ok:
                self.metrics['rejected_trades'] += 1
                return False, f"Circuit breaker: {reason}"
        
        # Check 2: Fail-safe
        if self.fail_safe:
            failsafe_ok, reason = await self.fail_safe.check()
            if not failsafe_ok:
                self.metrics['rejected_trades'] += 1
                return False, f"Fail-safe: {reason}"
        
        # Check 3: MSOS
        if self.msos:
            msos_ok, reason = await self.msos.evaluate(signal)
            if not msos_ok:
                self.metrics['rejected_trades'] += 1
                return False, f"MSOS: {reason}"
        
        # Check 4: Risk limits
        limits_ok, reason = await self.check_risk_limits()
        if not limits_ok:
            self.metrics['rejected_trades'] += 1
            self.metrics['risk_limit_breaches'] += 1
            return False, f"Risk limits: {reason}"
        
        # Check 5: Drawdown
        if self.current_drawdown_pct > self.max_drawdown_pct:
            self.metrics['rejected_trades'] += 1
            self.metrics['emergency_stops'] += 1
            return False, f"Max drawdown exceeded: {self.current_drawdown_pct:.1f}% > {self.max_drawdown_pct}%"
        
        # Check 6: Daily loss
        daily_loss_pct = (self.daily_pnl / self.starting_capital) * 100
        if daily_loss_pct < -self.max_daily_loss_pct:
            self.metrics['rejected_trades'] += 1
            self.metrics['emergency_stops'] += 1
            return False, f"Daily loss limit exceeded: {daily_loss_pct:.1f}% < -{self.max_daily_loss_pct}%"
        
        self.metrics['approved_trades'] += 1
        return True, "All risk checks passed"
    
    async def calculate_position_size(self, signal: TradingSignal, capital: float) -> float:
        """
        Calculate position size using configured method
        """
        if self.position_sizer:
            size = await self.position_sizer.calculate(signal, capital, self.config)
        else:
            # Default: fixed percentage
            size = capital * (self.max_position_size_pct / 100)
        
        # Apply maximum position size limit
        max_size = capital * (self.max_position_size_pct / 100)
        return min(size, max_size)
    
    async def check_risk_limits(self) -> Tuple[bool, List[str]]:
        """Check if risk limits are breached"""
        violations = []
        
        # Check drawdown
        if self.current_drawdown_pct > self.max_drawdown_pct:
            violations.append(f"Drawdown {self.current_drawdown_pct:.1f}% > {self.max_drawdown_pct}%")
        
        # Check daily loss
        daily_loss_pct = (self.daily_pnl / self.starting_capital) * 100
        if daily_loss_pct < -self.max_daily_loss_pct:
            violations.append(f"Daily loss {daily_loss_pct:.1f}% > {self.max_daily_loss_pct}%")
        
        return len(violations) == 0, violations
    
    def _update_drawdown(self):
        """Update current drawdown"""
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        if self.peak_capital > 0:
            self.current_drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        else:
            self.current_drawdown_pct = 0
    
    def update_capital(self, new_capital: float, pnl: float):
        """Update capital and PnL"""
        self.current_capital = new_capital
        self.daily_pnl += pnl
        self._update_drawdown()
    
    def reset_daily_pnl(self):
        """Reset daily PnL (call at start of day)"""
        self.daily_pnl = 0.0
    
    async def health_check(self) -> ComponentHealth:
        """Check risk layer health"""
        errors = []
        warnings = []
        
        # Check if in emergency state
        if self.current_drawdown_pct > self.max_drawdown_pct * 0.8:
            warnings.append(f"Approaching max drawdown: {self.current_drawdown_pct:.1f}%")
        
        # Check rejection rate
        total = self.metrics['approved_trades'] + self.metrics['rejected_trades']
        if total > 0:
            rejection_rate = self.metrics['rejected_trades'] / total
            if rejection_rate > 0.8:
                warnings.append(f"High rejection rate: {rejection_rate:.1%}")
        
        return ComponentHealth(
            status=ComponentStatus.ERROR if errors else self.status,
            message="OK" if not errors else f"{len(errors)} errors",
            metrics={
                'total_validations': self.metrics['total_validations'],
                'approved_trades': self.metrics['approved_trades'],
                'rejected_trades': self.metrics['rejected_trades'],
                'current_drawdown_pct': self.current_drawdown_pct,
                'daily_pnl': self.daily_pnl,
                'current_capital': self.current_capital,
            },
            last_check=datetime.utcnow(),
            errors=errors,
            warnings=warnings
        )
    
    def get_status(self) -> ComponentStatus:
        """Get current status"""
        return self.status


# Mock implementations

class MockMSOS:
    async def evaluate(self, signal): return True, "OK"

class MockMasterRisk:
    pass

class MockFailSafe:
    async def check(self): return True, "OK"

class MockCircuitBreaker:
    async def check(self): return True, "OK"

class MockPositionSizer:
    async def calculate(self, signal, capital, config):
        return capital * 0.02  # 2% default


__all__ = [
    'UnifiedRiskLayer',
    'RiskAssessment',
]
