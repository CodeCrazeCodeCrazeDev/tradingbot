"""
Systemic Protection
===================

Protects against systemic risks:
1. Market Impact - Prevent moving the market
2. Contagion - Prevent cascading failures
3. Regulatory Compliance - Stay within legal bounds
4. Counterparty Risk - Manage exposure to counterparties

PRINCIPLE: The system should not create systemic risk for itself or others.
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import hashlib

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class MarketImpactLevel(Enum):
    """Market impact levels"""
    NEGLIGIBLE = "negligible"   # < 0.01%
    LOW = "low"                 # 0.01% - 0.05%
    MODERATE = "moderate"       # 0.05% - 0.1%
    HIGH = "high"               # 0.1% - 0.5%
    SEVERE = "severe"           # > 0.5%


class RegulatoryRegime(Enum):
    """Regulatory regimes"""
    SEC = "sec"                 # US Securities
    CFTC = "cftc"               # US Commodities
    FCA = "fca"                 # UK
    ESMA = "esma"               # EU
    MAS = "mas"                 # Singapore
    ASIC = "asic"               # Australia


@dataclass
class MarketImpactEstimate:
    """Estimate of market impact"""
    symbol: str
    order_size: float
    avg_daily_volume: float
    participation_rate: float
    estimated_impact_bps: float
    impact_level: MarketImpactLevel
    recommended_max_size: float
    execution_strategy: str


@dataclass
class CounterpartyExposure:
    """Counterparty exposure record"""
    counterparty_id: str
    counterparty_name: str
    exposure_type: str
    gross_exposure: float
    net_exposure: float
    collateral: float
    credit_rating: str
    exposure_limit: float
    utilization: float


class MarketImpactLimiter:
    """
    Limits market impact of trades.
    
    IMMUTABLE LIMITS:
    - Maximum participation rate: 10% of ADV
    - Maximum single order: 5% of ADV
    - Maximum daily volume: 20% of ADV
    - Minimum execution time for large orders
    """
    
    # IMMUTABLE LIMITS
    MAX_PARTICIPATION_RATE = 0.10   # 10% of ADV
    MAX_SINGLE_ORDER = 0.05         # 5% of ADV
    MAX_DAILY_VOLUME = 0.20         # 20% of ADV
    
    # Impact thresholds (basis points)
    IMPACT_THRESHOLDS = {
        MarketImpactLevel.NEGLIGIBLE: 1,
        MarketImpactLevel.LOW: 5,
        MarketImpactLevel.MODERATE: 10,
        MarketImpactLevel.HIGH: 50,
        MarketImpactLevel.SEVERE: float('inf')
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Volume tracking
        self.daily_volume: Dict[str, float] = {}
        self.last_reset_date: Optional[str] = None
        
        # Impact history
        self.impact_history: deque = deque(maxlen=1000)
        
        logger.info("MarketImpactLimiter initialized")
    
    def estimate_impact(
        self,
        symbol: str,
        order_size: float,
        avg_daily_volume: float,
        current_spread_bps: float = 5
    ) -> MarketImpactEstimate:
        """
        Estimate market impact of an order.
        
        Uses simplified Almgren-Chriss model.
        """
        if avg_daily_volume <= 0:
            return MarketImpactEstimate(
                symbol=symbol,
                order_size=order_size,
                avg_daily_volume=0,
                participation_rate=1.0,
                estimated_impact_bps=1000,
                impact_level=MarketImpactLevel.SEVERE,
                recommended_max_size=0,
                execution_strategy="DO_NOT_TRADE"
            )
        
        # Calculate participation rate
        participation_rate = order_size / avg_daily_volume
        
        # Estimate impact (simplified model)
        # Impact = spread + temporary impact + permanent impact
        if NUMPY_AVAILABLE:
            temporary_impact = current_spread_bps * np.sqrt(participation_rate) * 10
            permanent_impact = current_spread_bps * participation_rate * 5
        else:
            temporary_impact = current_spread_bps * (participation_rate ** 0.5) * 10
            permanent_impact = current_spread_bps * participation_rate * 5
        
        total_impact_bps = current_spread_bps + temporary_impact + permanent_impact
        
        # Determine impact level
        impact_level = MarketImpactLevel.NEGLIGIBLE
        for level, threshold in self.IMPACT_THRESHOLDS.items():
            if total_impact_bps <= threshold:
                impact_level = level
                break
            impact_level = level
        
        # Calculate recommended max size
        recommended_max = min(
            avg_daily_volume * self.MAX_SINGLE_ORDER,
            avg_daily_volume * self.MAX_PARTICIPATION_RATE
        )
        
        # Determine execution strategy
        if participation_rate > self.MAX_SINGLE_ORDER:
            execution_strategy = "TWAP_MULTI_DAY"
        elif participation_rate > 0.02:
            execution_strategy = "VWAP"
        elif participation_rate > 0.01:
            execution_strategy = "TWAP"
        else:
            execution_strategy = "MARKET"
        
        return MarketImpactEstimate(
            symbol=symbol,
            order_size=order_size,
            avg_daily_volume=avg_daily_volume,
            participation_rate=participation_rate,
            estimated_impact_bps=total_impact_bps,
            impact_level=impact_level,
            recommended_max_size=recommended_max,
            execution_strategy=execution_strategy
        )
    
    def check_order(
        self,
        symbol: str,
        order_size: float,
        avg_daily_volume: float
    ) -> Tuple[bool, str, float]:
        """
        Check if an order is within market impact limits.
        
        Returns:
            Tuple of (is_allowed, reason, max_allowed_size)
        """
        # Reset daily tracking if needed
        today = datetime.now().strftime('%Y-%m-%d')
        if self.last_reset_date != today:
            self.daily_volume = {}
            self.last_reset_date = today
        
        if avg_daily_volume <= 0:
            return False, "No volume data available", 0
        
        # Check single order limit
        if order_size > avg_daily_volume * self.MAX_SINGLE_ORDER:
            max_size = avg_daily_volume * self.MAX_SINGLE_ORDER
            return False, f"Order exceeds {self.MAX_SINGLE_ORDER*100:.0f}% of ADV", max_size
        
        # Check daily volume limit
        current_daily = self.daily_volume.get(symbol, 0)
        if current_daily + order_size > avg_daily_volume * self.MAX_DAILY_VOLUME:
            remaining = avg_daily_volume * self.MAX_DAILY_VOLUME - current_daily
            return False, f"Would exceed daily volume limit", max(0, remaining)
        
        return True, "Order within limits", order_size
    
    def record_execution(self, symbol: str, executed_size: float):
        """Record an executed order for volume tracking"""
        self.daily_volume[symbol] = self.daily_volume.get(symbol, 0) + executed_size
    
    def get_remaining_capacity(self, symbol: str, avg_daily_volume: float) -> float:
        """Get remaining trading capacity for today"""
        current_daily = self.daily_volume.get(symbol, 0)
        max_daily = avg_daily_volume * self.MAX_DAILY_VOLUME
        return max(0, max_daily - current_daily)


class ContagionFirewall:
    """
    Prevents cascading failures and contagion.
    
    Protections:
    1. Isolate failing strategies
    2. Limit cross-strategy exposure
    3. Prevent feedback loops
    4. Circuit breakers per strategy
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Strategy isolation
        self.strategy_health: Dict[str, float] = {}  # 0-1 health score
        self.isolated_strategies: set = set()
        
        # Cross-strategy limits
        self.max_cross_exposure = self.config.get('max_cross_exposure', 0.3)
        
        # Feedback detection
        self.action_history: deque = deque(maxlen=1000)
        
        logger.info("ContagionFirewall initialized")
    
    def update_strategy_health(
        self,
        strategy_id: str,
        pnl: float,
        drawdown: float,
        error_rate: float
    ) -> float:
        """
        Update health score for a strategy.
        
        Returns:
            Health score (0-1)
        """
        # Calculate health score
        pnl_score = 1.0 if pnl >= 0 else max(0, 1 + pnl * 10)  # Penalize losses
        dd_score = max(0, 1 - drawdown * 5)  # Penalize drawdown
        error_score = max(0, 1 - error_rate * 10)  # Penalize errors
        
        health = (pnl_score + dd_score + error_score) / 3
        self.strategy_health[strategy_id] = health
        
        # Check for isolation
        if health < 0.3:
            self.isolate_strategy(strategy_id, f"Health score {health:.2f} below threshold")
        elif health > 0.5 and strategy_id in self.isolated_strategies:
            self.restore_strategy(strategy_id)
        
        return health
    
    def isolate_strategy(self, strategy_id: str, reason: str):
        """Isolate a failing strategy"""
        if strategy_id not in self.isolated_strategies:
            self.isolated_strategies.add(strategy_id)
            logger.warning(f"Strategy {strategy_id} ISOLATED: {reason}")
    
    def restore_strategy(self, strategy_id: str):
        """Restore an isolated strategy"""
        if strategy_id in self.isolated_strategies:
            self.isolated_strategies.remove(strategy_id)
            logger.info(f"Strategy {strategy_id} restored")
    
    def is_strategy_active(self, strategy_id: str) -> bool:
        """Check if a strategy is active (not isolated)"""
        return strategy_id not in self.isolated_strategies
    
    def check_feedback_loop(
        self,
        action_type: str,
        action_details: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Check for potential feedback loops.
        
        Returns:
            Tuple of (is_feedback_loop, description)
        """
        self.action_history.append({
            'type': action_type,
            'details': action_details,
            'timestamp': datetime.now()
        })
        
        # Check for repeated patterns
        recent = list(self.action_history)[-20:]
        
        if len(recent) < 10:
            return False, "Not enough history"
        
        # Count action types
        type_counts = {}
        for action in recent:
            t = action['type']
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Check for dominance of single action type
        max_count = max(type_counts.values())
        if max_count > 15:  # 75% of recent actions
            dominant_type = max(type_counts, key=type_counts.get)
            return True, f"Potential feedback loop: {dominant_type} repeated {max_count} times"
        
        return False, "No feedback loop detected"
    
    def get_active_strategies(self) -> List[str]:
        """Get list of active (non-isolated) strategies"""
        return [s for s in self.strategy_health.keys() if s not in self.isolated_strategies]


class RegulatoryCompliance:
    """
    Ensures regulatory compliance.
    
    Monitors:
    1. Position limits
    2. Reporting requirements
    3. Trading restrictions
    4. Record keeping
    """
    
    # Position limits by asset class (as fraction of market)
    POSITION_LIMITS = {
        'equity': 0.05,      # 5% of outstanding shares
        'futures': 0.10,     # 10% of open interest
        'options': 0.10,     # 10% of open interest
        'forex': 1.0,        # No limit (but leverage limits apply)
        'crypto': 0.05,      # 5% of daily volume
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Compliance state
        self.violations: List[Dict] = []
        self.pending_reports: List[Dict] = []
        
        # Trading restrictions
        self.restricted_symbols: set = set()
        self.restricted_periods: List[Dict] = []
        
        logger.info("RegulatoryCompliance initialized")
    
    def check_position_limit(
        self,
        symbol: str,
        asset_class: str,
        position_size: float,
        market_size: float
    ) -> Tuple[bool, str]:
        """
        Check if position is within regulatory limits.
        
        Returns:
            Tuple of (is_compliant, reason)
        """
        limit = self.POSITION_LIMITS.get(asset_class, 0.05)
        
        if market_size <= 0:
            return True, "No market size data"
        
        position_pct = position_size / market_size
        
        if position_pct > limit:
            self._record_violation(
                'position_limit',
                f"{symbol} position {position_pct*100:.2f}% exceeds {limit*100:.0f}% limit"
            )
            return False, f"Position exceeds {limit*100:.0f}% limit"
        
        return True, "Within position limits"
    
    def check_trading_restriction(
        self,
        symbol: str,
        trade_time: datetime
    ) -> Tuple[bool, str]:
        """
        Check for trading restrictions.
        
        Returns:
            Tuple of (can_trade, reason)
        """
        # Check symbol restrictions
        if symbol in self.restricted_symbols:
            return False, f"{symbol} is restricted"
        
        # Check time restrictions
        for restriction in self.restricted_periods:
            if restriction['start'] <= trade_time <= restriction['end']:
                if symbol in restriction.get('symbols', []) or not restriction.get('symbols'):
                    return False, f"Trading restricted: {restriction.get('reason', 'Unknown')}"
        
        return True, "No restrictions"
    
    def add_restriction(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        reason: str = "Regulatory restriction"
    ):
        """Add a trading restriction"""
        if symbol and not start_time:
            self.restricted_symbols.add(symbol)
            logger.warning(f"Added symbol restriction: {symbol}")
        elif start_time and end_time:
            self.restricted_periods.append({
                'symbols': [symbol] if symbol else [],
                'start': start_time,
                'end': end_time,
                'reason': reason
            })
            logger.warning(f"Added time restriction: {start_time} to {end_time}")
    
    def _record_violation(self, violation_type: str, description: str):
        """Record a compliance violation"""
        self.violations.append({
            'type': violation_type,
            'description': description,
            'timestamp': datetime.now()
        })
        logger.error(f"COMPLIANCE VIOLATION: {violation_type} - {description}")
    
    def generate_report(self, report_type: str) -> Dict[str, Any]:
        """Generate a compliance report"""
        return {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'violations': self.violations[-100:],
            'restricted_symbols': list(self.restricted_symbols),
            'active_restrictions': len(self.restricted_periods)
        }
    
    def get_violations(self, limit: int = 100) -> List[Dict]:
        """Get recent violations"""
        return self.violations[-limit:]


class CounterpartyRiskManager:
    """
    Manages counterparty risk exposure.
    
    Monitors:
    1. Exposure per counterparty
    2. Credit quality
    3. Collateral requirements
    4. Concentration limits
    """
    
    # IMMUTABLE LIMITS
    MAX_SINGLE_COUNTERPARTY = 0.20      # 20% of portfolio
    MAX_UNCOLLATERALIZED = 0.05         # 5% of portfolio
    MIN_CREDIT_RATING = 'BBB'           # Minimum investment grade
    
    CREDIT_RATINGS = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 
                      'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-',
                      'B+', 'B', 'B-', 'CCC', 'CC', 'C', 'D']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Exposures
        self.exposures: Dict[str, CounterpartyExposure] = {}
        
        # Limits
        self.counterparty_limits: Dict[str, float] = {}
        
        logger.info("CounterpartyRiskManager initialized")
    
    def update_exposure(
        self,
        counterparty_id: str,
        counterparty_name: str,
        exposure_type: str,
        gross_exposure: float,
        net_exposure: float,
        collateral: float,
        credit_rating: str,
        portfolio_value: float
    ) -> CounterpartyExposure:
        """Update counterparty exposure"""
        limit = self.counterparty_limits.get(
            counterparty_id,
            portfolio_value * self.MAX_SINGLE_COUNTERPARTY
        )
        
        utilization = net_exposure / limit if limit > 0 else 1.0
        
        exposure = CounterpartyExposure(
            counterparty_id=counterparty_id,
            counterparty_name=counterparty_name,
            exposure_type=exposure_type,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            collateral=collateral,
            credit_rating=credit_rating,
            exposure_limit=limit,
            utilization=utilization
        )
        
        self.exposures[counterparty_id] = exposure
        return exposure
    
    def check_new_exposure(
        self,
        counterparty_id: str,
        additional_exposure: float,
        portfolio_value: float
    ) -> Tuple[bool, str, float]:
        """
        Check if additional exposure is allowed.
        
        Returns:
            Tuple of (is_allowed, reason, max_additional)
        """
        current = self.exposures.get(counterparty_id)
        current_exposure = current.net_exposure if current else 0
        
        limit = portfolio_value * self.MAX_SINGLE_COUNTERPARTY
        
        if current_exposure + additional_exposure > limit:
            max_additional = max(0, limit - current_exposure)
            return False, f"Would exceed counterparty limit", max_additional
        
        # Check credit rating
        if current and self._is_below_min_rating(current.credit_rating):
            return False, f"Counterparty below minimum credit rating", 0
        
        return True, "Exposure allowed", additional_exposure
    
    def _is_below_min_rating(self, rating: str) -> bool:
        """Check if rating is below minimum"""
        try:
            rating_idx = self.CREDIT_RATINGS.index(rating)
            min_idx = self.CREDIT_RATINGS.index(self.MIN_CREDIT_RATING)
            return rating_idx > min_idx
        except ValueError:
            return True  # Unknown rating treated as below minimum
    
    def get_total_exposure(self) -> Dict[str, float]:
        """Get total exposure summary"""
        total_gross = sum(e.gross_exposure for e in self.exposures.values())
        total_net = sum(e.net_exposure for e in self.exposures.values())
        total_collateral = sum(e.collateral for e in self.exposures.values())
        
        return {
            'total_gross': total_gross,
            'total_net': total_net,
            'total_collateral': total_collateral,
            'uncollateralized': max(0, total_net - total_collateral),
            'counterparty_count': len(self.exposures)
        }
    
    def get_high_risk_counterparties(self) -> List[CounterpartyExposure]:
        """Get counterparties with high utilization or low credit"""
        high_risk = []
        
        for exposure in self.exposures.values():
            if exposure.utilization > 0.8:
                high_risk.append(exposure)
            elif self._is_below_min_rating(exposure.credit_rating):
                high_risk.append(exposure)
        
        return high_risk


class SystemicProtection:
    """
    Master Systemic Protection System
    
    Coordinates all systemic risk protections:
    - Market Impact Limiting
    - Contagion Firewall
    - Regulatory Compliance
    - Counterparty Risk
    
    CORE PRINCIPLE: Don't be a source of systemic risk.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.market_impact = MarketImpactLimiter(config.get('market_impact', {}))
        self.contagion = ContagionFirewall(config.get('contagion', {}))
        self.compliance = RegulatoryCompliance(config.get('compliance', {}))
        self.counterparty = CounterpartyRiskManager(config.get('counterparty', {}))
        
        # Overall state
        self.is_safe = True
        
        # Lock
        self._lock = threading.Lock()
        
        logger.info("SystemicProtection system initialized")
    
    def validate_order(
        self,
        symbol: str,
        order_size: float,
        avg_daily_volume: float,
        asset_class: str,
        market_size: float,
        counterparty_id: Optional[str] = None,
        portfolio_value: float = 0
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate an order against all systemic protections.
        
        Returns:
            Tuple of (is_allowed, reason, adjustments)
        """
        with self._lock:
            adjustments = {}
            
            # Check 1: Market impact
            is_allowed, impact_reason, max_size = self.market_impact.check_order(
                symbol, order_size, avg_daily_volume
            )
            if not is_allowed:
                adjustments['max_size'] = max_size
                return False, impact_reason, adjustments
            
            # Check 2: Regulatory compliance
            is_compliant, compliance_reason = self.compliance.check_position_limit(
                symbol, asset_class, order_size, market_size
            )
            if not is_compliant:
                return False, compliance_reason, {}
            
            # Check 3: Trading restrictions
            can_trade, restriction_reason = self.compliance.check_trading_restriction(
                symbol, datetime.now()
            )
            if not can_trade:
                return False, restriction_reason, {}
            
            # Check 4: Counterparty exposure
            if counterparty_id:
                is_allowed, cp_reason, max_exposure = self.counterparty.check_new_exposure(
                    counterparty_id, order_size, portfolio_value
                )
                if not is_allowed:
                    adjustments['max_exposure'] = max_exposure
                    return False, cp_reason, adjustments
            
            # Get impact estimate for execution strategy
            impact = self.market_impact.estimate_impact(
                symbol, order_size, avg_daily_volume
            )
            adjustments['execution_strategy'] = impact.execution_strategy
            adjustments['estimated_impact_bps'] = impact.estimated_impact_bps
            
            return True, "Order approved", adjustments
    
    def update_strategy_health(
        self,
        strategy_id: str,
        pnl: float,
        drawdown: float,
        error_rate: float
    ) -> Tuple[bool, float]:
        """
        Update strategy health and check for isolation.
        
        Returns:
            Tuple of (is_active, health_score)
        """
        health = self.contagion.update_strategy_health(
            strategy_id, pnl, drawdown, error_rate
        )
        is_active = self.contagion.is_strategy_active(strategy_id)
        
        return is_active, health
    
    def check_feedback_loop(
        self,
        action_type: str,
        action_details: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check for feedback loops"""
        return self.contagion.check_feedback_loop(action_type, action_details)
    
    def get_status(self) -> Dict[str, Any]:
        """Get systemic protection status"""
        return {
            'is_safe': self.is_safe,
            'isolated_strategies': list(self.contagion.isolated_strategies),
            'active_strategies': self.contagion.get_active_strategies(),
            'compliance_violations': len(self.compliance.violations),
            'counterparty_exposure': self.counterparty.get_total_exposure(),
            'high_risk_counterparties': len(self.counterparty.get_high_risk_counterparties())
        }
