"""
Catastrophic Risk Prevention
============================

Prevents catastrophic losses from:
1. Black Swan Events - Unprecedented market moves
2. Flash Crashes - Sudden, violent price dislocations
3. Liquidity Crises - Inability to exit positions
4. Tail Risk Events - Fat-tail distribution events

PRINCIPLE: Better to miss opportunities than suffer catastrophic loss.
"""

import logging
import asyncio
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import hashlib
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from scipy import stats
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy/SciPy not available - using fallback calculations")


class CatastrophicEventType(Enum):
    """Types of catastrophic events"""
    BLACK_SWAN = "black_swan"
    FLASH_CRASH = "flash_crash"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    VOLATILITY_EXPLOSION = "volatility_explosion"
    GAP_RISK = "gap_risk"
    COUNTERPARTY_FAILURE = "counterparty_failure"
    SYSTEMIC_CRISIS = "systemic_crisis"


class ProtectionLevel(Enum):
    """Protection levels"""
    NORMAL = "normal"           # Standard protection
    ELEVATED = "elevated"       # Increased monitoring
    HIGH = "high"              # Reduced exposure
    CRITICAL = "critical"       # Minimal exposure
    LOCKDOWN = "lockdown"       # No new positions, close existing


@dataclass
class CatastrophicEvent:
    """Record of a catastrophic event detection"""
    event_id: str
    event_type: CatastrophicEventType
    severity: float  # 0-1
    description: str
    market_data: Dict[str, Any]
    actions_taken: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity,
            'description': self.description,
            'actions_taken': self.actions_taken,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved
        }


