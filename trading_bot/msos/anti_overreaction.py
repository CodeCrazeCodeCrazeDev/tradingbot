"""
AlphaAlgo MSOS - Anti-Overreaction Constraints

You are forbidden from reacting impulsively.

Enforce:
- Evidence thresholds before changes
- Cooldown periods after losses
- Rate limits on parameter updates

Stability dominates responsiveness.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Set

import numpy as np

logger = logging.getLogger(__name__)


class ReactionType(Enum):
    """Types of reactions that need control"""
    PARAMETER_CHANGE = auto()
    SIZE_INCREASE = auto()
    SIZE_DECREASE = auto()
    STRATEGY_ENABLE = auto()
    STRATEGY_DISABLE = auto()
    EXPOSURE_INCREASE = auto()
    EXPOSURE_DECREASE = auto()
    LEARNING_UPDATE = auto()


class ReactionStatus(Enum):
    """Status of a reaction request"""
    ALLOWED = auto()
    BLOCKED_COOLDOWN = auto()
    BLOCKED_EVIDENCE = auto()
    BLOCKED_RATE_LIMIT = auto()
    BLOCKED_STABILITY = auto()
    PENDING = auto()


@dataclass
class EvidenceThreshold:
    """Evidence threshold for changes"""
    reaction_type: ReactionType
    min_observations: int = 20
    min_confidence: float = 0.8
    min_statistical_significance: float = 0.95
    current_observations: int = 0
    current_confidence: float = 0.0
    is_met: bool = False
    
    def check(self, observations: int, confidence: float) -> bool:
        """Check if evidence threshold is met"""
        try:
            self.current_observations = observations
            self.current_confidence = confidence
            self.is_met = (
                observations >= self.min_observations and
                confidence >= self.min_confidence
            )
            return self.is_met
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


@dataclass
class CooldownPeriod:
    """Cooldown period after events"""
    event_type: str
    duration_seconds: int
    start_time: Optional[float] = None
    is_active: bool = False
    
    def activate(self):
        """Activate cooldown"""
        try:
            self.start_time = time.time()
            self.is_active = True
        except Exception as e:
            logger.error(f"Error in activate: {e}")
            raise
    
    def check(self) -> bool:
        """Check if cooldown is still active"""
        try:
            if not self.is_active or self.start_time is None:
                return False
        
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration_seconds:
                self.is_active = False
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise
    
    def remaining_seconds(self) -> float:
        """Get remaining cooldown time"""
        try:
            if not self.is_active or self.start_time is None:
                return 0.0
        
            elapsed = time.time() - self.start_time
            return max(0, self.duration_seconds - elapsed)
        except Exception as e:
            logger.error(f"Error in remaining_seconds: {e}")
            raise


@dataclass
class ChangeRateLimit:
    """Rate limit for changes"""
    reaction_type: ReactionType
    max_changes_per_hour: int = 3
    max_changes_per_day: int = 10
    change_timestamps: List[float] = field(default_factory=list)
    
    def can_change(self) -> bool:
        """Check if change is allowed under rate limit"""
        try:
            now = time.time()
        
            # Clean old timestamps
            hour_ago = now - 3600
            day_ago = now - 86400
            self.change_timestamps = [t for t in self.change_timestamps if t > day_ago]
        
            # Count recent changes
            hourly_changes = sum(1 for t in self.change_timestamps if t > hour_ago)
            daily_changes = len(self.change_timestamps)
        
            return (
                hourly_changes < self.max_changes_per_hour and
                daily_changes < self.max_changes_per_day
            )
        except Exception as e:
            logger.error(f"Error in can_change: {e}")
            raise
    
    def record_change(self):
        """Record a change"""
        try:
            self.change_timestamps.append(time.time())
        except Exception as e:
            logger.error(f"Error in record_change: {e}")
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """Get rate limit statistics"""
        try:
            now = time.time()
            hour_ago = now - 3600
        
            hourly = sum(1 for t in self.change_timestamps if t > hour_ago)
            daily = len(self.change_timestamps)
        
            return {
                'hourly_changes': hourly,
                'hourly_remaining': self.max_changes_per_hour - hourly,
                'daily_changes': daily,
                'daily_remaining': self.max_changes_per_day - daily
            }
        except Exception as e:
            logger.error(f"Error in get_stats: {e}")
            raise


@dataclass
class OverreactionResult:
    """Result from anti-overreaction check"""
    reaction_type: ReactionType
    status: ReactionStatus
    is_allowed: bool
    reason: str
    evidence: Optional[EvidenceThreshold] = None
    cooldown: Optional[CooldownPeriod] = None
    rate_limit: Optional[ChangeRateLimit] = None
    wait_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reaction_type': self.reaction_type.name,
            'status': self.status.name,
            'is_allowed': self.is_allowed,
            'reason': self.reason,
            'wait_seconds': self.wait_seconds,
            'timestamp': self.timestamp
        }


class StabilityMonitor:
    """Monitors system stability to prevent changes during instability"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._returns: Deque[float] = deque(maxlen=window_size)
            self._changes: Deque[float] = deque(maxlen=window_size)
            self._stability_score: float = 1.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, return_value: float):
        """Update with new return"""
        try:
            self._returns.append(return_value)
        
            if len(self._returns) >= 20:
                recent = list(self._returns)[-20:]
                volatility = np.std(recent)
            
                # Stability is inverse of volatility
                self._stability_score = max(0, 1 - volatility * 10)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def record_change(self):
        """Record a system change"""
        try:
            self._changes.append(time.time())
        except Exception as e:
            logger.error(f"Error in record_change: {e}")
            raise
    
    def get_stability(self) -> float:
        """Get current stability score (0-1)"""
        return self._stability_score
    
    def is_stable(self, threshold: float = 0.5) -> bool:
        """Check if system is stable enough for changes"""
        return self._stability_score >= threshold
    
    def get_recent_change_count(self, hours: float = 1.0) -> int:
        """Get number of changes in recent period"""
        try:
            cutoff = time.time() - hours * 3600
            return sum(1 for t in self._changes if t > cutoff)
        except Exception as e:
            logger.error(f"Error in get_recent_change_count: {e}")
            raise


