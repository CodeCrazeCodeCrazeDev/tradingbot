"""
AlphaAlgo MSOS - Learning Firewall

You are forbidden from learning directly from:
- Black swan events
- Liquidity vacuums
- Tail events

These events are logged, analyzed, and isolated — never generalized.
Learning from extremes poisons models.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ExtremeEvent(Enum):
    """Types of extreme events that block learning"""
    BLACK_SWAN = auto()          # Unprecedented market event
    LIQUIDITY_VACUUM = auto()    # Sudden liquidity disappearance
    TAIL_EVENT = auto()          # Extreme return (>3 sigma)
    FLASH_CRASH = auto()         # Rapid price collapse
    CORRELATION_SPIKE = auto()   # Sudden correlation convergence
    VOLATILITY_EXPLOSION = auto() # Extreme volatility spike
    STRUCTURAL_BREAK = auto()    # Fundamental market structure change
    DATA_ANOMALY = auto()        # Suspicious data quality


class LearningState(Enum):
    """Learning system states"""
    ACTIVE = auto()           # Normal learning
    PAUSED = auto()           # Temporarily paused
    FROZEN = auto()           # Frozen due to extreme event
    QUARANTINED = auto()      # Data quarantined, no learning
    DISABLED = auto()         # Learning disabled


@dataclass
class PoisonedLearning:
    """Record of poisoned learning attempt"""
    event_type: ExtremeEvent
    event_data: Dict[str, Any]
    timestamp: float
    severity: float  # 0-1
    reason: str
    data_quarantined: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type.name,
            'timestamp': self.timestamp,
            'severity': self.severity,
            'reason': self.reason,
            'data_quarantined': self.data_quarantined
        }


@dataclass
class FirewallResult:
    """Result from learning firewall check"""
    state: LearningState
    can_learn: bool
    data_allowed: bool
    reason: str
    detected_events: List[ExtremeEvent]
    quarantined_data: List[Dict[str, Any]]
    freeze_duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.name,
            'can_learn': self.can_learn,
            'data_allowed': self.data_allowed,
            'reason': self.reason,
            'detected_events': [e.name for e in self.detected_events],
            'quarantined_count': len(self.quarantined_data),
            'freeze_duration_seconds': self.freeze_duration_seconds,
            'timestamp': self.timestamp
        }


class ExtremeEventDetector:
    """Detects extreme events that should block learning"""
    
    def __init__(self, window_size: int = 252):
        try:
            self.window_size = window_size
            self._returns: Deque[float] = deque(maxlen=window_size)
            self._volatility: Deque[float] = deque(maxlen=window_size)
            self._correlations: Deque[float] = deque(maxlen=window_size)
            self._liquidity: Deque[float] = deque(maxlen=window_size)
        
            # Thresholds
            self.tail_threshold = 3.0  # Standard deviations
            self.volatility_threshold = 3.0
            self.correlation_threshold = 0.9
            self.liquidity_threshold = 0.3
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect(self, market_data: Dict[str, Any]) -> List[ExtremeEvent]:
        """Detect extreme events in market data"""
        try:
            events = []
        
            return_value = market_data.get('return', 0.0)
            volatility = market_data.get('volatility', 0.0)
            correlation = market_data.get('correlation', 0.0)
            liquidity = market_data.get('liquidity', 1.0)
        
            self._returns.append(return_value)
            self._volatility.append(volatility)
            self._correlations.append(correlation)
            self._liquidity.append(liquidity)
        
            if len(self._returns) < 30:
                return events
        
            # Check for tail event
            returns = np.array(list(self._returns))
            mean_ret = np.mean(returns)
            std_ret = np.std(returns)
        
            if std_ret > 0:
                z_score = abs(return_value - mean_ret) / std_ret
                if z_score > self.tail_threshold:
                    events.append(ExtremeEvent.TAIL_EVENT)
                    if z_score > 5:
                        events.append(ExtremeEvent.BLACK_SWAN)
        
            # Check for volatility explosion
            vols = np.array(list(self._volatility))
            mean_vol = np.mean(vols)
            std_vol = np.std(vols)
        
            if std_vol > 0:
                vol_z = abs(volatility - mean_vol) / std_vol
                if vol_z > self.volatility_threshold:
                    events.append(ExtremeEvent.VOLATILITY_EXPLOSION)
        
            # Check for correlation spike
            if correlation > self.correlation_threshold:
                events.append(ExtremeEvent.CORRELATION_SPIKE)
        
            # Check for liquidity vacuum
            if liquidity < self.liquidity_threshold:
                events.append(ExtremeEvent.LIQUIDITY_VACUUM)
        
            # Check for flash crash (rapid price decline)
            if len(self._returns) >= 5:
                recent_returns = list(self._returns)[-5:]
                cumulative = sum(recent_returns)
                if cumulative < -0.05:  # 5% decline in 5 periods
                    events.append(ExtremeEvent.FLASH_CRASH)
        
            # Check for data anomaly
            if self._is_data_anomaly(market_data):
                events.append(ExtremeEvent.DATA_ANOMALY)
        
            return events
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise
    
    def _is_data_anomaly(self, data: Dict[str, Any]) -> bool:
        """Check for data quality issues"""
        # Check for missing data
        try:
            if data.get('return') is None:
                return True
        
            # Check for impossible values
            if abs(data.get('return', 0)) > 0.5:  # 50% move
                return True
        
            # Check for stale data
            if data.get('data_age_seconds', 0) > 60:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _is_data_anomaly: {e}")
            raise


class DataQuarantine:
    """Quarantines data from extreme events"""
    
    def __init__(self, max_quarantine_size: int = 1000):
        try:
            self.max_size = max_quarantine_size
            self._quarantined: Deque[Dict[str, Any]] = deque(maxlen=max_quarantine_size)
            self._quarantine_reasons: Dict[str, str] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def quarantine(self, data: Dict[str, Any], reason: str):
        """Quarantine data point"""
        try:
            entry = {
                'data': data,
                'reason': reason,
                'timestamp': time.time()
            }
            self._quarantined.append(entry)
        except Exception as e:
            logger.error(f"Error in quarantine: {e}")
            raise
    
    def get_quarantined(self) -> List[Dict[str, Any]]:
        """Get all quarantined data"""
        return list(self._quarantined)
    
    def get_count(self) -> int:
        """Get count of quarantined data"""
        return len(self._quarantined)
    
    def clear_old(self, max_age_days: int = 30):
        """Clear old quarantined data"""
        try:
            cutoff = time.time() - max_age_days * 86400
            self._quarantined = deque(
                [q for q in self._quarantined if q['timestamp'] > cutoff],
                maxlen=self.max_size
            )
        except Exception as e:
            logger.error(f"Error in clear_old: {e}")
            raise


class LearningFirewall:
    """
    Main Learning Firewall
    
    RULES:
    1. NEVER learn from black swan events
    2. NEVER learn from liquidity vacuums
    3. NEVER learn from tail events
    4. These events are LOGGED, ANALYZED, and ISOLATED
    5. Learning from extremes POISONS models
    """
    
    # Freeze durations (seconds)
    FREEZE_DURATIONS = {
        ExtremeEvent.BLACK_SWAN: 86400,        # 24 hours
        ExtremeEvent.LIQUIDITY_VACUUM: 7200,   # 2 hours
        ExtremeEvent.TAIL_EVENT: 3600,         # 1 hour
        ExtremeEvent.FLASH_CRASH: 14400,       # 4 hours
        ExtremeEvent.CORRELATION_SPIKE: 3600,  # 1 hour
        ExtremeEvent.VOLATILITY_EXPLOSION: 7200,  # 2 hours
        ExtremeEvent.STRUCTURAL_BREAK: 86400,  # 24 hours
        ExtremeEvent.DATA_ANOMALY: 1800,       # 30 minutes
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.firewall")
        
            # Components
            self._detector = ExtremeEventDetector()
            self._quarantine = DataQuarantine()
        
            # State
            self._state = LearningState.ACTIVE
            self._freeze_until: Optional[float] = None
            self._freeze_reason: str = ""
            self._poisoned_attempts: List[PoisonedLearning] = []
            self._event_history: Deque[Tuple[float, ExtremeEvent]] = deque(maxlen=1000)
        
            self.logger.info("Learning Firewall initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check(self, market_data: Dict[str, Any]) -> FirewallResult:
        """
        Check if learning is allowed with current data.
        
        If extreme events detected, learning is blocked and data quarantined.
        """
        # Detect extreme events
        try:
            events = self._detector.detect(market_data)
        
            # Record events
            for event in events:
                self._event_history.append((time.time(), event))
        
            # Check if currently frozen
            if self._freeze_until and time.time() < self._freeze_until:
                remaining = self._freeze_until - time.time()
                return FirewallResult(
                    state=LearningState.FROZEN,
                    can_learn=False,
                    data_allowed=False,
                    reason=f"Learning frozen: {self._freeze_reason}",
                    detected_events=events,
                    quarantined_data=self._quarantine.get_quarantined(),
                    freeze_duration_seconds=remaining
                )
            elif self._freeze_until:
                # Freeze expired
                self._freeze_until = None
                self._freeze_reason = ""
                self._state = LearningState.ACTIVE
        
            # Handle detected events
            if events:
                # Quarantine data
                reason = f"Extreme events: {[e.name for e in events]}"
                self._quarantine.quarantine(market_data, reason)
            
                # Record poisoned attempt
                for event in events:
                    self._poisoned_attempts.append(PoisonedLearning(
                        event_type=event,
                        event_data=market_data,
                        timestamp=time.time(),
                        severity=self._calculate_severity(event),
                        reason=reason
                    ))
            
                # Freeze learning
                max_freeze = max(self.FREEZE_DURATIONS.get(e, 3600) for e in events)
                self._freeze_until = time.time() + max_freeze
                self._freeze_reason = reason
                self._state = LearningState.FROZEN
            
                self.logger.warning(
                    f"LEARNING BLOCKED: {reason} | Freeze: {max_freeze}s"
                )
            
                return FirewallResult(
                    state=LearningState.FROZEN,
                    can_learn=False,
                    data_allowed=False,
                    reason=reason,
                    detected_events=events,
                    quarantined_data=self._quarantine.get_quarantined(),
                    freeze_duration_seconds=max_freeze
                )
        
            # No extreme events - learning allowed
            return FirewallResult(
                state=self._state,
                can_learn=True,
                data_allowed=True,
                reason="Learning allowed",
                detected_events=[],
                quarantined_data=[]
            )
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise
    
    def _calculate_severity(self, event: ExtremeEvent) -> float:
        """Calculate severity of extreme event"""
        try:
            severities = {
                ExtremeEvent.BLACK_SWAN: 1.0,
                ExtremeEvent.LIQUIDITY_VACUUM: 0.9,
                ExtremeEvent.FLASH_CRASH: 0.9,
                ExtremeEvent.STRUCTURAL_BREAK: 0.95,
                ExtremeEvent.TAIL_EVENT: 0.7,
                ExtremeEvent.VOLATILITY_EXPLOSION: 0.8,
                ExtremeEvent.CORRELATION_SPIKE: 0.6,
                ExtremeEvent.DATA_ANOMALY: 0.5,
            }
            return severities.get(event, 0.5)
        except Exception as e:
            logger.error(f"Error in _calculate_severity: {e}")
            raise
    
    def force_freeze(self, reason: str, duration_seconds: int = 3600):
        """Force freeze learning"""
        try:
            self._freeze_until = time.time() + duration_seconds
            self._freeze_reason = reason
            self._state = LearningState.FROZEN
            self.logger.critical(f"LEARNING FORCE FROZEN: {reason}")
        except Exception as e:
            logger.error(f"Error in force_freeze: {e}")
            raise
    
    def unfreeze(self) -> bool:
        """Attempt to unfreeze learning"""
        try:
            if self._freeze_until and time.time() < self._freeze_until:
                self.logger.warning("Cannot unfreeze - freeze period not expired")
                return False
        
            self._freeze_until = None
            self._freeze_reason = ""
            self._state = LearningState.ACTIVE
            self.logger.info("Learning unfrozen")
            return True
        except Exception as e:
            logger.error(f"Error in unfreeze: {e}")
            raise
    
    def get_state(self) -> LearningState:
        """Get current learning state"""
        return self._state
    
    def can_learn(self) -> bool:
        """Check if learning is currently allowed"""
        try:
            if self._freeze_until and time.time() < self._freeze_until:
                return False
            return self._state == LearningState.ACTIVE
        except Exception as e:
            logger.error(f"Error in can_learn: {e}")
            raise
    
    def get_poisoned_attempts(self) -> List[PoisonedLearning]:
        """Get list of poisoned learning attempts"""
        return self._poisoned_attempts.copy()
    
    def get_event_history(self, hours: float = 24) -> List[Tuple[float, ExtremeEvent]]:
        """Get recent extreme event history"""
        try:
            cutoff = time.time() - hours * 3600
            return [(t, e) for t, e in self._event_history if t > cutoff]
        except Exception as e:
            logger.error(f"Error in get_event_history: {e}")
            raise
    
    def get_quarantine_stats(self) -> Dict[str, Any]:
        """Get quarantine statistics"""
        return {
            'quarantined_count': self._quarantine.get_count(),
            'poisoned_attempts': len(self._poisoned_attempts),
            'is_frozen': self._state == LearningState.FROZEN,
            'freeze_reason': self._freeze_reason,
            'freeze_remaining': max(0, (self._freeze_until or 0) - time.time())
        }
