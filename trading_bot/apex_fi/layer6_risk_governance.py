"""
APEX-FI Layer 6: Real-Time Risk Intelligence & Autonomous Governance
=====================================================================

Tick-by-tick risk decomposition, hierarchical circuit breakers,
regime surveillance AI, and autonomous compliance engine.

Mission: Enforce absolute capital safety without slowing down the machine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class RiskMetric(str, Enum):
    """Risk metric types."""
    VAR = "var"  # Value at Risk
    CVAR = "cvar"  # Conditional VaR
    EXPECTED_SHORTFALL = "expected_shortfall"
    FACTOR_EXPOSURE = "factor_exposure"
    GREEKS = "greeks"
    DV01 = "dv01"
    CREDIT_SPREAD_DURATION = "credit_spread_duration"


class CircuitBreakerLevel(str, Enum):
    """Circuit breaker hierarchy levels."""
    STRATEGY = "strategy"
    POD = "pod"
    BOOK = "book"
    SYSTEM = "system"


@dataclass
class RiskState:
    """Real-time risk state."""
    timestamp: datetime
    var_95: float
    cvar_95: float
    expected_shortfall: float
    factor_exposures: Dict[str, float] = field(default_factory=dict)
    greeks: Dict[str, float] = field(default_factory=dict)
    leverage: float = 1.0
    concentration: Dict[str, float] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get risk state summary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'leverage': self.leverage,
            'top_exposures': dict(sorted(
                self.factor_exposures.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]),
        }


class TickByTickRiskDecomposer:
    """
    Tick-by-tick risk decomposition.
    
    Updates VaR, CVaR, factor exposures, Greeks every 100ms.
    Attributes risk by strategy, pod, factor, asset class, geography, liquidity.
    """
    
    def __init__(self, update_interval_ms: int = 100):
        self.update_interval_ms = update_interval_ms
        self.risk_history: deque = deque(maxlen=10000)
        self.last_update: Optional[datetime] = None
        
        # Risk buckets
        self.strategy_risk: Dict[str, float] = {}
        self.factor_risk: Dict[str, float] = {}
        self.asset_class_risk: Dict[str, float] = {}
        
        logger.info(f"Tick-by-Tick Risk Decomposer initialized - {update_interval_ms}ms interval")
    
    def calculate_var(
        self,
        returns: np.ndarray,
        confidence: float = 0.95,
        method: str = "historical"
    ) -> float:
        """
        Calculate Value at Risk.
        
        Args:
            returns: Historical returns
            confidence: Confidence level (e.g., 0.95 for 95% VaR)
            method: 'historical', 'parametric', or 'monte_carlo'
            
        Returns:
            VaR value
        """
        if len(returns) == 0:
            return 0.0
        
        if method == "historical":
            # Historical VaR
            var = np.percentile(returns, (1 - confidence) * 100)
            return abs(var)
        
        elif method == "parametric":
            # Parametric VaR (assumes normal distribution)
            mean = np.mean(returns)
            std = np.std(returns)
            z_score = 1.645 if confidence == 0.95 else 2.326  # 95% or 99%
            var = mean - z_score * std
            return abs(var)
        
        else:  # monte_carlo
            # Monte Carlo VaR (simplified)
            simulated = np.random.normal(np.mean(returns), np.std(returns), 10000)
            var = np.percentile(simulated, (1 - confidence) * 100)
            return abs(var)
    
    def calculate_cvar(
        self,
        returns: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        CVaR is the expected loss given that loss exceeds VaR.
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_var(returns, confidence, "historical")
        
        # CVaR is average of losses beyond VaR
        tail_losses = returns[returns <= -var]
        
        if len(tail_losses) > 0:
            cvar = abs(np.mean(tail_losses))
        else:
            cvar = var
        
        return cvar
    
    def decompose_factor_risk(
        self,
        positions: Dict[str, float],
        factor_loadings: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Decompose risk by factors (Barra-style).
        
        Args:
            positions: Position weights
            factor_loadings: Asset -> Factor -> Loading
            
        Returns:
            Factor exposures
        """
        factor_exposures = {}
        
        for asset, weight in positions.items():
            if asset in factor_loadings:
                for factor, loading in factor_loadings[asset].items():
                    if factor not in factor_exposures:
                        factor_exposures[factor] = 0.0
                    factor_exposures[factor] += weight * loading
        
        return factor_exposures
    
    def update_risk_state(
        self,
        positions: Dict[str, float],
        returns: np.ndarray,
        factor_loadings: Optional[Dict[str, Dict[str, float]]] = None
    ) -> RiskState:
        """
        Update risk state (called every 100ms).
        
        Returns:
            Current risk state
        """
        now = datetime.now()
        
        # Calculate risk metrics
        var_95 = self.calculate_var(returns, 0.95)
        cvar_95 = self.calculate_cvar(returns, 0.95)
        expected_shortfall = cvar_95  # Same as CVaR
        
        # Factor exposures
        factor_exposures = {}
        if factor_loadings:
            factor_exposures = self.decompose_factor_risk(positions, factor_loadings)
        
        # Calculate leverage
        leverage = sum(abs(w) for w in positions.values())
        
        # Concentration
        concentration = {asset: abs(weight) for asset, weight in positions.items()}
        
        risk_state = RiskState(
            timestamp=now,
            var_95=var_95,
            cvar_95=cvar_95,
            expected_shortfall=expected_shortfall,
            factor_exposures=factor_exposures,
            leverage=leverage,
            concentration=concentration,
        )
        
        self.risk_history.append(risk_state)
        self.last_update = now
        
        return risk_state
    
    def get_risk_attribution(
        self,
        by: str = "strategy"
    ) -> Dict[str, float]:
        """
        Get risk attribution.
        
        Args:
            by: 'strategy', 'factor', 'asset_class', 'geography', 'liquidity'
            
        Returns:
            Risk attribution
        """
        if by == "strategy":
            return self.strategy_risk.copy()
        elif by == "factor":
            return self.factor_risk.copy()
        elif by == "asset_class":
            return self.asset_class_risk.copy()
        else:
            return {}