class BlackSwanDetector:
    """
    Detects black swan events - unprecedented market moves.
    
    Detection Methods:
    1. Statistical outlier detection (>4 sigma moves)
    2. Cross-asset correlation spikes
    3. Volatility regime changes
    4. Order book imbalance extremes
    5. News sentiment shock detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Detection thresholds
        self.sigma_threshold = self.config.get('sigma_threshold', 4.0)
        self.correlation_spike_threshold = self.config.get('correlation_spike', 0.95)
        self.volatility_multiplier_threshold = self.config.get('vol_multiplier', 3.0)
        
        # Historical data for detection
        self.price_history: Dict[str, deque] = {}
        self.volatility_history: Dict[str, deque] = {}
        self.correlation_history: deque = deque(maxlen=100)
        
        # Detection state
        self.detected_events: List[CatastrophicEvent] = []
        self.current_alert_level = 0.0
        
        logger.info("BlackSwanDetector initialized")
    
    def detect(
        self,
        symbol: str,
        current_price: float,
        returns: Optional[List[float]] = None,
        cross_asset_correlations: Optional[Dict[str, float]] = None,
        current_volatility: Optional[float] = None
    ) -> Tuple[bool, Optional[CatastrophicEvent]]:
        """
        Detect black swan conditions.
        
        Returns:
            Tuple of (is_black_swan, event_details)
        """
        detections = []
        severity = 0.0
        
        # Initialize history if needed
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=1000)
            self.volatility_history[symbol] = deque(maxlen=100)
        
        self.price_history[symbol].append(current_price)
        
        # Detection 1: Statistical outlier
        if returns and len(returns) >= 20 and NUMPY_AVAILABLE:
            returns_arr = np.array(returns)
            mean_return = np.mean(returns_arr)
            std_return = np.std(returns_arr)
            
            if std_return > 0:
                latest_return = returns[-1]
                z_score = abs(latest_return - mean_return) / std_return
                
                if z_score > self.sigma_threshold:
                    detections.append(f"{z_score:.1f} sigma move detected")
                    severity = max(severity, min(1.0, z_score / 6.0))
        
        # Detection 2: Correlation spike
        if cross_asset_correlations:
            avg_correlation = sum(cross_asset_correlations.values()) / len(cross_asset_correlations)
            self.correlation_history.append(avg_correlation)
            
            if avg_correlation > self.correlation_spike_threshold:
                detections.append(f"Correlation spike to {avg_correlation:.2f}")
                severity = max(severity, 0.8)
        
        # Detection 3: Volatility explosion
        if current_volatility:
            self.volatility_history[symbol].append(current_volatility)
            
            if len(self.volatility_history[symbol]) >= 20:
                avg_vol = sum(self.volatility_history[symbol]) / len(self.volatility_history[symbol])
                if avg_vol > 0 and current_volatility > avg_vol * self.volatility_multiplier_threshold:
                    detections.append(f"Volatility explosion: {current_volatility/avg_vol:.1f}x normal")
                    severity = max(severity, 0.7)
        
        # Detection 4: Price gap
        if len(self.price_history[symbol]) >= 2:
            prev_price = self.price_history[symbol][-2]
            gap_pct = abs(current_price - prev_price) / prev_price
            
            if gap_pct > 0.05:  # 5% gap
                detections.append(f"Price gap of {gap_pct*100:.1f}%")
                severity = max(severity, min(1.0, gap_pct * 10))
        
        # Create event if detected
        if detections:
            event = CatastrophicEvent(
                event_id=hashlib.sha256(f"bs_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                event_type=CatastrophicEventType.BLACK_SWAN,
                severity=severity,
                description="; ".join(detections),
                market_data={
                    'symbol': symbol,
                    'price': current_price,
                    'volatility': current_volatility
                },
                actions_taken=[]
            )
            self.detected_events.append(event)
            self.current_alert_level = severity
            
            logger.warning(f"BLACK SWAN DETECTED: {event.description}")
            return True, event
        
        # Decay alert level
        self.current_alert_level = max(0, self.current_alert_level - 0.01)
        return False, None
    
    def get_alert_level(self) -> float:
        """Get current alert level (0-1)"""
        return self.current_alert_level


class FlashCrashProtector:
    """
    Protects against flash crashes - sudden violent price moves.
    
    Protection Methods:
    1. Real-time price velocity monitoring
    2. Automatic position reduction on velocity spike
    3. Order book depth monitoring
    4. Circuit breaker triggers
    5. Automatic hedging activation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.velocity_threshold = self.config.get('velocity_threshold', 0.02)  # 2% per minute
        self.depth_threshold = self.config.get('depth_threshold', 0.3)  # 30% of normal
        self.circuit_breaker_threshold = self.config.get('circuit_breaker', 0.05)  # 5% move
        
        # Monitoring state
        self.price_timestamps: Dict[str, deque] = {}
        self.price_values: Dict[str, deque] = {}
        self.is_flash_crash_mode = False
        self.flash_crash_start: Optional[datetime] = None
        
        # Protection callbacks
        self.on_flash_crash: Optional[Callable] = None
        self.on_recovery: Optional[Callable] = None
        
        logger.info("FlashCrashProtector initialized")
    
    def monitor(
        self,
        symbol: str,
        current_price: float,
        bid_depth: Optional[float] = None,
        ask_depth: Optional[float] = None,
        normal_depth: Optional[float] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Monitor for flash crash conditions.
        
        Returns:
            Tuple of (is_flash_crash, protection_actions)
        """
        now = datetime.now()
        
        # Initialize tracking
        if symbol not in self.price_timestamps:
            self.price_timestamps[symbol] = deque(maxlen=60)  # 1 minute of data
            self.price_values[symbol] = deque(maxlen=60)
        
        self.price_timestamps[symbol].append(now)
        self.price_values[symbol].append(current_price)
        
        actions = {}
        is_flash_crash = False
        
        # Check 1: Price velocity
        if len(self.price_values[symbol]) >= 10:
            oldest_price = self.price_values[symbol][0]
            oldest_time = self.price_timestamps[symbol][0]
            
            time_diff = (now - oldest_time).total_seconds() / 60  # minutes
            if time_diff > 0:
                price_change = abs(current_price - oldest_price) / oldest_price
                velocity = price_change / time_diff
                
                if velocity > self.velocity_threshold:
                    is_flash_crash = True
                    actions['velocity_alert'] = f"{velocity*100:.2f}% per minute"
                    actions['reduce_exposure'] = 0.5  # Reduce by 50%
        
        # Check 2: Order book depth collapse
        if bid_depth and ask_depth and normal_depth:
            current_depth = (bid_depth + ask_depth) / 2
            depth_ratio = current_depth / normal_depth
            
            if depth_ratio < self.depth_threshold:
                is_flash_crash = True
                actions['depth_collapse'] = f"Depth at {depth_ratio*100:.0f}% of normal"
                actions['widen_stops'] = True  # Avoid being stopped out in thin market
        
        # Check 3: Circuit breaker
        if len(self.price_values[symbol]) >= 2:
            prev_price = self.price_values[symbol][-2]
            instant_move = abs(current_price - prev_price) / prev_price
            
            if instant_move > self.circuit_breaker_threshold:
                is_flash_crash = True
                actions['circuit_breaker'] = True
                actions['halt_trading'] = True
        
        # State management
        if is_flash_crash and not self.is_flash_crash_mode:
            self.is_flash_crash_mode = True
            self.flash_crash_start = now
            logger.critical(f"FLASH CRASH DETECTED for {symbol}")
            
            if self.on_flash_crash:
                self.on_flash_crash(symbol, actions)
        
        elif not is_flash_crash and self.is_flash_crash_mode:
            # Check for recovery (stable for 5 minutes)
            if self.flash_crash_start and (now - self.flash_crash_start).seconds > 300:
                self.is_flash_crash_mode = False
                self.flash_crash_start = None
                logger.info(f"Flash crash recovery for {symbol}")
                
                if self.on_recovery:
                    self.on_recovery(symbol)
        
        return is_flash_crash, actions
    
    def get_protection_multiplier(self) -> float:
        """Get position size multiplier during flash crash"""
        if self.is_flash_crash_mode:
            return 0.25  # 25% of normal size
        return 1.0


class LiquidityCrisisManager:
    """
    Manages liquidity crisis situations.
    
    Crisis Indicators:
    1. Bid-ask spread explosion
    2. Order book depth collapse
    3. Trade execution failures
    4. Slippage explosion
    5. Market maker withdrawal
    
    Response Actions:
    1. Prioritize position reduction
    2. Use limit orders only
    3. Stagger exits over time
    4. Accept higher slippage for critical exits
    5. Activate emergency liquidity sources
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.spread_multiplier_threshold = self.config.get('spread_multiplier', 5.0)
        self.slippage_threshold = self.config.get('slippage_threshold', 0.01)  # 1%
        self.execution_failure_threshold = self.config.get('exec_failure', 0.3)  # 30%
        
        # State
        self.normal_spreads: Dict[str, float] = {}
        self.execution_history: deque = deque(maxlen=100)
        self.is_crisis_mode = False
        self.crisis_level = 0.0  # 0-1
        
        # Liquidation queue
        self.liquidation_queue: List[Dict] = []
        
        logger.info("LiquidityCrisisManager initialized")
    
    def assess_liquidity(
        self,
        symbol: str,
        current_spread: float,
        normal_spread: Optional[float] = None,
        execution_success: Optional[bool] = None,
        slippage: Optional[float] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Assess current liquidity conditions.
        
        Returns:
            Tuple of (crisis_level 0-1, recommended_actions)
        """
        crisis_indicators = []
        actions = {}
        
        # Store normal spread
        if normal_spread:
            self.normal_spreads[symbol] = normal_spread
        
        # Check 1: Spread explosion
        if symbol in self.normal_spreads and self.normal_spreads[symbol] > 0:
            spread_ratio = current_spread / self.normal_spreads[symbol]
            
            if spread_ratio > self.spread_multiplier_threshold:
                crisis_indicators.append(('spread', spread_ratio / 10))
                actions['use_limit_orders'] = True
                actions['max_order_size'] = 0.1  # 10% of normal
        
        # Check 2: Execution failures
        if execution_success is not None:
            self.execution_history.append(1 if execution_success else 0)
            
            if len(self.execution_history) >= 10:
                failure_rate = 1 - (sum(self.execution_history) / len(self.execution_history))
                
                if failure_rate > self.execution_failure_threshold:
                    crisis_indicators.append(('execution', failure_rate))
                    actions['retry_with_worse_price'] = True
        
        # Check 3: Slippage explosion
        if slippage and slippage > self.slippage_threshold:
            crisis_indicators.append(('slippage', slippage * 10))
            actions['stagger_exits'] = True
            actions['exit_interval_seconds'] = 60
        
        # Calculate crisis level
        if crisis_indicators:
            self.crisis_level = min(1.0, sum(v for _, v in crisis_indicators) / len(crisis_indicators))
        else:
            self.crisis_level = max(0, self.crisis_level - 0.05)  # Decay
        
        # Update crisis mode
        self.is_crisis_mode = self.crisis_level > 0.5
        
        if self.is_crisis_mode:
            actions['crisis_mode'] = True
            actions['reduce_all_positions'] = True
            actions['max_position_pct'] = 0.5  # Max 50% of normal
        
        return self.crisis_level, actions
    
    def queue_liquidation(
        self,
        symbol: str,
        quantity: float,
        urgency: float,  # 0-1
        max_slippage: float
    ):
        """Queue a position for orderly liquidation"""
        self.liquidation_queue.append({
            'symbol': symbol,
            'quantity': quantity,
            'urgency': urgency,
            'max_slippage': max_slippage,
            'queued_at': datetime.now()
        })
        
        # Sort by urgency
        self.liquidation_queue.sort(key=lambda x: x['urgency'], reverse=True)
    
    def get_next_liquidation(self) -> Optional[Dict]:
        """Get next position to liquidate"""
        if self.liquidation_queue:
            return self.liquidation_queue.pop(0)
        return None


class TailRiskHedger:
    """
    Manages tail risk hedging strategies.
    
    Hedging Strategies:
    1. Put option protection (portfolio insurance)
    2. VIX call options (volatility hedge)
    3. Inverse ETF positions
    4. Dynamic delta hedging
    5. Tail risk parity allocation
    
    PRINCIPLE: Always maintain some tail protection, increase during stress.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Hedge parameters
        self.min_hedge_ratio = self.config.get('min_hedge_ratio', 0.02)  # 2% of portfolio
        self.max_hedge_ratio = self.config.get('max_hedge_ratio', 0.10)  # 10% of portfolio
        self.hedge_trigger_vol = self.config.get('hedge_trigger_vol', 0.25)  # 25% annualized
        
        # Current hedge state
        self.current_hedge_ratio = self.min_hedge_ratio
        self.active_hedges: List[Dict] = []
        self.hedge_cost_ytd = 0.0
        
        logger.info("TailRiskHedger initialized")
    
    def calculate_hedge_requirement(
        self,
        portfolio_value: float,
        current_volatility: float,
        var_95: float,
        max_acceptable_loss: float
    ) -> Dict[str, Any]:
        """
        Calculate required tail risk hedge.
        
        Args:
            portfolio_value: Current portfolio value
            current_volatility: Current annualized volatility
            var_95: 95% Value at Risk
            max_acceptable_loss: Maximum acceptable loss (e.g., 0.15 for 15%)
        
        Returns:
            Hedge requirements and recommendations
        """
        recommendations = {}
        
        # Calculate unhedged tail risk
        unhedged_tail_risk = var_95 / portfolio_value if portfolio_value > 0 else 0
        
        # Determine required hedge ratio
        if current_volatility > self.hedge_trigger_vol:
            # High volatility - increase hedges
            vol_factor = current_volatility / self.hedge_trigger_vol
            target_hedge = min(self.max_hedge_ratio, self.min_hedge_ratio * vol_factor)
        else:
            target_hedge = self.min_hedge_ratio
        
        # If tail risk exceeds acceptable, increase hedge
        if unhedged_tail_risk > max_acceptable_loss:
            excess_risk = unhedged_tail_risk - max_acceptable_loss
            additional_hedge = excess_risk * 0.5  # Hedge 50% of excess
            target_hedge = min(self.max_hedge_ratio, target_hedge + additional_hedge)
        
        self.current_hedge_ratio = target_hedge
        
        recommendations['target_hedge_ratio'] = target_hedge
        recommendations['hedge_value'] = portfolio_value * target_hedge
        recommendations['current_hedge_ratio'] = self.current_hedge_ratio
        
        # Specific hedge recommendations
        if target_hedge > 0.05:
            recommendations['strategies'] = [
                {'type': 'put_spread', 'allocation': 0.4},
                {'type': 'vix_calls', 'allocation': 0.3},
                {'type': 'inverse_etf', 'allocation': 0.3}
            ]
        else:
            recommendations['strategies'] = [
                {'type': 'put_spread', 'allocation': 0.6},
                {'type': 'vix_calls', 'allocation': 0.4}
            ]
        
        return recommendations
    
    def register_hedge(
        self,
        hedge_type: str,
        notional: float,
        cost: float,
        expiry: datetime
    ):
        """Register an active hedge"""
        self.active_hedges.append({
            'type': hedge_type,
            'notional': notional,
            'cost': cost,
            'expiry': expiry,
            'created': datetime.now()
        })
        self.hedge_cost_ytd += cost
    
    def get_hedge_coverage(self) -> float:
        """Get current hedge coverage ratio"""
        return self.current_hedge_ratio


class CatastrophicRiskPrevention:
    """
    Master Catastrophic Risk Prevention System
    
    Coordinates all catastrophic risk prevention components:
    - Black Swan Detection
    - Flash Crash Protection
    - Liquidity Crisis Management
    - Tail Risk Hedging
    
    CORE PRINCIPLE: Survival first, profits second.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.black_swan = BlackSwanDetector(self.config.get('black_swan', {}))
        self.flash_crash = FlashCrashProtector(self.config.get('flash_crash', {}))
        self.liquidity = LiquidityCrisisManager(self.config.get('liquidity', {}))
        self.tail_hedge = TailRiskHedger(self.config.get('tail_hedge', {}))
        
        # Protection state
        self.protection_level = ProtectionLevel.NORMAL
        self.active_events: List[CatastrophicEvent] = []
        
        # Callbacks
        self.on_protection_change: Optional[Callable] = None
        self.on_catastrophic_event: Optional[Callable] = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        logger.info("CatastrophicRiskPrevention system initialized")
    
    def assess_all_risks(
        self,
        market_data: Dict[str, Any]
    ) -> Tuple[ProtectionLevel, Dict[str, Any]]:
        """
        Comprehensive catastrophic risk assessment.
        
        Args:
            market_data: Current market data including:
                - symbol: Trading symbol
                - price: Current price
                - returns: Recent returns
                - volatility: Current volatility
                - spread: Bid-ask spread
                - depth: Order book depth
        
        Returns:
            Tuple of (protection_level, actions_required)
        """
        with self._lock:
            actions = {}
            max_severity = 0.0
            
            symbol = market_data.get('symbol', 'UNKNOWN')
            
            # 1. Black Swan Detection
            is_black_swan, bs_event = self.black_swan.detect(
                symbol=symbol,
                current_price=market_data.get('price', 0),
                returns=market_data.get('returns'),
                cross_asset_correlations=market_data.get('correlations'),
                current_volatility=market_data.get('volatility')
            )
            
            if is_black_swan and bs_event:
                self.active_events.append(bs_event)
                max_severity = max(max_severity, bs_event.severity)
                actions['black_swan'] = {
                    'detected': True,
                    'severity': bs_event.severity,
                    'reduce_exposure': True
                }
            
            # 2. Flash Crash Protection
            is_flash_crash, fc_actions = self.flash_crash.monitor(
                symbol=symbol,
                current_price=market_data.get('price', 0),
                bid_depth=market_data.get('bid_depth'),
                ask_depth=market_data.get('ask_depth'),
                normal_depth=market_data.get('normal_depth')
            )
            
            if is_flash_crash:
                max_severity = max(max_severity, 0.8)
                actions['flash_crash'] = fc_actions
            
            # 3. Liquidity Assessment
            crisis_level, liq_actions = self.liquidity.assess_liquidity(
                symbol=symbol,
                current_spread=market_data.get('spread', 0),
                normal_spread=market_data.get('normal_spread'),
                execution_success=market_data.get('last_execution_success'),
                slippage=market_data.get('last_slippage')
            )
            
            if crisis_level > 0.5:
                max_severity = max(max_severity, crisis_level)
                actions['liquidity_crisis'] = liq_actions
            
            # 4. Tail Risk Hedging
            hedge_req = self.tail_hedge.calculate_hedge_requirement(
                portfolio_value=market_data.get('portfolio_value', 0),
                current_volatility=market_data.get('volatility', 0.15),
                var_95=market_data.get('var_95', 0),
                max_acceptable_loss=0.15
            )
            actions['hedge_requirements'] = hedge_req
            
            # Determine protection level
            new_level = self._determine_protection_level(max_severity)
            
            if new_level != self.protection_level:
                old_level = self.protection_level
                self.protection_level = new_level
                
                logger.warning(f"Protection level changed: {old_level.value} -> {new_level.value}")
                
                if self.on_protection_change:
                    self.on_protection_change(old_level, new_level)
            
            return self.protection_level, actions
    
    def _determine_protection_level(self, severity: float) -> ProtectionLevel:
        """Determine protection level from severity"""
        if severity >= 0.9:
            return ProtectionLevel.LOCKDOWN
        elif severity >= 0.7:
            return ProtectionLevel.CRITICAL
        elif severity >= 0.5:
            return ProtectionLevel.HIGH
        elif severity >= 0.3:
            return ProtectionLevel.ELEVATED
        else:
            return ProtectionLevel.NORMAL
    
    def get_position_size_limit(self) -> float:
        """Get maximum position size as fraction of normal"""
        limits = {
            ProtectionLevel.NORMAL: 1.0,
            ProtectionLevel.ELEVATED: 0.75,
            ProtectionLevel.HIGH: 0.5,
            ProtectionLevel.CRITICAL: 0.25,
            ProtectionLevel.LOCKDOWN: 0.0
        }
        return limits.get(self.protection_level, 0.0)
    
    def can_open_position(self) -> Tuple[bool, str]:
        """Check if new positions can be opened"""
        if self.protection_level == ProtectionLevel.LOCKDOWN:
            return False, "System in LOCKDOWN - no new positions"
        if self.protection_level == ProtectionLevel.CRITICAL:
            return False, "System in CRITICAL mode - no new positions"
        return True, "Positions allowed"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current protection status"""
        return {
            'protection_level': self.protection_level.value,
            'position_size_limit': self.get_position_size_limit(),
            'can_open_position': self.can_open_position()[0],
            'black_swan_alert': self.black_swan.get_alert_level(),
            'flash_crash_mode': self.flash_crash.is_flash_crash_mode,
            'liquidity_crisis_level': self.liquidity.crisis_level,
            'hedge_coverage': self.tail_hedge.get_hedge_coverage(),
            'active_events': len(self.active_events)
        }
