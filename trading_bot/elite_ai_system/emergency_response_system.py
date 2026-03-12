"""
Emergency Response System - Market Stress and Technical Issue Management

Implements institutional-grade emergency protocols:
- Volatility spike response
- Liquidity crisis management
- Technical failure recovery
- Emergency exit procedures
- Circuit breaker mechanisms
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import numpy as np
from collections import deque
import asyncio

logger = logging.getLogger(__name__)


class EmergencyLevel(Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EmergencyType(Enum):
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    FLASH_CRASH = "flash_crash"
    TECHNICAL_FAILURE = "technical_failure"
    CONNECTION_LOSS = "connection_loss"
    DATA_FEED_ERROR = "data_feed_error"
    EXECUTION_FAILURE = "execution_failure"
    MARGIN_CALL = "margin_call"


@dataclass
class VolatilityResponse:
    """Volatility response state"""
    current_volatility: float
    volatility_percentile: float
    spike_detected: bool
    response_level: EmergencyLevel
    position_reduction: float
    stop_widening: float
    new_entries_blocked: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LiquidityCrisisManager:
    """Liquidity crisis management state"""
    liquidity_score: float
    crisis_detected: bool
    response_level: EmergencyLevel
    exit_priority: List[str]
    alternative_venues: List[str]
    slippage_tolerance: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EmergencyEvent:
    """Emergency event record"""
    event_id: str
    event_type: EmergencyType
    level: EmergencyLevel
    description: str
    actions_taken: List[str]
    resolved: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'level': self.level.value,
            'description': self.description,
            'actions_taken': self.actions_taken,
            'resolved': self.resolved,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class EmergencyResponseSystem:
    """
    Emergency Response System
    
    Handles market emergencies and technical issues:
    - Volatility spike detection and response
    - Liquidity crisis management
    - Flash crash protection
    - Technical failure recovery
    - Circuit breaker mechanisms
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Volatility thresholds
        self.volatility_normal = self.config.get('volatility_normal', 0.01)
        self.volatility_elevated = self.config.get('volatility_elevated', 0.02)
        self.volatility_high = self.config.get('volatility_high', 0.03)
        self.volatility_critical = self.config.get('volatility_critical', 0.05)
        
        # Flash crash detection
        self.flash_crash_threshold = self.config.get('flash_crash_threshold', 0.05)  # 5% in 5 min
        self.flash_crash_window = self.config.get('flash_crash_window', 5)  # minutes
        
        # Circuit breaker
        self.circuit_breaker_threshold = self.config.get('circuit_breaker_threshold', 3)
        self.circuit_breaker_cooldown = self.config.get('circuit_breaker_cooldown', 60)  # minutes
        
        # State
        self.current_level = EmergencyLevel.NORMAL
        self.active_emergencies: Dict[str, EmergencyEvent] = {}
        self.emergency_history: deque = deque(maxlen=1000)
        self.circuit_breaker_trips = 0
        self.circuit_breaker_until: Optional[datetime] = None
        
        # Callbacks
        self.emergency_callbacks: List[Callable] = []
        
        # Volatility history
        self.volatility_history: deque = deque(maxlen=1000)
        self.price_history: deque = deque(maxlen=1000)
        
        logger.info("EmergencyResponseSystem initialized")
    
    async def monitor_market(self, market_data: Dict[str, Any]) -> EmergencyLevel:
        """
        Monitor market conditions for emergencies
        
        Args:
            market_data: Current market data
            
        Returns:
            Current emergency level
        """
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        
        # Store price history
        if prices:
            self.price_history.append({
                'price': prices[-1],
                'timestamp': datetime.now()
            })
        
        # Check for various emergency conditions
        volatility_response = await self._check_volatility(prices)
        liquidity_crisis = await self._check_liquidity(prices, volumes)
        flash_crash = await self._check_flash_crash()
        
        # Determine overall emergency level
        levels = [
            volatility_response.response_level,
            liquidity_crisis.response_level,
            EmergencyLevel.CRITICAL if flash_crash else EmergencyLevel.NORMAL
        ]
        
        self.current_level = max(levels, key=lambda x: list(EmergencyLevel).index(x))
        
        # Trigger emergency protocols if needed
        if self.current_level in [EmergencyLevel.CRITICAL, EmergencyLevel.EMERGENCY]:
            await self._trigger_emergency_protocols(volatility_response, liquidity_crisis, flash_crash)
        
        return self.current_level
    
    async def _check_volatility(self, prices: List[float]) -> VolatilityResponse:
        """Check for volatility spikes"""
        if len(prices) < 20:
            return VolatilityResponse(
                current_volatility=0,
                volatility_percentile=50,
                spike_detected=False,
                response_level=EmergencyLevel.NORMAL,
                position_reduction=1.0,
                stop_widening=1.0,
                new_entries_blocked=False
            )
        
        price_array = np.array(prices)
        returns = np.diff(price_array) / price_array[:-1]
        current_vol = np.std(returns)
        
        # Store volatility
        self.volatility_history.append({
            'volatility': current_vol,
            'timestamp': datetime.now()
        })
        
        # Calculate percentile
        vol_history = [v['volatility'] for v in self.volatility_history]
        percentile = np.percentile(vol_history, [current_vol * 100]) if vol_history else 50
        
        # Determine response
        if current_vol > self.volatility_critical:
            level = EmergencyLevel.CRITICAL
            position_reduction = 0.25
            stop_widening = 2.0
            new_entries_blocked = True
            spike_detected = True
        elif current_vol > self.volatility_high:
            level = EmergencyLevel.HIGH
            position_reduction = 0.5
            stop_widening = 1.5
            new_entries_blocked = True
            spike_detected = True
        elif current_vol > self.volatility_elevated:
            level = EmergencyLevel.ELEVATED
            position_reduction = 0.75
            stop_widening = 1.25
            new_entries_blocked = False
            spike_detected = False
        else:
            level = EmergencyLevel.NORMAL
            position_reduction = 1.0
            stop_widening = 1.0
            new_entries_blocked = False
            spike_detected = False
        
        return VolatilityResponse(
            current_volatility=current_vol,
            volatility_percentile=float(percentile[0]) if len(percentile) > 0 else 50,
            spike_detected=spike_detected,
            response_level=level,
            position_reduction=position_reduction,
            stop_widening=stop_widening,
            new_entries_blocked=new_entries_blocked
        )
    
    async def _check_liquidity(self, prices: List[float], volumes: List[float]) -> LiquidityCrisisManager:
        """Check for liquidity crisis"""
        if not volumes or len(volumes) < 10:
            return LiquidityCrisisManager(
                liquidity_score=0.7,
                crisis_detected=False,
                response_level=EmergencyLevel.NORMAL,
                exit_priority=[],
                alternative_venues=[],
                slippage_tolerance=0.001
            )
        
        volume_array = np.array(volumes)
        avg_volume = np.mean(volume_array)
        recent_volume = np.mean(volume_array[-5:])
        
        # Liquidity score (0-1)
        liquidity_score = min(1.0, recent_volume / avg_volume) if avg_volume > 0 else 0.5
        
        # Determine crisis level
        if liquidity_score < 0.2:
            level = EmergencyLevel.CRITICAL
            crisis_detected = True
            slippage_tolerance = 0.01
        elif liquidity_score < 0.4:
            level = EmergencyLevel.HIGH
            crisis_detected = True
            slippage_tolerance = 0.005
        elif liquidity_score < 0.6:
            level = EmergencyLevel.ELEVATED
            crisis_detected = False
            slippage_tolerance = 0.002
        else:
            level = EmergencyLevel.NORMAL
            crisis_detected = False
            slippage_tolerance = 0.001
        
        return LiquidityCrisisManager(
            liquidity_score=liquidity_score,
            crisis_detected=crisis_detected,
            response_level=level,
            exit_priority=['reduce_largest', 'close_losers', 'hedge'],
            alternative_venues=['primary', 'secondary', 'dark_pool'],
            slippage_tolerance=slippage_tolerance
        )
    
    async def _check_flash_crash(self) -> bool:
        """Check for flash crash conditions"""
        if len(self.price_history) < 10:
            return False
        
        # Get prices from last N minutes
        cutoff = datetime.now() - timedelta(minutes=self.flash_crash_window)
        recent_prices = [
            p['price'] for p in self.price_history
            if p['timestamp'] > cutoff
        ]
        
        if len(recent_prices) < 2:
            return False
        
        # Check for rapid price movement
        price_change = abs(recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        if price_change > self.flash_crash_threshold:
            logger.warning(f"Flash crash detected: {price_change:.2%} in {self.flash_crash_window} minutes")
            return True
        
        return False
    
    async def _trigger_emergency_protocols(
        self,
        volatility: VolatilityResponse,
        liquidity: LiquidityCrisisManager,
        flash_crash: bool
    ):
        """Trigger emergency response protocols"""
        event_id = f"emg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        actions = []
        
        # Determine emergency type
        if flash_crash:
            event_type = EmergencyType.FLASH_CRASH
            description = "Flash crash detected"
            actions.append("Halt all trading")
            actions.append("Close all positions at market")
            actions.append("Activate circuit breaker")
        elif volatility.spike_detected:
            event_type = EmergencyType.VOLATILITY_SPIKE
            description = f"Volatility spike: {volatility.current_volatility:.4f}"
            actions.append(f"Reduce positions by {(1-volatility.position_reduction)*100:.0f}%")
            actions.append(f"Widen stops by {volatility.stop_widening:.1f}x")
            if volatility.new_entries_blocked:
                actions.append("Block new entries")
        elif liquidity.crisis_detected:
            event_type = EmergencyType.LIQUIDITY_CRISIS
            description = f"Liquidity crisis: score {liquidity.liquidity_score:.2f}"
            actions.append("Prioritize exits")
            actions.append(f"Increase slippage tolerance to {liquidity.slippage_tolerance:.4f}")
            actions.append("Route to alternative venues")
        else:
            return
        
        # Create emergency event
        event = EmergencyEvent(
            event_id=event_id,
            event_type=event_type,
            level=self.current_level,
            description=description,
            actions_taken=actions,
            resolved=False,
            start_time=datetime.now()
        )
        
        self.active_emergencies[event_id] = event
        self.emergency_history.append(event)
        
        # Trip circuit breaker if critical
        if self.current_level == EmergencyLevel.CRITICAL:
            self.circuit_breaker_trips += 1
            if self.circuit_breaker_trips >= self.circuit_breaker_threshold:
                self.circuit_breaker_until = datetime.now() + timedelta(minutes=self.circuit_breaker_cooldown)
                actions.append(f"Circuit breaker tripped until {self.circuit_breaker_until}")
        
        # Notify callbacks
        for callback in self.emergency_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Emergency callback error: {e}")
        
        logger.warning(f"Emergency triggered: {event_type.value} - {description}")
    
    def is_trading_allowed(self) -> tuple:
        """Check if trading is allowed"""
        reasons = []
        
        # Check circuit breaker
        if self.circuit_breaker_until and datetime.now() < self.circuit_breaker_until:
            return False, [f"Circuit breaker active until {self.circuit_breaker_until}"]
        
        # Check emergency level
        if self.current_level == EmergencyLevel.EMERGENCY:
            return False, ["Emergency level active"]
        
        if self.current_level == EmergencyLevel.CRITICAL:
            return False, ["Critical emergency level"]
        
        # Check active emergencies
        active_critical = [e for e in self.active_emergencies.values() 
                         if not e.resolved and e.level in [EmergencyLevel.CRITICAL, EmergencyLevel.EMERGENCY]]
        if active_critical:
            return False, [f"Active critical emergencies: {len(active_critical)}"]
        
        return True, []
    
    def resolve_emergency(self, event_id: str):
        """Resolve an emergency event"""
        if event_id in self.active_emergencies:
            event = self.active_emergencies[event_id]
            event.resolved = True
            event.end_time = datetime.now()
            logger.info(f"Emergency resolved: {event_id}")
    
    def register_callback(self, callback: Callable):
        """Register emergency callback"""
        self.emergency_callbacks.append(callback)
    
    def get_emergency_status(self) -> Dict[str, Any]:
        """Get current emergency status"""
        return {
            'current_level': self.current_level.value,
            'active_emergencies': len([e for e in self.active_emergencies.values() if not e.resolved]),
            'circuit_breaker_trips': self.circuit_breaker_trips,
            'circuit_breaker_until': self.circuit_breaker_until.isoformat() if self.circuit_breaker_until else None,
            'trading_allowed': self.is_trading_allowed()[0],
            'recent_events': [e.to_dict() for e in list(self.emergency_history)[-10:]]
        }
    
    async def emergency_close_all(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Emergency close all positions"""
        logger.warning("EMERGENCY: Closing all positions")
        
        results = []
        for position in positions:
            result = {
                'symbol': position.get('symbol'),
                'action': 'EMERGENCY_CLOSE',
                'size': position.get('size'),
                'status': 'PENDING',
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        return results