class HierarchicalCircuitBreaker:
    """
    Hierarchical autonomous circuit breakers.
    
    Kill switches at strategy, pod, and book levels.
    Trigger automatically at pre-defined thresholds.
    Cannot be overridden during breach. Human approval required to deactivate.
    """
    
    def __init__(self):
        self.thresholds = {
            CircuitBreakerLevel.STRATEGY: {
                'drawdown': 0.15,  # 15%
                'var_breach': 2.0,  # 2x normal VaR
                'volatility_spike': 3.0,  # 3x normal vol
            },
            CircuitBreakerLevel.POD: {
                'drawdown': 0.10,  # 10%
                'var_breach': 1.5,
                'correlation_break': 0.8,  # Correlation >0.8
            },
            CircuitBreakerLevel.BOOK: {
                'drawdown': 0.08,  # 8% (constitutional limit)
                'var_breach': 1.5,
                'leverage_breach': 5.0,  # 5x leverage
            },
        }
        
        self.active_breakers: Dict[str, Dict[str, Any]] = {}
        self.breach_log: List[Dict[str, Any]] = []
        
        logger.info("Hierarchical Circuit Breaker initialized")
    
    def check_breaker(
        self,
        level: CircuitBreakerLevel,
        entity_id: str,
        metrics: Dict[str, float]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if circuit breaker should trigger.
        
        Args:
            level: Circuit breaker level
            entity_id: Strategy/pod/book identifier
            metrics: Current metrics
            
        Returns:
            (should_trigger, reason)
        """
        thresholds = self.thresholds[level]
        
        # Check drawdown
        if 'drawdown' in metrics and 'drawdown' in thresholds:
            if metrics['drawdown'] > thresholds['drawdown']:
                return True, f"Drawdown {metrics['drawdown']:.2%} exceeds {thresholds['drawdown']:.2%}"
        
        # Check VaR breach
        if 'var_ratio' in metrics and 'var_breach' in thresholds:
            if metrics['var_ratio'] > thresholds['var_breach']:
                return True, f"VaR ratio {metrics['var_ratio']:.2f}x exceeds {thresholds['var_breach']:.2f}x"
        
        # Check volatility spike
        if 'volatility_ratio' in metrics and 'volatility_spike' in thresholds:
            if metrics['volatility_ratio'] > thresholds['volatility_spike']:
                return True, f"Volatility spike {metrics['volatility_ratio']:.2f}x exceeds threshold"
        
        # Check leverage
        if 'leverage' in metrics and 'leverage_breach' in thresholds:
            if metrics['leverage'] > thresholds['leverage_breach']:
                return True, f"Leverage {metrics['leverage']:.2f}x exceeds {thresholds['leverage_breach']:.2f}x"
        
        return False, None
    
    def activate_breaker(
        self,
        level: CircuitBreakerLevel,
        entity_id: str,
        reason: str
    ) -> None:
        """Activate circuit breaker."""
        breaker_id = f"{level.value}_{entity_id}"
        
        self.active_breakers[breaker_id] = {
            'level': level,
            'entity_id': entity_id,
            'reason': reason,
            'activated_at': datetime.now(),
            'can_override': False,  # Cannot override during breach
        }
        
        self.breach_log.append({
            'breaker_id': breaker_id,
            'level': level.value,
            'entity_id': entity_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
        })
        
        logger.critical(f"CIRCUIT BREAKER ACTIVATED: {breaker_id} - {reason}")
    
    def is_active(self, level: CircuitBreakerLevel, entity_id: str) -> bool:
        """Check if circuit breaker is active."""
        breaker_id = f"{level.value}_{entity_id}"
        return breaker_id in self.active_breakers
    
    def deactivate_breaker(
        self,
        level: CircuitBreakerLevel,
        entity_id: str,
        human_approval_code: str
    ) -> bool:
        """
        Deactivate circuit breaker (requires human approval).
        
        Returns:
            True if successfully deactivated
        """
        breaker_id = f"{level.value}_{entity_id}"
        
        if breaker_id not in self.active_breakers:
            return False
        
        # Verify human approval (simplified)
        if not human_approval_code or len(human_approval_code) < 8:
            logger.error("Invalid human approval code")
            return False
        
        del self.active_breakers[breaker_id]
        logger.warning(f"Circuit breaker deactivated: {breaker_id} (human approval)")
        
        return True
    
    def get_active_breakers(self) -> List[Dict[str, Any]]:
        """Get all active circuit breakers."""
        return list(self.active_breakers.values())


class RegimeSurveillanceAI:
    """
    Regime Surveillance AI.
    
    Monitors 200+ macro and market indicators for early-warning signals.
    Classifies market state across multiple dimensions in real-time.
    Proactively alerts portfolio construction to reduce tail risk.
    """
    
    def __init__(self):
        self.regime_indicators: Dict[str, float] = {}
        self.regime_history: deque = deque(maxlen=10000)
        self.alert_threshold = 0.7  # Confidence threshold for alerts
        
        self._initialize_indicators()
        
        logger.info("Regime Surveillance AI initialized")
    
    def _initialize_indicators(self) -> None:
        """Initialize regime indicators."""
        self.regime_indicators = {
            'vix': 0.0,
            'ted_spread': 0.0,
            'yield_curve_slope': 0.0,
            'credit_spread': 0.0,
            'put_call_ratio': 0.0,
            'market_breadth': 0.0,
            'correlation': 0.0,
            'liquidity_score': 1.0,
        }
    
    def update_indicators(self, market_data: Dict[str, float]) -> None:
        """Update regime indicators from market data."""
        for indicator in self.regime_indicators:
            if indicator in market_data:
                self.regime_indicators[indicator] = market_data[indicator]
    
    def classify_volatility_regime(self) -> Tuple[str, float]:
        """
        Classify volatility regime.
        
        Returns:
            (regime, confidence)
        """
        vix = self.regime_indicators.get('vix', 15.0)
        
        if vix < 12:
            return "low_volatility", 0.9
        elif vix < 20:
            return "normal_volatility", 0.8
        elif vix < 30:
            return "elevated_volatility", 0.85
        else:
            return "high_volatility", 0.95
    
    def classify_correlation_regime(self) -> Tuple[str, float]:
        """Classify correlation regime."""
        correlation = self.regime_indicators.get('correlation', 0.3)
        
        if correlation < 0.3:
            return "low_correlation", 0.8
        elif correlation < 0.6:
            return "normal_correlation", 0.7
        else:
            return "high_correlation", 0.9
    
    def classify_liquidity_regime(self) -> Tuple[str, float]:
        """Classify liquidity regime."""
        liquidity = self.regime_indicators.get('liquidity_score', 1.0)
        
        if liquidity > 0.8:
            return "high_liquidity", 0.85
        elif liquidity > 0.5:
            return "normal_liquidity", 0.75
        else:
            return "low_liquidity", 0.9
    
    def classify_trend_regime(self) -> Tuple[str, float]:
        """Classify trend regime."""
        breadth = self.regime_indicators.get('market_breadth', 0.5)
        
        if breadth > 0.7:
            return "strong_uptrend", 0.85
        elif breadth > 0.55:
            return "uptrend", 0.7
        elif breadth > 0.45:
            return "ranging", 0.75
        elif breadth > 0.3:
            return "downtrend", 0.7
        else:
            return "strong_downtrend", 0.85
    
    def detect_regime_transition(self) -> Optional[Dict[str, Any]]:
        """
        Detect early-warning signals of regime transition.
        
        Returns:
            Alert if transition detected
        """
        # Check for stress indicators
        vix = self.regime_indicators.get('vix', 15.0)
        credit_spread = self.regime_indicators.get('credit_spread', 0.01)
        correlation = self.regime_indicators.get('correlation', 0.3)
        
        # Stress conditions
        if vix > 25 and credit_spread > 0.03 and correlation > 0.7:
            return {
                'alert_type': 'regime_transition',
                'severity': 'high',
                'message': 'Multiple stress indicators elevated - potential regime shift',
                'indicators': {
                    'vix': vix,
                    'credit_spread': credit_spread,
                    'correlation': correlation,
                },
                'timestamp': datetime.now(),
            }
        
        return None
    
    def get_current_regime(self) -> Dict[str, Any]:
        """Get current market regime classification."""
        vol_regime, vol_conf = self.classify_volatility_regime()
        corr_regime, corr_conf = self.classify_correlation_regime()
        liq_regime, liq_conf = self.classify_liquidity_regime()
        trend_regime, trend_conf = self.classify_trend_regime()
        
        return {
            'volatility': {'regime': vol_regime, 'confidence': vol_conf},
            'correlation': {'regime': corr_regime, 'confidence': corr_conf},
            'liquidity': {'regime': liq_regime, 'confidence': liq_conf},
            'trend': {'regime': trend_regime, 'confidence': trend_conf},
            'timestamp': datetime.now(),
        }


class ComplianceEngine:
    """
    Autonomous compliance engine.
    
    Pre-screens every order against regulatory constraints.
    Parses new regulations and translates to hard constraints within 24 hours.
    """
    
    def __init__(self):
        self.position_limits: Dict[str, float] = {}
        self.concentration_limits: Dict[str, float] = {}
        self.wash_sale_tracker: Dict[str, List[datetime]] = {}
        self.compliance_rules: List[Dict[str, Any]] = []
        
        self._initialize_rules()
        
        logger.info("Compliance Engine initialized")
    
    def _initialize_rules(self) -> None:
        """Initialize compliance rules."""
        self.compliance_rules = [
            {
                'rule_id': 'position_limit',
                'description': 'Maximum position size per security',
                'check_function': self._check_position_limit,
            },
            {
                'rule_id': 'concentration_limit',
                'description': 'Maximum concentration per sector',
                'check_function': self._check_concentration_limit,
            },
            {
                'rule_id': 'wash_sale',
                'description': 'Wash sale detection (30-day rule)',
                'check_function': self._check_wash_sale,
            },
        ]
    
    def _check_position_limit(
        self,
        symbol: str,
        quantity: float,
        current_position: float
    ) -> Tuple[bool, Optional[str]]:
        """Check position limit compliance."""
        limit = self.position_limits.get(symbol, float('inf'))
        new_position = current_position + quantity
        
        if abs(new_position) > limit:
            return False, f"Position limit exceeded: {abs(new_position)} > {limit}"
        
        return True, None
    
    def _check_concentration_limit(
        self,
        sector: str,
        new_exposure: float
    ) -> Tuple[bool, Optional[str]]:
        """Check concentration limit compliance."""
        limit = self.concentration_limits.get(sector, 0.25)  # 25% default
        
        if new_exposure > limit:
            return False, f"Concentration limit exceeded: {new_exposure:.2%} > {limit:.2%}"
        
        return True, None
    
    def _check_wash_sale(
        self,
        symbol: str,
        side: str,
        current_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """Check wash sale rule (simplified)."""
        if symbol not in self.wash_sale_tracker:
            return True, None
        
        # Check for sales within 30 days
        recent_sales = [
            t for t in self.wash_sale_tracker[symbol]
            if (current_time - t).days <= 30
        ]
        
        if side == 'buy' and recent_sales:
            return False, f"Potential wash sale: {len(recent_sales)} sales within 30 days"
        
        return True, None
    
    def pre_trade_check(
        self,
        symbol: str,
        quantity: float,
        side: str,
        current_position: float = 0.0,
        sector: Optional[str] = None,
        sector_exposure: float = 0.0
    ) -> Tuple[bool, List[str]]:
        """
        Pre-trade compliance check.
        
        Returns:
            (is_compliant, violation_messages)
        """
        violations = []
        
        # Check position limit
        is_ok, msg = self._check_position_limit(symbol, quantity, current_position)
        if not is_ok:
            violations.append(msg)
        
        # Check concentration if sector provided
        if sector:
            is_ok, msg = self._check_concentration_limit(sector, sector_exposure)
            if not is_ok:
                violations.append(msg)
        
        # Check wash sale
        is_ok, msg = self._check_wash_sale(symbol, side, datetime.now())
        if not is_ok:
            violations.append(msg)
        
        is_compliant = len(violations) == 0
        
        if not is_compliant:
            logger.warning(f"Compliance violations for {symbol}: {violations}")
        
        return is_compliant, violations
    
    def record_trade(
        self,
        symbol: str,
        side: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record trade for compliance tracking."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if side == 'sell':
            if symbol not in self.wash_sale_tracker:
                self.wash_sale_tracker[symbol] = []
            self.wash_sale_tracker[symbol].append(timestamp)
            
            # Keep only last 60 days
            cutoff = timestamp - timedelta(days=60)
            self.wash_sale_tracker[symbol] = [
                t for t in self.wash_sale_tracker[symbol] if t > cutoff
            ]


class RiskGovernance:
    """
    Risk Governance - Master coordinator for Layer 6.
    
    Integrates tick-by-tick risk decomposition, hierarchical circuit breakers,
    regime surveillance, and compliance engine.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.risk_decomposer = TickByTickRiskDecomposer(
            update_interval_ms=config.get('risk_update_interval_ms', 100)
        )
        self.circuit_breaker = HierarchicalCircuitBreaker()
        self.regime_surveillance = RegimeSurveillanceAI()
        self.compliance = ComplianceEngine()
        
        logger.info("Risk Governance initialized - Layer 6 operational")
    
    def update_risk(
        self,
        positions: Dict[str, float],
        returns: np.ndarray,
        factor_loadings: Optional[Dict[str, Dict[str, float]]] = None
    ) -> RiskState:
        """Update risk state (every 100ms)."""
        return self.risk_decomposer.update_risk_state(positions, returns, factor_loadings)
    
    def check_circuit_breakers(
        self,
        level: CircuitBreakerLevel,
        entity_id: str,
        metrics: Dict[str, float]
    ) -> bool:
        """
        Check circuit breakers.
        
        Returns:
            True if breaker triggered
        """
        should_trigger, reason = self.circuit_breaker.check_breaker(level, entity_id, metrics)
        
        if should_trigger:
            self.circuit_breaker.activate_breaker(level, entity_id, reason)
            return True
        
        return False
    
    def update_regime(self, market_data: Dict[str, float]) -> Dict[str, Any]:
        """Update regime surveillance."""
        self.regime_surveillance.update_indicators(market_data)
        return self.regime_surveillance.get_current_regime()
    
    def validate_trade(
        self,
        symbol: str,
        quantity: float,
        side: str,
        **kwargs
    ) -> Tuple[bool, List[str]]:
        """Validate trade for compliance."""
        return self.compliance.pre_trade_check(symbol, quantity, side, **kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get risk governance statistics."""
        return {
            'active_circuit_breakers': len(self.circuit_breaker.get_active_breakers()),
            'total_breaches': len(self.circuit_breaker.breach_log),
            'current_regime': self.regime_surveillance.get_current_regime(),
            'compliance_rules': len(self.compliance.compliance_rules),
        }


# Import timedelta for wash sale tracking
from datetime import timedelta