class AntiOverreactionEngine:
    """
    Main Anti-Overreaction Engine
    
    RULES:
    1. Evidence thresholds MUST be met before changes
    2. Cooldown periods MUST be respected after losses
    3. Rate limits MUST be enforced on all changes
    4. Stability DOMINATES responsiveness
    """
    
    # Default cooldown periods (seconds)
    DEFAULT_COOLDOWNS = {
        'loss': 3600,           # 1 hour after loss
        'drawdown': 7200,       # 2 hours after drawdown
        'volatility_spike': 1800,  # 30 min after vol spike
        'strategy_change': 900,    # 15 min after strategy change
        'parameter_change': 600,   # 10 min after param change
    }
    
    # Default rate limits
    DEFAULT_RATE_LIMITS = {
        ReactionType.PARAMETER_CHANGE: (3, 10),  # (per hour, per day)
        ReactionType.SIZE_INCREASE: (2, 5),
        ReactionType.SIZE_DECREASE: (5, 20),
        ReactionType.STRATEGY_ENABLE: (1, 3),
        ReactionType.STRATEGY_DISABLE: (3, 10),
        ReactionType.EXPOSURE_INCREASE: (2, 5),
        ReactionType.EXPOSURE_DECREASE: (5, 20),
        ReactionType.LEARNING_UPDATE: (1, 3),
    }
    
    # Default evidence thresholds
    DEFAULT_EVIDENCE = {
        ReactionType.PARAMETER_CHANGE: (30, 0.9),  # (observations, confidence)
        ReactionType.SIZE_INCREASE: (50, 0.95),
        ReactionType.SIZE_DECREASE: (10, 0.7),
        ReactionType.STRATEGY_ENABLE: (100, 0.95),
        ReactionType.STRATEGY_DISABLE: (20, 0.8),
        ReactionType.EXPOSURE_INCREASE: (30, 0.9),
        ReactionType.EXPOSURE_DECREASE: (10, 0.7),
        ReactionType.LEARNING_UPDATE: (50, 0.9),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.anti_overreaction")
        
            # Cooldowns
            self._cooldowns: Dict[str, CooldownPeriod] = {}
            for event_type, duration in self.DEFAULT_COOLDOWNS.items():
                self._cooldowns[event_type] = CooldownPeriod(event_type, duration)
        
            # Rate limits
            self._rate_limits: Dict[ReactionType, ChangeRateLimit] = {}
            for reaction_type, (hourly, daily) in self.DEFAULT_RATE_LIMITS.items():
                self._rate_limits[reaction_type] = ChangeRateLimit(
                    reaction_type, hourly, daily
                )
        
            # Evidence thresholds
            self._evidence: Dict[ReactionType, EvidenceThreshold] = {}
            for reaction_type, (obs, conf) in self.DEFAULT_EVIDENCE.items():
                self._evidence[reaction_type] = EvidenceThreshold(
                    reaction_type, obs, conf
                )
        
            # Stability monitor
            self._stability = StabilityMonitor()
        
            # Pending reactions
            self._pending: Dict[str, Dict[str, Any]] = {}
        
            self.logger.info("Anti-Overreaction Engine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_reaction(
        self,
        reaction_type: ReactionType,
        observations: int = 0,
        confidence: float = 0.0,
        force: bool = False
    ) -> OverreactionResult:
        """
        Check if a reaction is allowed.
        
        Returns OverreactionResult with status and reason.
        """
        # Check cooldowns first
        try:
            for event_type, cooldown in self._cooldowns.items():
                if cooldown.check():
                    return OverreactionResult(
                        reaction_type=reaction_type,
                        status=ReactionStatus.BLOCKED_COOLDOWN,
                        is_allowed=False,
                        reason=f"Cooldown active: {event_type} ({cooldown.remaining_seconds():.0f}s remaining)",
                        cooldown=cooldown,
                        wait_seconds=cooldown.remaining_seconds()
                    )
        
            # Check rate limits
            rate_limit = self._rate_limits.get(reaction_type)
            if rate_limit and not rate_limit.can_change():
                stats = rate_limit.get_stats()
                return OverreactionResult(
                    reaction_type=reaction_type,
                    status=ReactionStatus.BLOCKED_RATE_LIMIT,
                    is_allowed=False,
                    reason=f"Rate limit exceeded: {stats['hourly_changes']}/{rate_limit.max_changes_per_hour} hourly",
                    rate_limit=rate_limit,
                    wait_seconds=3600  # Wait an hour
                )
        
            # Check stability (except for decreases which are always allowed)
            if reaction_type not in [ReactionType.SIZE_DECREASE, ReactionType.EXPOSURE_DECREASE]:
                if not self._stability.is_stable(0.5):
                    return OverreactionResult(
                        reaction_type=reaction_type,
                        status=ReactionStatus.BLOCKED_STABILITY,
                        is_allowed=False,
                        reason=f"System unstable: stability={self._stability.get_stability():.2f}",
                        wait_seconds=1800  # Wait 30 min
                    )
        
            # Check evidence thresholds
            evidence = self._evidence.get(reaction_type)
            if evidence and not force:
                if not evidence.check(observations, confidence):
                    return OverreactionResult(
                        reaction_type=reaction_type,
                        status=ReactionStatus.BLOCKED_EVIDENCE,
                        is_allowed=False,
                        reason=f"Evidence insufficient: {observations}/{evidence.min_observations} obs, {confidence:.1%}/{evidence.min_confidence:.1%} conf",
                        evidence=evidence
                    )
        
            # All checks passed
            return OverreactionResult(
                reaction_type=reaction_type,
                status=ReactionStatus.ALLOWED,
                is_allowed=True,
                reason="Reaction allowed",
                evidence=evidence,
                rate_limit=rate_limit
            )
        except Exception as e:
            logger.error(f"Error in check_reaction: {e}")
            raise
    
    def record_reaction(self, reaction_type: ReactionType):
        """Record that a reaction occurred"""
        try:
            rate_limit = self._rate_limits.get(reaction_type)
            if rate_limit:
                rate_limit.record_change()
        
            self._stability.record_change()
        
            # Activate cooldown for strategy/parameter changes
            if reaction_type in [ReactionType.STRATEGY_ENABLE, ReactionType.STRATEGY_DISABLE]:
                self._cooldowns['strategy_change'].activate()
            elif reaction_type == ReactionType.PARAMETER_CHANGE:
                self._cooldowns['parameter_change'].activate()
        
            self.logger.info(f"Reaction recorded: {reaction_type.name}")
        except Exception as e:
            logger.error(f"Error in record_reaction: {e}")
            raise
    
    def trigger_cooldown(self, event_type: str, duration_seconds: Optional[int] = None):
        """Trigger a cooldown period"""
        try:
            if event_type not in self._cooldowns:
                duration = duration_seconds or 3600
                self._cooldowns[event_type] = CooldownPeriod(event_type, duration)
        
            self._cooldowns[event_type].activate()
            self.logger.info(f"Cooldown triggered: {event_type}")
        except Exception as e:
            logger.error(f"Error in trigger_cooldown: {e}")
            raise
    
    def update_stability(self, return_value: float):
        """Update stability monitor with new return"""
        try:
            self._stability.update(return_value)
        except Exception as e:
            logger.error(f"Error in update_stability: {e}")
            raise
    
    def get_stability(self) -> float:
        """Get current stability score"""
        return self._stability.get_stability()
    
    def get_active_cooldowns(self) -> List[Dict[str, Any]]:
        """Get list of active cooldowns"""
        try:
            active = []
            for event_type, cooldown in self._cooldowns.items():
                if cooldown.check():
                    active.append({
                        'event_type': event_type,
                        'remaining_seconds': cooldown.remaining_seconds()
                    })
            return active
        except Exception as e:
            logger.error(f"Error in get_active_cooldowns: {e}")
            raise
    
    def get_rate_limit_stats(self) -> Dict[str, Dict[str, int]]:
        """Get rate limit statistics for all reaction types"""
        return {
            rt.name: rl.get_stats()
            for rt, rl in self._rate_limits.items()
        }
    
    def force_cooldown_all(self, reason: str, duration_seconds: int = 3600):
        """Force cooldown on all reactions"""
        try:
            self.logger.critical(f"FORCE COOLDOWN ALL: {reason}")
            for event_type in self._cooldowns:
                self._cooldowns[event_type] = CooldownPeriod(event_type, duration_seconds)
                self._cooldowns[event_type].activate()
        except Exception as e:
            logger.error(f"Error in force_cooldown_all: {e}")
            raise
